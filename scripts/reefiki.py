#!/usr/bin/env python3
"""
Small local tools for REEFIKI projects.

Markdown stays the source of truth. The SQLite database under .reefiki/ is a
rebuildable search/cache layer.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import posixpath
import re
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from reefiki_memory import (
    AccessBoundaryContext,
    MemoryDecisionTrace,
    PolicySafetyLayer,
    PromotionCandidate,
    RouteDecision,
    build_default_registry,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


SKIP_WIKI_FILES = {"index.md", "log.md", "_schema.md", "_dashboard.md", "_domain.md"}
SKIP_WIKI_DIRS = {"logs"}
CONCEPT_TYPES = {"concept", "decision", "skill", "synthesis", "source_note"}
TYPE_DUPLICATE_COMPATIBILITY = {
    "source": {"source"},
    "entity": {"entity"},
    "concept": {"concept", "decision", "synthesis"},
    "decision": {"concept", "decision", "synthesis"},
    "synthesis": {"concept", "decision", "synthesis"},
    "skill": {"skill"},
}
DUPLICATE_TITLE_STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "by",
    "for",
    "in",
    "of",
    "or",
    "the",
    "to",
    "vs",
    "with",
    "как",
    "для",
    "и",
    "или",
    "между",
    "по",
    "про",
    "что",
}
SECRET_PATTERNS = [
    ".env",
    ".env.*",
    "secrets.*",
    "credentials.*",
    "id_rsa",
    "id_rsa.pub",
    "*.pem",
    "*.key",
    "*.pfx",
    "*.p12",
    ".npmrc",
    ".netrc",
]
SECRET_PARTS = {".aws", ".ssh"}
FORBIDDEN_PARTS = {
    ".git",
    "node_modules",
    "vendor",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".next",
    ".cache",
}
BINARY_EXTS = {
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".iso",
    ".img",
    ".dmg",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    ".mp4",
    ".mov",
    ".mkv",
    ".mp3",
    ".wav",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
}
GLOBAL_MEMOIR_STORE = Path(
    os.environ.get("REEFIKI_MEMOIR_STORE", r"C:\Users\kissl\.codex\memoir-stores\reefiki")
)


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 4 :]
    data: dict[str, object] = {}
    current_key = ""
    for line in raw.splitlines():
        key_match = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if key_match:
            current_key = key_match.group(1)
            value = key_match.group(2).strip()
            data[current_key] = parse_value(value)
            continue
        item_match = re.match(r"^\s*-\s*(.*)$", line)
        if item_match and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(parse_value(item_match.group(1).strip()))
    return data, body


def parse_value(value: str) -> object:
    if value in {"", "null", "Null", "NULL"}:
        return None if value else []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_value(part.strip()) for part in split_inline_list(inner)]
    if value.isdigit():
        return int(value)
    return value.strip("\"'")


def split_inline_list(value: str) -> list[str]:
    parts: list[str] = []
    buf = ""
    in_quote = False
    quote = ""
    for char in value:
        if char in {"'", '"'}:
            if not in_quote:
                in_quote = True
                quote = char
            elif quote == char:
                in_quote = False
        if char == "," and not in_quote:
            parts.append(buf)
            buf = ""
            continue
        buf += char
    if buf:
        parts.append(buf)
    return parts


def as_text(value: object) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def project_root(path: Path) -> Path:
    path = path.resolve()
    if path.name == "wiki":
        return path.parent
    if (path / "wiki").is_dir():
        return path
    raise SystemExit(f"Project root not found: {path}")


def repo_root(path: Path) -> Path:
    path = path.resolve()
    for candidate in [path, *path.parents]:
        if (candidate / "projects").is_dir():
            return candidate
    raise SystemExit(f"REEFIKI root not found: {path}")


def list_projects(root: Path) -> list[Path]:
    projects_dir = root / "projects"
    return sorted(
        path for path in projects_dir.iterdir() if path.is_dir() and path.name != "_template"
    )


def find_project(root: Path, name: str) -> Path:
    normalized = name.strip().lower()
    for path in list_projects(root):
        if path.name.lower() == normalized:
            return path
    raise SystemExit(f"Unknown REEFIKI project: {name}")


def iter_pages(project: Path) -> list[Path]:
    wiki = project / "wiki"
    return sorted(
        p
        for p in wiki.glob("*/*.md")
        if p.name not in SKIP_WIKI_FILES and p.parent.name not in SKIP_WIKI_DIRS
    )


def db_path(project: Path) -> Path:
    state = project / ".reefiki"
    state.mkdir(exist_ok=True)
    return state / "index.sqlite"


def relative(project: Path, path: Path) -> str:
    return path.relative_to(project).as_posix()


def build_index(project: Path) -> int:
    database = db_path(project)
    conn = sqlite3.connect(database)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        DROP TABLE IF EXISTS pages;
        DROP TABLE IF EXISTS pages_fts;
        DROP TABLE IF EXISTS chunks;
        DROP TABLE IF EXISTS chunks_fts;
        DROP TABLE IF EXISTS links;
        CREATE TABLE pages (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            tags TEXT NOT NULL,
            useful_when TEXT NOT NULL,
            sources TEXT NOT NULL,
            file TEXT NOT NULL,
            date_added TEXT NOT NULL,
            use_count INTEGER NOT NULL,
            last_used TEXT,
            body TEXT NOT NULL,
            sha256 TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE pages_fts USING fts5(
            id,
            title,
            tags,
            useful_when,
            body,
            content='pages',
            content_rowid='rowid'
        );
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id TEXT NOT NULL,
            heading_path TEXT NOT NULL,
            content TEXT NOT NULL,
            file TEXT NOT NULL,
            start_line INTEGER NOT NULL
        );
        CREATE VIRTUAL TABLE chunks_fts USING fts5(
            page_id,
            heading_path,
            content,
            content='chunks',
            content_rowid='id'
        );
        CREATE TABLE links (
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            resolved INTEGER NOT NULL,
            file TEXT NOT NULL,
            line INTEGER NOT NULL
        );
        CREATE INDEX idx_links_source ON links(source_id);
        CREATE INDEX idx_links_target ON links(target_id);
        CREATE INDEX idx_chunks_page ON chunks(page_id);
        """
    )
    count = 0
    known_ids: set[str] = set()
    pending_links: list[dict[str, object]] = []
    for page in iter_pages(project):
        text = page.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        page_id = str(fm.get("id") or page.stem)
        known_ids.add(page_id)
        row = {
            "id": page_id,
            "title": as_text(fm.get("title")) or page_id,
            "type": as_text(fm.get("type")) or page.parent.name.rstrip("s"),
            "tags": as_text(fm.get("tags")),
            "useful_when": as_text(fm.get("useful_when")),
            "sources": as_text(fm.get("sources")),
            "file": relative(project, page),
            "date_added": as_text(fm.get("date_added")),
            "use_count": int(fm.get("use_count") or 0),
            "last_used": as_text(fm.get("last_used")) or None,
            "body": body.strip(),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
        conn.execute(
            """
            INSERT INTO pages VALUES (
                :id, :title, :type, :tags, :useful_when, :sources, :file,
                :date_added, :use_count, :last_used, :body, :sha256
            )
            """,
            row,
        )
        rowid = conn.execute("SELECT rowid FROM pages WHERE id = ?", (page_id,)).fetchone()[0]
        conn.execute(
            "INSERT INTO pages_fts(rowid, id, title, tags, useful_when, body) VALUES (?, ?, ?, ?, ?, ?)",
            (rowid, page_id, row["title"], row["tags"], row["useful_when"], row["body"]),
        )
        for chunk in extract_heading_chunks(body):
            cursor = conn.execute(
                """
                INSERT INTO chunks(page_id, heading_path, content, file, start_line)
                VALUES (?, ?, ?, ?, ?)
                """,
                (page_id, chunk["heading_path"], chunk["content"], row["file"], chunk["start_line"]),
            )
            conn.execute(
                "INSERT INTO chunks_fts(rowid, page_id, heading_path, content) VALUES (?, ?, ?, ?)",
                (cursor.lastrowid, page_id, chunk["heading_path"], chunk["content"]),
            )
        for link in extract_wiki_links(body):
            pending_links.append(
                {
                    "source_id": page_id,
                    "target_id": link["target_id"],
                    "kind": link["kind"],
                    "resolved": 0,
                    "file": row["file"],
                    "line": link["line"],
                }
            )
        count += 1
    for link in pending_links:
        link["resolved"] = 1 if as_text(link["target_id"]) in known_ids else 0
        conn.execute(
            """
            INSERT INTO links(source_id, target_id, kind, resolved, file, line)
            VALUES (:source_id, :target_id, :kind, :resolved, :file, :line)
            """,
            link,
        )
    conn.commit()
    conn.close()
    return count


def extract_wiki_links(body: str) -> list[dict[str, object]]:
    links: list[dict[str, object]] = []
    for lineno, line in enumerate(body.splitlines(), 1):
        for match in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", line):
            target = slugify(match.group(1).strip())
            if not target:
                continue
            links.append({"target_id": target, "kind": "wikilink", "line": lineno})
    return links


def extract_heading_chunks(body: str) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    heading_stack: list[tuple[int, str]] = []
    current_lines: list[str] = []
    current_path = "Page"
    start_line = 1

    def flush() -> None:
        content = "\n".join(current_lines).strip()
        if content:
            chunks.append(
                {
                    "heading_path": current_path,
                    "content": content,
                    "start_line": start_line,
                }
            )

    for lineno, line in enumerate(body.splitlines(), 1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).strip()
            heading_stack = [(lvl, text) for lvl, text in heading_stack if lvl < level]
            heading_stack.append((level, title))
            current_path = " > ".join(text for _lvl, text in heading_stack)
            current_lines = []
            start_line = lineno + 1
            continue
        current_lines.append(line)
    flush()
    return chunks


def escape_fts(query: str) -> str:
    # Keep FTS queries in plain token mode; raw hyphens can be parsed as FTS syntax
    # and make user text like "anti-daily-log" fail with "no such column".
    tokens = re.findall(r"\w+", query, flags=re.UNICODE)
    return " OR ".join(tokens) if tokens else query


def search(
    project: Path,
    query: str,
    limit: int,
    page_type: str | None = None,
    tag: str | None = None,
    link_to: str | None = None,
    linked_by: str | None = None,
    orphan: bool = False,
    chunked: bool = False,
) -> list[sqlite3.Row]:
    database = db_path(project)
    if not database.exists():
        build_index(project)
    return search_existing(
        project,
        database,
        query,
        limit,
        page_type=page_type,
        tag=tag,
        link_to=link_to,
        linked_by=linked_by,
        orphan=orphan,
        chunked=chunked,
    )


def search_existing(
    project: Path,
    database: Path,
    query: str,
    limit: int,
    page_type: str | None = None,
    tag: str | None = None,
    link_to: str | None = None,
    linked_by: str | None = None,
    orphan: bool = False,
    chunked: bool = False,
) -> list[sqlite3.Row]:
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    fts_query = escape_fts(query)
    filters: list[str] = []
    params: list[object] = []
    if page_type:
        filters.append("p.type = ?")
        params.append(page_type)
    if tag:
        filters.append("p.tags LIKE ?")
        params.append(f"%{tag}%")
    if link_to:
        filters.append(
            "EXISTS (SELECT 1 FROM links l WHERE l.source_id = p.id AND l.target_id = ?)"
        )
        params.append(slugify(link_to))
    if linked_by:
        filters.append(
            "EXISTS (SELECT 1 FROM links l WHERE l.target_id = p.id AND l.source_id = ?)"
        )
        params.append(slugify(linked_by))
    if orphan:
        filters.append(
            "NOT EXISTS (SELECT 1 FROM links l WHERE l.target_id = p.id AND l.resolved = 1)"
        )
    where_sql = " AND ".join(filters)
    if query.strip():
        fts_table = "chunks_fts" if chunked else "pages_fts"
        where_sql = (f"{fts_table} MATCH ?" + (f" AND {where_sql}" if where_sql else ""))
        params = [fts_query, *params]
        if chunked:
            from_sql = "chunks_fts JOIN chunks c ON c.id = chunks_fts.rowid JOIN pages p ON p.id = c.page_id"
            score_sql = "bm25(chunks_fts, 2.0, 4.0, 5.0) AS score, c.heading_path AS heading_path, c.content AS snippet"
        else:
            from_sql = "pages_fts JOIN pages p ON p.rowid = pages_fts.rowid"
            score_sql = "bm25(pages_fts, 5.0, 4.0, 3.0, 2.0, 1.0) AS score, '' AS heading_path, '' AS snippet"
        order_sql = "score"
    else:
        where_sql = where_sql or "1=1"
        from_sql = "pages p"
        score_sql = "0.0 AS score, '' AS heading_path, '' AS snippet"
        order_sql = "p.title"
    try:
        rows = conn.execute(
            f"""
            SELECT p.*, {score_sql}
            FROM {from_sql}
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT ?
            """,
            (*params, limit * 3 if chunked else limit),
        ).fetchall()
        if chunked:
            seen_ids: set[str] = set()
            deduped: list[sqlite3.Row] = []
            for row in rows:
                row_id = as_text(row["id"])
                if row_id in seen_ids:
                    continue
                seen_ids.add(row_id)
                deduped.append(row)
                if len(deduped) >= limit:
                    break
            return deduped
        return rows
    except sqlite3.OperationalError as exc:
        if "no such table" not in str(exc):
            raise
    finally:
        conn.close()
    build_index(project)
    return search_existing(
        project,
        database,
        query,
        limit,
        page_type=page_type,
        tag=tag,
        link_to=link_to,
        linked_by=linked_by,
        orphan=orphan,
        chunked=chunked,
    )


def print_search(
    project: Path,
    query: str,
    limit: int,
    fmt: str,
    page_type: str | None,
    tag: str | None,
    link_to: str | None,
    linked_by: str | None,
    orphan: bool,
    chunked: bool,
) -> int:
    rows = search(
        project,
        query,
        limit,
        page_type=page_type,
        tag=tag,
        link_to=link_to,
        linked_by=linked_by,
        orphan=orphan,
        chunked=chunked,
    )
    if fmt == "json":
        print(json.dumps([dict(row) for row in rows], ensure_ascii=False, indent=2))
        return 0
    for idx, row in enumerate(rows, 1):
        print(f"{idx}. {row['title']} ({row['file']})")
        print(f"   type: {row['type']} | tags: {row['tags']}")
        print(f"   useful_when: {row['useful_when']}")
        if row["heading_path"]:
            print(f"   heading: {row['heading_path']}")
        print(f"   provenance: page={row['file']} sources={row['sources'] or '-'} sha256={row['sha256'][:12]}")
    if not rows:
        print("No matches.")
    return 0


def best_chunk_context(project: Path, query: str, page_id: str) -> dict[str, str]:
    if not query.strip():
        return {"heading_path": "", "snippet": ""}
    database = db_path(project)
    if not database.exists():
        build_index(project)
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT c.heading_path, c.content AS snippet, bm25(chunks_fts, 2.0, 4.0, 5.0) AS score
            FROM chunks_fts
            JOIN chunks c ON c.id = chunks_fts.rowid
            WHERE chunks_fts MATCH ? AND c.page_id = ?
            ORDER BY score
            LIMIT 1
            """,
            (escape_fts(query), page_id),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        conn.close()
        if "no such table" not in str(exc):
            raise
        build_index(project)
        return best_chunk_context(project, query, page_id)
    finally:
        if conn:
            conn.close()
    if not row:
        return {"heading_path": "", "snippet": ""}
    return {"heading_path": as_text(row["heading_path"]), "snippet": as_text(row["snippet"])}


def classify_path(value: str, project: Path) -> tuple[bool, str]:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        ext = Path(parsed.path).suffix.lower()
        if ext in BINARY_EXTS:
            return False, f"binary-url:{ext}"
        return True, "ok"
    path = Path(value)
    if not path.is_absolute():
        path = project / path
    name = path.name
    lower_parts = {part.lower() for part in path.parts}
    if lower_parts & FORBIDDEN_PARTS:
        return False, "forbidden-directory"
    if lower_parts & SECRET_PARTS:
        return False, "secret-directory"
    for pattern in SECRET_PATTERNS:
        if fnmatch.fnmatch(name.lower(), pattern.lower()):
            return False, "secret-name"
    if path.suffix.lower() in BINARY_EXTS:
        return False, f"binary-file:{path.suffix.lower()}"
    if path.exists() and path.is_file() and path.stat().st_size > 5 * 1024 * 1024:
        return False, "large-file"
    return True, "ok"


def is_url(value: str) -> bool:
    return urlparse(value).scheme in {"http", "https"}


def canonical_url(value: str) -> str:
    parsed = urlparse(value.strip())
    scheme = "https" if parsed.scheme in {"http", "https"} else parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    port = ""
    if parsed.port and not (
        (scheme == "http" and parsed.port == 80) or (scheme == "https" and parsed.port == 443)
    ):
        port = f":{parsed.port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)), doseq=True)
    return urlunparse((scheme, f"{host}{port}", path, "", query, ""))


def extract_urls(text: str) -> list[str]:
    raw_urls = re.findall(r"https?://[^\s<>\]\)\"']+", text)
    return [url.rstrip(".,;:!?") for url in raw_urls]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_project_text_files(project: Path) -> list[Path]:
    files: list[Path] = list(iter_pages(project))
    for root in [project / "inbox", project / "seen"]:
        if root.exists():
            files.extend(path for path in root.rglob("*.md") if path.is_file())
    return sorted(files)


def dedup_check(project: Path, source: str) -> int:
    matches: list[str] = []
    if is_url(source):
        source_url = canonical_url(source)
        for path in iter_project_text_files(project):
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(canonical_url(url) == source_url for url in extract_urls(text)):
                matches.append(f"url:{relative(project, path)}")
    else:
        path = Path(source)
        if not path.is_absolute():
            path = project / path
        if not path.exists() or not path.is_file():
            print(f"Source file not found: {path}")
            return 2
        inbox_same_name = project / "inbox" / path.name
        if inbox_same_name.exists() and inbox_same_name.resolve() != path.resolve():
            matches.append(f"name:{relative(project, inbox_same_name)}")
        source_hash = file_sha256(path)
        for candidate in iter_project_text_files(project):
            if candidate.resolve() == path.resolve():
                continue
            try:
                if file_sha256(candidate) == source_hash:
                    matches.append(f"sha256:{relative(project, candidate)}")
            except OSError:
                continue
    if matches:
        print("Duplicate candidate(s):")
        for match in matches:
            print(f"  {match}")
        return 1
    print("No duplicates found.")
    return 0


def privacy_scan(project: Path) -> int:
    problems: list[str] = []
    for folder in ["inbox", "wiki", "seen"]:
        root = project / folder
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                ok, reason = classify_path(str(path), project)
                if not ok:
                    problems.append(f"{relative(project, path)}: {reason}")
    if problems:
        print("Privacy guard FAILED:")
        for problem in problems:
            print(f"  x {problem}")
        return 1
    print("Privacy guard OK.")
    return 0


def status(project: Path) -> int:
    inbox = sorted(p.name for p in (project / "inbox").glob("*") if p.is_file())
    seen = list((project / "seen").glob("*.md"))
    expired = 0
    active = 0
    today = date.today().isoformat()
    for path in seen:
        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^quarantine_until:\s*(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
        if match and match.group(1) <= today:
            expired += 1
        else:
            active += 1
    counts: Counter[str] = Counter()
    stale = 0
    for page in iter_pages(project):
        fm, _ = parse_frontmatter(page.read_text(encoding="utf-8"))
        counts[as_text(fm.get("type")) or "unknown"] += 1
        date_added = as_text(fm.get("date_added"))
        if int(fm.get("use_count") or 0) == 0 and date_added:
            try:
                age = (date.today() - date.fromisoformat(date_added)).days
                if age > 60:
                    stale += 1
            except ValueError:
                pass
    log = (project / "wiki" / "log.md").read_text(encoding="utf-8", errors="replace")
    last_lint = "never"
    lint_matches = re.findall(r"^## \[(\d{4}-\d{2}-\d{2})\] /lint", log, re.MULTILINE)
    if lint_matches:
        last_lint = lint_matches[-1]
    print(f"Project: {project.name}")
    print(f"Inbox: {len(inbox)}" + (f" ({', '.join(inbox[:5])})" if inbox else ""))
    print(f"Seen: {len(seen)} ({expired} expired, {active} active)")
    print(
        "Wiki: "
        + ", ".join(f"{key}={counts[key]}" for key in sorted(counts))
        + f" | stale={stale}"
    )
    print(f"Last lint: {last_lint}")
    return 0


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9а-яё]+", "-", value, flags=re.IGNORECASE)
    return re.sub(r"-+", "-", value).strip("-") or "plan"


def source_slug(source: str) -> str:
    if is_url(source):
        parsed = urlparse(source)
        value = f"{parsed.netloc}{parsed.path}"
        return slugify(value)
    return slugify(Path(source).stem)


def unique_inbox_path(project: Path, source: str) -> Path:
    inbox = project / "inbox"
    inbox.mkdir(exist_ok=True)
    suffix = ".md" if is_url(source) else Path(source).suffix
    stem = source_slug(source)
    path = inbox / f"{stem}{suffix}"
    counter = 2
    while path.exists():
        path = inbox / f"{stem}-{counter}{suffix}"
        counter += 1
    return path


def append_save_log(project: Path, source: str) -> None:
    log = project / "wiki" / "log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"\n## [{date.today().isoformat()}] /save | {source}\n")


def save_source(project: Path, source: str) -> int:
    ok, reason = classify_path(source, project)
    if not ok:
        print(f"Refused: {reason}")
        return 2
    duplicate_code = dedup_check(project, source)
    if duplicate_code != 0:
        return duplicate_code
    destination = unique_inbox_path(project, source)
    if is_url(source):
        destination.write_text(f"{source}\n", encoding="utf-8")
    else:
        path = Path(source)
        if not path.is_absolute():
            path = project / path
        destination.write_bytes(path.read_bytes())
    append_save_log(project, source)
    inbox_count = len([path for path in (project / "inbox").iterdir() if path.is_file()])
    print(f"Saved: {relative(project, destination)}")
    print(f"Inbox entries: {inbox_count}")
    return 0


def plan_create(project: Path, title: str) -> int:
    plans = project / "plans"
    plans.mkdir(exist_ok=True)
    slug = slugify(title)
    path = plans / f"{slug}.md"
    if path.exists():
        raise SystemExit(f"Plan already exists: {relative(project, path)}")
    body = f"""# {title}

Created: {date.today().isoformat()}
Status: active

## Goal

## Non-goals

## Current State

## Steps

- [ ]

## Decisions

## Evidence

## Recovery Notes

Read this file, `wiki/log.md`, and changed files before resuming.
"""
    checksum = hashlib.sha256(body.encode("utf-8")).hexdigest()
    path.write_text(body + f"\n<!-- reefiki-plan-sha256:{checksum} -->\n", encoding="utf-8")
    print(relative(project, path))
    return 0


def plan_check(project: Path, path_arg: str) -> int:
    path = Path(path_arg)
    if not path.is_absolute():
        path = project / path
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\n<!-- reefiki-plan-sha256:([a-f0-9]{64}) -->\s*$", text)
    if not match:
        print(f"{relative(project, path)}: no checksum")
        return 1
    body = text[: match.start()]
    actual = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if actual != match.group(1):
        print(f"{relative(project, path)}: checksum mismatch")
        return 1
    print(f"{relative(project, path)}: checksum OK")
    return 0


def timeline(project: Path, limit: int) -> int:
    lines = (project / "wiki" / "log.md").read_text(encoding="utf-8", errors="replace").splitlines()
    entries: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("## ["):
            if current:
                entries.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        entries.append("\n".join(current))
    for entry in entries[-limit:]:
        print(entry.rstrip())
        print()
    return 0


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _title_tokens(value: str) -> set[str]:
    tokens = set(re.findall(r"[a-zа-я0-9]+", value.lower(), flags=re.IGNORECASE))
    return {token for token in tokens if len(token) > 2 and token not in DUPLICATE_TITLE_STOP_WORDS}


def _titles_are_similar(left: str, right: str) -> bool:
    left_tokens = _title_tokens(left)
    right_tokens = _title_tokens(right)
    if not left_tokens or not right_tokens:
        return False
    overlap = len(left_tokens & right_tokens)
    ratio = overlap / len(left_tokens | right_tokens)
    return overlap >= 3 or (overlap >= 2 and ratio >= 0.67)


def _is_duplicate_source_signal(source: str) -> bool:
    normalized = _normalize_text(source)
    if not normalized:
        return False
    if normalized.startswith("current-session-"):
        return False
    if normalized.startswith(("session-", "local-session-", "repo-local-")):
        return False
    if re.fullmatch(r"[a-z0-9-]+", normalized):
        return False
    return True


def _wiki_rows(project: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for page in iter_pages(project):
        text = page.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        rows.append(
            {
                "id": as_text(fm.get("id")) or page.stem,
                "type": as_text(fm.get("type")) or page.parent.name.rstrip("s"),
                "title": as_text(fm.get("title")) or page.stem,
                "tags": fm.get("tags") if isinstance(fm.get("tags"), list) else [],
                "useful_when": fm.get("useful_when") if isinstance(fm.get("useful_when"), list) else [],
                "sources": fm.get("sources") if isinstance(fm.get("sources"), list) else [],
                "date_added": as_text(fm.get("date_added")),
                "last_used": as_text(fm.get("last_used")) or None,
                "verified": as_text(fm.get("verified")) or None,
                "file": relative(project, page),
                "body": body.strip(),
            }
        )
    return rows


def project_code_path(project: Path) -> Path | None:
    domain = project / "_domain.md"
    if not domain.exists():
        return None
    text = domain.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^Путь:\s*`([^`]+)`", text, re.MULTILINE)
    if not match:
        match = re.search(r"^- Путь:\s*`([^`]+)`", text, re.MULTILINE)
    if not match:
        return None
    return Path(match.group(1))


def graphify_report_path(project: Path) -> Path | None:
    code_path = project_code_path(project)
    if not code_path:
        return None
    report = code_path / "graphify-out" / "GRAPH_REPORT.md"
    return report if report.exists() else None


def _memoir_base_command(store: Path) -> list[str]:
    return [
        "uvx",
        "--from",
        "memoir-ai",
        "memoir",
        "--json",
        "--store",
        str(store),
    ]


def run_memoir(store: Path, args: list[str]) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        _memoir_base_command(store) + args,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "memoir command failed"
        raise SystemExit(detail)
    output = completed.stdout.strip()
    if not output:
        return {}
    lines = [line for line in output.splitlines() if line.strip()]
    payload = lines[-1]
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid memoir JSON output: {exc}") from exc


def git_staged_paths(repo: Path, env: dict[str, str] | None = None) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git staged path scan failed"
        raise SystemExit(detail)
    return sorted(line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip())


def run_git(repo: Path, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return completed


def require_git_success(completed: subprocess.CompletedProcess[str], fallback: str) -> str:
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or fallback
        raise SystemExit(detail)
    return completed.stdout.strip()


def git_status_paths(repo: Path) -> list[str]:
    completed = run_git(repo, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git status scan failed"
        raise SystemExit(detail)
    output = completed.stdout
    paths: list[str] = []
    entries = output.split("\0") if output else []
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if not entry:
            continue
        status = entry[:2]
        path = entry[3:].replace("\\", "/") if len(entry) > 3 else ""
        if path:
            paths.append(path)
        if "R" in status or "C" in status:
            i += 1
    return sorted(set(paths))


def normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = posixpath.normpath(normalized)
    if normalized in {"", "."} or normalized.startswith("../") or normalized == ".." or normalized.startswith("/"):
        raise SystemExit(f"invalid repo-relative path: {path}")
    return normalized


def guard_staged_payload(repo: Path, target_project: str) -> dict[str, object]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", target_project):
        raise SystemExit("target project must contain only letters, numbers, '_' or '-'")
    allowed_prefix = f"projects/{target_project}/wiki/"
    staged = git_staged_paths(repo)
    blocking = [path for path in staged if not path.startswith(allowed_prefix)]
    return {
        "target_project": target_project,
        "allowed_prefix": allowed_prefix,
        "outcome": "pass" if not blocking else "block",
        "staged_paths": staged,
        "blocking_paths": blocking,
    }


def print_guard_staged(repo: Path, target_project: str, fmt: str) -> int:
    payload = guard_staged_payload(repo, target_project)
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"target_project: {payload['target_project']}")
        print(f"allowed_prefix: {payload['allowed_prefix']}")
        print(f"outcome: {payload['outcome']}")
        print("staged_paths:")
        for path in payload["staged_paths"]:
            print(f"- {path}")
        if payload["blocking_paths"]:
            print("blocking_paths:")
            for path in payload["blocking_paths"]:
                print(f"- {path}")
    return 0 if payload["outcome"] == "pass" else 1


def harvest_commit_payload(
    repo: Path,
    target_project: str,
    paths: list[str],
    message: str,
    validate: bool,
) -> tuple[int, dict[str, object]]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", target_project):
        raise SystemExit("target project must contain only letters, numbers, '_' or '-'")
    if not message.strip():
        raise SystemExit("commit message is required")
    if not paths:
        raise SystemExit("at least one --path is required")

    allowed_prefix = f"projects/{target_project}/wiki/"
    normalized_paths = sorted({normalize_repo_path(path) for path in paths})
    blocking_paths = [path for path in normalized_paths if not path.startswith(allowed_prefix)]
    pre_staged = git_staged_paths(repo)
    already_staged_target_paths = [path for path in pre_staged if path in normalized_paths]
    excluded_dirty_paths = [path for path in git_status_paths(repo) if path not in normalized_paths]

    base_payload: dict[str, object] = {
        "target_project": target_project,
        "allowed_prefix": allowed_prefix,
        "requested_paths": normalized_paths,
        "preexisting_staged_paths": pre_staged,
        "excluded_dirty_paths": excluded_dirty_paths,
    }
    if blocking_paths:
        return 1, {
            **base_payload,
            "outcome": "block",
            "reason": "path_outside_target_wiki",
            "blocking_paths": blocking_paths,
        }
    if already_staged_target_paths:
        return 1, {
            **base_payload,
            "outcome": "block",
            "reason": "target_paths_already_staged",
            "blocking_paths": already_staged_target_paths,
        }

    if validate:
        validator = SCRIPT_DIR / "validate_frontmatter.py"
        if validator.exists():
            completed = subprocess.run(
                [sys.executable, str(validator), str(repo / "projects" / target_project / "wiki")],
                cwd=repo,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            if completed.returncode != 0:
                return 1, {
                    **base_payload,
                    "outcome": "block",
                    "reason": "validation_failed",
                    "validation_output": (completed.stdout + completed.stderr).strip(),
                }

    with tempfile.TemporaryDirectory(prefix="reefiki-harvest-index-") as tempdir:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(Path(tempdir) / "index")
        require_git_success(run_git(repo, ["read-tree", "HEAD"], env=env), "temporary index setup failed")
        require_git_success(run_git(repo, ["add", "--", *normalized_paths], env=env), "temporary harvest staging failed")
        temp_staged = git_staged_paths(repo, env=env)
        temp_blocking = [path for path in temp_staged if not path.startswith(allowed_prefix)]
        if temp_blocking:
            return 1, {
                **base_payload,
                "outcome": "block",
                "reason": "temporary_index_scope_violation",
                "staged_paths": temp_staged,
                "blocking_paths": temp_blocking,
            }
        diff_check = run_git(repo, ["diff", "--cached", "--quiet"], env=env)
        if diff_check.returncode == 0:
            return 1, {
                **base_payload,
                "outcome": "block",
                "reason": "no_changes_to_commit",
                "staged_paths": temp_staged,
                "blocking_paths": [],
            }
        if diff_check.returncode != 1:
            require_git_success(diff_check, "temporary harvest diff failed")
        require_git_success(run_git(repo, ["commit", "-m", message], env=env), "harvest commit failed")

    commit = require_git_success(run_git(repo, ["rev-parse", "--short", "HEAD"]), "commit lookup failed")
    require_git_success(run_git(repo, ["reset", "-q", "HEAD", "--", *normalized_paths]), "post-commit index refresh failed")
    return 0, {
        **base_payload,
        "outcome": "pass",
        "commit": commit,
        "committed_paths": normalized_paths,
        "staged_paths": temp_staged,
        "blocking_paths": [],
    }


def print_harvest_commit(
    repo: Path,
    target_project: str,
    paths: list[str],
    message: str,
    validate: bool,
    fmt: str,
) -> int:
    code, payload = harvest_commit_payload(repo, target_project, paths, message, validate)
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"target_project: {payload['target_project']}")
        print(f"allowed_prefix: {payload['allowed_prefix']}")
        print(f"outcome: {payload['outcome']}")
        if payload.get("reason"):
            print(f"reason: {payload['reason']}")
        if payload.get("commit"):
            print(f"commit: {payload['commit']}")
        print("committed_paths:")
        for path in payload.get("committed_paths", []):
            print(f"- {path}")
        print("excluded_dirty_paths:")
        for path in payload.get("excluded_dirty_paths", []):
            print(f"- {path}")
        if payload.get("blocking_paths"):
            print("blocking_paths:")
            for path in payload["blocking_paths"]:
                print(f"- {path}")
    return code


def private_project_names(repo: Path) -> list[str]:
    config_path = repo / "scripts" / "public-snapshot.private-projects.txt"
    if not config_path.exists():
        return []
    names: list[str] = []
    for line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            names.append(stripped)
    return names


def git_current_branch(repo: Path) -> str:
    branch = require_git_success(run_git(repo, ["branch", "--show-current"]), "current branch lookup failed")
    return branch or "HEAD"


def git_head(repo: Path, short: bool = False) -> str:
    args = ["rev-parse"]
    if short:
        args.append("--short")
    args.append("HEAD")
    return require_git_success(run_git(repo, args), "HEAD lookup failed")


def git_changed_paths(repo: Path, base: str) -> list[str]:
    output = require_git_success(run_git(repo, ["diff", "--name-only", f"{base}...HEAD"]), "changed path scan failed")
    return sorted(line.strip().replace("\\", "/") for line in output.splitlines() if line.strip())


def git_ref_exists(repo: Path, ref: str) -> bool:
    return run_git(repo, ["rev-parse", "--verify", "--quiet", ref]).returncode == 0


def git_is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    return run_git(repo, ["merge-base", "--is-ancestor", ancestor, descendant]).returncode == 0


def classify_publish_diff(paths: list[str], private_projects: list[str]) -> str:
    private_prefixes = tuple(f"projects/{name}/" for name in private_projects)
    private_paths = [path for path in paths if path.startswith(private_prefixes)]
    public_paths = [path for path in paths if not path.startswith(private_prefixes)]
    if private_paths and public_paths:
        return "mixed"
    if private_paths:
        return "private-only"
    if public_paths:
        return "public-safe"
    return "empty"


def publish_task_payload(
    repo: Path,
    base: str,
    private_remote: str,
    public_remote: str,
    dry_run: bool,
    cleanup: bool,
    public_snapshot: bool,
) -> tuple[int, dict[str, object]]:
    branch = git_current_branch(repo)
    status_paths = git_status_paths(repo)
    private_projects = private_project_names(repo)
    if status_paths:
        return 1, {
            "outcome": "block",
            "reason": "dirty_worktree",
            "branch": branch,
            "dirty_paths": status_paths,
        }
    if branch in {"", "HEAD"}:
        return 1, {"outcome": "block", "reason": "detached_head", "branch": branch}
    if not git_ref_exists(repo, base):
        return 1, {"outcome": "block", "reason": "base_ref_missing", "base": base, "branch": branch}

    changed_paths = git_changed_paths(repo, base)
    diff_class = classify_publish_diff(changed_paths, private_projects)
    actions: list[str] = []
    post_merge_actions: list[str] = []
    requires_pr = False
    base_is_ancestor = git_is_ancestor(repo, base, "HEAD")

    if diff_class != "empty":
        actions.append("push_task_branch")
        if base_is_ancestor:
            actions.append("push_private_main")
        else:
            actions.append("create_pr_required")
            requires_pr = True
        if diff_class in {"public-safe", "mixed"}:
            actions.append("push_public_snapshot")
        if cleanup and base_is_ancestor:
            post_merge_actions.append("cleanup_task_worktree")
            post_merge_actions.append("cleanup_task_branch")
    elif public_snapshot:
        actions.append("push_public_snapshot")

    payload: dict[str, object] = {
        "outcome": "pass" if not requires_pr else "block",
        "reason": "create_pr_required" if requires_pr else None,
        "dry_run": dry_run,
        "branch": branch,
        "head": git_head(repo, short=True),
        "base": base,
        "base_is_ancestor": base_is_ancestor,
        "private_remote": private_remote,
        "public_remote": public_remote,
        "private_projects": private_projects,
        "public_snapshot_exclusions": [f"projects/{name}" for name in private_projects if any(path.startswith(f"projects/{name}/") for path in changed_paths)],
        "changed_paths": changed_paths,
        "diff_class": diff_class,
        "actions": actions,
        "post_merge_actions": post_merge_actions,
        "public_snapshot_requested": public_snapshot,
    }
    if dry_run or requires_pr or diff_class == "empty":
        return (1 if requires_pr else 0), payload

    require_git_success(run_git(repo, ["push", private_remote, f"HEAD:{branch}"]), "task branch push failed")
    if base_is_ancestor:
        require_git_success(run_git(repo, ["push", private_remote, "HEAD:main"]), "private main push failed")
    if diff_class in {"public-safe", "mixed"} or public_snapshot:
        push_public_snapshot(repo, public_remote, private_projects)
    payload["applied"] = True
    return 0, payload


def push_public_snapshot(repo: Path, public_remote: str, private_projects: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="reefiki-public-snapshot-") as tempdir:
        snapshot = Path(tempdir) / "snapshot"
        require_git_success(run_git(repo, ["worktree", "add", "--detach", str(snapshot), "HEAD"]), "public snapshot worktree failed")
        try:
            branch = f"public-snapshot-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            require_git_success(run_git(snapshot, ["checkout", "--orphan", branch]), "public snapshot branch failed")
            require_git_success(run_git(snapshot, ["add", "-A"]), "public snapshot staging failed")
            for name in private_projects:
                project_path = snapshot / "projects" / name
                if project_path.exists():
                    require_git_success(
                        run_git(snapshot, ["rm", "-r", "--cached", f"projects/{name}"]),
                        f"public snapshot private project removal failed: {name}",
                    )
            staged = require_git_success(run_git(snapshot, ["diff", "--cached", "--name-only"]), "public snapshot scan failed")
            leaked = [
                path
                for path in staged.splitlines()
                if any(path.startswith(f"projects/{name}/") for name in private_projects)
            ]
            if leaked:
                raise SystemExit(f"public snapshot still contains private paths: {', '.join(leaked)}")
            require_git_success(
                run_git(snapshot, ["commit", "-m", f"public: template snapshot {date.today().isoformat()}"]),
                "public snapshot commit failed",
            )
            require_git_success(run_git(snapshot, ["push", public_remote, "HEAD:main", "--force-with-lease"]), "public snapshot push failed")
        finally:
            run_git(repo, ["worktree", "remove", "--force", str(snapshot)])


def print_publish_task(
    repo: Path,
    base: str,
    private_remote: str,
    public_remote: str,
    dry_run: bool,
    cleanup: bool,
    public_snapshot: bool,
    fmt: str,
) -> int:
    code, payload = publish_task_payload(repo, base, private_remote, public_remote, dry_run, cleanup, public_snapshot)
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"outcome: {payload['outcome']}")
        if payload.get("reason"):
            print(f"reason: {payload['reason']}")
        print(f"branch: {payload.get('branch')}")
        print(f"diff_class: {payload.get('diff_class')}")
        print("actions:")
        for action in payload.get("actions", []):
            print(f"- {action}")
        print("changed_paths:")
        for path in payload.get("changed_paths", []):
            print(f"- {path}")
    return code


def cleanup_worktree_payload(repo: Path, worktree: Path, base: str, dry_run: bool) -> tuple[int, dict[str, object]]:
    target = worktree.resolve()
    if not target.exists():
        return 1, {"outcome": "block", "reason": "worktree_missing", "worktree": str(target)}
    status = git_status_paths(target)
    branch = git_current_branch(target)
    head = git_head(target, short=True)
    payload: dict[str, object] = {
        "worktree": str(target),
        "branch": branch,
        "head": head,
        "base": base,
        "dry_run": dry_run,
    }
    if status:
        return 1, {**payload, "outcome": "block", "reason": "dirty_worktree", "dirty_paths": status}
    if not git_ref_exists(target, base):
        return 1, {**payload, "outcome": "block", "reason": "base_ref_missing"}
    if not git_is_ancestor(target, "HEAD", base):
        return 1, {**payload, "outcome": "block", "reason": "unmerged_worktree_head"}
    if target == repo.resolve():
        return 1, {**payload, "outcome": "block", "reason": "refuse_current_worktree"}
    if dry_run:
        return 0, {**payload, "outcome": "pass", "actions": ["remove_worktree", "delete_local_branch"]}
    require_git_success(run_git(repo, ["worktree", "remove", "--force", str(target)]), "worktree removal failed")
    if branch not in {"", "HEAD", "main"}:
        run_git(repo, ["branch", "-d", branch])
    return 0, {**payload, "outcome": "pass", "removed": True}


def print_cleanup_worktree(repo: Path, worktree: str, base: str, dry_run: bool, fmt: str) -> int:
    code, payload = cleanup_worktree_payload(repo, Path(worktree), base, dry_run)
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"outcome: {payload['outcome']}")
        if payload.get("reason"):
            print(f"reason: {payload['reason']}")
        print(f"worktree: {payload.get('worktree')}")
        print(f"branch: {payload.get('branch')}")
    return code


UNDERSTAND_ANYTHING_TRIGGERS = {
    "visual",
    "graph",
    "knowledge graph",
    "onboarding",
    "large codebase",
    "unknown codebase",
    "wiki graph",
    "understand-knowledge",
    "interactive",
}


def tool_trigger_payload(tool: str, signal: str) -> dict[str, object]:
    normalized_tool = tool.strip().lower()
    normalized_signal = signal.strip().lower()
    guards = [
        "do_not_install_globally",
        "isolated_sandbox_only",
        "no_auto_update_hooks",
        "do_not_commit_generated_graph_without_review",
        "compare_against_graphify_codegraph_reefiki",
    ]
    if normalized_tool not in {"understand-anything", "understand anything"}:
        if normalized_tool == "ecc":
            return {
                "tool": "ECC",
                "outcome": "reference-only",
                "matched_triggers": [],
                "guards": [
                    "do_not_install",
                    "borrow_patterns_only",
                    "avoid_hooks_and_memory_layer_duplication",
                    "keep_reefiki_as_governance_layer",
                ],
                "next_action": "use as pattern reference for trigger gates, readiness snapshots, security checklist or selective install design",
            }
        return {
            "tool": tool,
            "outcome": "unsupported",
            "matched_triggers": [],
            "guards": guards,
            "next_action": "no automation rule exists for this tool",
        }
    matched = sorted(trigger for trigger in UNDERSTAND_ANYTHING_TRIGGERS if trigger in normalized_signal)
    if matched:
        return {
            "tool": "Understand-Anything",
            "outcome": "sandbox-recommended",
            "matched_triggers": matched,
            "guards": guards,
            "next_action": "run isolated sandbox smoke; do not install globally or enable auto-update hooks",
        }
    return {
        "tool": "Understand-Anything",
        "outcome": "watch",
        "matched_triggers": [],
        "guards": guards,
        "next_action": "keep documented as candidate; do not run sandbox smoke yet",
    }


def print_tool_trigger(tool: str, signal: str, fmt: str) -> int:
    payload = tool_trigger_payload(tool, signal)
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["outcome"] != "unsupported" else 1
    print(f"tool: {payload['tool']}")
    print(f"outcome: {payload['outcome']}")
    if payload["matched_triggers"]:
        print(f"matched: {', '.join(payload['matched_triggers'])}")
    print(f"next: {payload['next_action']}")
    return 0 if payload["outcome"] != "unsupported" else 1


def memory_route(text: str, project_hint: str | None = None) -> dict[str, object]:
    normalized = text.strip().lower()
    if not normalized:
        raise SystemExit("Empty content.")
    if any(token in normalized for token in ["where is", "где леж", "структур", "file", "module", "repo map"]):
        return _route_payload(
            RouteDecision(
                recommended_layer="graphify",
                reason="structure/navigation intent",
                target_project=project_hint,
            )
        )
    if any(
        token in normalized
        for token in ["decide", "decision", "решили", "процедур", "policy", "contract", "pack", "handoff"]
    ):
        return _route_payload(
            RouteDecision(
                recommended_layer="reefiki",
                secondary_layers=["graphify"],
                reason="durable decision/procedure intent",
                target_project=project_hint or "reefiki",
                risk_flags=["durable_write_requires_review"],
            )
        )
    if len(normalized) < 160 and any(
        token in normalized for token in ["prefer", "prefers", "from now on", "remember", "предпоч", "правило"]
    ):
        return _route_payload(
            RouteDecision(
                recommended_layer="memoir",
                reason="working preference/rule intent",
                target_project=project_hint,
            )
        )
    return _route_payload(
        RouteDecision(
            recommended_layer="memoir",
            reason="default short working memory",
            target_project=project_hint,
        )
    )


def _route_payload(decision: RouteDecision) -> dict[str, object]:
    payload = decision.to_dict()
    payload["layer"] = payload["recommended_layer"]
    payload["project_hint"] = payload["target_project"]
    return payload


def memory_status(root: Path, project_name: str = "reefiki") -> dict[str, object]:
    project = find_project(root, project_name) if (root / "projects").exists() else root
    registry = build_default_registry(project)
    result = registry.to_dict()
    result["project"] = project.name
    result["policy"] = memory_preflight(
        project=project.name,
        visibility="public",
        operation="status",
        content="",
        paths=[f"projects/{project.name}"],
    )
    report = graphify_report_path(project)
    result["graphify"] = {
        "status": "available" if report else "missing_report",
        "report_path": str(report) if report else None,
        "next_action": None if report else "run graphify only when structural navigation is needed",
    }
    try:
        queue_items = review_queue_scan(project)
        counts = Counter(as_text(item.get("queue_type")) for item in queue_items)
        result["review_queues"] = {
            "total": len(queue_items),
            "counts": dict(sorted(counts.items())),
        }
    except Exception as exc:  # pragma: no cover - defensive status reporting
        result["review_queues"] = {"error": str(exc)}
    try:
        result["promotion_inbox"] = promotion_inbox_summary(project)
    except Exception as exc:  # pragma: no cover - defensive status reporting
        result["promotion_inbox"] = {"error": str(exc)}
    return result


def memory_status_all_projects(root: Path, only_open: bool = False) -> dict[str, object]:
    projects = [
        memory_status(root, project.name)
        for project in list_projects(root)
    ]
    if only_open:
        projects = [
            item for item in projects
            if int(item.get("review_queues", {}).get("total", 0)) > 0
            or int(item.get("promotion_inbox", {}).get("active", 0)) > 0
        ]
    totals = {
        "review_queues": sum(
            int(item.get("review_queues", {}).get("total", 0))
            for item in projects
            if isinstance(item.get("review_queues"), dict)
        ),
        "promotion_active": sum(
            int(item.get("promotion_inbox", {}).get("active", 0))
            for item in projects
            if isinstance(item.get("promotion_inbox"), dict)
        ),
        "promotion_closed": sum(
            int(item.get("promotion_inbox", {}).get("closed", 0))
            for item in projects
            if isinstance(item.get("promotion_inbox"), dict)
        ),
    }
    return {
        "project": "all",
        "only_open": only_open,
        "total": len(projects),
        "totals": totals,
        "projects": projects,
    }


def memory_status_has_open(result: dict[str, object]) -> bool:
    if result.get("project") == "all":
        projects = result.get("projects", [])
        if isinstance(projects, list) and any(
            memory_status_has_open(item)
            for item in projects
            if isinstance(item, dict)
        ):
            return True
        totals = result.get("totals", {})
        if not isinstance(totals, dict):
            return False
        return int(totals.get("review_queues", 0)) > 0 or int(totals.get("promotion_active", 0)) > 0
    queues = result.get("review_queues", {})
    promotion = result.get("promotion_inbox", {})
    if isinstance(queues, dict) and queues.get("error"):
        return True
    if isinstance(promotion, dict) and promotion.get("error"):
        return True
    queue_total = int(queues.get("total", 0)) if isinstance(queues, dict) else 0
    promotion_active = int(promotion.get("active", 0)) if isinstance(promotion, dict) else 0
    return queue_total > 0 or promotion_active > 0


def compact_status_item(item: dict[str, object]) -> dict[str, object]:
    queues = item.get("review_queues", {}) if isinstance(item.get("review_queues"), dict) else {}
    promotion = item.get("promotion_inbox", {}) if isinstance(item.get("promotion_inbox"), dict) else {}
    graphify = item.get("graphify", {}) if isinstance(item.get("graphify"), dict) else {}
    policy = item.get("policy", {}) if isinstance(item.get("policy"), dict) else {}
    return {
        "project": item.get("project"),
        "policy": policy.get("outcome"),
        "graphify": graphify.get("status"),
        "review_queues": queues,
        "promotion_inbox": promotion,
        "has_open": memory_status_has_open(item),
    }


def compact_status_result(result: dict[str, object]) -> dict[str, object]:
    if result.get("project") == "all":
        return {
            "project": "all",
            "summary": True,
            "only_open": result.get("only_open", False),
            "total": result.get("total", 0),
            "totals": result.get("totals", {}),
            "has_open": memory_status_has_open(result),
            "projects": [
                compact_status_item(item)
                for item in result.get("projects", [])
                if isinstance(item, dict)
            ],
        }
    compact = compact_status_item(result)
    compact["summary"] = True
    return compact


def promotion_inbox_summary(project: Path) -> dict[str, object]:
    active = promotion_inbox(project, include_all=False)
    all_drafts = promotion_inbox(project, include_all=True)
    closed_items = [
        item for item in all_drafts.get("drafts", [])
        if isinstance(item, dict) and item.get("review_state") in {"applied", "rejected"}
    ]
    closed_counts = Counter(as_text(item.get("review_state")) for item in closed_items)
    active_count = int(active.get("total", 0))
    closed_count = len(closed_items)
    return {
        "active": active_count,
        "closed": closed_count,
        "total": active_count + closed_count,
        "closed_counts": dict(sorted(closed_counts.items())),
    }


def memory_explain(root: Path, query: str, project_name: str) -> dict[str, object]:
    project = find_project(root, project_name)
    route = memory_route(query, project_hint=project.name)
    policy = memory_preflight(
        project=project.name,
        visibility="private",
        operation="explain",
        content=query,
        paths=[f"projects/{project.name}"],
    )
    registry = build_default_registry(project)
    selected_layers = {as_text(route.get("recommended_layer"))}
    selected_layers.update(as_text(layer) for layer in route.get("secondary_layers", []))
    graph_report = graphify_report_path(project)
    source_decisions: list[dict[str, object]] = []
    for layer in sorted(registry.providers):
        if policy["outcome"] == "block":
            status = "blocked"
            reason = "policy block"
        elif layer == "graphify" and graph_report is None and layer in selected_layers:
            status = "unavailable"
            reason = "missing graphify report"
        elif layer == route.get("recommended_layer"):
            status = "selected"
            reason = as_text(route.get("reason"))
        elif layer in route.get("secondary_layers", []):
            status = "secondary"
            reason = "secondary layer from route"
        else:
            status = "excluded"
            reason = "not selected by route"
        source_decisions.append(
            {
                "layer": layer,
                "status": status,
                "reason": reason,
                "capabilities": [
                    str(capability)
                    for capability in registry.providers[layer].capabilities
                ],
            }
        )
    excluded_sources = [
        as_text(item["layer"])
        for item in source_decisions
        if item["status"] in {"blocked", "excluded", "unavailable"}
    ]
    next_action = f"run memory lookup --project {project.name} --layer {route.get('recommended_layer')}"
    if policy["outcome"] == "block":
        next_action = "resolve policy block before reading providers"
    elif "graphify" in excluded_sources and route.get("recommended_layer") == "graphify":
        next_action = "run graphify only when structural navigation is needed"
    return {
        "query": query,
        "project": project.name,
        "route": route,
        "policy": policy,
        "source_decisions": source_decisions,
        "excluded_sources": excluded_sources,
        "next_action": next_action,
    }


def memory_preflight(
    project: str,
    visibility: str,
    operation: str,
    content: str,
    paths: list[str],
) -> dict[str, object]:
    cross_project_forbidden = [
        scope for scope in ["projects/metrica", "projects/hermes"]
        if scope != f"projects/{project}"
    ]
    boundary = AccessBoundaryContext(
        project=project,
        allowed_scopes=[f"projects/{project}"],
        forbidden_scopes=[*cross_project_forbidden, "secrets", "raw"],
        visibility=visibility,
    )
    return PolicySafetyLayer().preflight(
        boundary,
        operation=operation,
        content=content,
        paths=paths,
    ).to_dict()


def memory_global_strict_preflight(
    project: str,
    visibility: str,
    operation: str,
    content: str,
    paths: list[str],
) -> dict[str, object]:
    boundary = AccessBoundaryContext(
        project=project,
        allowed_scopes=[f"projects/{project}"],
        forbidden_scopes=["projects/metrica", "projects/hermes", "secrets", "raw"],
        visibility=visibility,
    )
    return PolicySafetyLayer().preflight(
        boundary,
        operation=operation,
        content=content,
        paths=paths,
    ).to_dict()


def global_lookup(
    root: Path,
    query: str,
    project: str | None,
    include_memoir: bool,
    include_reefiki: bool,
    include_graph: bool,
    limit: int,
) -> dict[str, object]:
    target_project = project or "reefiki"
    policy = memory_global_strict_preflight(
        project=target_project,
        visibility="private",
        operation="lookup",
        content=query,
        paths=[f"projects/{target_project}"] if project else [],
    )
    result: dict[str, object] = {
        "query": query,
        "policy": policy,
        "memoir": None,
        "reefiki": [],
        "graphify": [],
    }
    if policy["outcome"] == "block":
        return result

    target_projects = [find_project(root, project)] if project else list_projects(root)

    if include_memoir:
        try:
            result["memoir"] = run_memoir(
                GLOBAL_MEMOIR_STORE,
                ["recall", query, "--limit", str(limit), "--threshold", "0.35"],
            )
        except SystemExit as exc:
            result["memoir"] = {"error": str(exc)}

    if include_reefiki:
        reefiki_hits: list[dict[str, object]] = []
        per_project_limit = max(1, limit)
        for project_path in target_projects:
            for row in search(project_path, query, per_project_limit):
                chunk_context = best_chunk_context(project_path, query, as_text(row["id"]))
                reefiki_hits.append(
                    {
                        "project": project_path.name,
                        "id": row["id"],
                        "title": row["title"],
                        "type": row["type"],
                        "file": row["file"],
                        "useful_when": row["useful_when"],
                        "matched_heading": chunk_context["heading_path"],
                        "matched_chunk": chunk_context["snippet"],
                        "score": row["score"],
                    }
                )
        reefiki_hits.sort(key=lambda item: item["score"])
        result["reefiki"] = reefiki_hits[:limit]

    if include_graph:
        graph_hits: list[dict[str, object]] = []
        query_lower = query.lower()
        for project_path in target_projects:
            report = graphify_report_path(project_path)
            if not report:
                continue
            lines = report.read_text(encoding="utf-8", errors="replace").splitlines()
            matches: list[dict[str, object]] = []
            for idx, line in enumerate(lines, 1):
                if query_lower in line.lower():
                    matches.append(
                        {
                            "project": project_path.name,
                            "report": str(report),
                            "line": idx,
                            "text": line.strip(),
                        }
                    )
                    if len(matches) >= limit:
                        break
            graph_hits.extend(matches)
        result["graphify"] = graph_hits[:limit]
    return result


def _parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]


def load_golden_queries(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(f"Missing golden query file: {path}")
    data: dict[str, object] = {"queries": []}
    current: dict[str, object] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "queries:":
            continue
        if stripped.startswith("- "):
            if current is not None:
                data["queries"].append(current)  # type: ignore[union-attr]
            current = {}
            stripped = stripped[2:].strip()
            if not stripped:
                continue
        if ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        value = raw_value.strip()
        parsed: object
        if value.startswith("[") and value.endswith("]"):
            parsed = _parse_inline_list(value)
        elif value.lower() == "null":
            parsed = None
        elif value.isdigit():
            parsed = int(value)
        else:
            parsed = value.strip("\"'")
        if current is None:
            data[key.strip()] = parsed
        else:
            current[key.strip()] = parsed
    if current is not None:
        data["queries"].append(current)  # type: ignore[union-attr]
    return data


def run_golden_queries(root: Path, project_name: str, path: Path | None = None) -> dict[str, object]:
    project = find_project(root, project_name)
    golden_path = path or project / "golden-queries.yml"
    config = load_golden_queries(golden_path)
    cases: list[dict[str, object]] = []
    misses: list[dict[str, object]] = []
    for case in config.get("queries", []):
        if not isinstance(case, dict):
            continue
        case_id = as_text(case.get("id")) or "unnamed"
        kind = as_text(case.get("kind"))
        errors: list[str] = []
        details: dict[str, object] = {}
        if kind == "lookup":
            layer = as_text(case.get("layer")) or "reefiki"
            lookup = global_lookup(
                root,
                query=as_text(case.get("query")),
                project=project_name,
                include_memoir=layer in {"all", "memoir"},
                include_reefiki=layer in {"all", "reefiki"},
                include_graph=layer in {"all", "graphify"},
                limit=5,
            )
            actual_ids = [as_text(item.get("id")) for item in lookup.get("reefiki", []) if isinstance(item, dict)]
            expected_ids = [as_text(item) for item in case.get("expect_ids", [])]
            missing = [expected for expected in expected_ids if expected not in actual_ids]
            if missing:
                errors.append(f"missing_ids:{','.join(missing)}")
                misses.append(
                    {
                        "case_id": case_id,
                        "missing_ids": missing,
                        "actual_ids": actual_ids,
                        "expected_ids": expected_ids,
                        "query": as_text(case.get("query")),
                    }
                )
            details = {"actual_ids": actual_ids, "expected_ids": expected_ids}
        elif kind == "promote":
            result = promotion_dry_run(
                project,
                as_text(case.get("content")),
                confidence=0.8,
            )
            expected_verdict = as_text(case.get("expect_verdict"))
            expected_type = as_text(case.get("expect_target_type"))
            if expected_verdict and result["verdict"] != expected_verdict:
                errors.append(f"verdict:{result['verdict']}")
            if expected_type and result["suggested_target_type"] != expected_type:
                errors.append(f"target_type:{result['suggested_target_type']}")
            details = {
                "verdict": result["verdict"],
                "suggested_target_type": result["suggested_target_type"],
            }
        elif kind == "pack":
            result = memory_pack(
                root,
                project_name,
                as_text(case.get("task")),
                limit=8,
                include_golden=False,
            )
            actual_ids = [
                as_text(item.get("id"))
                for item in result.get("contents", [])
                if isinstance(item, dict)
            ]
            expected_ids = [as_text(item) for item in case.get("expect_ids", [])]
            missing = [expected for expected in expected_ids if expected not in actual_ids]
            if missing:
                errors.append(f"missing_ids:{','.join(missing)}")
                misses.append(
                    {
                        "case_id": case_id,
                        "missing_ids": missing,
                        "actual_ids": actual_ids,
                        "expected_ids": expected_ids,
                        "task": as_text(case.get("task")),
                    }
                )
            expected_route = as_text(case.get("expect_route_layer"))
            actual_route = as_text(
                result.get("task_route", {})
                .get("route_decision", {})
                .get("recommended_layer")
                if isinstance(result.get("task_route"), dict)
                else ""
            )
            if expected_route and actual_route != expected_route:
                errors.append(f"route_layer:{actual_route}")
            expected_pack_layers = [as_text(item) for item in case.get("expect_pack_layers", [])]
            actual_pack_layers = [
                as_text(item)
                for item in (
                    result.get("assembly_trace", {})
                    .get("pack_scope", {})
                    .get("source_layers", [])
                    if isinstance(result.get("assembly_trace"), dict)
                    else []
                )
            ]
            if expected_pack_layers and actual_pack_layers != expected_pack_layers:
                errors.append(f"pack_layers:{','.join(actual_pack_layers)}")
            details = {
                "actual_ids": actual_ids,
                "expected_ids": expected_ids,
                "route_layer": actual_route,
                "pack_layers": actual_pack_layers,
            }
        else:
            errors.append(f"unsupported_kind:{kind}")
        cases.append(
            {
                "id": case_id,
                "kind": kind,
                "status": "pass" if not errors else "fail",
                "errors": errors,
                "details": details,
            }
        )
    failed = len([case for case in cases if case["status"] != "pass"])
    return {
        "project": project_name,
        "path": relative(project, golden_path) if golden_path.is_relative_to(project) else str(golden_path),
        "total": len(cases),
        "passed": len(cases) - failed,
        "failed": failed,
        "misses": misses,
        "eval": {
            "outcome": "pass" if failed == 0 else "fail",
            "miss_count": len(misses),
        },
        "cases": cases,
    }


def _run_git(root: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise SystemExit(detail)
    return completed.stdout


EMPTY_TREE_REF = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def resolve_since_date_ref(root: Path, since_date: str, pathspec: str) -> str:
    datetime.fromisoformat(since_date)
    commit = _run_git(
        root,
        [
            "rev-list",
            "--reverse",
            f"--since={since_date} 00:00:00",
            "HEAD",
            "--",
            pathspec,
        ],
    ).splitlines()
    if not commit:
        return "HEAD"
    first = commit[0].strip()
    parents = _run_git(root, ["rev-list", "--parents", "-n", "1", first]).strip().split()
    return parents[1] if len(parents) > 1 else EMPTY_TREE_REF


def memory_diff(
    root: Path,
    project_name: str,
    from_ref: str,
    to_ref: str | None = None,
    since_date: str | None = None,
) -> dict[str, object]:
    project = find_project(root, project_name)
    wiki_prefix = f"projects/{project.name}/wiki"
    resolved_from_ref = from_ref
    if since_date:
        resolved_from_ref = resolve_since_date_ref(root, since_date, wiki_prefix)
    policy = memory_preflight(
        project=project.name,
        visibility="private",
        operation="diff",
        content="",
        paths=[wiki_prefix],
    )
    result: dict[str, object] = {
        "project": project.name,
        "from": resolved_from_ref,
        "to": to_ref or "WORKTREE",
        "since_date": since_date,
        "policy": policy,
        "counts": {},
        "total": 0,
        "files": [],
    }
    if policy["outcome"] == "block":
        return result

    diff_args = ["diff", "--name-status", resolved_from_ref]
    if to_ref:
        diff_args.append(to_ref)
    diff_args.extend(["--", wiki_prefix])
    files: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    for line in _run_git(root, diff_args).splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        path = parts[-1]
        if path.endswith("/index.md") or path.endswith("/log.md"):
            category = "meta"
        else:
            category = "page"
        short_path = path.removeprefix(f"projects/{project.name}/")
        files.append({"status": status, "path": short_path, "category": category})
        counts[status] += 1
    result["files"] = files
    result["counts"] = dict(sorted(counts.items()))
    result["total"] = len(files)
    return result


def memory_pack(
    root: Path,
    project_name: str,
    task: str,
    limit: int = 8,
    include_golden: bool = True,
) -> dict[str, object]:
    project = find_project(root, project_name)
    policy = memory_preflight(
        project=project.name,
        visibility="private",
        operation="pack",
        content=task,
        paths=[f"projects/{project.name}/wiki"],
    )
    route = memory_route(task, project_hint=project.name)
    task_route = {
        key: value for key, value in route.items() if key not in {"layer", "project_hint"}
    }
    assembly_trace = {
        "pack_scope": {
            "target_project": project.name,
            "source_layers": ["reefiki"],
            "include_golden": include_golden,
            "include_diff": True,
            "include_open_queues": True,
            "excluded_scopes": ["projects/metrica", "projects/hermes", "secrets", "raw"],
        }
    }
    result: dict[str, object] = {
        "pack_id": hashlib.sha256(f"{project.name}:{task}".encode("utf-8")).hexdigest()[:16],
        "task": task,
        "project": project.name,
        "policy": policy,
        "task_route": {
            "operation": "pack",
            "route_decision": task_route,
        },
        "assembly_trace": assembly_trace,
        "route_trace": {
            "operation": "pack",
            "route_decision": task_route,
        },
        "contents": [],
        "quality": None,
        "golden": None,
        "diff": None,
        "open_queues": [],
        "exclusions": assembly_trace["pack_scope"]["excluded_scopes"],
        "safety_outcome": "block" if policy["outcome"] == "block" else "pass",
    }
    if policy["outcome"] == "block":
        return result

    lookup = global_lookup(
        root,
        query=task,
        project=project.name,
        include_memoir=False,
        include_reefiki=True,
        include_graph=False,
        limit=limit,
    )
    critical_order = [
        "reefiki-2-control-plane-spec",
        "reefiki-2-external-agent-research-synthesis",
        "reefiki-2-control-plane-research-comparison",
        "reefiki-routing-and-promotion-contract",
        "global-memory-orchestration-cli",
    ]
    critical_ids = set(critical_order)
    critical_rank = {item_id: index for index, item_id in enumerate(critical_order)}
    max_items_by_type = {
        "synthesis": 5,
        "decision": 3,
        "skill": 2,
        "concept": 2,
        "source": 2,
        "entity": 2,
    }
    contents_by_id: dict[str, dict[str, object]] = {}
    for item in lookup.get("reefiki", []):
        if not isinstance(item, dict):
            continue
        item_id = as_text(item.get("id"))
        contents_by_id[item_id] = {
            "id": item_id,
            "type": item.get("type"),
            "title": item.get("title"),
            "path": item.get("file"),
            "layer": "reefiki",
            "why_included": "critical REEFIKI 2 handoff context"
            if item_id in critical_ids
            else "matched task lookup",
            "score": item.get("score"),
        }
    existing_ids = set(contents_by_id)
    wiki_rows = _wiki_rows(project)
    available_ids = {as_text(row.get("id")) for row in wiki_rows}
    required_ids = [item_id for item_id in critical_order if item_id in available_ids]
    for row in wiki_rows:
        row_id = as_text(row.get("id"))
        if row_id not in critical_ids or row_id in existing_ids:
            continue
        contents_by_id[row_id] = {
            "id": row_id,
            "type": row.get("type"),
            "title": row.get("title"),
            "path": row.get("file"),
            "layer": "reefiki",
            "why_included": "critical REEFIKI 2 handoff context",
            "score": None,
        }
    contents = list(contents_by_id.values())
    contents.sort(
        key=lambda item: (
            0 if item["id"] in critical_ids else 1,
            critical_rank.get(as_text(item["id"]), 999),
            as_text(item.get("type")),
            as_text(item.get("id")),
        )
    )
    packed_contents: list[dict[str, object]] = []
    type_counts: Counter[str] = Counter()
    for item in contents:
        item_type = as_text(item.get("type")) or "unknown"
        if item["id"] not in critical_ids and type_counts[item_type] >= max_items_by_type.get(item_type, 2):
            continue
        packed_contents.append(item)
        type_counts[item_type] += 1
        if len(packed_contents) >= limit:
            break
    result["contents"] = packed_contents
    packed_ids = {as_text(item.get("id")) for item in packed_contents}
    missing_required_ids = [item_id for item_id in required_ids if item_id not in packed_ids]
    violations: list[str] = []
    if missing_required_ids:
        violations.append("missing_required_ids")
    for item_type, count in sorted(type_counts.items()):
        max_count = max_items_by_type.get(item_type, 2)
        if count > max_count:
            violations.append(f"max_items_by_type:{item_type}")
    result["quality"] = {
        "outcome": "pass" if not violations else "warn",
        "required_ids": required_ids,
        "missing_required_ids": missing_required_ids,
        "max_items_by_type": max_items_by_type,
        "type_counts": dict(sorted(type_counts.items())),
        "violations": violations,
    }
    if include_golden:
        try:
            result["golden"] = {
                key: value
                for key, value in run_golden_queries(root, project.name).items()
                if key in {"total", "passed", "failed", "path"}
            }
        except SystemExit as exc:
            result["golden"] = {"error": str(exc)}
    try:
        diff = memory_diff(root, project.name, from_ref="HEAD")
        result["diff"] = {key: diff[key] for key in ["from", "to", "counts", "total", "files"]}
    except SystemExit as exc:
        result["diff"] = {"error": str(exc)}
    try:
        queue_items = review_queue_scan(project)
        grouped_queues: dict[str, list[dict[str, object]]] = {}
        for item in queue_items:
            grouped_queues.setdefault(as_text(item.get("queue_type")), []).append(item)
        result["open_queues"] = [
            {
                "queue_type": queue_type,
                "count": len(items),
                "items": [
                    {
                        "page_id": item.get("page_id"),
                        "reason": item.get("reason"),
                        "related_page_ids": item.get("related_page_ids", []),
                        "suggested_action": item.get("suggested_action"),
                    }
                    for item in items[:3]
                ],
            }
            for queue_type, items in sorted(grouped_queues.items())
        ]
    except Exception as exc:  # pragma: no cover - defensive reporting for handoff output
        result["open_queues"] = [{"error": str(exc)}]
    return result


def memory_pack_strict_result(result: dict[str, object]) -> dict[str, object]:
    blocking_reasons: list[str] = []
    if result.get("safety_outcome") == "block":
        blocking_reasons.append("policy:block")
    quality = result.get("quality")
    if isinstance(quality, dict) and quality.get("outcome") != "pass":
        violations = quality.get("violations") or ["warn"]
        blocking_reasons.extend(f"quality:{violation}" for violation in violations)
    golden = result.get("golden")
    if isinstance(golden, dict):
        if golden.get("error"):
            blocking_reasons.append("golden:error")
        if int(golden.get("failed") or 0) > 0:
            blocking_reasons.append("golden:failed")
    diff = result.get("diff")
    if isinstance(diff, dict) and diff.get("error"):
        blocking_reasons.append("diff:error")
    return {
        "outcome": "fail" if blocking_reasons else "pass",
        "blocking_reasons": blocking_reasons,
    }


def print_memory_route(text: str, project_hint: str | None, fmt: str) -> int:
    result = memory_route(text, project_hint=project_hint)
    if fmt == "json":
        contract_result = {
            key: value
            for key, value in result.items()
            if key not in {"layer", "project_hint"}
        }
        print(json.dumps(contract_result, ensure_ascii=False, indent=2))
        return 0
    print(f"layer: {result['recommended_layer']}")
    print(f"reason: {result['reason']}")
    if result.get("target_project"):
        print(f"project_hint: {result['target_project']}")
    return 0


def print_memory_status(
    root: Path,
    project_name: str,
    all_projects: bool,
    only_open: bool,
    summary: bool,
    fail_on_open: bool,
    fmt: str,
) -> int:
    result = memory_status_all_projects(root, only_open=only_open) if all_projects else memory_status(root, project_name=project_name)
    result["has_open"] = memory_status_has_open(result)
    output_result = compact_status_result(result) if summary else result
    if isinstance(output_result, dict):
        output_result["has_open"] = result["has_open"]
    if fmt == "jsonl":
        items = output_result.get("projects", []) if all_projects else [output_result]
        for item in items:
            print(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
        return 1 if fail_on_open and result["has_open"] else 0
    if fmt == "json":
        print(json.dumps(output_result, ensure_ascii=False, indent=2))
        return 1 if fail_on_open and result["has_open"] else 0
    if summary:
        if all_projects:
            print(f"projects: {output_result['total']}")
            print(f"open: {'yes' if result['has_open'] else 'no'}")
            totals = output_result.get("totals", {})
            if isinstance(totals, dict):
                print(f"review_queues: {totals.get('review_queues', '-')}")
                print(f"promotion_inbox: active={totals.get('promotion_active', '-')} closed={totals.get('promotion_closed', '-')}")
            for item in output_result.get("projects", []):
                if isinstance(item, dict):
                    queues = item.get("review_queues", {}) if isinstance(item.get("review_queues"), dict) else {}
                    promotion = item.get("promotion_inbox", {}) if isinstance(item.get("promotion_inbox"), dict) else {}
                    print(
                        f"  - {item.get('project')}: "
                        f"review_queues={queues.get('total', '-')} "
                        f"promotion_active={promotion.get('active', '-')} "
                        f"promotion_closed={promotion.get('closed', '-')}"
                    )
        else:
            print(f"project: {output_result.get('project')}")
            print(f"open: {'yes' if result['has_open'] else 'no'}")
            print(f"graphify: {output_result.get('graphify')}")
            queues = output_result.get("review_queues", {}) if isinstance(output_result.get("review_queues"), dict) else {}
            promotion = output_result.get("promotion_inbox", {}) if isinstance(output_result.get("promotion_inbox"), dict) else {}
            print(f"review_queues: {queues.get('total', '-')}")
            print(f"promotion_inbox: active={promotion.get('active', '-')} closed={promotion.get('closed', '-')}")
        return 1 if fail_on_open and result["has_open"] else 0
    if all_projects:
        print(f"projects: {result['total']}")
        totals = result.get("totals", {})
        if isinstance(totals, dict):
            print(f"review_queues: {totals.get('review_queues', '-')}")
            print(f"promotion_inbox: active={totals.get('promotion_active', '-')} closed={totals.get('promotion_closed', '-')}")
        for item in result.get("projects", []):
            if not isinstance(item, dict):
                continue
            queues = item.get("review_queues", {}) if isinstance(item.get("review_queues"), dict) else {}
            promotion = item.get("promotion_inbox", {}) if isinstance(item.get("promotion_inbox"), dict) else {}
            print(
                f"  - {item.get('project')}: "
                f"review_queues={queues.get('total', '-')} "
                f"promotion_active={promotion.get('active', '-')} "
                f"promotion_closed={promotion.get('closed', '-')}"
            )
        return 1 if fail_on_open and result["has_open"] else 0
    providers = result.get("providers", {})
    print(f"providers: {len(providers)}")
    if isinstance(providers, dict):
        for provider_id, provider in providers.items():
            capabilities = ", ".join(provider.get("capabilities", []))
            print(f"  - {provider_id}: {provider.get('kind')} [{capabilities}]")
    graphify = result.get("graphify", {})
    if isinstance(graphify, dict):
        print(f"graphify: {graphify.get('status')}")
    queues = result.get("review_queues", {})
    if isinstance(queues, dict):
        print(f"review_queues: {queues.get('total', '-')}")
    promotion = result.get("promotion_inbox", {})
    if isinstance(promotion, dict):
        print(f"promotion_inbox: active={promotion.get('active', '-')} closed={promotion.get('closed', '-')}")
    return 1 if fail_on_open and result["has_open"] else 0


def print_memory_explain(root: Path, query: str, project_name: str, fmt: str) -> int:
    result = memory_explain(root, query, project_name)
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["policy"]["outcome"] != "block" else 1
    print(f"query: {result['query']}")
    print(f"project: {result['project']}")
    route = result["route"]
    print(f"route: {route.get('recommended_layer')}")
    print(f"reason: {route.get('reason')}")
    print(f"policy: {result['policy'].get('outcome')}")
    print("sources:")
    for item in result["source_decisions"]:
        print(f"  - {item['layer']}: {item['status']} ({item['reason']})")
    print(f"next_action: {result['next_action']}")
    return 0 if result["policy"]["outcome"] != "block" else 1


def print_memory_preflight(
    project: str,
    visibility: str,
    operation: str,
    content: str,
    paths: list[str],
    fmt: str,
) -> int:
    result = memory_preflight(
        project=project,
        visibility=visibility,
        operation=operation,
        content=content,
        paths=paths,
    )
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"outcome: {result['outcome']}")
        if result["blocking_reasons"]:
            print(f"blocking_reasons: {', '.join(result['blocking_reasons'])}")
        if result["warnings"]:
            print(f"warnings: {', '.join(result['warnings'])}")
    return 1 if result["outcome"] == "block" else 0


def print_global_lookup(
    root: Path,
    query: str,
    project: str | None,
    include_memoir: bool,
    include_reefiki: bool,
    include_graph: bool,
    limit: int,
    fmt: str,
) -> int:
    result = global_lookup(
        root,
        query=query,
        project=project,
        include_memoir=include_memoir,
        include_reefiki=include_reefiki,
        include_graph=include_graph,
        limit=limit,
    )
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("policy", {}).get("outcome") == "block" else 0
    if result.get("policy", {}).get("outcome") == "block":
        print(f"query: {result['query']}")
        print(f"policy: block")
        print(f"blocking_reasons: {', '.join(result['policy']['blocking_reasons'])}")
        return 1
    print(f"query: {result['query']}")
    memoir_block = result.get("memoir")
    if memoir_block:
        if isinstance(memoir_block, dict) and memoir_block.get("error"):
            print(f"memoir: error: {memoir_block['error']}")
        else:
            memories = memoir_block.get("memories", []) if isinstance(memoir_block, dict) else []
            print(f"memoir: {len(memories)} hit(s)")
            for item in memories[:limit]:
                print(f"  - {item.get('path')}: {item.get('content')}")
    reefiki_block = result.get("reefiki", [])
    print(f"reefiki: {len(reefiki_block)} hit(s)")
    for item in reefiki_block:
        print(f"  - [{item['project']}] {item['title']} ({item['file']})")
    graph_block = result.get("graphify", [])
    print(f"graphify: {len(graph_block)} hit(s)")
    for item in graph_block:
        print(f"  - [{item['project']}] {item['text']} ({item['report']}:{item['line']})")
    return 0


def print_memory_golden(root: Path, project_name: str, path: str | None, fmt: str) -> int:
    result = run_golden_queries(root, project_name, Path(path) if path else None)
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"project: {result['project']}")
        print(f"golden: {result['passed']}/{result['total']} passed")
        for case in result["cases"]:
            print(f"  - {case['status']}: {case['id']}")
    return 1 if result["failed"] else 0


def print_memory_diff(
    root: Path,
    project_name: str,
    from_ref: str,
    to_ref: str | None,
    since_date: str | None,
    fmt: str,
) -> int:
    result = memory_diff(
        root,
        project_name,
        from_ref=from_ref,
        to_ref=to_ref,
        since_date=since_date,
    )
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"project: {result['project']}")
        print(f"diff: {result['from']}..{result['to']}")
        print(f"total: {result['total']}")
        for item in result["files"]:
            print(f"  - {item['status']}: {item['path']}")
    return 1 if result.get("policy", {}).get("outcome") == "block" else 0


def print_memory_pack(root: Path, project_name: str, task: str, limit: int, strict: bool, fmt: str) -> int:
    result = memory_pack(root, project_name, task, limit=limit)
    result["strict"] = memory_pack_strict_result(result)
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"# Memory Pack: {result['task']}")
        print("")
        print(f"- project: {result['project']}")
        print(f"- safety: {result['safety_outcome']}")
        print(f"- items: {len(result['contents'])}")
        print(f"- strict: {result['strict']['outcome']}")
        if result["strict"]["blocking_reasons"]:
            print(f"- strict_reasons: {', '.join(result['strict']['blocking_reasons'])}")
        print("")
        print("## Contents")
        for item in result["contents"]:
            print(f"- {item['id']} ({item['path']}) - {item['why_included']}")
        print("")
        print("## Quality")
        quality = result.get("quality")
        if isinstance(quality, dict):
            print(f"- outcome: {quality.get('outcome', '-')}")
            missing = quality.get("missing_required_ids") or []
            if missing:
                print(f"- missing_required_ids: {', '.join(str(item) for item in missing)}")
            else:
                print("- missing_required_ids: none")
            violations = quality.get("violations") or []
            if violations:
                print(f"- violations: {', '.join(str(item) for item in violations)}")
            else:
                print("- violations: none")
        else:
            print("- outcome: unknown")
        print("")
        print("## Golden")
        golden = result.get("golden")
        if isinstance(golden, dict):
            print(f"- passed: {golden.get('passed', '-')}/{golden.get('total', '-')}")
            if golden.get("failed"):
                print(f"- failed: {golden.get('failed')}")
            if golden.get("error"):
                print(f"- error: {golden.get('error')}")
        print("")
        print("## Diff")
        diff = result.get("diff")
        if isinstance(diff, dict):
            print(f"- total: {diff.get('total', '-')}")
            print(f"- from: {diff.get('from', '-')}")
            print(f"- to: {diff.get('to', '-')}")
        print("")
        print("## Open Queues")
        queues = result.get("open_queues", [])
        if queues:
            for queue in queues:
                if isinstance(queue, dict):
                    label = queue.get("queue_type") or "error"
                    count = queue.get("count") or queue.get("error")
                    print(f"- {label}: {count}")
                    for item in queue.get("items", [])[:3] if isinstance(queue.get("items"), list) else []:
                        if not isinstance(item, dict):
                            continue
                        print(f"  - {item.get('page_id')}: {item.get('reason')}")
                        print(f"    action: {item.get('suggested_action')}")
        else:
            print("- none")
        print("")
        print("## Exclusions")
        for exclusion in result["exclusions"]:
            print(f"- {exclusion}")
    if result.get("safety_outcome") == "block":
        return 1
    if strict and result["strict"]["outcome"] == "fail":
        return 1
    return 0


def print_global_promote(
    root: Path,
    content: str,
    target_project: str,
    memory_id: str | None,
    confidence: float,
    write_draft: bool,
    fmt: str,
) -> int:
    policy = memory_global_strict_preflight(
        project=target_project,
        visibility="private",
        operation="promote",
        content=content,
        paths=[f"projects/{target_project}"],
    )
    if policy["outcome"] == "block":
        result: dict[str, object] = {
            "target_project": target_project,
            "policy": policy,
            "verdict": "blocked",
        }
        if fmt == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
        print(f"target_project: {target_project}")
        print("policy: block")
        print(f"blocking_reasons: {', '.join(policy['blocking_reasons'])}")
        return 1

    project = find_project(root, target_project)
    result = promotion_dry_run(project, content, memory_id=memory_id, confidence=confidence)
    result["target_project"] = project.name
    result["policy"] = policy
    action = "NOOP"
    if result["verdict"] == "promote":
        action = "DUPLICATE" if result["duplicate_candidate_refs"] else "CREATE"
    candidate = PromotionCandidate(
        content=as_text(result["distilled_summary"]),
        source_layer="memoir",
        target_project=project.name,
        suggested_action=action,
        target_type=as_text(result["suggested_target_type"]) or None,
        duplicate_candidates=[as_text(ref) for ref in result["duplicate_candidate_refs"]],
        review_state=as_text(result["review_state"]) or "noop",
    )
    result["promotion_candidate"] = candidate.to_dict()
    trace = MemoryDecisionTrace(
        operation="promote",
        boundary_context=AccessBoundaryContext(
            project=project.name,
            allowed_scopes=[f"projects/{project.name}"],
            forbidden_scopes=["projects/metrica", "projects/hermes", "secrets", "raw"],
            visibility="private",
        ),
        route_decision=RouteDecision(
            recommended_layer="reefiki" if result["verdict"] == "promote" else "memoir",
            reason="global promotion gate",
            target_project=project.name,
            risk_flags=["durable_write_requires_review"] if result["verdict"] == "promote" else [],
        ),
        policy_checks=[policy],
        promotion_candidates=[candidate],
        safety_outcome="needs_review" if result["verdict"] == "promote" else "pass",
    )
    result["trace"] = trace.to_dict()
    if write_draft:
        draft = write_promotion_draft(project, content, memory_id=memory_id, confidence=confidence)
        result["draft_path"] = relative(project, draft)
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(f"target_project: {project.name}")
    print(f"verdict: {result['verdict']}")
    if result["suggested_target_type"]:
        print(f"target_type: {result['suggested_target_type']}")
    print(f"confidence: {result['confidence']}")
    if result["review_state"]:
        print(f"review_state: {result['review_state']}")
    if result["duplicate_candidate_refs"]:
        print(f"duplicates: {', '.join(result['duplicate_candidate_refs'])}")
    if write_draft:
        print(f"draft: {result['draft_path']}")
    print(f"summary: {result['distilled_summary']}")
    return 0


def print_memory_promotion_inbox(
    root: Path,
    project_name: str,
    show: str | None,
    apply: str | None,
    reject: str | None,
    reason: str | None,
    yes: bool,
    include_all: bool,
    prune_closed: bool,
    fmt: str,
) -> int:
    project = find_project(root, project_name)
    if prune_closed:
        result = prune_closed_promotion_drafts(project, yes=yes)
        if fmt == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"moved: {result['moved']}")
            for draft in result["drafts"]:
                print(f"  - {draft['from']} -> {draft['to']}")
        return 0
    if apply:
        result = apply_promotion_inbox_draft(project, apply, yes=yes)
        if fmt == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"applied: {result['draft_path']}")
            print(f"page: {result['page_path']}")
        return 0
    if reject:
        result = reject_promotion_inbox_draft(project, reject, reason=reason, yes=yes)
        if fmt == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"rejected: {result['draft_path']}")
        return 0
    result = promotion_inbox(project, show=show, include_all=include_all)
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("policy", {}).get("outcome") == "block" else 0
    print(f"project: {result['project']}")
    print(f"policy: {result['policy'].get('outcome')}")
    if result.get("draft"):
        draft = result["draft"]
        print(f"draft: {draft.get('path')}")
        print(f"verdict: {draft.get('verdict')}")
        print(f"target_type: {draft.get('target_type')}")
        print(f"review_state: {draft.get('review_state')}")
        print(f"memory_id: {draft.get('memory_id')}")
        print(f"summary: {draft.get('summary')}")
        return 0
    print(f"drafts: {result.get('total', 0)}")
    for draft in result.get("drafts", []):
        print(f"  - {draft.get('path')}: {draft.get('verdict')} -> {draft.get('target_type')}")
    return 1 if result.get("policy", {}).get("outcome") == "block" else 0


def _related_ids(body: str) -> set[str]:
    match = re.search(r"(?ms)^## Related\s*\n(.*?)(?:\n## |\Z)", body)
    if not match:
        return set()
    related_block = match.group(1)
    return set(re.findall(r"\[\[([a-z0-9\-]+)\]\]", related_block))


def _all_wiki_link_ids(body: str) -> set[str]:
    return {as_text(item["target_id"]) for item in extract_wiki_links(body)}


def _conflicting_claim_ids(body: str) -> set[str]:
    match = re.search(r"(?ms)^## Conflicting claims?\s*\n(.*?)(?:\n## |\Z)", body)
    if not match:
        match = re.search(r"(?ms)^## Conflicts?\s*\n(.*?)(?:\n## |\Z)", body)
    if not match:
        return set()
    conflict_block = match.group(1)
    return set(re.findall(r"\[\[([a-z0-9\-]+)\]\]", conflict_block))


def _incoming_link_counts(rows: list[dict[str, object]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        for rel in _all_wiki_link_ids(as_text(row.get("body"))):
            counts[rel] += 1
    return counts


def _stale_days(row: dict[str, object], today: date) -> int | None:
    verified = as_text(row.get("verified")) or as_text(row.get("last_used")) or as_text(row.get("date_added"))
    if not verified:
        return None
    try:
        return (today - date.fromisoformat(verified)).days
    except ValueError:
        return None


def review_queue_scan(project: Path, stale_days: int = 90, queue_type: str | None = None) -> list[dict[str, object]]:
    rows = _wiki_rows(project)
    incoming = _incoming_link_counts(rows)
    today = date.today()
    title_groups: dict[str, list[dict[str, object]]] = {}
    source_groups: dict[str, list[dict[str, object]]] = {}
    file_to_row = {as_text(row["file"]): row for row in rows}
    row_ids = {as_text(row["id"]) for row in rows}
    outgoing_by_id = {as_text(row["id"]): _all_wiki_link_ids(as_text(row["body"])) for row in rows}
    for row in rows:
        title_groups.setdefault(_normalize_text(as_text(row["title"])), []).append(row)
        for source in row["sources"]:
            if not _is_duplicate_source_signal(as_text(source)):
                continue
            source_groups.setdefault(_normalize_text(as_text(source)), []).append(row)

    items: list[dict[str, object]] = []
    for row in rows:
        row_id = as_text(row["id"])
        row_type = as_text(row["type"])
        related_ids: list[str] = []
        if row_type in {"synthesis", "decision", "concept"} and not row["sources"]:
            items.append(
                {
                    "page_id": row_id,
                    "queue_type": "needs_verification",
                    "reason": "durable page has no sources metadata",
                    "related_page_ids": [],
                    "suggested_action": "add sources or mark evidence explicitly",
                }
            )
        stale = _stale_days(row, today)
        if stale is not None and stale > stale_days:
            items.append(
                {
                    "page_id": row_id,
                    "queue_type": "stale_review",
                    "reason": f"page not reviewed for {stale} day(s)",
                    "related_page_ids": [],
                    "suggested_action": "re-verify or deprecate",
                }
            )
        if row_type in {"concept", "decision", "synthesis", "skill"} and incoming[row_id] == 0:
            items.append(
                {
                    "page_id": row_id,
                    "queue_type": "orphan_review",
                    "reason": "page has no inbound wiki links",
                    "related_page_ids": [],
                    "suggested_action": "attach to index/related pages or merge/remove",
                }
            )
        compatible_types = TYPE_DUPLICATE_COMPATIBILITY.get(row_type, {row_type})
        dup_related = {
            as_text(other["id"])
            for other in title_groups.get(_normalize_text(as_text(row["title"])), [])
            if as_text(other["id"]) != row_id and as_text(other["type"]) in compatible_types
        }
        for source in row["sources"]:
            if not _is_duplicate_source_signal(as_text(source)):
                continue
            dup_related.update(
                as_text(other["id"])
                for other in source_groups.get(_normalize_text(as_text(source)), [])
                if as_text(other["id"]) != row_id and as_text(other["type"]) in compatible_types
                and _titles_are_similar(as_text(row["title"]), as_text(other["title"]))
            )
        if dup_related:
            related_ids = sorted(dup_related)
            items.append(
                {
                    "page_id": row_id,
                    "queue_type": "duplicate_candidate",
                    "reason": "high-confidence overlap by exact title or source plus similar title",
                    "related_page_ids": related_ids,
                    "suggested_action": "choose canonical page and merge or bridge",
                }
            )
        body = as_text(row["body"])
        all_links = outgoing_by_id[row_id]
        for rel in sorted(all_links):
            if rel not in file_to_row and rel not in row_ids:
                items.append(
                    {
                        "page_id": row_id,
                        "queue_type": "placeholder_link",
                        "reason": f"wikilink points to missing page: {rel}",
                        "related_page_ids": [rel],
                        "suggested_action": "resolve missing/moved page or update linkage",
                    }
                )
        for source_row in rows:
            source_id = as_text(source_row["id"])
            if source_id == row_id:
                continue
            source_links = outgoing_by_id[source_id]
            if row_id in source_links and source_id not in all_links:
                items.append(
                    {
                        "page_id": row_id,
                        "queue_type": "missing_backlink",
                        "reason": f"page is linked by {source_id} but does not link back",
                        "related_page_ids": [source_id],
                        "suggested_action": "add reciprocal Related link or mark one-way relation as intentional",
                    }
                )
        related = _related_ids(body)
        for rel in related:
            if rel not in file_to_row and rel not in row_ids:
                items.append(
                    {
                        "page_id": row_id,
                        "queue_type": "conflict_review",
                        "reason": f"related reference points to missing page: {rel}",
                        "related_page_ids": [rel],
                        "suggested_action": "resolve missing/moved page or update linkage",
                    }
                )
        for conflict_id in sorted(_conflicting_claim_ids(body)):
            items.append(
                {
                    "page_id": row_id,
                    "queue_type": "conflict_review",
                    "reason": "explicit conflicting-claims marker",
                    "related_page_ids": [conflict_id],
                    "suggested_action": "resolve conflicting claim or mark superseded/deprecated",
                }
            )

    if queue_type:
        return [item for item in items if item["queue_type"] == queue_type]
    return items


def print_review_queues(project: Path, stale_days: int, fmt: str, queue_type: str | None) -> int:
    items = review_queue_scan(project, stale_days=stale_days, queue_type=queue_type)
    if fmt == "json":
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return 0
    if not items:
        print("No review queue candidates.")
        return 0
    for item in items:
        print(f"{item['queue_type']}: {item['page_id']}")
        print(f"  reason: {item['reason']}")
        if item["related_page_ids"]:
            print(f"  related: {', '.join(item['related_page_ids'])}")
        print(f"  action: {item['suggested_action']}")
    return 0


def write_review_queue_report(project: Path, stale_days: int) -> Path:
    items = review_queue_scan(project, stale_days=stale_days)
    reports = project / "plans"
    reports.mkdir(exist_ok=True)
    path = reports / f"review-queues-{date.today().isoformat()}.md"
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in items:
        grouped.setdefault(as_text(item["queue_type"]), []).append(item)
    lines = [
        "# Review Queue Report",
        "",
        f"Date: {date.today().isoformat()}",
        f"Stale threshold: {stale_days} days",
        f"Total items: {len(items)}",
        "",
    ]
    if not items:
        lines.extend(
            [
                "No review queue candidates.",
                "",
            ]
        )
    else:
        for queue_type in sorted(grouped):
            lines.append(f"## {queue_type}")
            lines.append("")
            for item in grouped[queue_type]:
                lines.append(f"- page: `{item['page_id']}`")
                lines.append(f"  reason: {item['reason']}")
                if item["related_page_ids"]:
                    lines.append(f"  related: {', '.join(item['related_page_ids'])}")
                lines.append(f"  action: {item['suggested_action']}")
            lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def build_backlink_index(project: Path) -> dict[str, object]:
    rows = _wiki_rows(project)
    row_by_id = {as_text(row["id"]): row for row in rows}
    pages: dict[str, dict[str, object]] = {}
    incoming: dict[str, set[str]] = {page_id: set() for page_id in row_by_id}
    broken_links: list[dict[str, object]] = []

    for page_id, row in row_by_id.items():
        outgoing_details = extract_wiki_links(as_text(row.get("body")))
        outgoing = sorted({as_text(link["target_id"]) for link in outgoing_details})
        pages[page_id] = {
            "title": as_text(row.get("title")),
            "type": as_text(row.get("type")),
            "file": as_text(row.get("file")),
            "outgoing": outgoing,
            "incoming": [],
        }
        for link in outgoing_details:
            target_id = as_text(link["target_id"])
            if target_id in incoming:
                incoming[target_id].add(page_id)
            else:
                broken_links.append(
                    {
                        "source_id": page_id,
                        "target_id": target_id,
                        "file": as_text(row.get("file")),
                        "line": int(link["line"]),
                    }
                )

    for page_id in pages:
        pages[page_id]["incoming"] = sorted(incoming[page_id])

    return {
        "schema_version": 1,
        "project": project.name,
        "generated_on": date.today().isoformat(),
        "pages": dict(sorted(pages.items())),
        "orphans": sorted(page_id for page_id, links in incoming.items() if not links),
        "broken_links": sorted(
            broken_links,
            key=lambda item: (as_text(item["source_id"]), as_text(item["target_id"]), int(item["line"])),
        ),
    }


def write_backlink_index(project: Path) -> Path:
    payload = build_backlink_index(project)
    path = project / "wiki" / "_backlinks.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def print_backlink_index(project: Path, fmt: str, write: bool) -> int:
    if write:
        path = write_backlink_index(project)
        print(relative(project, path))
        return 0
    payload = build_backlink_index(project)
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"pages: {len(payload['pages'])}")
    print(f"orphans: {len(payload['orphans'])}")
    print(f"broken_links: {len(payload['broken_links'])}")
    return 0


def _suggest_target_type(text: str) -> str:
    normalized = text.lower()
    if any(token in normalized for token in ["always", "from now on", "workflow", "rule", "prefer", "step", "procedure"]):
        return "skill"
    if any(token in normalized for token in ["decide", "decision", "tradeoff", "choose", "chose", "because"]):
        return "decision"
    if any(token in normalized for token in ["pattern", "model", "means", "difference", "concept"]):
        return "concept"
    return "synthesis"


def promotion_dry_run(
    project: Path,
    content: str,
    memory_id: str | None = None,
    confidence: float = 0.6,
) -> dict[str, object]:
    text = content.strip()
    if not text:
        raise SystemExit("Empty content.")
    normalized = text.lower()
    duplicate_refs: list[str] = []
    for row in _wiki_rows(project):
        title = _normalize_text(as_text(row["title"]))
        body = _normalize_text(as_text(row["body"]))
        if text and (text[:80].lower() in body or title and title in normalized):
            duplicate_refs.append(as_text(row["id"]))
    duplicate_refs = sorted(set(duplicate_refs))

    memoir_only_markers = ["prefer ", "prefers ", "workflow rule", "from now on"]
    if len(text) < 60 and not duplicate_refs:
        verdict = "memoir-only"
    elif any(marker in normalized for marker in memoir_only_markers) and len(text) < 160 and not duplicate_refs:
        verdict = "memoir-only"
    else:
        verdict = "promote"

    if any(token in normalized for token in ["port ", "running now", "currently", "today only"]):
        verdict = "ignore"

    target_type = _suggest_target_type(text) if verdict == "promote" else None
    review_state = "needs_verification" if verdict == "promote" else None
    return {
        "verdict": verdict,
        "suggested_target_type": target_type,
        "distilled_summary": text[:240],
        "confidence": confidence,
        "review_state": review_state,
        "duplicate_candidate_refs": duplicate_refs,
        "memory_id": memory_id,
    }


def print_promotion_dry_run(
    project: Path,
    content: str,
    memory_id: str | None,
    confidence: float,
    fmt: str,
) -> int:
    result = promotion_dry_run(project, content, memory_id=memory_id, confidence=confidence)
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(f"verdict: {result['verdict']}")
    if result["suggested_target_type"]:
        print(f"target_type: {result['suggested_target_type']}")
    print(f"confidence: {result['confidence']}")
    if result["review_state"]:
        print(f"review_state: {result['review_state']}")
    if result["duplicate_candidate_refs"]:
        print(f"duplicates: {', '.join(result['duplicate_candidate_refs'])}")
    print(f"summary: {result['distilled_summary']}")
    return 0


def write_promotion_draft(
    project: Path,
    content: str,
    memory_id: str | None = None,
    confidence: float = 0.6,
) -> Path:
    result = promotion_dry_run(project, content, memory_id=memory_id, confidence=confidence)
    drafts = project / "plans"
    drafts.mkdir(exist_ok=True)
    target = as_text(result.get("suggested_target_type")) or "memoir-only"
    slug = slugify(target + "-" + content[:60])
    path = drafts / f"promotion-draft-{slug}.md"
    lines = [
        "# Promotion Draft",
        "",
        f"Date: {date.today().isoformat()}",
        f"Verdict: {result['verdict']}",
        f"Suggested target type: {result['suggested_target_type'] or '-'}",
        f"Confidence: {result['confidence']}",
        f"Review state: {result['review_state'] or '-'}",
        f"Memory ID: {result['memory_id'] or '-'}",
        "",
        "## Distilled summary",
        "",
        as_text(result["distilled_summary"]),
        "",
    ]
    duplicates = result["duplicate_candidate_refs"]
    if duplicates:
        lines.extend(
            [
                "## Duplicate candidates",
                "",
            ]
        )
        lines.extend(f"- {ref}" for ref in duplicates)
        lines.append("")
    lines.extend(
        [
            "## Next step",
            "",
            "- Review this draft before any durable write to REEFIKI.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def parse_promotion_draft(project: Path, draft_path: Path, include_body: bool = False) -> dict[str, object]:
    text = draft_path.read_text(encoding="utf-8")

    def field(label: str) -> str | None:
        match = re.search(rf"^{re.escape(label)}:\s*(.+)$", text, re.MULTILINE)
        if not match:
            return None
        value = match.group(1).strip()
        return None if value == "-" else value

    summary_match = re.search(r"(?ms)^## Distilled summary\s*\n\n(.*?)(?:\n## |\Z)", text)
    result: dict[str, object] = {
        "path": relative(project, draft_path),
        "date": field("Date"),
        "verdict": field("Verdict"),
        "target_type": field("Suggested target type"),
        "confidence": field("Confidence"),
        "review_state": field("Review state"),
        "memory_id": field("Memory ID"),
        "summary": summary_match.group(1).strip() if summary_match else "",
    }
    if include_body:
        result["body"] = text
    return result


def promotion_inbox(project: Path, show: str | None = None, include_all: bool = False) -> dict[str, object]:
    policy = memory_preflight(
        project=project.name,
        visibility="private",
        operation="promotion-inbox",
        content="",
        paths=[f"projects/{project.name}/plans"],
    )
    result: dict[str, object] = {
        "project": project.name,
        "policy": policy,
    }
    if policy["outcome"] == "block":
        result["total"] = 0
        result["drafts"] = []
        return result

    plans = project / "plans"
    if show:
        draft_path = Path(show)
        if not draft_path.is_absolute():
            draft_path = project / draft_path
        resolved = draft_path.resolve()
        project_root = project.resolve()
        if project_root not in [resolved, *resolved.parents]:
            raise SystemExit(f"{show}: outside project scope")
        result["draft"] = parse_promotion_draft(project, draft_path, include_body=True)
        return result

    drafts = []
    if plans.exists():
        draft_paths = list(plans.glob("promotion-draft-*.md"))
        if include_all:
            draft_paths.extend((plans / "closed").glob("promotion-draft-*.md"))
        for path in sorted(draft_paths):
            if not path.is_file():
                continue
            draft = parse_promotion_draft(project, path)
            if include_all or draft.get("review_state") not in {"applied", "rejected"}:
                drafts.append(draft)
    result["total"] = len(drafts)
    result["drafts"] = drafts
    return result


def _resolve_project_path(project: Path, path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = project / path
    resolved = path.resolve()
    project_root = project.resolve()
    if project_root not in [resolved, *resolved.parents]:
        raise SystemExit(f"{path_text}: outside project scope")
    return path


def update_promotion_draft_review_state(project: Path, draft_path: str, state: str, note: str | None = None) -> Path:
    path = _resolve_project_path(project, draft_path)
    text = path.read_text(encoding="utf-8")
    if re.search(r"^Review state:\s*.+$", text, re.MULTILINE):
        text = re.sub(r"^Review state:\s*.+$", f"Review state: {state}", text, count=1, flags=re.MULTILINE)
    else:
        text = text.replace("Memory ID:", f"Review state: {state}\nMemory ID:", 1)
    if note:
        block = f"\n## Review note\n\n{note.strip()}\n"
        if "## Review note" in text:
            text = re.sub(r"(?ms)^## Review note\s*\n\n.*?(?:\n## |\Z)", block.strip() + "\n", text, count=1)
        else:
            text = text.rstrip() + block
    path.write_text(text, encoding="utf-8")
    return path


def apply_promotion_inbox_draft(project: Path, draft_path: str, yes: bool) -> dict[str, object]:
    page = apply_promotion_draft(project, draft_path, yes=yes)
    draft = update_promotion_draft_review_state(project, draft_path, "applied")
    return {
        "action": "applied",
        "draft_path": relative(project, draft),
        "page_path": relative(project, page),
    }


def reject_promotion_inbox_draft(project: Path, draft_path: str, reason: str | None, yes: bool) -> dict[str, object]:
    if not yes:
        raise SystemExit("Refusing to reject without --yes.")
    draft = update_promotion_draft_review_state(project, draft_path, "rejected", note=reason or "Rejected in promotion inbox review.")
    log = project / "wiki" / "log.md"
    with log.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            f"\n## [{date.today().isoformat()}] meta | promotion draft rejected\n\n"
            f"- draft: {relative(project, draft)}\n"
            f"- reason: {reason or 'not specified'}\n"
        )
    return {
        "action": "rejected",
        "draft_path": relative(project, draft),
        "reason": reason,
    }


def prune_closed_promotion_drafts(project: Path, yes: bool) -> dict[str, object]:
    if not yes:
        raise SystemExit("Refusing to prune without --yes.")
    plans = project / "plans"
    closed = plans / "closed"
    moved: list[dict[str, str]] = []
    if plans.exists():
        closed.mkdir(exist_ok=True)
        for path in sorted(plans.glob("promotion-draft-*.md")):
            if not path.is_file():
                continue
            draft = parse_promotion_draft(project, path)
            if draft.get("review_state") not in {"applied", "rejected"}:
                continue
            destination = closed / path.name
            counter = 2
            while destination.exists():
                destination = closed / f"{path.stem}-{counter}{path.suffix}"
                counter += 1
            path.replace(destination)
            moved.append({"from": relative(project, path), "to": relative(project, destination)})
    if moved:
        log = project / "wiki" / "log.md"
        with log.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(
                f"\n## [{date.today().isoformat()}] meta | promotion drafts pruned\n\n"
                f"- moved: {len(moved)}\n"
            )
            for draft in moved:
                handle.write(f"- {draft['from']} -> {draft['to']}\n")
    return {
        "action": "pruned",
        "moved": len(moved),
        "drafts": moved,
    }


def _target_subdir(target_type: str) -> str:
    mapping = {
        "concept": "concepts",
        "decision": "decisions",
        "synthesis": "synthesis",
    }
    if target_type not in mapping:
        raise SystemExit(f"Unsupported apply target type: {target_type}")
    return mapping[target_type]


def _promotion_body(target_type: str, summary: str) -> str:
    if target_type == "decision":
        return (
            "## Контекст\n\n"
            f"{summary}\n\n"
            "## Варианты\n\n"
            "- TBD\n\n"
            "## Решение\n\n"
            f"{summary}\n\n"
            "## Последствия\n\n"
            "- needs verification\n"
        )
    if target_type == "concept":
        return (
            "## Суть\n\n"
            f"{summary}\n\n"
            "## Дельта\n\n"
            "Сформировано из promotion draft; требует review.\n\n"
            "## Применение\n\n"
            "- уточнить useful_when и context по результатам review\n"
        )
    return (
        "## Суть\n\n"
        f"{summary}\n\n"
        "## Дельта\n\n"
        "Сформировано из promotion draft; требует review.\n\n"
        "## Применение\n\n"
        "- уточнить practical value по результатам review\n"
    )


def apply_promotion_draft(project: Path, draft_path: str, yes: bool) -> Path:
    if not yes:
        raise SystemExit("Refusing to apply without --yes.")
    path = _resolve_project_path(project, draft_path)
    text = path.read_text(encoding="utf-8")
    verdict_match = re.search(r"^Verdict:\s*(.+)$", text, re.MULTILINE)
    target_match = re.search(r"^Suggested target type:\s*(.+)$", text, re.MULTILINE)
    summary_match = re.search(r"(?ms)^## Distilled summary\s*\n\n(.*?)(?:\n## |\Z)", text)
    if not verdict_match or verdict_match.group(1).strip() != "promote":
        raise SystemExit(f"{relative(project, path)}: draft verdict is not promote")
    if not target_match:
        raise SystemExit(f"{relative(project, path)}: missing target type")
    target_type = target_match.group(1).strip()
    summary = summary_match.group(1).strip() if summary_match else ""
    if not summary:
        raise SystemExit(f"{relative(project, path)}: missing distilled summary")

    page_id = slugify(summary[:80])
    subdir = _target_subdir(target_type)
    page_path = project / "wiki" / subdir / f"{page_id}.md"
    counter = 2
    while page_path.exists():
        page_path = project / "wiki" / subdir / f"{page_id}-{counter}.md"
        counter += 1
    page_id = page_path.stem
    title = summary[:120]
    body = _promotion_body(target_type, summary)
    page_text = (
        "---\n"
        f"id: {page_id}\n"
        f"type: {target_type}\n"
        f'title: "{title}"\n'
        "tags: [memoir, promotion-draft]\n"
        "useful_when:\n"
        '  - "уточнить и принять durable artifact после promotion draft"\n'
        f"date_added: {date.today().isoformat()}\n"
        "use_count: 0\n"
        "last_used: null\n"
    )
    if target_type == "synthesis":
        page_text += "sources: [current-session-2026-05-14]\n"
    page_text += f"---\n\n{body}\n"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(page_text, encoding="utf-8")

    log = project / "wiki" / "log.md"
    with log.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            f"\n## [{date.today().isoformat()}] meta | promotion draft applied\n\n"
            f"- draft: {relative(project, path)}\n"
            f"- page: {relative(project, page_path)}\n"
            f"- target_type: {target_type}\n"
        )
    build_index(project)
    return page_path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="REEFIKI local tools")
    parser.add_argument("--project", dest="root_path", default=".", help="project root with wiki/")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index")
    search_parser = sub.add_parser("search")
    search_parser.add_argument("query", nargs="?", default="")
    search_parser.add_argument("--limit", type=int, default=7)
    search_parser.add_argument("--format", choices=["text", "json"], default="text")
    search_parser.add_argument("--type", dest="page_type")
    search_parser.add_argument("--tag")
    search_parser.add_argument("--link-to")
    search_parser.add_argument("--linked-by")
    search_parser.add_argument("--orphan", action="store_true")
    search_parser.add_argument("--chunks", action="store_true")
    sub.add_parser("privacy")
    dedup_parser = sub.add_parser("dedup")
    dedup_parser.add_argument("source")
    save_parser = sub.add_parser("save")
    save_parser.add_argument("source")
    sub.add_parser("status")
    plan_parser = sub.add_parser("plan")
    plan_sub = plan_parser.add_subparsers(dest="plan_cmd", required=True)
    plan_create_parser = plan_sub.add_parser("create")
    plan_create_parser.add_argument("title")
    plan_check_parser = plan_sub.add_parser("check")
    plan_check_parser.add_argument("path")
    timeline_parser = sub.add_parser("timeline")
    timeline_parser.add_argument("--limit", type=int, default=10)
    guard_parser = sub.add_parser("guard-staged")
    guard_parser.add_argument("--target-project", required=True)
    guard_parser.add_argument("--format", choices=["text", "json"], default="text")
    harvest_commit_parser = sub.add_parser("harvest-commit")
    harvest_commit_parser.add_argument("--target-project", required=True)
    harvest_commit_parser.add_argument("--path", action="append", default=[])
    harvest_commit_parser.add_argument("--message", required=True)
    harvest_commit_parser.add_argument("--no-validate", action="store_true")
    harvest_commit_parser.add_argument("--format", choices=["text", "json"], default="text")
    publish_task_parser = sub.add_parser("publish-task")
    publish_task_parser.add_argument("--base", default="origin/main")
    publish_task_parser.add_argument("--private-remote", default="origin")
    publish_task_parser.add_argument("--public-remote", default="public")
    publish_task_parser.add_argument("--dry-run", action="store_true")
    publish_task_parser.add_argument("--apply", action="store_true")
    publish_task_parser.add_argument("--cleanup", action="store_true")
    publish_task_parser.add_argument("--public-snapshot", action="store_true")
    publish_task_parser.add_argument("--format", choices=["text", "json"], default="text")
    cleanup_worktree_parser = sub.add_parser("cleanup-worktree")
    cleanup_worktree_parser.add_argument("--worktree", required=True)
    cleanup_worktree_parser.add_argument("--base", default="origin/main")
    cleanup_worktree_parser.add_argument("--dry-run", action="store_true")
    cleanup_worktree_parser.add_argument("--apply", action="store_true")
    cleanup_worktree_parser.add_argument("--format", choices=["text", "json"], default="text")
    tool_trigger_parser = sub.add_parser("tool-trigger")
    tool_trigger_parser.add_argument("tool")
    tool_trigger_parser.add_argument("--signal", default="")
    tool_trigger_parser.add_argument("--format", choices=["text", "json"], default="text")
    review_parser = sub.add_parser("review-queues")
    review_parser.add_argument("--stale-days", type=int, default=90)
    review_parser.add_argument("--format", choices=["text", "json"], default="text")
    review_parser.add_argument("--write-report", action="store_true")
    review_parser.add_argument("--type", dest="queue_type")
    backlink_parser = sub.add_parser("backlinks")
    backlink_parser.add_argument("--format", choices=["text", "json"], default="text")
    backlink_parser.add_argument("--write", action="store_true")
    promote_parser = sub.add_parser("promote-dry-run")
    promote_parser.add_argument("content")
    promote_parser.add_argument("--memory-id")
    promote_parser.add_argument("--confidence", type=float, default=0.6)
    promote_parser.add_argument("--format", choices=["text", "json"], default="text")
    promote_parser.add_argument("--write-draft", action="store_true")
    promote_parser.add_argument("--apply-draft")
    promote_parser.add_argument("--yes", action="store_true")
    memory_parser = sub.add_parser("memory")
    memory_sub = memory_parser.add_subparsers(dest="memory_cmd", required=True)
    memory_status_parser = memory_sub.add_parser("status")
    memory_status_parser.add_argument("--project", default="reefiki")
    memory_status_parser.add_argument("--all-projects", action="store_true")
    memory_status_parser.add_argument("--only-open", action="store_true")
    memory_status_parser.add_argument("--summary", action="store_true")
    memory_status_parser.add_argument("--fail-on-open", action="store_true")
    memory_status_parser.add_argument("--format", choices=["text", "json", "jsonl"], default="text")
    memory_preflight_parser = memory_sub.add_parser("preflight")
    memory_preflight_parser.add_argument("--project-name", default="reefiki")
    memory_preflight_parser.add_argument(
        "--visibility",
        choices=["private", "project", "public"],
        default="private",
    )
    memory_preflight_parser.add_argument("--operation", default="lookup")
    memory_preflight_parser.add_argument("--content", default="")
    memory_preflight_parser.add_argument("--path", action="append", default=[])
    memory_preflight_parser.add_argument("--format", choices=["text", "json"], default="text")
    memory_route_parser = memory_sub.add_parser("route")
    memory_route_parser.add_argument("content")
    memory_route_parser.add_argument("--project-hint")
    memory_route_parser.add_argument("--format", choices=["text", "json"], default="text")
    memory_explain_parser = memory_sub.add_parser("explain")
    memory_explain_parser.add_argument("query")
    memory_explain_parser.add_argument("--project", default="reefiki")
    memory_explain_parser.add_argument("--format", choices=["text", "json"], default="text")
    memory_lookup_parser = memory_sub.add_parser("lookup")
    memory_lookup_parser.add_argument("query")
    memory_lookup_parser.add_argument("--project")
    memory_lookup_parser.add_argument("--limit", type=int, default=5)
    memory_lookup_parser.add_argument(
        "--layer",
        choices=["all", "memoir", "reefiki", "graphify"],
        default="all",
    )
    memory_lookup_parser.add_argument("--format", choices=["text", "json"], default="text")
    memory_golden_parser = memory_sub.add_parser("golden")
    memory_golden_parser.add_argument("--project", dest="golden_project", default="reefiki")
    memory_golden_parser.add_argument("--path")
    memory_golden_parser.add_argument("--format", choices=["text", "json"], default="text")
    memory_diff_parser = memory_sub.add_parser("diff")
    memory_diff_parser.add_argument("--project", dest="diff_project", default="reefiki")
    memory_diff_source = memory_diff_parser.add_mutually_exclusive_group(required=True)
    memory_diff_source.add_argument("--from", dest="from_ref")
    memory_diff_source.add_argument("--since-date", dest="since_date")
    memory_diff_parser.add_argument("--to", dest="to_ref")
    memory_diff_parser.add_argument("--format", choices=["text", "json"], default="text")
    memory_pack_parser = memory_sub.add_parser("pack")
    memory_pack_parser.add_argument("task")
    memory_pack_parser.add_argument("--project", dest="pack_project", default="reefiki")
    memory_pack_parser.add_argument("--limit", type=int, default=8)
    memory_pack_parser.add_argument("--strict", action="store_true")
    memory_pack_parser.add_argument("--format", choices=["md", "json"], default="md")
    memory_promote_parser = memory_sub.add_parser("promote")
    memory_promote_parser.add_argument("content")
    memory_promote_parser.add_argument("--target-project", default="reefiki")
    memory_promote_parser.add_argument("--memory-id")
    memory_promote_parser.add_argument("--confidence", type=float, default=0.6)
    memory_promote_parser.add_argument("--write-draft", action="store_true")
    memory_promote_parser.add_argument("--format", choices=["text", "json"], default="text")
    memory_promotion_inbox_parser = memory_sub.add_parser("promotion-inbox")
    memory_promotion_inbox_parser.add_argument("--project", default="reefiki")
    memory_promotion_inbox_parser.add_argument("--show")
    inbox_action = memory_promotion_inbox_parser.add_mutually_exclusive_group()
    inbox_action.add_argument("--apply")
    inbox_action.add_argument("--reject")
    memory_promotion_inbox_parser.add_argument("--reason")
    memory_promotion_inbox_parser.add_argument("--yes", action="store_true")
    memory_promotion_inbox_parser.add_argument("--all", action="store_true")
    memory_promotion_inbox_parser.add_argument("--prune-closed", action="store_true")
    memory_promotion_inbox_parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args(argv)
    repo = repo_root(Path(args.root_path))
    if args.cmd == "guard-staged":
        return print_guard_staged(repo, args.target_project, args.format)
    if args.cmd == "harvest-commit":
        return print_harvest_commit(
            repo,
            args.target_project,
            args.path,
            args.message,
            validate=not args.no_validate,
            fmt=args.format,
        )
    if args.cmd == "publish-task":
        dry_run = args.dry_run or not args.apply
        return print_publish_task(
            repo,
            args.base,
            args.private_remote,
            args.public_remote,
            dry_run=dry_run,
            cleanup=args.cleanup,
            public_snapshot=args.public_snapshot,
            fmt=args.format,
        )
    if args.cmd == "cleanup-worktree":
        dry_run = args.dry_run or not args.apply
        return print_cleanup_worktree(repo, args.worktree, args.base, dry_run, args.format)
    if args.cmd == "tool-trigger":
        return print_tool_trigger(args.tool, args.signal, args.format)
    if args.cmd == "memory":
        if args.memory_cmd == "status":
            return print_memory_status(
                repo,
                args.project,
                args.all_projects,
                args.only_open,
                args.summary,
                args.fail_on_open,
                args.format,
            )
        if args.memory_cmd == "preflight":
            return print_memory_preflight(
                project=args.project_name,
                visibility=args.visibility,
                operation=args.operation,
                content=args.content,
                paths=args.path,
                fmt=args.format,
            )
        if args.memory_cmd == "route":
            return print_memory_route(args.content, args.project_hint, args.format)
        if args.memory_cmd == "explain":
            return print_memory_explain(
                repo,
                query=args.query,
                project_name=args.project,
                fmt=args.format,
            )
        if args.memory_cmd == "lookup":
            layer = args.layer
            return print_global_lookup(
                repo,
                query=args.query,
                project=args.project,
                include_memoir=layer in {"all", "memoir"},
                include_reefiki=layer in {"all", "reefiki"},
                include_graph=layer in {"all", "graphify"},
                limit=args.limit,
                fmt=args.format,
            )
        if args.memory_cmd == "golden":
            return print_memory_golden(
                repo,
                project_name=args.golden_project,
                path=args.path,
                fmt=args.format,
            )
        if args.memory_cmd == "diff":
            return print_memory_diff(
                repo,
                project_name=args.diff_project,
                from_ref=args.from_ref or "HEAD",
                to_ref=args.to_ref,
                since_date=args.since_date,
                fmt=args.format,
            )
        if args.memory_cmd == "pack":
            return print_memory_pack(
                repo,
                project_name=args.pack_project,
                task=args.task,
                limit=args.limit,
                strict=args.strict,
                fmt=args.format,
            )
        if args.memory_cmd == "promote":
            return print_global_promote(
                repo,
                content=args.content,
                target_project=args.target_project,
                memory_id=args.memory_id,
                confidence=args.confidence,
                write_draft=args.write_draft,
                fmt=args.format,
            )
        if args.memory_cmd == "promotion-inbox":
            return print_memory_promotion_inbox(
                repo,
                project_name=args.project,
                show=args.show,
                apply=args.apply,
                reject=args.reject,
                reason=args.reason,
                yes=args.yes,
                include_all=args.all,
                prune_closed=args.prune_closed,
                fmt=args.format,
            )
    project = project_root(Path(args.root_path))
    if args.cmd == "index":
        count = build_index(project)
        print(f"Indexed {count} page(s): {relative(project, db_path(project))}")
        return 0
    if args.cmd == "search":
        return print_search(
            project,
            args.query,
            args.limit,
            args.format,
            args.page_type,
            args.tag,
            args.link_to,
            args.linked_by,
            args.orphan,
            args.chunks,
        )
    if args.cmd == "privacy":
        return privacy_scan(project)
    if args.cmd == "dedup":
        return dedup_check(project, args.source)
    if args.cmd == "save":
        return save_source(project, args.source)
    if args.cmd == "status":
        return status(project)
    if args.cmd == "plan":
        if args.plan_cmd == "create":
            return plan_create(project, args.title)
        if args.plan_cmd == "check":
            return plan_check(project, args.path)
    if args.cmd == "timeline":
        return timeline(project, args.limit)
    if args.cmd == "review-queues":
        if args.write_report:
            report = write_review_queue_report(project, args.stale_days)
            print(relative(project, report))
            return 0
        return print_review_queues(project, args.stale_days, args.format, args.queue_type)
    if args.cmd == "backlinks":
        return print_backlink_index(project, args.format, args.write)
    if args.cmd == "promote-dry-run":
        if args.apply_draft:
            page = apply_promotion_draft(project, args.apply_draft, yes=args.yes)
            print(relative(project, page))
            return 0
        if args.write_draft:
            draft = write_promotion_draft(project, args.content, memory_id=args.memory_id, confidence=args.confidence)
            print(relative(project, draft))
            return 0
        return print_promotion_dry_run(project, args.content, args.memory_id, args.confidence, args.format)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
