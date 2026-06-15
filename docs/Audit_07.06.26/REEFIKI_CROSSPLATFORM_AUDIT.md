# REEFIKI — Cross-Platform Audit

> Audited: June 1, 2026. Commit snapshot at `kisslex2013-alt/reefiki` (main).

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [What Works Well (Cross-Platform Wins)](#2-what-works-well)
3. [Python Runtime](#3-python-runtime)
4. [Dependencies](#4-dependencies)
5. [Path and Filesystem Handling](#5-path-and-filesystem-handling)
6. [Git and Subprocess Calls](#6-git-and-subprocess-calls)
7. [Shell Commands in Documentation](#7-shell-commands-in-documentation)
8. [Installation and Onboarding](#8-installation-and-onboarding)
9. [Tests](#9-tests)
10. [Proposals (P0 → P3)](#10-proposals)
11. [Quick-Start Per OS](#11-quick-start-per-os)

---

## 1. Executive Summary

REEFIKI's Python core is **mostly cross-platform by accident** — the developer made good architectural choices (pathlib everywhere, list-form subprocess, UTF-8 encoding), but a handful of real issues remain:

| Severity | Count | Highest-impact items |
|---|---|---|
| P0 — Blocker | 4 | Hardcoded `C:\Users\kissl\...` default path; `StrEnum` requires Python 3.11 undocumented; no `.gitattributes`; pre-commit `entry: python` breaks on macOS/Linux |
| P1 — High | 5 | `rg` undocumented; `uvx`/`memoir-ai` undocumented; no bash equivalent for `push-public.ps1`; all README code blocks PowerShell-only; backslash path in AGENTS.md |
| P2 — Medium | 3 | Windows junction requires admin/Developer Mode; no Python version stated; no CI matrix |
| P3 — Low | 2 | No Python badge; PowerShell-only validation command example |

**Primary OS in practice:** Windows 11 (based on hardcoded path `C:\Users\kissl\`, backslash examples, PowerShell blocks). macOS and Linux users can run the core tools **if they know what Python version to install** and accept the missing bash equivalents for a few operations.

---

## 2. What Works Well

Before the issues — the code has solid cross-platform foundations that are worth preserving:

| Aspect | Evidence | Notes |
|---|---|---|
| `pathlib.Path` used throughout | `from pathlib import Path`; no `os.path` calls in production code | ✅ Correct. `Path` is cross-platform by design |
| `as_posix()` for path strings | Line 254: `return path.relative_to(project).as_posix()` | ✅ Converts to forward-slash string regardless of OS |
| Backslash normalization on git output | Lines 1068, 1106, 1115, 1318: `.replace("\\", "/")` | ✅ Git on Windows emits backslash paths; all 4 callsites normalize |
| All subprocess calls use list form | `["git", "diff", ...]`, `["git", *args]`, `[sys.executable, ...]` | ✅ Never `shell=True`; no injection risk |
| UTF-8 encoding on all subprocess calls | Every `subprocess.run` has `encoding="utf-8"` | ✅ Correct; avoids Windows CP-1252/cp950 surprises |
| `sys.stdout.reconfigure` guard | Line 37–38: `if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")` | ✅ Standard Windows UTF-8 fix pattern |
| `sys.executable` for sub-process Python | Line 1204: `[sys.executable, str(validator), ...]` | ✅ Finds the right Python even in virtualenvs |
| `posixpath` for git path normalization | Line 1118: `posixpath.normpath(normalized)` | ✅ Explicitly using posix rules for git paths |
| Tests use `tempfile.TemporaryDirectory()` | All 4 test files | ✅ Cross-platform temp dirs |
| `from __future__ import annotations` | Both `reefiki.py` and `reefiki_memory/__init__.py` | ✅ Allows `X \| Y` union syntax on Python 3.9+ |

---

## 3. Python Runtime

### 3.1 Minimum Python Version — **Not documented; actual minimum: 3.11**

**File:** `scripts/reefiki_memory/__init__.py`, line 4:
```python
from enum import StrEnum
```

`StrEnum` was added to the Python standard library in **Python 3.11** (CPython issue #91842, released October 2022). It does **not** exist in Python 3.10's `enum` module without a third-party package.

This import will raise `ImportError: cannot import name 'StrEnum' from 'enum'` on Python 3.10 or earlier.

**Minimum Python version: 3.11.** This is not stated anywhere in the repository — not in README, not in any `pyproject.toml` (which doesn't exist), not in any comment.

**What to do:**

Option A — add a version check at startup (temporary):
```python
# scripts/reefiki.py, after imports
import sys
if sys.version_info < (3, 11):
    raise SystemExit(
        f"REEFIKI requires Python 3.11+. You are running {sys.version}.\n"
        "Install Python 3.11+ from https://python.org or via your package manager."
    )
```

Option B — add `pyproject.toml` (the correct long-term fix, covered in §10):
```toml
[project]
requires-python = ">=3.11"
```

**Other version-sensitive features used:**

| Feature | Introduced | Usage in REEFIKI |
|---|---|---|
| `StrEnum` in stdlib | Python **3.11** | `reefiki_memory/__init__.py` line 4 — **blocking** |
| `X \| Y` union type hints (runtime) | Python 3.10 | 35 uses in `reefiki.py` — **safe** because `from __future__ import annotations` makes them lazy strings |
| `str.removeprefix` / `str.removesuffix` | Python 3.9 | Not found |
| `match/case` statement | Python 3.10 | Not used (the `match =` lines are variable assignments) |
| `ExceptionGroup` | Python 3.11 | Not used |
| `tomllib` | Python 3.11 | Not used |

### 3.2 Shebang

**File:** `scripts/reefiki.py` line 1, `scripts/validate_frontmatter.py` line 1:
```
#!/usr/bin/env python3
```

On **macOS and Linux:** works correctly when the file is executable.

On **Windows:** shebangs are ignored by default. The file must be called explicitly:
```cmd
python scripts\reefiki.py ...
```

This is not a bug — Windows Python does not use shebangs — but the README and documentation should make the Windows invocation explicit, not imply the shebang path is universal.

### 3.3 `python` vs `python3`

On **Windows:** `python` typically works (Microsoft Store Python uses `python`).

On **macOS (Homebrew):** `python3` exists; `python` may be `/usr/bin/python3` alias or may not exist depending on Xcode tools version.

On **Ubuntu/Debian:** `python3` exists; `python` requires `python-is-python3` package.

This creates the pre-commit problem described in §10 CROSS-03.

---

## 4. Dependencies

### 4.1 Python packages — stdlib only ✅

`reefiki.py` imports only Python standard library modules:

```
argparse, fnmatch, hashlib, json, os, posixpath, re, sqlite3,
subprocess, sys, tempfile, collections, datetime, pathlib, urllib.parse
```

Plus the local `reefiki_memory` module. **No pip-installable packages required for the core CLI.** This is excellent.

### 4.2 External tools — undocumented

| Tool | Required/Optional | Used where | Documented? | Fallback? |
|---|---|---|---|---|
| `git` | **Required** | All git operations (`harvest-commit`, `guard-staged`, `publish-task`, `memory diff`) | Implicitly assumed | No — fails with "git command failed" |
| `python 3.11+` | **Required** | Running any script | ❌ Not stated | No |
| `pre-commit` | Optional (but documented as part of setup) | `.pre-commit-config.yaml` | Partially | Not installing it just disables the hook |
| `uvx` (from `uv`) | Optional (memoir layer only) | `_memoir_base_command()` line 1020 | ❌ Not documented | No — `memoir` features silently fail |
| `memoir-ai` package | Optional (memoir layer only) | `uvx --from memoir-ai memoir` | ❌ Not documented | No |
| `rg` (ripgrep) | Optional (validation convenience) | README examples only | ❌ Not documented | Find equivalent below |
| Obsidian | Optional (visualization) | Documentation only | Stated as optional | N/A |

### 4.3 Critical undocumented dependency: `uvx` / `memoir-ai`

**File:** `scripts/reefiki.py`, lines 1018–1027:
```python
def _memoir_base_command(store: Path) -> list[str]:
    return [
        "uvx",
        "--from",
        "memoir-ai",
        "memoir",
        "--json",
        "--store",
        str(store),
    ]
```

`uvx` is the tool-runner from [astral-sh/uv](https://github.com/astral-sh/uv). It must be installed separately. On systems without `uv`, calling any `memory lookup`, `memory preflight`, or `memory pack` with `include_memoir=True` will fail with a generic "memoir command failed" message — no hint that `uvx` is missing.

**Installation not documented anywhere in the repository.**

`uv` installs cleanly on Windows, macOS, and Linux:
```bash
# All platforms
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS/Linux
# Windows PowerShell:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 4.4 Critical undocumented dependency: `rg` (ripgrep)

**File:** `README.md`, lines 186 and 192:
```powershell
python scripts/validate_frontmatter.py (rg --files projects | ? { $_ -match '[/\\]wiki[/\\].+\.md$' })
```

`rg` (ripgrep) is a third-party tool. If absent, this command fails entirely — and the user gets no hint about what `rg` is.

**Bash equivalent (no rg required):**
```bash
python3 scripts/validate_frontmatter.py \
  $(find projects -path "*/wiki/*.md" ! -name "_*" ! -name "log.md")
```

**PowerShell equivalent (no rg required):**
```powershell
$files = Get-ChildItem -Path projects -Recurse -Filter "*.md" |
  Where-Object { $_.FullName -match '\\wiki\\' -and $_.Name -notmatch '^_|^log\.md$' } |
  Select-Object -ExpandProperty FullName
python scripts/validate_frontmatter.py @files
```

---

## 5. Path and Filesystem Handling

### 5.1 Hardcoded Personal Windows Path — **P0 Critical**

**File:** `scripts/reefiki.py`, line 134:
```python
os.environ.get("REEFIKI_MEMOIR_STORE", r"C:\Users\kissl\.codex\memoir-stores\reefiki")
```

This is a **hardcoded personal Windows path** used as the default memoir store location. On macOS or Linux (and on any Windows machine belonging to any user other than `kissl`), this path does not exist. Any memoir operation that reads this default will silently operate against a non-existent store or raise a confusing error.

**Affected OS:** macOS, Linux, any Windows user that is not `kissl`

**Fix:**
```python
def _default_memoir_store() -> Path:
    """Cross-platform default memoir store path."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "memoir" / "reefiki"

MEMOIR_STORE_DEFAULT = _default_memoir_store()
# Usage:
store = Path(os.environ.get("REEFIKI_MEMOIR_STORE", str(MEMOIR_STORE_DEFAULT)))
```

### 5.2 Path API Usage — Mostly Good

| Pattern | Assessment |
|---|---|
| `pathlib.Path` for all file operations | ✅ Correct |
| `path.relative_to(project).as_posix()` | ✅ Correct — returns forward-slash string for storage/display |
| `posixpath.normpath()` for git path strings | ✅ Correct — git always uses POSIX paths |
| `.replace("\\", "/")` on git stdout | ✅ 4 callsites normalize Windows backslashes in git output |
| `import os` but zero `os.path` calls | ✅ `os` is imported for `os.environ`, not path operations |

### 5.3 No `.gitattributes` — **P0**

The `.gitattributes` file does not exist. On Windows with Git configured to `autocrlf=true` (the Windows default), markdown files will be checked out with CRLF line endings.

REEFIKI's frontmatter parser (`parse_frontmatter` in `reefiki.py` and `validate_frontmatter.py`) uses `re.compile(r"^---\n(.*?)\n---", re.DOTALL)`. On a CRLF file, the `---\r\n` does not match `---\n`, causing **frontmatter parsing to silently fail** — pages are treated as having no frontmatter, validation errors are reported for all pages.

**Fix:** create `.gitattributes` at repo root:
```gitattributes
# Normalize line endings to LF everywhere
* text=auto eol=lf

# Markdown files — always LF
*.md text eol=lf

# YAML — always LF
*.yaml text eol=lf
*.yml text eol=lf

# Python — always LF
*.py text eol=lf

# Binary files — do not touch
*.png binary
*.jpg binary
*.svg binary
*.ico binary
*.db binary
*.sqlite binary
```

### 5.4 Windows Junction for `/connect` — **P2**

The `/connect` command (creating `_wiki/` junction from a code project to the REEFIKI wiki) is an agent-executed operation that creates filesystem junctions on Windows. NTFS junctions require either:
- Administrator rights, or
- Developer Mode enabled (Windows 10 1703+, Windows 11)

This is not documented. On macOS/Linux the equivalent is a regular symlink (`ln -s`), which requires no special permissions.

**Documentation fix:** add to QUICKSTART / COMMANDS.md:

```
Windows: /connect requires either Developer Mode (Settings → For developers → Developer Mode) 
or an admin terminal. To enable Developer Mode: Settings → System → For developers.

macOS/Linux: /connect creates a standard symlink, no special permissions needed.
```

### 5.5 Long Paths on Windows

REEFIKI's path structure is: `REEFIKI/projects/<name>/wiki/<subdir>/<slug>.md`

A project named `my-long-project-name` with a deeply-nested wiki slug can approach the Windows `MAX_PATH` (260 chars) if the REEFIKI root itself is in a deep path like `C:\Users\username\Documents\Projects\REEFIKI\`.

**No immediate action needed** — this is a user setup concern, but documenting the recommendation to keep REEFIKI at a short root path (e.g., `C:\REEFIKI\` or `D:\wiki\`) in the QUICKSTART would prevent hard-to-diagnose failures.

---

## 6. Git and Subprocess Calls

### 6.1 All Subprocess Calls — Clean ✅

All 5 `subprocess.run` calls in `reefiki.py`:

| Line | Command | Form | `shell=` | `encoding=` |
|---|---|---|---|---|
| 1033 | `uvx memoir ...` | list via `_memoir_base_command()` | False | `utf-8` |
| 1056 | `git diff --cached --name-only` | list | False | `utf-8` |
| 1072 | `git *args` (generic runner) | list | False | `utf-8` |
| 1203 | `python validate_frontmatter.py` | list via `sys.executable` | False | `utf-8` |
| 2179 | `git *args` (memory diff runner) | list | False | `utf-8` |

All are correct: list form, no `shell=True`, explicit UTF-8 encoding.

### 6.2 `REEFIKI_MEMOIR_STORE` Environment Variable

The `run_memoir` function passes a modified `env` to subprocess with `PYTHONIOENCODING=utf-8` set. This is good practice for subprocess UTF-8 stability.

---

## 7. Shell Commands in Documentation

### 7.1 README — PowerShell-only Code Blocks

All code blocks in `README.md` use `powershell` as the language tag. There are no `bash`, `sh`, or `zsh` equivalents. Commands shown:

| README command (PowerShell) | macOS/Linux equivalent |
|---|---|
| `git clone https://github.com/<user>/reefiki` | Same — git clone is cross-platform |
| `python scripts/validate_frontmatter.py (rg --files projects \| ? { $_ -match ... })` | `python3 scripts/validate_frontmatter.py $(find projects -path "*/wiki/*.md" ! -name "_*" ! -name "log.md")` |
| `.\scripts\push-public.ps1` | `python3 scripts/reefiki.py publish-task --apply --public-snapshot` (Python CLI equivalent) |

### 7.2 AGENTS.md — Backslash Path

**File:** `AGENTS.md`, line 158:
```
python scripts\reefiki.py publish-task --dry-run --cleanup --format json
```

The backslash (`scripts\reefiki.py`) is valid PowerShell/CMD but **fails on macOS/Linux** if an agent or user copies this command verbatim into a bash terminal.

**Fix:** use forward slash (valid on all platforms including Windows):
```
python scripts/reefiki.py publish-task --dry-run --cleanup --format json
```

### 7.3 `rg` in README — Undocumented External Dependency

See §4.4. The `rg` tool appears only in the README validation commands. It is not used in `reefiki.py` itself. The commands should provide `rg`-free equivalents (shown above in §4.4).

### 7.4 No `/dev/null`, No Bash Pipes in Python Code

The Python scripts themselves contain no shell-specific constructs. All shell-ism is in documentation examples (PowerShell) or in `push-public.ps1` (PowerShell). The Python CLI is clean.

---

## 8. Installation and Onboarding

### 8.1 What Exists

- ❌ No `pyproject.toml`
- ❌ No `requirements.txt`
- ❌ No `setup.py`
- ❌ No `Makefile`
- ❌ No explicit Python version requirement stated anywhere
- ❌ No `pre-commit install` instruction in README
- ✅ `scripts/push-public.ps1` (Windows PowerShell)
- ✅ `scripts/reefiki.py publish-task` (Python CLI, all platforms)
- ✅ `.pre-commit-config.yaml` exists (but setup not documented)

### 8.2 What Is Needed Per Platform

**Windows:** Python installer from python.org does not add `python` to PATH by default (checkbox must be checked). Standard Python 3.11+ install, then `pre-commit`.

**macOS:** Homebrew `python3` installs Python 3.x but `python` may not be in PATH. `pre-commit` via `brew install pre-commit` or `pip3 install pre-commit`.

**Linux:** System package manager typically has Python 3.9–3.11. Python 3.11+ may need a PPA/backport on older Ubuntu. `pre-commit` via `pip3 install pre-commit`.

**WSL2:** Same as Linux but filesystem paths must be within the WSL2 filesystem (`~/` or `/home/...`) for performance; accessing Windows drives (`/mnt/c/...`) works but SQLite WAL mode can have issues on cross-filesystem mounts (very rare, not a blocker).

### 8.3 Recommended `pyproject.toml` to Add

```toml
[project]
name = "reefiki"
version = "0.1.0"
description = "Multi-project personal knowledge distillation wiki and memory control plane"
requires-python = ">=3.11"
dependencies = []   # stdlib only; memoir requires uv separately

[project.scripts]
reefiki = "reefiki:main"

[project.optional-dependencies]
dev = [
    "pre-commit>=3.0",
    "pytest>=8.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"
```

With this in place:
- `python -m pytest` works from root without further config
- `requires-python = ">=3.11"` surfaces a clear error if wrong Python version is used
- Tools like Dependabot and GitHub Actions matrix picks up the version requirement

---

## 9. Tests

### 9.1 Test Runner

Tests use `unittest` with `if __name__ == "__main__": unittest.main()`. They can be run as:
```bash
python -m pytest tests/        # recommended (discovers all files)
python -m unittest discover tests/   # stdlib alternative
```

Neither is documented in the README.

### 9.2 Cross-Platform Assessment — Mostly Good

All 4 test files use:
- `tempfile.TemporaryDirectory()` for isolation ✅
- `pathlib.Path` for all file creation ✅
- `Path.mkdir(parents=True)` for directory creation ✅
- No hardcoded `\` separators ✅

**One potential issue in `test_reefiki_dedup.py`, line 112:**
```python
self.assertIn("Saved: inbox/example-com-path.md", output)
```

This asserts a forward-slash path in the CLI output. The `save_source` function stores paths internally using `Path`, which on Windows would normally produce backslashes in `str()`. However, since the output comes through `relative().as_posix()` (line 254), the output is always forward-slash regardless of OS. ✅ This is safe.

**No platform-specific `os.sep` assertions found.** Tests are cross-platform. ✅

### 9.3 No CI — All Platforms Untested

As noted in the general audit, there is no `.github/workflows/ci.yml`. Tests only pass "on the last machine the developer ran them". A multi-OS matrix in CI would catch platform regressions early.

---

## 10. Proposals

### P0 — Blockers

---

**CROSS-01 — Fix hardcoded personal Windows path**
- **Problem:** `scripts/reefiki.py`, line 134: default memoir store hardcoded to `C:\Users\kissl\.codex\memoir-stores\reefiki`
- **Affected OS:** macOS, Linux, Windows (any user who is not `kissl`)
- **Solution:**
```python
# Replace line 134
def _default_memoir_store() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "memoir" / "reefiki"

MEMOIR_STORE = Path(os.environ.get("REEFIKI_MEMOIR_STORE", str(_default_memoir_store())))
```
- **Complexity:** S
- **Priority:** P0

---

**CROSS-02 — Document Python 3.11+ requirement; add startup version guard**
- **Problem:** `from enum import StrEnum` (reefiki_memory/__init__.py line 4) requires Python 3.11+, but this is not stated anywhere. Users with Python 3.10 get `ImportError`.
- **Affected OS:** All (especially Linux where distro Python may be 3.10)
- **Solution A — startup guard** in `reefiki.py`:
```python
import sys
if sys.version_info < (3, 11):
    raise SystemExit(
        f"REEFIKI requires Python 3.11+. Running: {sys.version.split()[0]}\n"
        "See https://python.org or use: pyenv install 3.11 / brew install python@3.11"
    )
```
- **Solution B — pyproject.toml** (see §8.3): `requires-python = ">=3.11"`
- Both solutions should be applied. B is the canonical machine-readable form; A gives humans a clear error message.
- **Complexity:** S
- **Priority:** P0

---

**CROSS-03 — Fix pre-commit hook entry: `python` → `python3`**
- **Problem:** `.pre-commit-config.yaml` local hook:
```yaml
entry: python scripts/validate_frontmatter.py
language: python
```
On macOS (Homebrew) and Ubuntu/Debian, `python` is not guaranteed to exist. `python3` is the portable command.
- **Affected OS:** macOS, Linux
- **Solution:** Change to `python3`:
```yaml
  - repo: local
    hooks:
      - id: reefiki-frontmatter
        name: Validate REEFIKI wiki frontmatter
        entry: python3 scripts/validate_frontmatter.py
        language: python
        language_version: python3
        files: ^projects/.*/wiki/.*\.md$
        pass_filenames: true
        always_run: false
```
Alternatively, since `language: python` is already specified, pre-commit manages its own Python environment when `additional_dependencies` is used. The safest portable form is to add an `additional_dependencies: []` line and let pre-commit handle the interpreter:
```yaml
        language: python
        language_version: "3.11"
```
- **Complexity:** S
- **Priority:** P0

---

**CROSS-04 — Add `.gitattributes` for LF line endings**
- **Problem:** No `.gitattributes`. Git on Windows (`autocrlf=true` default) checks out `.md` and `.yaml` files with CRLF. The frontmatter regex `^---\n` does not match `---\r\n`. All pages fail frontmatter parsing silently.
- **Affected OS:** Windows (with default Git config)
- **Solution:** Create `.gitattributes`:
```gitattributes
# Force LF for all text files
* text=auto eol=lf
*.md text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
*.py text eol=lf
*.ps1 text eol=crlf
*.txt text eol=lf
*.json text eol=lf
*.toml text eol=lf

# Binary — no line ending conversion
*.png binary
*.jpg binary
*.jpeg binary
*.svg binary
*.ico binary
*.db binary
*.sqlite binary
```
Note: `.ps1` is set to `crlf` because PowerShell execution policy on Windows may reject LF-only PS1 files in some configurations.
- **Complexity:** S
- **Priority:** P0

---

### P1 — High

---

**CROSS-05 — Add `pyproject.toml` with Python version and dev dependencies**
- **Problem:** No installation file. Users cannot discover the Python version requirement, cannot install dev dependencies with one command, and `pytest` discovery requires manual path specification.
- **Affected OS:** All
- **Solution:** Create `pyproject.toml` per §8.3. Minimal version:
```toml
[project]
name = "reefiki"
requires-python = ">=3.11"
version = "0.1.0"
dependencies = []

[project.optional-dependencies]
dev = ["pre-commit>=3.7", "pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```
- **Complexity:** S
- **Priority:** P1

---

**CROSS-06 — Document `uvx`/`memoir-ai` and provide fallback message**
- **Problem:** `_memoir_base_command` calls `uvx` without checking if it exists. `memoir` features fail silently with "memoir command failed".
- **Affected OS:** All (no platform distinction — uvx is just undocumented)
- **Solution A — friendly error:** wrap the subprocess call:
```python
def run_memoir(store: Path, args: list[str]) -> dict[str, object]:
    import shutil
    if not shutil.which("uvx"):
        return {
            "error": "uvx not found",
            "detail": (
                "The memoir layer requires uv (https://github.com/astral-sh/uv). "
                "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh  "
                "(or on Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\")"
            ),
        }
    # ... existing subprocess.run ...
```
- **Solution B — document in README/QUICKSTART:** add optional dependencies table with install commands per OS.
- Both should be done. A protects users at runtime; B educates before first run.
- **Complexity:** S
- **Priority:** P1

---

**CROSS-07 — Document `rg` (ripgrep) as optional; provide `find`-based alternatives**
- **Problem:** README validation examples use `rg --files` with no mention that `rg` must be installed. No fallback shown.
- **Affected OS:** macOS, Linux (rg not pre-installed); Windows (rg not pre-installed)
- **Solution:** Update README validation section:
```markdown
### Checking wiki integrity

**Using ripgrep (if installed):**
```powershell
# Windows PowerShell
python scripts/validate_frontmatter.py (rg --files projects | ? { $_ -match '[/\\]wiki[/\\].+\.md$' })
```

**Using find (macOS/Linux — no extra tools needed):**
```bash
python3 scripts/validate_frontmatter.py \
  $(find projects -path "*/wiki/*.md" ! -name "_*" ! -name "log.md" ! -name "status.md")
```

**Using Get-ChildItem (Windows PowerShell — no extra tools needed):**
```powershell
$files = Get-ChildItem -Path projects -Recurse -Filter "*.md" |
  Where-Object { $_.FullName -match '\\wiki\\' -and $_.Name -notmatch '^_|^log\.md$' } |
  Select-Object -ExpandProperty FullName
if ($files) { python scripts/validate_frontmatter.py @files }
```
```
- **Complexity:** S
- **Priority:** P1

---

**CROSS-08 — Create `scripts/push-public.sh` (bash equivalent of push-public.ps1)**
- **Problem:** `push-public.ps1` is PowerShell-only. macOS/Linux users have no shell equivalent for the convenient `.\push-public.ps1` workflow. They must use the Python CLI (`publish-task`) which works but is not documented as the equivalent.
- **Affected OS:** macOS, Linux
- **Solution:** Create `scripts/push-public.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="$SCRIPT_DIR/public-snapshot.private-projects.txt"

if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "ERROR: Missing private-projects config: $CONFIG_PATH" >&2
    exit 1
fi

# Read private projects (skip comments and empty lines)
mapfile -t PRIVATE_PROJECTS < <(grep -v '^\s*#' "$CONFIG_PATH" | grep -v '^\s*$')

if [[ ${#PRIVATE_PROJECTS[@]} -eq 0 ]]; then
    echo "ERROR: No private projects configured in $CONFIG_PATH" >&2
    exit 1
fi

PROJECTS_ROOT="$SCRIPT_DIR/../projects"
if [[ ! -d "$PROJECTS_ROOT" ]]; then
    echo "ERROR: Projects directory not found: $PROJECTS_ROOT" >&2
    exit 1
fi

# Check all actual projects are listed as private
while IFS= read -r -d '' proj_dir; do
    proj_name=$(basename "$proj_dir")
    if [[ "$proj_name" == "_template" ]]; then continue; fi
    if ! printf '%s\n' "${PRIVATE_PROJECTS[@]}" | grep -qx "$proj_name"; then
        echo "ERROR: Project '$proj_name' not listed in public-snapshot.private-projects.txt" >&2
        echo "Add it to the file before pushing the public snapshot." >&2
        exit 1
    fi
done < <(find "$PROJECTS_ROOT" -mindepth 1 -maxdepth 1 -type d -print0)

read -rp "Push filtered snapshot to public remote main? (y/N) " confirmation
if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
    echo "Cancelled."
    exit 0
fi

TEMP_BRANCH="public-snapshot-$(date +%Y%m%d%H%M%S)"

echo "Creating temp branch: $TEMP_BRANCH"
git checkout --orphan "$TEMP_BRANCH"

echo "Staging all files..."
git add -A

echo "Removing personal projects..."
for project in "${PRIVATE_PROJECTS[@]}"; do
    path="projects/$project"
    if [[ -d "$path" ]]; then
        git rm -r --cached "$path" > /dev/null
    fi
done

echo "Committing public snapshot..."
git commit -m "public: template snapshot $(date +%Y-%m-%d)"

echo "Pushing to public remote..."
git push public "${TEMP_BRANCH}:main" --force-with-lease

echo "Cleaning up..."
git checkout --force main
git branch -D "$TEMP_BRANCH"

echo "Done. Public remote updated."
```
Make it executable: `chmod +x scripts/push-public.sh`
- **Complexity:** S
- **Priority:** P1

---

**CROSS-09 — Fix backslash path in AGENTS.md**
- **Problem:** `AGENTS.md` line 158: `python scripts\reefiki.py publish-task --dry-run --cleanup --format json` — backslash fails on macOS/Linux.
- **Affected OS:** macOS, Linux
- **Solution:** Change to forward slash (valid on Windows too):
```
python scripts/reefiki.py publish-task --dry-run --cleanup --format json
```
- **Complexity:** S (single character)
- **Priority:** P1

---

### P2 — Medium

---

**CROSS-10 — Document Windows junction requirement for `/connect`**
- **Problem:** `/connect` creates an NTFS junction (`_wiki/`) in the code project directory. This requires Developer Mode or admin rights on Windows.
- **Affected OS:** Windows
- **Solution:** Add to `QUICKSTART.md` and `COMMANDS.md`:
```
Windows prerequisite for /connect:
Enable Developer Mode: Settings → System → For developers → Developer Mode (ON)
Without it, junction creation will fail with "Access denied" or "A required privilege is not held."

macOS/Linux: no special permissions needed (/connect creates a regular symlink).
```
- **Complexity:** S
- **Priority:** P2

---

**CROSS-11 — Add CI with multi-OS matrix**
- **Problem:** Tests are never run on macOS or Linux in CI (there is no CI). Platform bugs can go undetected indefinitely.
- **Affected OS:** All
- **Solution:** Add to `.github/workflows/ci.yml` (extends the CI from the general audit):
```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pytest tests/ -v
  validate:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - shell: bash
        run: |
          find projects -path "*/wiki/*.md" ! -name "_*" ! -name "log.md" \
            -exec python scripts/validate_frontmatter.py {} +
```
Note: use `shell: bash` on Windows steps that use bash syntax (GitHub Actions provides Git Bash on Windows runners).
- **Complexity:** M
- **Priority:** P2

---

**CROSS-12 — Fix `PRAGMA journal_mode=WAL` note for edge cases**
- **Problem:** `build_index` sets WAL mode on the SQLite database. WAL mode requires shared-memory support, which may fail on some network drives (NFS, Samba) and older Docker overlayfs configurations.
- **Affected OS:** Primarily Linux (NFS/network mounts); not a desktop concern
- **Solution:** Add graceful fallback:
```python
try:
    conn.execute("PRAGMA journal_mode=WAL")
except sqlite3.OperationalError:
    pass  # Network filesystem — WAL not supported; default journal mode is fine
```
- **Complexity:** S
- **Priority:** P2

---

### P3 — Low

---

**CROSS-13 — Add Python version badge to README**
- **Solution:** Add to README.md:
```markdown
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
```
- **Complexity:** S
- **Priority:** P3

---

**CROSS-14 — Note that `push-public.ps1` is Windows-only in README**
- The README shows `.\scripts\push-public.ps1` without noting it is Windows/PowerShell-only. Add a one-line note pointing macOS/Linux users to `python scripts/reefiki.py publish-task`.
- **Complexity:** S
- **Priority:** P3

---

## 11. Quick-Start Per OS

### 11.1 Windows 11 (PowerShell)

**Prerequisites:**
- Python 3.11+ from [python.org](https://python.org) — check "Add to PATH" during install
- Git from [git-scm.com](https://git-scm.com)
- Developer Mode enabled (for `/connect` junctions): Settings → System → For developers → Developer Mode ON

```powershell
# 1. Verify Python version (must be 3.11+)
python --version

# 2. Clone the repository
git clone https://github.com/<your-user>/reefiki
cd reefiki

# 3. Install pre-commit hook
pip install pre-commit
pre-commit install

# 4. Verify core tools work
python scripts/reefiki.py --help

# 5. [Optional] Install uv for memoir layer
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Restart PowerShell after uv install

# 6. [Optional] Set memoir store location (skip if using default)
# Default on Windows: C:\Users\<you>\AppData\Local\memoir\reefiki
# To override: $env:REEFIKI_MEMOIR_STORE = "D:\path\to\store"

# 7. Open in your AI IDE (Claude Code, Cursor, Windsurf, etc.)
# The IDE should auto-load AGENTS.md

# 8. Create your first project (in the IDE chat):
# "Create a new project called 'test' about Python"

# 9. Save something:
# "Save https://peps.python.org/pep-0008/"

# 10. Run tests (optional)
python -m pytest tests\ -v
```

**⚠ Current blockers on Windows:**
- None for core functionality (Python CLI works)
- ~~Hardcoded `C:\Users\kissl\` default path for memoir~~ — affects only memoir features; fix in CROSS-01
- CRLF issues possible if Git `autocrlf=true` — fix by adding `.gitattributes` (CROSS-04)

---

### 11.2 macOS (zsh)

**Prerequisites:**
- Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- Python 3.11+: `brew install python@3.11`
- Git: pre-installed on macOS (Xcode Command Line Tools) or `brew install git`

```zsh
# 1. Verify Python version (must be 3.11+)
python3 --version
# If old: brew install python@3.11; then use python3.11 explicitly

# 2. Clone
git clone https://github.com/<your-user>/reefiki
cd reefiki

# 3. Install pre-commit
brew install pre-commit
# or: pip3 install pre-commit
pre-commit install

# 4. Verify core tools
python3 scripts/reefiki.py --help

# 5. [Optional] Install uv for memoir layer
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart terminal after uv install

# 6. Set REEFIKI_MEMOIR_STORE if needed
# Default (after CROSS-01 fix): ~/.local/share/memoir/reefiki
# export REEFIKI_MEMOIR_STORE="$HOME/.memoir/reefiki"  # custom

# 7. Open in AI IDE, create first project, etc. (same as Windows §11.1 steps 7-9)

# 8. Run validation (no rg needed)
python3 scripts/validate_frontmatter.py \
  $(find projects -path "*/wiki/*.md" ! -name "_*" ! -name "log.md")

# 9. Run tests
python3 -m pytest tests/ -v
```

**⚠ Current blockers on macOS:**
- `from enum import StrEnum` fails on Python < 3.11 — **install Python 3.11+**
- Pre-commit hook uses `python` not `python3` — **temporarily workaround:** `ln -s $(which python3) ~/.local/bin/python` or wait for CROSS-03 fix
- Memoir default store points to `C:\Users\kissl\...` — **set `REEFIKI_MEMOIR_STORE` env var** until CROSS-01 fix
- `push-public.ps1` unusable — **use:** `python3 scripts/reefiki.py publish-task --apply --public-snapshot`

---

### 11.3 Ubuntu/Debian (bash)

**Prerequisites check:**
```bash
# Ubuntu 22.04 ships Python 3.10 — NOT enough for StrEnum
python3 --version

# If < 3.11, install via deadsnakes PPA:
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-distutils

# Make 3.11 the default (optional):
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 10

sudo apt install git
```

```bash
# 1. Verify
python3.11 --version   # or python3 --version after update-alternatives

# 2. Clone
git clone https://github.com/<your-user>/reefiki
cd reefiki

# 3. Install pre-commit
pip3 install --user pre-commit
# or: sudo apt install pre-commit
pre-commit install

# 4. Verify
python3 scripts/reefiki.py --help

# 5. [Optional] uv for memoir
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env  # or restart terminal

# 6. Validation without rg
python3 scripts/validate_frontmatter.py \
  $(find projects -path "*/wiki/*.md" ! -name "_*" ! -name "log.md")

# 7. Tests
python3 -m pytest tests/ -v
```

**⚠ Current blockers on Ubuntu:**
- Ubuntu 22.04 default Python is 3.10 — **must install Python 3.11 via deadsnakes PPA**
- Ubuntu 24.04 ships Python 3.12 — **no issue**
- Pre-commit `entry: python` may fail if `python` not in PATH — set with `sudo apt install python-is-python3`
- Memoir default path is Windows-only — **set `REEFIKI_MEMOIR_STORE`**

---

### 11.4 WSL2 (bash)

WSL2 runs a full Linux environment. Follow the **Ubuntu/Debian** instructions (§11.3) inside WSL2.

**WSL2-specific notes:**

```bash
# IMPORTANT: Clone inside WSL2 filesystem for performance
# GOOD: ~/projects/reefiki
# SLOW: /mnt/c/Users/you/Documents/reefiki  (Windows FS access is ~10x slower)

# Recommended: clone within WSL2 home
cd ~
git clone https://github.com/<your-user>/reefiki
cd reefiki

# SQLite WAL mode works correctly on WSL2 ext4 filesystem ✅
# SQLite WAL mode may have issues on /mnt/c/ (Windows NTFS via 9P protocol) ⚠️
```

**Opening in Windows IDE from WSL2:**

```bash
# Cursor / VS Code with WSL extension
code .

# Claude Code (runs in WSL2 terminal natively)
# Navigate to ~/reefiki and open Claude Code

# For Windows-native IDEs (Cursor, Windsurf) pointing at WSL2 path:
# Use \\wsl.localhost\Ubuntu\home\<user>\reefiki as the Windows path
```

**⚠ Current blockers on WSL2:**
- Same Python 3.11 requirement as Ubuntu
- If repo cloned on `/mnt/c/` (Windows FS), SQLite WAL mode may occasionally fail — solution: clone to `~/`

---

## Summary Table

| Issue | CROSS-# | Windows | macOS | Linux | WSL2 | Priority |
|---|---|---|---|---|---|---|
| Hardcoded `C:\Users\kissl\` memoir default | CROSS-01 | ✅ (owner only) | ❌ Breaks | ❌ Breaks | ❌ Breaks | **P0** |
| `StrEnum` requires Python 3.11 undocumented | CROSS-02 | ⚠️ Easy to miss | ⚠️ | ❌ Ubuntu 22.04 | ⚠️ | **P0** |
| Pre-commit `entry: python` vs `python3` | CROSS-03 | ✅ | ⚠️ | ⚠️ | ⚠️ | **P0** |
| No `.gitattributes` (CRLF breaks frontmatter) | CROSS-04 | ❌ | ✅ | ✅ | ✅ | **P0** |
| No `pyproject.toml` / Python version stated | CROSS-05 | ⚠️ | ⚠️ | ⚠️ | ⚠️ | P1 |
| `uvx`/`memoir-ai` undocumented | CROSS-06 | ⚠️ | ⚠️ | ⚠️ | ⚠️ | P1 |
| `rg` undocumented in README examples | CROSS-07 | ⚠️ | ⚠️ | ⚠️ | ⚠️ | P1 |
| No `push-public.sh` for bash | CROSS-08 | N/A | ❌ Missing | ❌ Missing | ❌ Missing | P1 |
| Backslash path in AGENTS.md | CROSS-09 | ✅ | ❌ | ❌ | ❌ | P1 |
| Windows junction needs Developer Mode | CROSS-10 | ⚠️ Undocumented | N/A | N/A | N/A | P2 |
| No CI matrix (all OS untested) | CROSS-11 | — | — | — | — | P2 |
| WAL mode on network/overlay FS | CROSS-12 | Low risk | Low risk | Low risk | ⚠️ `/mnt/c` | P2 |

**Immediate sprint (fully independent, ~4 hours):**

1. CROSS-04 — Create `.gitattributes` (30 min)
2. CROSS-01 — Fix hardcoded Windows path (30 min)
3. CROSS-02 — Add Python version guard + note (30 min)
4. CROSS-03 — Fix pre-commit `python3` (15 min)
5. CROSS-09 — Fix backslash in AGENTS.md (5 min)
6. CROSS-05 — Create `pyproject.toml` (30 min)
7. CROSS-08 — Create `push-public.sh` (60 min)
8. CROSS-07 — Add bash/PowerShell alternatives in README (45 min)
