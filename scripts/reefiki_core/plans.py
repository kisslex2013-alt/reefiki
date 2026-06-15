from __future__ import annotations

import hashlib
import re
from datetime import date
from pathlib import Path

from .file_utils import slugify, write_new_text
from .project_paths import relative
from .repo_paths import resolve_contained_path


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
    try:
        path = write_new_text(path, body + f"\n<!-- reefiki-plan-sha256:{checksum} -->\n")
    except FileExistsError:
        raise SystemExit(f"Plan already exists: {relative(project, path)}") from None
    print(relative(project, path))
    return 0


def plan_check(project: Path, path_arg: str) -> int:
    path, reason = resolve_contained_path(project, path_arg)
    if path is None:
        print(f"Refused: {reason}")
        return 2
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
