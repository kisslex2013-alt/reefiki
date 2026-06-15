from scripts.reefiki_core.secret_scan import print_secret_scan, secret_content_scan_payload


def test_secret_content_scan_payload_passes_safe_files_and_skips_missing(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("safe public content", encoding="utf-8")

    payload = secret_content_scan_payload(repo, ["README.md", "missing.md"], "publish-task")

    assert payload == {
        "operation": "publish-task",
        "outcome": "pass",
        "reason": None,
        "checked_paths": ["README.md"],
        "blocking_paths": [],
    }


def test_secret_content_scan_payload_blocks_sensitive_content(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    marker = "api" + "_key"
    (repo / "notes.md").write_text(f"{marker} = 'value'\n", encoding="utf-8")

    payload = secret_content_scan_payload(repo, ["notes.md"], "publish-task")

    assert payload["outcome"] == "block"
    assert payload["reason"] == "secret_like_content"
    assert payload["checked_paths"] == ["notes.md"]
    assert payload["blocking_paths"] == ["notes.md"]


def test_print_secret_scan_text_reports_checked_paths(tmp_path, capsys) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("safe public content", encoding="utf-8")

    assert print_secret_scan(repo, ["README.md"], "text") == 0

    output = capsys.readouterr().out
    assert "outcome: pass" in output
    assert "- README.md" in output


def test_print_secret_scan_json_returns_nonzero_for_block(tmp_path, capsys) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    marker = "api" + "_key"
    (repo / "notes.md").write_text(f"{marker} = 'value'\n", encoding="utf-8")

    assert print_secret_scan(repo, ["notes.md"], "json") == 1

    output = capsys.readouterr().out
    assert '"outcome": "block"' in output
    assert '"blocking_paths": [' in output
