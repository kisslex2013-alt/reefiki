from pathlib import Path

from scripts.reefiki_core.memory_explain import memory_explain


def test_memory_explain_reports_graphify_unavailable_without_report(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    project = root / "projects" / "reefiki"
    (project / "wiki").mkdir(parents=True)

    payload = memory_explain(root, "where is the memory status implementation?", "reefiki")

    assert payload["query"] == "where is the memory status implementation?"
    assert payload["project"] == "reefiki"
    assert payload["route"]["recommended_layer"] == "graphify"
    assert payload["policy"]["outcome"] == "pass"
    graphify = next(item for item in payload["source_decisions"] if item["layer"] == "graphify")
    assert graphify["status"] == "unavailable"
    assert graphify["reason"] == "missing graphify report"
    assert "graphify" in payload["excluded_sources"]
    assert payload["next_action"] == "run graphify only when structural navigation is needed"


def test_memory_explain_keeps_roadmap_queries_on_reefiki(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    project = root / "projects" / "reefiki"
    (project / "wiki").mkdir(parents=True)

    payload = memory_explain(root, "continue REEFIKI roadmap development", "reefiki")

    reefiki_source = next(item for item in payload["source_decisions"] if item["layer"] == "reefiki")
    memoir_source = next(item for item in payload["source_decisions"] if item["layer"] == "memoir")
    assert payload["route"]["recommended_layer"] == "reefiki"
    assert reefiki_source["status"] == "selected"
    assert memoir_source["status"] == "secondary"
    assert payload["next_action"] == "run memory lookup --project reefiki --layer reefiki"
