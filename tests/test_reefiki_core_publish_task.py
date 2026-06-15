from scripts.reefiki_core import publish_task


def _inventory() -> dict[str, object]:
    return {
        "outcome": "pass",
        "reason": None,
        "private_projects": ["reefiki"],
        "real_projects": ["reefiki"],
        "missing_private_projects": [],
    }


def test_publish_task_payload_blocks_dirty_worktree(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(publish_task, "git_current_branch", lambda _repo: "codex/task")
    monkeypatch.setattr(publish_task, "git_status_paths", lambda _repo: ["TASKS.md"])
    monkeypatch.setattr(publish_task, "private_project_inventory_payload", lambda _repo: _inventory())

    code, payload = publish_task.publish_task_payload(
        tmp_path,
        base="origin/main",
        private_remote="origin",
        public_remote="public",
        dry_run=True,
        cleanup=True,
        public_snapshot=False,
    )

    assert code == 1
    assert payload["outcome"] == "block"
    assert payload["reason"] == "dirty_worktree"
    assert payload["error_code"] == "dirty_worktree"
    assert payload["dirty_paths"] == ["TASKS.md"]


def test_publish_task_payload_reports_mixed_dry_run_actions(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(publish_task, "git_current_branch", lambda _repo: "codex/task")
    monkeypatch.setattr(publish_task, "git_status_paths", lambda _repo: [])
    monkeypatch.setattr(publish_task, "private_project_inventory_payload", lambda _repo: _inventory())
    monkeypatch.setattr(publish_task, "git_ref_exists", lambda _repo, _base: True)
    monkeypatch.setattr(publish_task, "git_changed_paths", lambda _repo, _base: ["TASKS.md", "projects/reefiki/wiki/log.md"])
    monkeypatch.setattr(
        publish_task,
        "secret_content_scan_payload",
        lambda _repo, _paths, _operation: {"outcome": "pass", "reason": None, "checked_paths": [], "blocking_paths": []},
    )
    monkeypatch.setattr(publish_task, "git_is_ancestor", lambda _repo, _ancestor, _descendant: True)
    monkeypatch.setattr(publish_task, "git_head", lambda _repo, short=False: "abc123")
    monkeypatch.setattr(publish_task, "inspect_public_snapshot", lambda _repo, _private_projects: None)

    code, payload = publish_task.publish_task_payload(
        tmp_path,
        base="origin/main",
        private_remote="origin",
        public_remote="public",
        dry_run=True,
        cleanup=True,
        public_snapshot=False,
    )

    assert code == 0
    assert payload["outcome"] == "pass"
    assert payload["diff_class"] == "mixed"
    assert payload["actions"] == ["push_task_branch", "push_private_main", "push_public_snapshot"]
    assert payload["post_merge_actions"] == ["cleanup_task_worktree", "cleanup_task_branch"]
    assert payload["public_snapshot_exclusions"] == ["projects/reefiki"]
    assert payload["public_snapshot_intent"] == "diff-class:mixed"
    assert payload["snapshot_origin"] == "dry-run-inspect"


def test_publish_task_payload_blocks_secret_scan(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(publish_task, "git_current_branch", lambda _repo: "codex/task")
    monkeypatch.setattr(publish_task, "git_status_paths", lambda _repo: [])
    monkeypatch.setattr(publish_task, "private_project_inventory_payload", lambda _repo: _inventory())
    monkeypatch.setattr(publish_task, "git_ref_exists", lambda _repo, _base: True)
    monkeypatch.setattr(publish_task, "git_changed_paths", lambda _repo, _base: ["notes.md"])
    monkeypatch.setattr(
        publish_task,
        "secret_content_scan_payload",
        lambda _repo, _paths, _operation: {
            "outcome": "block",
            "reason": "secret_pattern_detected",
            "checked_paths": ["notes.md"],
            "blocking_paths": ["notes.md"],
        },
    )

    code, payload = publish_task.publish_task_payload(
        tmp_path,
        base="origin/main",
        private_remote="origin",
        public_remote="public",
        dry_run=True,
        cleanup=True,
        public_snapshot=False,
    )

    assert code == 1
    assert payload["outcome"] == "block"
    assert payload["reason"] == "secret_pattern_detected"
    assert payload["error_code"] == "secret_pattern_detected"
    assert payload["blocking_paths"] == ["notes.md"]


def test_publish_task_payload_reports_explicit_public_snapshot_request_for_private_only(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(publish_task, "git_current_branch", lambda _repo: "codex/task")
    monkeypatch.setattr(publish_task, "git_status_paths", lambda _repo: [])
    monkeypatch.setattr(publish_task, "private_project_inventory_payload", lambda _repo: _inventory())
    monkeypatch.setattr(publish_task, "git_ref_exists", lambda _repo, _base: True)
    monkeypatch.setattr(publish_task, "git_changed_paths", lambda _repo, _base: ["projects/reefiki/wiki/log.md"])
    monkeypatch.setattr(
        publish_task,
        "secret_content_scan_payload",
        lambda _repo, _paths, _operation: {"outcome": "pass", "reason": None, "checked_paths": [], "blocking_paths": []},
    )
    monkeypatch.setattr(publish_task, "git_is_ancestor", lambda _repo, _ancestor, _descendant: True)
    monkeypatch.setattr(publish_task, "git_head", lambda _repo, short=False: "abc123")

    code, payload = publish_task.publish_task_payload(
        tmp_path,
        base="origin/main",
        private_remote="origin",
        public_remote="public",
        dry_run=True,
        cleanup=True,
        public_snapshot=True,
    )

    assert code == 0
    assert payload["diff_class"] == "private-only"
    assert payload["public_snapshot_requested"] is True
    assert payload["public_snapshot_intent"] == "requested"
    assert payload["snapshot_origin"] == "none"


def test_print_publish_task_text(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(
        publish_task,
        "publish_task_payload",
        lambda *args, **kwargs: (
            0,
            {
                "outcome": "pass",
                "branch": "codex/task",
                "diff_class": "public-safe",
                "actions": ["push_task_branch"],
                "changed_paths": ["TASKS.md"],
            },
        ),
    )

    assert publish_task.print_publish_task(tmp_path, "origin/main", "origin", "public", True, True, False, "text") == 0

    output = capsys.readouterr().out
    assert "outcome: pass" in output
    assert "branch: codex/task" in output
    assert "- push_task_branch" in output
