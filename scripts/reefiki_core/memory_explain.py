from __future__ import annotations

import json
from pathlib import Path

try:
    from reefiki_memory import build_default_registry
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.reefiki_memory import build_default_registry

from .code_context import graphify_report_path
from .markdown import as_text
from .memory_preflight import memory_preflight
from .memory_route import memory_route
from .project_paths import find_project


def memory_explain(root: Path, query: str, project_name: str) -> dict[str, object]:
    project = find_project(root, project_name)
    route = memory_route(query, project_hint=project.name)
    policy = memory_preflight(
        project=project.name,
        visibility="private",
        operation="explain",
        content=query,
        paths=[f"projects/{project.name}"],
    )
    registry = build_default_registry(project)
    selected_layers = {as_text(route.get("recommended_layer"))}
    selected_layers.update(as_text(layer) for layer in route.get("secondary_layers", []))
    graph_report = graphify_report_path(project)
    source_decisions: list[dict[str, object]] = []
    for layer in sorted(registry.providers):
        if policy["outcome"] == "block":
            status = "blocked"
            reason = "policy block"
        elif layer == "graphify" and graph_report is None and layer in selected_layers:
            status = "unavailable"
            reason = "missing graphify report"
        elif layer == route.get("recommended_layer"):
            status = "selected"
            reason = as_text(route.get("reason"))
        elif layer in route.get("secondary_layers", []):
            status = "secondary"
            reason = "secondary layer from route"
        else:
            status = "excluded"
            reason = "not selected by route"
        source_decisions.append(
            {
                "layer": layer,
                "status": status,
                "reason": reason,
                "capabilities": [
                    str(capability)
                    for capability in registry.providers[layer].capabilities
                ],
            }
        )
    excluded_sources = [
        as_text(item["layer"])
        for item in source_decisions
        if item["status"] in {"blocked", "excluded", "unavailable"}
    ]
    next_action = f"run memory lookup --project {project.name} --layer {route.get('recommended_layer')}"
    if policy["outcome"] == "block":
        next_action = "resolve policy block before reading providers"
    elif "graphify" in excluded_sources and route.get("recommended_layer") == "graphify":
        next_action = "run graphify only when structural navigation is needed"
    return {
        "query": query,
        "project": project.name,
        "route": route,
        "policy": policy,
        "source_decisions": source_decisions,
        "excluded_sources": excluded_sources,
        "next_action": next_action,
    }


def print_memory_explain(root: Path, query: str, project_name: str, fmt: str) -> int:
    result = memory_explain(root, query, project_name)
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["policy"]["outcome"] != "block" else 1
    print(f"query: {result['query']}")
    print(f"project: {result['project']}")
    route = result["route"]
    print(f"route: {route.get('recommended_layer')}")
    print(f"reason: {route.get('reason')}")
    print(f"policy: {result['policy'].get('outcome')}")
    print("sources:")
    for item in result["source_decisions"]:
        print(f"  - {item['layer']}: {item['status']} ({item['reason']})")
    print(f"next_action: {result['next_action']}")
    return 0 if result["policy"]["outcome"] != "block" else 1
