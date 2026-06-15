from __future__ import annotations

import json
from datetime import date
from pathlib import Path


DEFAULT_ONBOARDING_PROJECT = "reefiki-onboarding-demo"
DEFAULT_ONBOARDING_SOURCE = "https://example.com/reefiki-onboarding"
DEFAULT_ONBOARDING_QUESTION = "What did the onboarding source establish?"
DEFAULT_ONBOARDING_SESSION_NOTE = "Finished the first REEFIKI onboarding run."


def _project_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _onboarding_steps(project_name: str, source: str, question: str, session_note: str) -> list[dict[str, object]]:
    return [
        {
            "step": "create",
            "intent": "create an isolated REEFIKI project from the template",
            "equivalent": f"/new {project_name}",
            "writes": [
                f"projects/{project_name}/AGENTS.md",
                f"projects/{project_name}/_domain.md",
                f"projects/{project_name}/wiki/index.md",
                f"projects/{project_name}/wiki/log.md",
            ],
        },
        {
            "step": "save",
            "intent": "put one source into the inbox without analysis",
            "equivalent": f"reefiki --project projects/{project_name} save {source}",
            "writes": [f"projects/{project_name}/inbox/onboarding-source.md"],
        },
        {
            "step": "process",
            "intent": "turn the saved source into a durable wiki page",
            "equivalent": "/process",
            "writes": [
                f"projects/{project_name}/raw/onboarding-source.md",
                f"projects/{project_name}/wiki/concepts/onboarding-first-source.md",
                f"projects/{project_name}/wiki/index.md",
                f"projects/{project_name}/wiki/log.md",
            ],
        },
        {
            "step": "query",
            "intent": "ask the local wiki with provenance",
            "equivalent": f"reefiki --project projects/{project_name} search \"{question}\" --format json",
            "writes": [],
        },
        {
            "step": "harvest",
            "intent": "record a session-level takeaway as durable wiki knowledge",
            "equivalent": f"/harvest {session_note}",
            "writes": [
                f"projects/{project_name}/wiki/synthesis/onboarding-session-summary.md",
                f"projects/{project_name}/wiki/index.md",
                f"projects/{project_name}/wiki/log.md",
            ],
        },
        {
            "step": "status",
            "intent": "show the resulting project state",
            "equivalent": f"reefiki --project projects/{project_name} status",
            "writes": [],
        },
    ]


def _write_onboarding_fixture(
    fixture_root: Path,
    project_name: str,
    source: str,
    question: str,
    session_note: str,
) -> list[str]:
    project = fixture_root / "projects" / project_name
    for dirname in [
        "inbox",
        "raw",
        "seen",
        "wiki/concepts",
        "wiki/synthesis",
    ]:
        (project / dirname).mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    artifacts: list[Path] = []

    files = {
        project / "AGENTS.md": "Onboarding demo project. Use project-level REEFIKI rules.\n",
        project / "_domain.md": (
            "# Domain\n\n"
            "A deterministic onboarding demo project used to learn the REEFIKI first-run flow.\n"
        ),
        project / "raw" / "onboarding-source.md": (
            f"# Onboarding Source\n\nSource: {source}\n\n"
            "The first source explains that REEFIKI keeps sources, distilled wiki pages and session harvests separate.\n"
        ),
        project / "wiki" / "concepts" / "onboarding-first-source.md": (
            "---\n"
            "id: onboarding-first-source\n"
            "type: concept\n"
            'title: "Onboarding first source"\n'
            "tags: [onboarding, first-run]\n"
            "useful_when:\n"
            '  - "checking that the first REEFIKI source was processed into durable wiki knowledge"\n'
            f"date_added: {today}\n"
            "use_count: 0\n"
            "last_used: null\n"
            "---\n\n"
            "# Onboarding first source\n\n"
            "The first source demonstrates the capture -> process -> query flow without relying on external services.\n"
        ),
        project / "wiki" / "synthesis" / "onboarding-session-summary.md": (
            "---\n"
            "id: onboarding-session-summary\n"
            "type: synthesis\n"
            'title: "Onboarding session summary"\n'
            "tags: [onboarding, harvest]\n"
            "useful_when:\n"
            '  - "remembering what a successful first REEFIKI run should leave behind"\n'
            f"date_added: {today}\n"
            "use_count: 0\n"
            "last_used: null\n"
            "---\n\n"
            "# Onboarding session summary\n\n"
            f"{session_note}\n\n"
            "A successful first run leaves an inbox source, a raw source copy, a distilled wiki page, a harvest page and a status check.\n"
        ),
        project / "wiki" / "index.md": (
            "# Index\n\n"
            f"Last updated: {today}\n"
            "Total pages: 2\n\n"
            "## Sources\n"
            "## Entities\n"
            "## Concepts\n\n"
            "### onboarding-first-source\n"
            "- type: concept\n"
            "- tags: [onboarding, first-run]\n"
            '- useful_when: ["checking that the first REEFIKI source was processed into durable wiki knowledge"]\n'
            "- file: wiki/concepts/onboarding-first-source.md\n"
            f"- date_added: {today}\n"
            "- use_count: 0\n\n"
            "## Synthesis\n\n"
            "### onboarding-session-summary\n"
            "- type: synthesis\n"
            "- tags: [onboarding, harvest]\n"
            '- useful_when: ["remembering what a successful first REEFIKI run should leave behind"]\n'
            "- file: wiki/synthesis/onboarding-session-summary.md\n"
            f"- date_added: {today}\n"
            "- use_count: 0\n\n"
            "## Decisions\n"
            "## Skills\n"
        ),
        project / "wiki" / "log.md": (
            f"# Log\n\n"
            f"- {today}: onboarding fixture created project `{project_name}`.\n"
            f"- {today}: /save | {source}\n"
            f"- {today}: /process | accepted onboarding-source -> wiki/concepts/onboarding-first-source.md\n"
            f"- {today}: /query | {question}\n"
            f"- {today}: /harvest | {session_note}\n"
            f"- {today}: /status | onboarding fixture complete\n"
        ),
    }
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        artifacts.append(path)
    return [_project_rel(path, fixture_root) for path in sorted(artifacts)]


def onboarding_wizard_payload(
    root: Path,
    project_name: str = DEFAULT_ONBOARDING_PROJECT,
    source: str = DEFAULT_ONBOARDING_SOURCE,
    question: str = DEFAULT_ONBOARDING_QUESTION,
    session_note: str = DEFAULT_ONBOARDING_SESSION_NOTE,
    fixture_root: Path | None = None,
) -> dict[str, object]:
    target_root = fixture_root or root
    mode = "fixture" if fixture_root else "dry-run"
    artifacts = (
        _write_onboarding_fixture(target_root, project_name, source, question, session_note)
        if fixture_root
        else []
    )
    return {
        "mode": mode,
        "project": project_name,
        "root": str(target_root),
        "source": source,
        "question": question,
        "session_note": session_note,
        "steps": _onboarding_steps(project_name, source, question, session_note),
        "artifacts": artifacts,
        "transient_artifacts": (
            [f"projects/{project_name}/inbox/onboarding-source.md"] if fixture_root else []
        ),
        "next_action": (
            f"open {target_root / 'projects' / project_name} and run status"
            if fixture_root
            else "rerun with --fixture-root <empty-folder> to create a deterministic demo project"
        ),
    }


def print_onboarding_wizard(
    root: Path,
    project_name: str,
    source: str,
    question: str,
    session_note: str,
    fixture_root: str | None,
    fmt: str,
) -> int:
    payload = onboarding_wizard_payload(
        root,
        project_name=project_name,
        source=source,
        question=question,
        session_note=session_note,
        fixture_root=Path(fixture_root) if fixture_root else None,
    )
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"# REEFIKI Onboarding ({payload['mode']})")
        print(f"- project: {payload['project']}")
        print(f"- source: {payload['source']}")
        print("")
        for step in payload["steps"]:
            if isinstance(step, dict):
                print(f"- {step['step']}: {step['intent']}")
                print(f"  command: {step['equivalent']}")
        if payload["artifacts"]:
            print("")
            print("## Artifacts")
            for artifact in payload["artifacts"]:
                print(f"- {artifact}")
        print("")
        print(f"next: {payload['next_action']}")
    return 0
