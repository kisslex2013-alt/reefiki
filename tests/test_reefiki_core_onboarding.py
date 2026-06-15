from pathlib import Path

from scripts.reefiki_core.onboarding import onboarding_wizard_payload


def test_onboarding_wizard_dry_run_does_not_write(tmp_path: Path) -> None:
    payload = onboarding_wizard_payload(tmp_path)

    assert payload["mode"] == "dry-run"
    assert payload["artifacts"] == []
    assert [step["step"] for step in payload["steps"]] == [
        "create",
        "save",
        "process",
        "query",
        "harvest",
        "status",
    ]
    assert not (tmp_path / "projects").exists()


def test_onboarding_wizard_fixture_writes_first_run_artifacts(tmp_path: Path) -> None:
    payload = onboarding_wizard_payload(tmp_path, fixture_root=tmp_path)

    assert payload["mode"] == "fixture"
    artifacts = set(payload["artifacts"])
    assert {
        "projects/reefiki-onboarding-demo/AGENTS.md",
        "projects/reefiki-onboarding-demo/_domain.md",
        "projects/reefiki-onboarding-demo/raw/onboarding-source.md",
        "projects/reefiki-onboarding-demo/wiki/concepts/onboarding-first-source.md",
        "projects/reefiki-onboarding-demo/wiki/synthesis/onboarding-session-summary.md",
        "projects/reefiki-onboarding-demo/wiki/index.md",
        "projects/reefiki-onboarding-demo/wiki/log.md",
    }.issubset(artifacts)
    assert payload["transient_artifacts"] == [
        "projects/reefiki-onboarding-demo/inbox/onboarding-source.md"
    ]
    assert not (tmp_path / "projects" / "reefiki-onboarding-demo" / "inbox" / "onboarding-source.md").exists()
    log = (tmp_path / "projects" / "reefiki-onboarding-demo" / "wiki" / "log.md").read_text(encoding="utf-8")
    assert "/save" in log
    assert "/process" in log
    assert "/query" in log
    assert "/harvest" in log
    assert "/status" in log
