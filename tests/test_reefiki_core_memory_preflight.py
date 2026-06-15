from scripts.reefiki_core.memory_preflight import (
    memory_global_strict_preflight,
    memory_preflight,
)


def test_memory_preflight_passes_selected_project_scope() -> None:
    payload = memory_preflight(
        project="reefiki",
        visibility="private",
        operation="lookup",
        content="normal query",
        paths=["projects/reefiki"],
    )

    assert payload["outcome"] == "pass"
    assert payload["blocking_reasons"] == []


def test_memory_preflight_blocks_other_project_scope() -> None:
    payload = memory_preflight(
        project="reefiki",
        visibility="private",
        operation="lookup",
        content="normal query",
        paths=["projects/metrica"],
    )

    assert payload["outcome"] == "block"
    assert "forbidden_scope:projects/metrica" in payload["blocking_reasons"]


def test_memory_preflight_blocks_public_secret_content() -> None:
    content = "api_" + "key=secret"
    payload = memory_preflight(
        project="reefiki",
        visibility="public",
        operation="export",
        content=content,
        paths=["projects/reefiki"],
    )

    assert payload["outcome"] == "block"
    assert "secret_like_content" in payload["blocking_reasons"]


def test_memory_global_strict_preflight_blocks_metrica_even_for_metrica_project() -> None:
    payload = memory_global_strict_preflight(
        project="metrica",
        visibility="private",
        operation="lookup",
        content="normal query",
        paths=["projects/metrica"],
    )

    assert payload["outcome"] == "block"
    assert "forbidden_scope:projects/metrica" in payload["blocking_reasons"]
