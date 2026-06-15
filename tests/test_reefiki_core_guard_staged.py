from scripts.reefiki_core import guard_staged


def test_guard_staged_payload_allows_only_target_project_wiki_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        guard_staged,
        "git_staged_entries",
        lambda _repo: [("M", "projects/reefiki/wiki/log.md")],
    )
    monkeypatch.setattr(guard_staged, "staged_file_is_append_only", lambda _repo, _path: True)

    payload = guard_staged.guard_staged_payload(tmp_path, "reefiki")

    assert payload["outcome"] == "pass"
    assert payload["mode"] == "harvest"
    assert payload["blocking_paths"] == []


def test_guard_staged_payload_blocks_cross_project_and_non_wiki_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        guard_staged,
        "git_staged_entries",
        lambda _repo: [
            ("M", "projects/reefiki/wiki/log.md"),
            ("M", "projects/metrica/wiki/log.md"),
            ("M", "scripts/reefiki.py"),
        ],
    )
    monkeypatch.setattr(guard_staged, "staged_file_is_append_only", lambda _repo, _path: True)

    payload = guard_staged.guard_staged_payload(tmp_path, "reefiki")

    assert payload["outcome"] == "block"
    assert payload["blocking_paths"] == ["projects/metrica/wiki/log.md", "scripts/reefiki.py"]


def test_guard_staged_process_mode_allows_process_paths_and_raw_creates(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        guard_staged,
        "git_staged_entries",
        lambda _repo: [
            ("D", "projects/reefiki/inbox/source.md"),
            ("A", "projects/reefiki/raw/source.md"),
            ("A", "projects/reefiki/seen/duplicate.md"),
            ("M", "projects/reefiki/wiki/index.md"),
            ("M", "projects/reefiki/wiki/log.md"),
            ("A", "projects/reefiki/wiki/sources/source.md"),
        ],
    )
    monkeypatch.setattr(guard_staged, "staged_file_is_append_only", lambda _repo, _path: True)

    payload = guard_staged.guard_staged_payload(tmp_path, "reefiki", mode="process")

    assert payload["outcome"] == "pass"
    assert payload["allowed_prefix"] == "process-profile:projects/reefiki"
    assert payload["blocking_paths"] == []


def test_guard_staged_process_mode_blocks_raw_modification(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        guard_staged,
        "git_staged_entries",
        lambda _repo: [("M", "projects/reefiki/raw/source.md")],
    )

    payload = guard_staged.guard_staged_payload(tmp_path, "reefiki", mode="process")

    assert payload["outcome"] == "block"
    assert payload["blocking_paths"] == ["projects/reefiki/raw/source.md"]
    assert payload["violations"] == [
        {
            "path": "projects/reefiki/raw/source.md",
            "reason": "raw_modify_delete_forbidden",
        }
    ]


def test_guard_staged_process_mode_blocks_raw_deletion(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        guard_staged,
        "git_staged_entries",
        lambda _repo: [("D", "projects/reefiki/raw/source.md")],
    )

    payload = guard_staged.guard_staged_payload(tmp_path, "reefiki", mode="process")

    assert payload["outcome"] == "block"
    assert payload["blocking_paths"] == ["projects/reefiki/raw/source.md"]
    assert payload["violations"] == [
        {
            "path": "projects/reefiki/raw/source.md",
            "reason": "raw_modify_delete_forbidden",
        }
    ]


def test_guard_staged_process_mode_blocks_cross_project_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        guard_staged,
        "git_staged_entries",
        lambda _repo: [("A", "projects/metrica/wiki/sources/source.md")],
    )

    payload = guard_staged.guard_staged_payload(tmp_path, "reefiki", mode="process")

    assert payload["outcome"] == "block"
    assert payload["blocking_paths"] == ["projects/metrica/wiki/sources/source.md"]
    assert payload["violations"] == [
        {
            "path": "projects/metrica/wiki/sources/source.md",
            "reason": "outside_mode_scope",
        }
    ]


def test_guard_staged_blocks_non_append_log_edits(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        guard_staged,
        "git_staged_entries",
        lambda _repo: [("M", "projects/reefiki/wiki/log.md")],
    )
    monkeypatch.setattr(guard_staged, "staged_file_is_append_only", lambda _repo, _path: False)

    payload = guard_staged.guard_staged_payload(tmp_path, "reefiki", mode="harvest")

    assert payload["outcome"] == "block"
    assert payload["blocking_paths"] == ["projects/reefiki/wiki/log.md"]
    assert payload["violations"] == [
        {
            "path": "projects/reefiki/wiki/log.md",
            "reason": "log_not_append_only",
        }
    ]


def test_guard_staged_docs_mode_blocks_raw_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        guard_staged,
        "git_staged_entries",
        lambda _repo: [("A", "projects/reefiki/raw/source.md")],
    )

    payload = guard_staged.guard_staged_payload(tmp_path, "reefiki", mode="docs")

    assert payload["outcome"] == "block"
    assert payload["blocking_paths"] == ["projects/reefiki/raw/source.md"]


def test_guard_staged_code_docs_mode_allows_schema_and_code_slice(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        guard_staged,
        "git_staged_entries",
        lambda _repo: [
            ("M", "TASKS.md"),
            ("M", "projects/reefiki/wiki/_schema.md"),
            ("M", "projects/reefiki/wiki/log.md"),
            ("M", "scripts/reefiki_core/link_confidence.py"),
            ("M", "tests/test_reefiki_core_link_confidence.py"),
        ],
    )
    monkeypatch.setattr(guard_staged, "staged_file_is_append_only", lambda _repo, _path: True)

    payload = guard_staged.guard_staged_payload(tmp_path, "reefiki", mode="code/docs")

    assert payload["outcome"] == "pass"
    assert payload["allowed_prefix"] == "code/docs-profile:projects/reefiki"
    assert payload["blocking_paths"] == []


def test_guard_staged_payload_normalizes_project_name_with_spaces(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        guard_staged,
        "git_staged_entries",
        lambda _repo: [("M", "projects/Security Guidance/wiki/log.md")],
    )
    monkeypatch.setattr(guard_staged, "staged_file_is_append_only", lambda _repo, _path: True)

    payload = guard_staged.guard_staged_payload(tmp_path, "Security Guidance")

    assert payload["outcome"] == "pass"
    assert payload["allowed_prefix"] == "projects/Security Guidance/wiki/"


def test_print_guard_staged_text_reports_blocking_paths(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(
        guard_staged,
        "guard_staged_payload",
        lambda _repo, _target_project, mode="harvest": {
            "target_project": "reefiki",
            "mode": mode,
            "allowed_prefix": "projects/reefiki/wiki/",
            "outcome": "block",
            "staged_paths": ["scripts/reefiki.py"],
            "blocking_paths": ["scripts/reefiki.py"],
            "violations": [{"path": "scripts/reefiki.py", "reason": "outside_mode_scope"}],
        },
    )

    assert guard_staged.print_guard_staged(tmp_path, "reefiki", "text") == 1

    output = capsys.readouterr().out
    assert "outcome: block" in output
    assert "blocking_paths:" in output
    assert "- scripts/reefiki.py" in output
