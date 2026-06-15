from scripts.reefiki_core.status import status


def test_status_prints_project_snapshot(tmp_path, capsys) -> None:
    project = tmp_path / "fixture"
    for directory in ["inbox", "seen", "wiki/concepts"]:
        (project / directory).mkdir(parents=True, exist_ok=True)
    (project / "inbox" / ".gitkeep").write_text("", encoding="utf-8")
    (project / "inbox" / "source.md").write_text("source", encoding="utf-8")
    (project / "seen" / "expired.md").write_text("quarantine_until: 2026-01-01\n", encoding="utf-8")
    (project / "seen" / "active.md").write_text("quarantine_until: 2999-01-01\n", encoding="utf-8")
    (project / "wiki" / "log.md").write_text(
        "# Log\n\n## [2026-06-01] /lint\n\n## [2026-06-10] /lint\n",
        encoding="utf-8",
    )
    (project / "wiki" / "index.md").write_text("# Index\n", encoding="utf-8")
    (project / "wiki" / "concepts" / "old.md").write_text(
        """---
id: old
type: concept
title: "Old"
tags: [test]
useful_when:
  - "checking project status summary"
date_added: 2026-01-01
use_count: 0
---
Body.
""",
        encoding="utf-8",
    )

    assert status(project) == 0

    output = capsys.readouterr().out
    assert "Project: fixture" in output
    assert "Inbox: 1 (source.md)" in output
    assert "Seen: 2 (1 expired, 1 active)" in output
    assert "Wiki: concept=1 | stale=1" in output
    assert "Last lint: 2026-06-10" in output
