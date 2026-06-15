from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from .duplicates import _is_duplicate_source_signal, _normalize_text, _titles_are_similar
from .markdown import as_text, extract_wiki_links
from .project_paths import relative
from .wiki_rows import _wiki_rows


def _related_ids(body: str) -> set[str]:
    match = re.search(r"(?ms)^## Related\s*\n(.*?)(?:\n## |\Z)", body)
    if not match:
        return set()
    related_block = match.group(1)
    return set(re.findall(r"\[\[([a-z0-9\-]+)\]\]", related_block))


def _all_wiki_link_ids(body: str) -> set[str]:
    return {as_text(item["target_id"]) for item in extract_wiki_links(body)}


def _intentional_one_way_inbound_ids(body: str) -> set[str]:
    match = re.search(r"(?ms)^## Intentional one-way inbound links\s*\n(.*?)(?:\n## |\Z)", body)
    if not match:
        return set()
    block = match.group(1)
    ids: set[str] = set()
    for line in block.splitlines():
        stripped = re.sub(r"^\s*[-*]\s*", "", line).strip()
        if not stripped:
            continue
        ids.update(re.findall(r"`([a-z0-9\-]+)`", stripped))
        ids.update(re.findall(r"\[\[([a-z0-9\-]+)\]\]", stripped))
        if re.fullmatch(r"[a-z0-9\-]+", stripped):
            ids.add(stripped)
    return ids


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
    intentional_one_way_inbound_by_id = {
        as_text(row["id"]): _intentional_one_way_inbound_ids(as_text(row["body"])) for row in rows
    }
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
                if as_text(other["id"]) != row_id
                and as_text(other["type"]) in compatible_types
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
            intentional_one_way_inbound = intentional_one_way_inbound_by_id[row_id]
            if row_id in source_links and source_id not in all_links and source_id not in intentional_one_way_inbound:
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


REVIEW_QUEUE_ORDER = [
    "placeholder_link",
    "conflict_review",
    "needs_verification",
    "duplicate_candidate",
    "orphan_review",
    "stale_review",
    "missing_backlink",
]


def _review_queue_sort_key(queue_type: str) -> tuple[int, str]:
    try:
        return (REVIEW_QUEUE_ORDER.index(queue_type), queue_type)
    except ValueError:
        return (len(REVIEW_QUEUE_ORDER), queue_type)


def review_queue_summary(items: list[dict[str, object]], limit: int = 5) -> dict[str, object]:
    counts = Counter(as_text(item["queue_type"]) for item in items)
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in items:
        grouped.setdefault(as_text(item["queue_type"]), []).append(item)
    queues: list[dict[str, object]] = []
    for queue_type in sorted(grouped, key=_review_queue_sort_key):
        queue_items = grouped[queue_type]
        sample_page_ids = list(dict.fromkeys(as_text(item["page_id"]) for item in queue_items))[:limit]
        page_counts = Counter(as_text(item["page_id"]) for item in queue_items)
        top_page_ids = [{"page_id": page_id, "count": count} for page_id, count in page_counts.most_common(limit)]
        queues.append(
            {
                "queue_type": queue_type,
                "count": counts[queue_type],
                "sample_page_ids": sample_page_ids,
                "top_page_ids": top_page_ids,
                "suggested_action": as_text(queue_items[0].get("suggested_action")),
            }
        )
    return {
        "total": len(items),
        "counts": {queue_type: counts[queue_type] for queue_type in sorted(counts, key=_review_queue_sort_key)},
        "queues": queues,
    }


def print_review_queue_summary(items: list[dict[str, object]], limit: int) -> None:
    summary = review_queue_summary(items, limit=limit)
    print(f"review queue candidates: {summary['total']}")
    for queue in summary["queues"]:
        samples = ", ".join(queue["sample_page_ids"])
        print(f"- {queue['queue_type']}: {queue['count']}")
        if samples:
            print(f"  sample: {samples}")
        top_pages = ", ".join(f"{item['page_id']} ({item['count']})" for item in queue["top_page_ids"])
        if top_pages:
            print(f"  top pages: {top_pages}")
        print(f"  action: {queue['suggested_action']}")
    if items:
        print("Use --type <queue> for details or --write-report for a triage artifact.")


def print_review_queues(
    project: Path,
    stale_days: int,
    fmt: str,
    queue_type: str | None,
    summary: bool = False,
    limit: int = 5,
) -> int:
    items = review_queue_scan(project, stale_days=stale_days, queue_type=queue_type)
    if summary:
        payload = review_queue_summary(items, limit=limit)
        if fmt == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        print_review_queue_summary(items, limit=limit)
        return 0
    if fmt == "json":
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return 0
    if not items:
        print("No review queue candidates.")
        return 0
    visible_items = items[: max(1, limit)]
    for item in visible_items:
        print(f"{item['queue_type']}: {item['page_id']}")
        print(f"  reason: {item['reason']}")
        if item["related_page_ids"]:
            print(f"  related: {', '.join(item['related_page_ids'])}")
        print(f"  action: {item['suggested_action']}")
    if len(visible_items) < len(items):
        print(f"Showing first {len(visible_items)} of {len(items)} candidate(s). Use --limit to adjust.")
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
        lines.extend(["No review queue candidates.", ""])
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


TYPE_DUPLICATE_COMPATIBILITY = {
    "source": {"source"},
    "entity": {"entity"},
    "concept": {"concept", "decision", "synthesis"},
    "decision": {"concept", "decision", "synthesis"},
    "synthesis": {"concept", "decision", "synthesis"},
    "skill": {"skill"},
}
