# REEFIKI Install

Languages: [Русский](#русский) · [English](#english) · [中文](#中文)

## Русский

Это публичная страница установки REEFIKI CLI. Поддерживаемый путь для пользователя:

```powershell
pipx install git+https://github.com/kisslex2013-alt/reefiki.git
reefiki --help
reefiki onboarding
```

Требования: Git, Python 3.11+, `pipx` для изолированной установки или virtualenv для разработки из checkout.

Для безопасной первой проверки используй:

```powershell
reefiki onboarding
reefiki onboarding --fixture-root C:\Temp\reefiki-demo
```

Первый вызов ничего не пишет. Fixture-режим пишет только в указанный `--fixture-root`.

## English

This page is the public install landing for the current REEFIKI CLI. It documents the supported local install paths without adding an installer, marketplace package, auto-update mechanism or curl-to-shell script.

## 中文

这是 REEFIKI CLI 的公开安装入口。推荐用户安装方式：

```powershell
pipx install git+https://github.com/kisslex2013-alt/reefiki.git
reefiki --help
reefiki onboarding
```

要求：Git、Python 3.11+，以及用于隔离安装的 `pipx`，或用于 checkout 开发的 virtualenv。

安全的首次检查：

```powershell
reefiki onboarding
reefiki onboarding --fixture-root C:\Temp\reefiki-demo
```

第一个命令不会写入文件。Fixture 模式只会写入你指定的 `--fixture-root`。

## Requirements

- Git.
- Python 3.11 or newer.
- `pipx` for isolated user installs, or a Python virtual environment for checkout/developer installs.

REEFIKI core CLI has no runtime package dependencies beyond the Python standard library. Development and test workflows use optional tools such as `pytest` and `pre-commit`.

## User Install With pipx

Install from the git repository:

```powershell
pipx install git+https://github.com/kisslex2013-alt/reefiki.git
reefiki --help
reefiki onboarding
```

If the package is already installed:

```powershell
pipx upgrade reefiki
```

Uninstall:

```powershell
pipx uninstall reefiki
```

## Checkout Install

Use this path when you already cloned the repository or want to develop REEFIKI itself:

```powershell
git clone https://github.com/kisslex2013-alt/reefiki.git
cd reefiki
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\reefiki --help
.\.venv\Scripts\reefiki onboarding
```

The compatibility entrypoint remains available:

```powershell
python scripts\reefiki.py --help
python scripts\reefiki.py onboarding --format json
```

## First Safe Commands

Start with read-only or fixture-safe commands:

```powershell
reefiki --help
reefiki onboarding
reefiki onboarding --fixture-root C:\Temp\reefiki-demo
reefiki --project C:\Temp\reefiki-demo\projects\reefiki-onboarding-demo status
```

The dry-run onboarding command writes nothing. The fixture command writes only under the `--fixture-root` folder you provide.

## Developer Install

For tests and local development:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python scripts\reefiki.py publish-task --dry-run --cleanup --format json
```

Do not publish with raw `git push`. REEFIKI uses a guarded private/public workflow:

```powershell
python scripts\reefiki.py publish-task --dry-run --cleanup --format json
python scripts\reefiki.py publish-task --apply --cleanup --format json
```

## Current Boundaries

This install path does not provide:

- a hosted cloud account;
- a managed sync backend;
- an MCP server;
- vector or hybrid search runtime;
- marketplace submission or paid-gating;
- a curl-to-shell installer.

Those items stay behind separate product decisions and proof gates.

## Install Smoke

Minimal local smoke from a clean temporary virtual environment:

```powershell
$tmp = Join-Path $env:TEMP "reefiki-install-smoke"
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
python -m venv $tmp
& "$tmp\Scripts\python.exe" -m pip install .
& "$tmp\Scripts\reefiki.exe" --help
& "$tmp\Scripts\reefiki.exe" onboarding --format json
```

Expected result:

- `reefiki --help` prints the CLI command list;
- `reefiki onboarding --format json` returns a dry-run plan;
- no files are written outside the temporary virtual environment unless you explicitly pass `--fixture-root`.
