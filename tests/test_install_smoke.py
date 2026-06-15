from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def installed_script(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "reefiki.exe"
    return venv / "bin" / "reefiki"


def venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def write_fixture_project(project: Path) -> None:
    (project / "wiki" / "concepts").mkdir(parents=True)
    (project / "inbox").mkdir(parents=True)
    (project / "seen").mkdir(parents=True)
    (project / "raw").mkdir(parents=True)
    (project / "wiki" / "log.md").write_text("", encoding="utf-8")
    (project / "wiki" / "index.md").write_text(
        """# Index

Last updated: 2026-06-11
Total pages: 1

## Sources
## Entities
## Concepts

### install-smoke
- type: concept
- tags: [install]
- useful_when: ["checking installed CLI status"]
- file: wiki/concepts/install-smoke.md
- date_added: 2026-06-11
- use_count: 0

## Synthesis
## Decisions
## Skills
""",
        encoding="utf-8",
    )
    (project / "wiki" / "concepts" / "install-smoke.md").write_text(
        """---
id: install-smoke
title: Install Smoke
type: concept
tags: [install]
useful_when:
  - "checking installed CLI status"
date_added: 2026-06-11
use_count: 0
last_used:
---

# Install Smoke
""",
        encoding="utf-8",
    )


def test_local_package_install_entrypoint_status_and_uninstall() -> None:
    with tempfile.TemporaryDirectory(prefix="reefiki-install-test-") as temp:
        temp_path = Path(temp)
        venv = temp_path / "venv"
        project = temp_path / "fixture"
        write_fixture_project(project)

        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True, text=True)
        python = venv_python(venv)
        reefiki = installed_script(venv)

        subprocess.run([str(python), "-m", "pip", "install", str(ROOT)], check=True, capture_output=True, text=True)

        help_result = subprocess.run([str(reefiki), "--help"], check=True, capture_output=True, text=True)
        assert "REEFIKI local tools" in help_result.stdout

        status_result = subprocess.run([str(reefiki), "--project", str(project), "status"], check=True, capture_output=True, text=True)
        assert "Project: fixture" in status_result.stdout
        assert "Wiki: concept=1" in status_result.stdout

        subprocess.run([str(python), "-m", "pip", "uninstall", "-y", "reefiki"], check=True, capture_output=True, text=True)
        show_result = subprocess.run([str(python), "-m", "pip", "show", "reefiki"], check=False, capture_output=True, text=True)
        assert show_result.returncode != 0
