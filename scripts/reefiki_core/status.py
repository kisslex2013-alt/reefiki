from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path

from .markdown import as_text, parse_frontmatter
from .privacy import inbox_items
from .project_paths import iter_pages


def status(project: Path) -> int:
    inbox = [path.name for path in inbox_items(project)]
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
