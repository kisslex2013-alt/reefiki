from __future__ import annotations

import tempfile
from datetime import date, datetime
from pathlib import Path

from .git_utils import require_git_success, run_git
from .publish_classification import private_project_inventory_payload
from .repo_paths import repo_path_in_scope
from .secret_scan import secret_content_scan_payload


def inspect_public_snapshot(repo: Path, private_projects: list[str]) -> dict[str, object] | None:
    return run_public_snapshot(repo, public_remote=None, private_projects=private_projects)


def push_public_snapshot(repo: Path, public_remote: str, private_projects: list[str]) -> dict[str, object] | None:
    return run_public_snapshot(repo, public_remote=public_remote, private_projects=private_projects)


def run_public_snapshot(repo: Path, public_remote: str | None, private_projects: list[str]) -> dict[str, object] | None:
    inventory = private_project_inventory_payload(repo)
    if inventory["outcome"] != "pass":
        raise SystemExit(str(inventory["reason"]))
    private_projects = list(inventory["private_projects"])
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
            staged = require_git_success(run_git(snapshot, ["ls-files"]), "public snapshot scan failed")
            leaked = [
                path
                for path in staged.splitlines()
                if any(repo_path_in_scope(path, f"projects/{name}") for name in private_projects)
            ]
            if leaked:
                return {
                    "outcome": "block",
                    "reason": "private_path_leak",
                    "blocking_paths": leaked,
                }
            staged_paths = [line.strip() for line in staged.splitlines() if line.strip()]
            secret_scan = secret_content_scan_payload(snapshot, staged_paths, "public-snapshot")
            if secret_scan["outcome"] != "pass":
                return {
                    "outcome": "block",
                    "reason": secret_scan["reason"],
                    "checked_paths": secret_scan["checked_paths"],
                    "blocking_paths": secret_scan["blocking_paths"],
                }
            if public_remote is None:
                return None
            require_git_success(
                run_git(snapshot, ["commit", "-m", f"public: template snapshot {date.today().isoformat()}"]),
                "public snapshot commit failed",
            )
            require_git_success(run_git(snapshot, ["push", public_remote, "HEAD:main", "--force-with-lease"]), "public snapshot push failed")
            return None
        finally:
            run_git(repo, ["worktree", "remove", "--force", str(snapshot)])
