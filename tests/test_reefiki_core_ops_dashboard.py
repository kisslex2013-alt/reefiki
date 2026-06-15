import json
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from reefiki_core.ops_dashboard import (
    build_ops_dashboard_server,
    detect_stack,
    discover_git_repositories,
    match_reefiki_mapping,
    ops_dashboard_snapshot,
    parse_roadmap_md,
    parse_tasks_md,
    scan_project_metadata,
)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def init_git(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-b", "main")


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_reefiki_root(root: Path) -> Path:
    write(root / "ROADMAP.md", "#### Phase 0j - audit-driven stabilization ⚡ АКТИВНА\n\nCurrent stage text.\n")
    write(
        root / "TASKS.md",
        """# TASKS

## Sprint 20 - Product readiness

- [x] **T-108** Done task
  - 2026-06-11 closeout: completed.
- [~] **T-111** Split package
  - 2026-06-11 progress: moved helpers.
- [ ] **T-116** Add local Codex Workspace Ops Board
""",
    )
    for project_name in ["reefiki", "Demo"]:
        project = root / "projects" / project_name
        write(project / "AGENTS.md", "rules\n")
        write(project / "_domain.md", "domain\n")
        (project / "raw").mkdir(parents=True, exist_ok=True)
        (project / "inbox").mkdir(parents=True, exist_ok=True)
        (project / "seen").mkdir(parents=True, exist_ok=True)
        write(project / "wiki" / "index.md", "# Index\n")
        write(
            project / "wiki" / "log.md",
            """# Log

## [2026-06-11] meta | sample

- sample log line
""",
        )
    return root


def non_git_file_snapshot(root: Path) -> dict[str, bytes]:
    snapshot: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/") or "/.git/" in rel:
            continue
        snapshot[rel] = path.read_bytes()
    return snapshot


def test_workspace_discovery_finds_one_level_git_repos_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repo = workspace / "app"
    nested = workspace / "plain" / "nested"
    init_git(repo)
    init_git(nested)
    (workspace / "plain").mkdir(exist_ok=True)

    repos, warnings = discover_git_repositories(workspace)

    assert warnings == []
    assert [path.name for path in repos] == ["app"]


def test_safe_metadata_scan_skips_secret_paths_and_forbidden_dirs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_git(repo)
    write(repo / ".env.local", "SHOULD_NOT_BE_READ=1\n")
    write(repo / "node_modules" / "leftpad" / "package.json", "{}")
    write(repo / "raw" / "source.md", "raw should be skipped")
    write(repo / "_wiki" / "AGENTS.md", "linked wiki should be skipped")
    write(repo / "package.json", "{}")
    write(repo / "AGENTS.md", "rules")
    write(repo / "tests" / "test_app.py", "def test_ok(): pass")

    metadata = scan_project_metadata(repo)
    files = set(metadata["files"])

    assert ".env.local" not in files
    assert "node_modules/leftpad/package.json" not in files
    assert "raw/source.md" not in files
    assert "_wiki/AGENTS.md" not in files
    assert "package.json" in files
    assert "tests/test_app.py" in files
    assert metadata["skipped_secret_paths"] == [".env.local"]
    assert "node_modules" in metadata["skipped_dirs"]
    assert "raw" in metadata["skipped_dirs"]
    assert "_wiki" in metadata["skipped_dirs"]


def test_stack_detection_handles_docs_only_without_app_manifest() -> None:
    stack = detect_stack({"README.md", "docs/one.md", "notes/two.md"}, {"docs", "notes"})

    assert stack == ["docs-only"]


def test_tasks_parser_detects_sprint_task_states_and_progress() -> None:
    payload = parse_tasks_md(
        """## Sprint 20 - Product readiness

- [x] **T-108** Done
  - 2026-06-11 closeout: complete.
- [~] **T-111** Active
  - 2026-06-11 progress: moved helpers.
- [ ] **T-116** Todo
"""
    )

    assert payload["current_sprint"] == "Sprint 20 - Product readiness"
    assert payload["task_counts"] == {"done": 1, "todo": 1, "active": 1}
    assert payload["active_tasks"][0]["id"] == "T-111"
    assert payload["next_tasks"][0]["id"] == "T-116"
    assert payload["t111_package_split_status"]["progress"] == ["2026-06-11 progress: moved helpers."]


def test_roadmap_parser_returns_compact_active_phase_summary() -> None:
    payload = parse_roadmap_md(
        """# Roadmap

#### Phase 0j - audit-driven stabilization ⚡ АКТИВНА

Current stage.

More detail.
"""
    )

    assert payload["current_phase"] == "Phase 0j - audit-driven stabilization ⚡ АКТИВНА"
    assert "Current stage" in payload["current_stage_summary"]


def test_reefiki_mapping_exact_missing_and_ambiguous() -> None:
    catalog = {
        "by_exact": {"Demo": Path("projects/Demo"), "Other": Path("projects/Other")},
        "by_lower": {"demo": [Path("projects/Demo")], "other": [Path("projects/Other")]},
    }

    assert match_reefiki_mapping("Demo", {}, catalog)["mapping_status"] == "connected"
    assert match_reefiki_mapping("Missing", {}, catalog)["mapping_status"] == "missing"
    ambiguous = match_reefiki_mapping("Demo", {"project_name": "Other"}, catalog)
    assert ambiguous["mapping_status"] == "ambiguous"


def test_snapshot_shape_contains_required_top_level_and_project_fields(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repo = workspace / "Demo"
    init_git(repo)
    write(repo / "AGENTS.md", "rules")
    write(repo / "pyproject.toml", "[project]\nname='demo'\n")
    write(repo / ".reefiki", "project_name: Demo\n")
    reefiki = make_reefiki_root(tmp_path / "reefiki")

    payload = ops_dashboard_snapshot(workspace, reefiki)

    assert set(payload) == {
        "schema_version",
        "generated_at",
        "workspace_root",
        "reefiki_root",
        "workspace_warnings",
        "kpi",
        "current_work",
        "activity_feed",
        "projects",
        "reefiki",
    }
    assert payload["schema_version"] == "ops-dashboard.v2"
    assert payload["kpi"]["total"] == 1
    project = payload["projects"][0]
    for key in [
        "name",
        "path",
        "is_git_repo",
        "branch",
        "head",
        "last_activity",
        "dirty",
        "dirty_paths_count",
        "ahead",
        "behind",
        "worktree_count",
        "remotes",
        "detected_stack",
        "gates",
        "detected_files",
        "readiness",
        "reefiki_mapping",
        "reefiki_status",
        "latest_log_entries",
        "warnings",
    ]:
        assert key in project
    assert project["reefiki_mapping"]["mapping_status"] == "connected"


def test_server_smoke_returns_html_and_json(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repo = workspace / "Demo"
    init_git(repo)
    write(repo / "AGENTS.md", "rules")
    reefiki = make_reefiki_root(tmp_path / "reefiki")
    server = build_ops_dashboard_server(workspace, reefiki, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        html_body = urllib.request.urlopen(f"http://{host}:{port}/", timeout=5).read().decode("utf-8")
        json_body = urllib.request.urlopen(f"http://{host}:{port}/api/snapshot", timeout=5).read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert "REEFIKI Ops Dashboard v2" in html_body
    assert "REEFIKI Workspace" in html_body
    static_dir = ROOT / "scripts" / "reefiki_core" / "ops_dashboard" / "static"
    app_body = (static_dir / "app.js").read_text(encoding="utf-8")
    i18n_body = (static_dir / "i18n.json").read_text(encoding="utf-8")

    assert 'id="current-work"' in html_body
    assert 'id="reefiki-control"' in html_body
    assert 'id="lang"' in html_body
    assert 'id="theme"' in html_body
    assert "reefiki.opsDashboard.language" in app_body
    assert "reefiki.opsDashboard.theme" in app_body
    assert "setInterval(() => snapshot && renderLogs(snapshot)" not in app_body
    assert 'class="activity-list"' in html_body
    assert 'class="inspector__body"' in html_body
    assert "Русский" in html_body
    assert "Светлая" in i18n_body
    assert json.loads(json_body)["kpi"]["total"] == 1


def test_snapshot_does_not_mutate_target_repo_fixture(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    repo = workspace / "Demo"
    init_git(repo)
    write(repo / "AGENTS.md", "rules")
    write(repo / ".reefiki", "project_name: Demo\n")
    write(repo / "notes.md", "unchanged\n")
    reefiki = make_reefiki_root(tmp_path / "reefiki")
    before = non_git_file_snapshot(repo)

    ops_dashboard_snapshot(workspace, reefiki)

    assert non_git_file_snapshot(repo) == before


def test_server_rejects_non_localhost_bind(tmp_path: Path) -> None:
    from reefiki_core.ops_dashboard import build_ops_dashboard_server

    with pytest.raises(SystemExit, match="localhost"):
        build_ops_dashboard_server(tmp_path, tmp_path, port=0, host="0.0.0.0")
