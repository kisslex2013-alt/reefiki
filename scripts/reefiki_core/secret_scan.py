from __future__ import annotations

import json
from pathlib import Path

try:
    from reefiki_memory import AccessBoundaryContext, PolicySafetyLayer
except ModuleNotFoundError:  # pragma: no cover - used when imported as scripts.reefiki_core in tests
    from scripts.reefiki_memory import AccessBoundaryContext, PolicySafetyLayer

from .repo_paths import normalize_repo_path


def secret_content_scan_payload(
    repo: Path,
    paths: list[str],
    operation: str,
) -> dict[str, object]:
    boundary = AccessBoundaryContext(
        project="repo",
        allowed_scopes=[],
        forbidden_scopes=[],
        visibility="private",
    )
    scanner = PolicySafetyLayer()
    checked_paths: list[str] = []
    blocking_paths: list[str] = []
    for path_text in paths:
        normalized = normalize_repo_path(path_text)
        path = repo / normalized
        if not path.exists() or not path.is_file():
            continue
        checked_paths.append(normalized)
        content = path.read_text(encoding="utf-8", errors="replace")
        result = scanner.preflight(
            boundary,
            operation=operation,
            content=content,
            paths=[normalized],
        )
        if "secret_like_content" in result.blocking_reasons:
            blocking_paths.append(normalized)
    return {
        "operation": operation,
        "outcome": "block" if blocking_paths else "pass",
        "reason": "secret_like_content" if blocking_paths else None,
        "checked_paths": checked_paths,
        "blocking_paths": blocking_paths,
    }


def print_secret_scan(repo: Path, paths: list[str], fmt: str) -> int:
    payload = secret_content_scan_payload(repo, paths, "secret-scan")
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"outcome: {payload['outcome']}")
        if payload.get("reason"):
            print(f"reason: {payload['reason']}")
        print("checked_paths:")
        for path in payload.get("checked_paths", []):
            print(f"- {path}")
        if payload.get("blocking_paths"):
            print("blocking_paths:")
            for path in payload["blocking_paths"]:
                print(f"- {path}")
    return 0 if payload["outcome"] == "pass" else 1
