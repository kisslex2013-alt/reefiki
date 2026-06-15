from pathlib import Path

import pytest

from scripts.reefiki_core import public_snapshot


def test_public_snapshot_wrappers_delegate_with_expected_remote(monkeypatch) -> None:
    calls: list[tuple[Path, str | None, list[str]]] = []

    def fake_run(repo: Path, public_remote: str | None, private_projects: list[str]):
        calls.append((repo, public_remote, private_projects))
        return {"outcome": "pass"}

    monkeypatch.setattr(public_snapshot, "run_public_snapshot", fake_run)

    repo = Path("repo")
    assert public_snapshot.inspect_public_snapshot(repo, ["reefiki"]) == {"outcome": "pass"}
    assert public_snapshot.push_public_snapshot(repo, "public", ["reefiki"]) == {"outcome": "pass"}
    assert calls == [(repo, None, ["reefiki"]), (repo, "public", ["reefiki"])]


def test_run_public_snapshot_blocks_failed_private_inventory(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        public_snapshot,
        "private_project_inventory_payload",
        lambda _repo: {"outcome": "block", "reason": "private_project_inventory_missing"},
    )

    with pytest.raises(SystemExit, match="private_project_inventory_missing"):
        public_snapshot.run_public_snapshot(tmp_path, public_remote=None, private_projects=[])
