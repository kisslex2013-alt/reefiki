# REEFIKI — Аудит зависимостей и требований к установке

> Дата: 1 июня 2026. Срез main-ветки `kisslex2013-alt/reefiki`.

---

## Содержание

1. [Шаг 1 — Инвентаризация импортов](#шаг-1--инвентаризация-импортов)
2. [Шаг 2 — Аудит системных инструментов](#шаг-2--аудит-системных-инструментов)
3. [Шаг 3 — Понижение версии Python](#шаг-3--понижение-версии-python)
4. [Шаг 4 — Git-опциональность](#шаг-4--git-опциональность)
5. [Шаг 5 — Анализ установки](#шаг-5--анализ-установки)
6. [Шаг 6 — Pre-commit и dev-инструменты](#шаг-6--pre-commit-и-dev-инструменты)
7. [Шаг 7 — Obsidian](#шаг-7--obsidian)
8. [Шаг 8 — Сводная таблица требований](#шаг-8--сводная-таблица-требований)
9. [Шаг 9 — Идеальный setup flow по платформам](#шаг-9--идеальный-setup-flow-по-платформам)

---

## Шаг 1 — Инвентаризация импортов

### 1.1 Полная таблица: все файлы, все импорты

| Файл | `__future__`? | Импорт | Тип | Min Python |
|---|---|---|---|---|
| `scripts/reefiki.py` | ✅ да | `from __future__ import annotations` | stdlib | 3.7+ |
| | | `import argparse` | stdlib | 3.2+ |
| | | `import fnmatch` | stdlib | 2.0+ |
| | | `import hashlib` | stdlib | 2.5+ |
| | | `import json` | stdlib | 2.6+ |
| | | `import os` | stdlib | — |
| | | `import posixpath` | stdlib | — |
| | | `import re` | stdlib | — |
| | | `import sqlite3` | stdlib | 2.5+ |
| | | `import subprocess` | stdlib | 2.4+ |
| | | `import sys` | stdlib | — |
| | | `import tempfile` | stdlib | — |
| | | `from collections import Counter` | stdlib | 2.7+ |
| | | `from datetime import date, datetime` | stdlib | — |
| | | `from pathlib import Path` | stdlib | 3.4+ |
| | `from urllib.parse import ...` | stdlib | 3.0+ |
| | | `from reefiki_memory import (...)` | local | — |
| `scripts/validate_frontmatter.py` | ❌ **нет** | `import sys` | stdlib | — |
| | | `import re` | stdlib | — |
| | | `import json` | stdlib | — |
| | | `from pathlib import Path` | stdlib | 3.4+ |
| | | `int \| None` в сигнатурах | runtime syntax | **3.10+** ⚠️ |
| | | `dict[str, object]` в сигнатурах | runtime syntax | **3.9+** |
| `scripts/reefiki_memory/__init__.py` | ✅ да | `from __future__ import annotations` | stdlib | 3.7+ |
| | | `from dataclasses import dataclass, field` | stdlib | 3.7+ |
| | | `from enum import StrEnum` | stdlib | **3.11+** ❌ |
| | | `from pathlib import Path` | stdlib | 3.4+ |
| | | `import re` | stdlib | — |
| | | `from typing import Any` | stdlib | 3.5+ |
| `tests/test_reefiki_memory_contracts.py` | ❌ нет | `import unittest, contextlib, importlib.util, io, json, os, subprocess, tempfile` | stdlib | — |
| | | `from pathlib import Path` | stdlib | 3.4+ |
| | | `from scripts.reefiki_memory import (...)` | local | — |
| `tests/test_reefiki_dedup.py` | ❌ нет | `import contextlib, importlib.util, io, tempfile, unittest` | stdlib | — |
| | | `from pathlib import Path` | stdlib | 3.4+ |
| `tests/test_reefiki_memory_governance.py` | ❌ нет | `import importlib.util, tempfile, unittest` | stdlib | — |
| | | `from pathlib import Path` | stdlib | 3.4+ |
| `tests/test_public_snapshot_guard.py` | ❌ нет | `import unittest` | stdlib | — |
| | | `from pathlib import Path` | stdlib | 3.4+ |
| `tests/test_validate_frontmatter.py` | ❌ нет | `import contextlib, importlib.util, io, json, tempfile, unittest` | stdlib | — |
| | | `from pathlib import Path` | stdlib | 3.4+ |

### 1.2 Ключевые выводы по импортам

**Единственный реальный ограничивающий импорт:**

```python
# scripts/reefiki_memory/__init__.py, строка 4
from enum import StrEnum   # требует Python 3.11+
```

`StrEnum` появился в `enum` модуле stdlib только в **Python 3.11** (CPython issue #91842, октябрь 2022). В Python 3.10 и ниже этого класса в stdlib нет.

**Второй скрытый ограничитель — `validate_frontmatter.py`:**

Файл не имеет `from __future__ import annotations`. Все аннотации вычисляются **в рантайме** при загрузке модуля:

```python
# validate_frontmatter.py, строки 50–57 (runtime!)
def error(
    path: Path,
    code: str,
    message: str,
    line: int | None = None,      # X | Y без __future__ → TypeError на Python 3.9
    column: int | None = None,
    expected: object | None = None,
    actual: object | None = None,
) -> dict[str, object]:
```

`int | None` в аннотации функции **без `from __future__ import annotations`** — синтаксис PEP 604, добавлен в **Python 3.10**. На Python 3.9 упадёт с `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` при первом вызове этой функции.

**Роль `from __future__ import annotations`:**

В `reefiki.py` и `reefiki_memory/__init__.py` этот import есть → все аннотации `X | Y`, `dict[str, ...]`, `list[str, ...]` становятся строками и не вычисляются в рантайме → безопасны на Python 3.9+.

В `validate_frontmatter.py` его нет → аннотации вычисляются → требуется Python 3.10+.

**Сводная матрица по файлам:**

| Файл | Min Python (факт) | Причина |
|---|---|---|
| `reefiki.py` | 3.9 (сам по себе) | `__future__` защищает все `X\|Y`; нет 3.11-фич |
| `validate_frontmatter.py` | **3.10** | `int \| None` runtime без `__future__` |
| `reefiki_memory/__init__.py` | **3.11** | `from enum import StrEnum` |
| Тесты | 3.4 | Только stdlib |
| **Весь проект** | **3.11** | Из-за `StrEnum` в `reefiki_memory` |

---

## Шаг 2 — Аудит системных инструментов

### 2.1 Все вызовы `subprocess.run` — детальный разбор

В `scripts/reefiki.py` ровно **5** вызовов `subprocess.run`.

---

**Вызов 1 — `uvx` (memoir-ai)**
```python
# scripts/reefiki.py, строки 1033–1040
# Функция: run_memoir(store, args)
# Вызывается из: global_lookup() (когда include_memoir=True),
#                memory_explain(), memory_pack() (через memoir слой)
completed = subprocess.run(
    ["uvx", "--from", "memoir-ai", "memoir", "--json", "--store", str(store)],
    check=False, capture_output=True, text=True, encoding="utf-8", env=env,
)
```

| Параметр | Значение |
|---|---|
| Команда | `uvx --from memoir-ai memoir ...` |
| Команды CLI, использующие | `memory lookup --layer memoir`, `memory lookup --layer all` |
| Что происходит при отсутствии `uvx` | `FileNotFoundError` — **неперехваченный**, traceback в stderr |
| Проверка наличия перед вызовом | ❌ **нет** (`shutil.which` не вызывается) |
| Graceful fallback | ❌ нет |

---

**Вызов 2 — `git diff --cached` (staged paths)**
```python
# scripts/reefiki.py, строки 1056–1068
# Функция: git_staged_paths(repo, env)
# Вызывается из: guard_staged_payload(), harvest_commit_payload()
completed = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
    cwd=repo, check=False, capture_output=True, text=True, encoding="utf-8", env=env,
)
```

| Параметр | Значение |
|---|---|
| Команда | `git diff --cached --name-only --diff-filter=ACMRT` |
| Команды CLI, использующие | `guard-staged`, `harvest-commit` |
| Что происходит при отсутствии `git` | `FileNotFoundError` — **неперехваченный** |
| Проверка наличия | ❌ нет |

---

**Вызов 3 — `git *args` (generic runner)**
```python
# scripts/reefiki.py, строки 1072–1081
# Функция: run_git(repo, args, env)
# Вызывается из: git_status_paths(), git_current_branch(), git_head(),
#                git_changed_paths(), git_ref_exists(), git_is_ancestor(),
#                publish_task_payload(), cleanup_worktree_payload(),
#                push_public_snapshot()
completed = subprocess.run(
    ["git", *args],
    cwd=repo, check=False, capture_output=True, text=True, encoding="utf-8", env=env,
)
```

| Параметр | Значение |
|---|---|
| Команды git | `status --porcelain=v1`, `rev-parse HEAD`, `log`, `diff`, `branch`, `checkout`, `push`, `commit`, и др. |
| Команды CLI, использующие | `guard-staged`, `harvest-commit`, `publish-task`, `cleanup-worktree` |
| Что происходит при отсутствии `git` | `FileNotFoundError` — **неперехваченный** |
| Проверка наличия | ❌ нет |

---

**Вызов 4 — `sys.executable validate_frontmatter.py`**
```python
# scripts/reefiki.py, строки 1203–1210
# Функция: harvest_commit_payload() — шаг validate перед коммитом
completed = subprocess.run(
    [sys.executable, str(validator), str(repo / "projects" / target_project / "wiki")],
    cwd=repo, check=False, capture_output=True, text=True, encoding="utf-8",
)
```

| Параметр | Значение |
|---|---|
| Команда | `python validate_frontmatter.py <wiki-dir>` |
| Используется | только в `harvest-commit` как шаг валидации |
| Что происходит при отсутствии | `validator.exists()` проверяется заранее — **безопасно** ✅ |
| Graceful | ✅ — если файл не найден, блок пропускается |

---

**Вызов 5 — `git *args` (memory diff runner)**
```python
# scripts/reefiki.py, строки 2179–2190
# Функция: _run_git(root, args)
# Вызывается из: memory_diff(), resolve_since_date_ref()
completed = subprocess.run(
    ["git", *args],
    cwd=root, check=False, capture_output=True, text=True, encoding="utf-8",
)
if completed.returncode != 0:
    raise SystemExit(detail)
```

| Параметр | Значение |
|---|---|
| Команды git | `log --name-only --diff-filter=AM`, `rev-list --min-parents=0 HEAD`, `rev-parse --verify` |
| Команды CLI, использующие | `memory diff` |
| Что происходит при отсутствии `git` | `FileNotFoundError` — **неперехваченный** |

---

### 2.2 Наличие / необходимость системных инструментов

| Инструмент | Нужен? | Где используется | При отсутствии | Документирован? |
|---|---|---|---|---|
| `git` | **Обязателен** для 5 команд; опционален для 13+ | `guard-staged`, `harvest-commit`, `publish-task`, `cleanup-worktree`, `memory diff` | `FileNotFoundError` (crash) | ❌ не задокументирован |
| `uvx` (uv) | **Опционален** | `memory lookup --layer memoir/all` | `FileNotFoundError` (crash) | ❌ не задокументирован |
| `sqlite3` (CLI) | ❌ не нужен | — | — | — |
| `rg` / ripgrep | ❌ не используется в коде | Только в примерах README | — | ❌ не задокументирован как внешний |
| `pre-commit` | **Опционален** (только хук) | `.pre-commit-config.yaml` | Хук не работает; код работает | Упоминается, setup не показан |
| `obsidian` | ❌ не используется в коде | Только визуализация (README) | Ничего не ломается | Да — как опция |
| `gh` (GitHub CLI) | ❌ не используется | — | — | — |
| `python 3.11+` | ✅ **Обязателен** | Весь проект | `ImportError: StrEnum` | ❌ нигде не указана версия |

---

## Шаг 3 — Понижение версии Python

### 3.1 Как используется `StrEnum`

Полный анализ `scripts/reefiki_memory/__init__.py`:

```python
from enum import StrEnum

class ProviderCapability(StrEnum):
    READ = "read"
    WRITE_DRAFT = "write_draft"
    SEARCH = "search"
    PROMOTE_SOURCE = "promote_source"
    HEALTH = "health"
    PROVENANCE = "provenance"
    RELATED_SUGGESTIONS = "related_suggestions"
```

Используется в двух местах:
1. `ProviderDescriptor.capabilities: list[ProviderCapability]` — просто хранится как список
2. `to_dict()` → `[str(capability) for capability in self.capabilities]` — конвертируется в строку

Место в `reefiki.py` (строка 1833):
```python
for capability in registry.providers[layer].capabilities
```
Просто итерация — без `str()`.

### 3.2 Критическая разница в `str()` между StrEnum и `str(str, Enum)`

Это **единственный подводный камень** при использовании naïve-полифилла:

```python
# Python 3.11 StrEnum
str(ProviderCapability.READ)  # → "read"   ✅ (возвращает value)

# class StrEnum(str, enum.Enum) без __str__
str(ProviderCapability.READ)  # → "ProviderCapability.read"  ❌ (Enum.__str__ берёт верх)
```

Это сломает `to_dict()` → `capabilities` вернёт `["ProviderCapability.read", ...]` вместо `["read", ...]`.

### 3.3 Безопасный полифилл

```python
# scripts/reefiki_memory/__init__.py — замена строки 4

try:
    from enum import StrEnum
except ImportError:
    # Python 3.9 / 3.10 polyfill
    import enum as _enum

    class StrEnum(str, _enum.Enum):  # type: ignore[no-redef]
        """Минимальный полифилл enum.StrEnum для Python < 3.11."""

        def __str__(self) -> str:
            return self.value

        def __repr__(self) -> str:
            return f"{type(self).__name__}.{self.name}"
```

**Что сохраняет полифилл:**
- `str(ProviderCapability.READ)` → `"read"` ✅
- `ProviderCapability.READ == "read"` → `True` ✅ (наследование от `str`)
- Итерация, хранение в списках — без изменений ✅
- JSON-сериализация через `to_dict()` — правильные значения ✅

**Что полифилл НЕ воспроизводит (но в проекте не используется):**
- `StrEnum._missing_()` hook — не используется
- Специфика `_generate_next_value_()` — не используется
- `format()` / f-string behavior (у полифилла `format()` вернёт value через `str`, что совпадает) ✅

**Вывод: полифилл безопасен для данного кода.**

### 3.4 Второй барьер: `validate_frontmatter.py` на Python 3.9

После применения полифилла для StrEnum остаётся второй барьер:

```python
# validate_frontmatter.py, строки 50–57 (NO __future__)
def error(..., line: int | None = None, ...) -> dict[str, object]:
```

**На Python 3.9:** `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`

**Два варианта фикса:**

*Вариант А — добавить `__future__` (рекомендуется):*
```python
# validate_frontmatter.py, строка 1 (добавить)
from __future__ import annotations
```
Это делает все аннотации строками → работает на Python 3.7+.

*Вариант Б — явные Optional:*
```python
from typing import Optional
def error(..., line: Optional[int] = None, ...) -> "dict[str, object]":
```
Работает на Python 3.5+, но многословно.

### 3.5 Матрица совместимости Python

| Python | `reefiki.py` | `validate_frontmatter.py` | `reefiki_memory` | Итог |
|---|---|---|---|---|
| 3.8 | ❌ `pathlib.Path` ok, но `reefiki_memory` не импортируется | ❌ `int\|None` crash | ❌ StrEnum нет + `dataclass` ok | ❌ |
| 3.9 | ✅ (`__future__` защищает) | ❌ `int\|None` runtime crash | ❌ StrEnum нет | ❌ |
| **3.10** | ✅ | ✅ (`int\|None` работает) | ❌ StrEnum нет | ❌ |
| **3.11** | ✅ | ✅ | ✅ | ✅ текущий минимум |
| 3.12 | ✅ | ✅ | ✅ | ✅ |
| 3.13 | ✅ | ✅ | ✅ | ✅ |

**После применения обоих фиксов (StrEnum polyfill + `__future__` в validate_frontmatter.py):**

| Python | Итог | Примечания |
|---|---|---|
| 3.8 | ❌ | `dataclass` ok, но `dict[str,...]` в builtin generic требует 3.9 |
| **3.9** | ✅ | Полностью рабочий после двух патчей |
| 3.10 | ✅ | |
| 3.11+ | ✅ | |

**Реальный достижимый минимум: Python 3.9** (после двух однострочных патчей).

---

## Шаг 4 — Git-опциональность

### 4.1 Классификация команд по зависимости от git

**Группа A — git НЕ нужен (read-only, filesystem/SQLite):**

| Команда | Что делает | Реальная зависимость |
|---|---|---|
| `index` | Индексирует wiki в SQLite FTS5 | Filesystem walk + SQLite |
| `search` | Полнотекстовый поиск | SQLite only |
| `status` | Inbox, seen, wiki stats | Filesystem only |
| `privacy` | Сканирует приватные данные | Filesystem only |
| `dedup` | Проверка дублей по URL/файлам | Filesystem + hash |
| `save` | Сохраняет URL/файл в inbox | HTTP fetch + filesystem |
| `plan create/check` | Создаёт/верифицирует планы | Filesystem + SHA256 |
| `timeline` | Хронология log.md | Filesystem only |
| `review-queues` | Анализ очередей | Filesystem + SQLite |
| `backlinks` | Индекс обратных ссылок | Filesystem only |
| `promote-dry-run` | Анализ промоции | Filesystem + SQLite |
| `tool-trigger` | JSON-payload для триггера | Pure logic |
| `memory route` | Маршрутизация памяти | Pure logic |
| `memory status` | Статус провайдеров памяти | Filesystem + memoir (optional) |
| `memory preflight` | Политика доступа | Pure logic |
| `memory explain` | Объяснение поиска | SQLite |
| `memory pack` | Пакует контекст для задачи | Filesystem + SQLite |
| `memory promote` | Предлагает промоцию | Filesystem + SQLite |
| `memory promotion-inbox` | Управление promotion inbox | Filesystem |
| `memory lookup --layer reefiki` | Поиск в wiki | SQLite |

**Группа B — git ОБЯЗАТЕЛЕН:**

| Команда | Что делает git | Операция |
|---|---|---|
| `guard-staged` | `git status --porcelain=v1 -z`, `git diff --cached` | Проверяет staged files |
| `harvest-commit` | `git diff --cached`, `git add`, `git commit` | Создаёт изолированный коммит |
| `publish-task` | `git rev-parse`, `git log`, `git branch`, `git push` | Публикует задачу в public remote |
| `cleanup-worktree` | `git worktree list/remove`, `git branch -d` | Чистит worktree |
| `memory diff` | `git log --name-only`, `git rev-parse` | Diff wiki по git-истории |
| `memory lookup --layer memoir` | нет git, но нужен `uvx` | memoir layer через uvx |

### 4.2 Сколько точек нужно обернуть для git-free работы

Все git-вызовы проходят через 4 функции-gateway:

```
run_git()          → строки 1071–1081 (generic git runner, check=False)
_run_git()         → строки 2178–2190 (memory diff runner, raises SystemExit)
git_staged_paths() → строки 1055–1068 (staged files)
git_status_paths() → строки 1091–1111 (status --porcelain)
```

**4 точки обёртки** — для graceful degradation без git:

```python
# Предложение: добавить в начало каждой функции
import shutil

def _git_available() -> bool:
    return shutil.which("git") is not None

def git_staged_paths(repo: Path, env: dict[str, str] | None = None) -> list[str]:
    if not _git_available():
        raise SystemExit(
            "git не найден. Команды guard-staged и harvest-commit требуют git.\n"
            "Установи git: https://git-scm.com"
        )
    # ... существующий код ...
```

Или centralised guard в `main()`:

```python
# Добавить в main(), до dispatch git-команд
GIT_COMMANDS = {"guard-staged", "harvest-commit", "publish-task", "cleanup-worktree", "memory"}

def _require_git(cmd: str) -> None:
    import shutil
    GIT_REQUIRED = {"guard-staged", "harvest-commit", "publish-task", "cleanup-worktree"}
    if cmd in GIT_REQUIRED and not shutil.which("git"):
        raise SystemExit(
            f"Команда '{cmd}' требует git.\n"
            "Установи: https://git-scm.com\n\n"
            "Команды без git: index, search, status, save, dedup, plan, timeline,\n"
            "  review-queues, backlinks, promote-dry-run, memory (кроме diff)"
        )
```

**Группа A работает без git уже сейчас.** Только для `memory diff` нужна обёртка `_run_git`.

---

## Шаг 5 — Анализ установки

### 5.1 Существующие установочные файлы

```
pyproject.toml       — НЕ СУЩЕСТВУЕТ
setup.py             — НЕ СУЩЕСТВУЕТ
requirements.txt     — НЕ СУЩЕСТВУЕТ
requirements-dev.txt — НЕ СУЩЕСТВУЕТ
Makefile             — НЕ СУЩЕСТВУЕТ
QUICKSTART.md        — НЕ СУЩЕСТВУЕТ
INSTALL.md           — НЕ СУЩЕСТВУЕТ
```

**Нет ни одного установочного файла.**

### 5.2 Работает ли `python scripts/reefiki.py status` без pip install?

**Да — работает.** Механизм:
1. Python добавляет директорию скрипта (`scripts/`) в `sys.path[0]`
2. `from reefiki_memory import (...)` находит `scripts/reefiki_memory/__init__.py`
3. Все зависимости — stdlib

Условия:
- Python ≥ 3.11 (или 3.9 после патчей)
- Запуск из корня репозитория
- Наличие директории `wiki/` в текущей директории (или `--project /path/to/project`)

```bash
# Работает:
git clone https://github.com/kisslex2013-alt/reefiki
cd reefiki/projects/_template   # или любой проект с wiki/
python ../../scripts/reefiki.py status

# Или из корня с явным --project:
python scripts/reefiki.py --project projects/_template status
```

### 5.3 Что нужно для первого запуска

**Минимальный набор (только core CLI):**
1. Python ≥ 3.11
2. git (для `guard-staged`, `harvest-commit`, `publish-task`)
3. `git clone https://github.com/kisslex2013-alt/reefiki`

Всё. Никакого pip install.

**Расширенный набор (+ memoir layer):**
4. `uv` → автоматически устанавливает `memoir-ai` через `uvx`

**Dev набор (+ хуки + тесты):**
5. `pip install pre-commit`
6. `pre-commit install`
7. `pip install pytest`

### 5.4 Минимальный setup script

```bash
#!/usr/bin/env bash
# scripts/setup.sh — однострочная установка
set -euo pipefail

# Проверка Python
PY=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
MAJOR=$(echo "$PY" | cut -d. -f1)
MINOR=$(echo "$PY" | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || [ "$MINOR" -lt 11 ]; then
    echo "❌ Нужен Python 3.11+. Найден: $PY"
    echo "   macOS: brew install python@3.11"
    echo "   Ubuntu: sudo apt install python3.11"
    echo "   Windows: https://python.org"
    exit 1
fi
echo "✅ Python $PY"

# Проверка git
if ! command -v git &>/dev/null; then
    echo "⚠️  git не найден. Команды guard-staged / harvest-commit / publish-task работать не будут."
    echo "   Установи git: https://git-scm.com"
else
    echo "✅ git $(git --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')"
fi

# Проверка uv (опционально)
if command -v uvx &>/dev/null; then
    echo "✅ uvx (memoir layer доступен)"
else
    echo "ℹ️  uvx не найден (memoir layer недоступен)"
    echo "   Установи uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# Быстрый тест
python3 scripts/reefiki.py --project projects/_template status 2>/dev/null && \
    echo "✅ reefiki работает" || echo "⚠️  Запусти из корня репозитория"

echo ""
echo "Готово. Первый запуск:"
echo "  python3 scripts/reefiki.py --project projects/_template status"
```

### 5.5 Можно ли `curl ... | python3`? (standalone)

**Нет** — из-за `from reefiki_memory import (...)`. При `curl .../reefiki.py | python3` интерпретатор получает только `reefiki.py`, без `reefiki_memory/` директории, и упадёт с `ModuleNotFoundError`.

Для standalone-запуска нужно либо:
- Клонировать репозиторий (текущий способ)
- **Или** сделать `reefiki.py` по-настоящему standalone: вставить содержимое `reefiki_memory/__init__.py` прямо в `reefiki.py` через автоматическую сборку (`scripts/build_standalone.py`):

```python
# Идея: scripts/build_standalone.py
from pathlib import Path
memory = Path("scripts/reefiki_memory/__init__.py").read_text()
reefiki = Path("scripts/reefiki.py").read_text()
# Убрать 'from reefiki_memory import ...' и вставить содержимое модуля выше
standalone = memory.replace("from __future__ import annotations\n", "") + "\n" + reefiki
Path("dist/reefiki_standalone.py").write_text(standalone)
```

### 5.6 Возможен ли `pipx install`?

**Сейчас — нет.** Нужен `pyproject.toml` с `[project.scripts]`. После добавления:

```toml
# pyproject.toml
[project]
name = "reefiki"
version = "0.1.0"
description = "Personal knowledge control plane"
requires-python = ">=3.11"
dependencies = []   # только stdlib + local module

[project.scripts]
reefiki = "reefiki:main"

[tool.setuptools.packages.find]
where = ["scripts"]

[tool.setuptools.package-dir]
"" = "scripts"

[project.optional-dependencies]
memoir = []   # uv/uvx устанавливается отдельно
dev = [
    "pre-commit>=3.7",
    "pytest>=8.0",
]
```

```bash
# После добавления pyproject.toml:
pipx install .
reefiki --project /path/to/project status
```

---

## Шаг 6 — Pre-commit и dev-инструменты

### 6.1 Hooks в `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: check-yaml          # stdlib, нет внешних зависимостей
      - id: trailing-whitespace  # stdlib
      - id: end-of-file-fixer    # stdlib

  - repo: local
    hooks:
      - id: reefiki-frontmatter
        entry: python scripts/validate_frontmatter.py   # ⚠️ python vs python3
        language: python
        files: ^projects/.*/wiki/.*\.md$
```

**Внешние зависимости хуков:**
- `pre-commit-hooks` — встроенные в пакет `pre-commit`, не требуют доп. установки
- `reefiki-frontmatter` — вызывает `python` (не `python3`) + `validate_frontmatter.py`

**Проблема `entry: python`:** на macOS/Linux команда `python` может отсутствовать. Нужна `python3`:

```yaml
entry: python3 scripts/validate_frontmatter.py
language: python
language_version: "3.11"
```

### 6.2 pre-commit — нужен ли для работы?

**Нет.** `pre-commit` нужен только для автоматической проверки при `git commit`. Без него:
- Весь core CLI работает
- Фронтматтер можно проверить вручную: `python3 scripts/validate_frontmatter.py wiki/путь/к/файлу.md`
- Хук просто не активируется автоматически

### 6.3 pytest — нужен ли для работы?

**Нет.** `pytest` нужен только для запуска тестов в разработке. Тесты написаны на `unittest`, запустить без pytest:

```bash
python -m unittest discover tests/
```

### 6.4 Схема зависимостей по ролям

```
ПОЛЬЗОВАТЕЛЬ (только CLI):
  Обязательно:  Python 3.11+
  Обязательно:  git (для 5 команд из 18)
  Опционально:  uv/uvx (memoir layer)

РАЗРАБОТЧИК WIKI (+ проверки):
  + pre-commit
  + pre-commit install

РАЗРАБОТЧИК КОДА (+ тесты):
  + pytest (или python -m unittest)

CONTRIB (+ публичный snapshot):
  + push-public.sh (или PowerShell)
```

### 6.5 Итоговый `pyproject.toml` с разделением зависимостей

```toml
[project]
name = "reefiki"
version = "0.1.0"
description = "Personal knowledge distillation wiki and memory control plane"
requires-python = ">=3.9"   # после применения патчей
dependencies = []            # только stdlib + bundled reefiki_memory

[project.optional-dependencies]
dev = [
    "pre-commit>=3.7",
    "pytest>=8.0",
]

[project.scripts]
reefiki = "reefiki:main"

[tool.setuptools.packages.find]
where = ["scripts"]

[tool.setuptools.package-dir]
"" = "scripts"

[tool.pytest.ini_options]
testpaths = ["tests"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"
```

---

## Шаг 7 — Obsidian

### 7.1 Как Obsidian используется в проекте

**Obsidian используется только как UI-viewer.** В коде нет ни одного вызова Obsidian CLI, API или плагина.

Упоминания в README (строки 208–214):
```
REEFIKI — это папка с markdown-файлами. Открой её в Obsidian как Vault:
узлы графа — wiki-страницы, рёбра — [[wikilinks]].
```

Obsidian используется для:
1. **Граф-вью** (`[[wikilinks]]` → визуальный граф) — декоративно, не функционально
2. **Полнотекстовый поиск** — дублирует SQLite FTS5 CLI
3. **Просмотр markdown** — любой viewer справится

### 7.2 Что ломается без Obsidian

**Ничего не ломается.** Абсолютно всё функциональное работает без Obsidian:
- Индексация — `python reefiki.py index`
- Поиск — `python reefiki.py search "запрос"`
- Сохранение — `python reefiki.py save https://...`
- Граф обратных ссылок — `python reefiki.py backlinks --format json`

### 7.3 Альтернативы для просмотра wiki

| Инструмент | Graфы? | Поиск? | Бесплатный? | Установка |
|---|---|---|---|---|
| **VS Code** + Markdown All in One | ❌ | ✅ | ✅ | `code .` |
| **Typora** | ❌ | ✅ | Платный | — |
| **Logseq** | ✅ (частично) | ✅ | ✅ | [logseq.com](https://logseq.com) |
| **markmap** | ✅ mindmap | ❌ | ✅ | `npx markmap` |
| **reefiki search** (CLI) | — | ✅ | ✅ | встроен |
| **Любой файловый менеджер** | ❌ | ❌ | ✅ | — |

Для AI-агентов Obsidian не нужен вообще — они работают с файлами напрямую.

---

## Шаг 8 — Сводная таблица требований

| Требование | Обязательно? | Опционально? | Как сделать опциональным | Сложность | Что теряется |
|---|---|---|---|---|---|
| **Python 3.11+** | ✅ сейчас | ✅ → 3.9 | StrEnum polyfill + `__future__` в validate_frontmatter.py | S (2 строки) | Ничего |
| **git** | ✅ для 5 команд | ✅ для 13+ | Graceful error в 4 функциях | S | `guard-staged`, `harvest-commit`, `publish-task`, `cleanup-worktree`, `memory diff` |
| **uv / uvx** | ❌ | ✅ memoir layer | `shutil.which` + человекочитаемый error | S | memoir lookup |
| **rg / ripgrep** | ❌ (не в коде) | ✅ полностью | Убрать из README-примеров, дать `find`-эквивалент | S | Только удобство в README |
| **pre-commit** | ❌ | ✅ | Это dev-зависимость; `pip install pre-commit[optional]` | S | Нет автопроверки на commit |
| **pytest** | ❌ | ✅ | `python -m unittest discover tests/` работает без pytest | — | Удобство запуска тестов |
| **Obsidian** | ❌ | ✅ | Уже опционален, только README-упоминание | — | Граф-вью |
| **pyproject.toml** | ❌ сейчас | — | Нужно создать для `pipx install` и управления версией | S | Нет `pipx install` |
| **sqlite3 CLI** | ❌ | ✅ | Не используется вообще | — | — |
| **gh CLI** | ❌ | ✅ | Не используется вообще | — | — |
| **QUICKSTART.md** | ❌ | — | Нужно создать | M | Высокий барьер входа |
| **.gitattributes** | ❌ | — | Нужно создать — CRLF на Windows | S | CRLF-баг на Windows |

**Итог: 2 реальных барьера входа**, оба устраняются за <30 минут:
1. Python 3.11 (большой барьер на Ubuntu 22.04) → фиксируется polyfill
2. Отсутствие QUICKSTART.md → фиксируется документом

---

## Шаг 9 — Идеальный setup flow по платформам

### 9.1 Windows 11 — чистая система

**Требования:** Windows 11, PowerShell 7+, интернет.

```powershell
# === Шаг 1: Python ===
# Скачай Python 3.11+ с https://python.org/downloads/
# ВАЖНО при установке: поставь галочку "Add Python to PATH"
# Проверка:
python --version
# Ожидаемо: Python 3.11.x или новее

# === Шаг 2: Git ===
# Скачай с https://git-scm.com/download/win
# Оставь настройки по умолчанию (LF line endings рекомендуется)
git --version
# Ожидаемо: git version 2.x.x.windows.x

# === Шаг 3: Клонирование ===
git clone https://github.com/kisslex2013-alt/reefiki
cd reefiki

# === Шаг 4: Первый запуск ===
python scripts\reefiki.py --project projects\_template status
# Ожидаемо:
# Project: _template
# Inbox: 0
# Seen: 0 (0 expired, 0 active)
# Wiki: ...

# === Шаг 5 (опционально): memoir layer ===
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Перезапусти PowerShell
uvx --version

# === Шаг 6 (опционально): pre-commit хуки ===
pip install pre-commit
pre-commit install
# Проверка: git commit вызовет валидацию frontmatter

# === Шаг 7: Developer Mode (для команды /connect) ===
# Настройки → Система → Для разработчиков → Режим разработчика: ВКЛ
```

**Возможные проблемы:**

| Ошибка | Причина | Решение |
|---|---|---|
| `python` не найден | PATH не настроен | Переустанови Python с галочкой "Add to PATH" |
| `ImportError: cannot import name 'StrEnum'` | Python < 3.11 | Обновись до Python 3.11+ |
| frontmatter regex не матчит | CRLF в файлах | Добавить `.gitattributes` (CROSS-04 из cross-platform аудита) |
| `git` не распознан | Git не в PATH | Перезапусти PowerShell после установки git |

---

### 9.2 macOS с Homebrew — минимальные шаги

```bash
# === Шаг 1: Homebrew (если нет) ===
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# === Шаг 2: Python 3.11+ ===
brew install python@3.11
python3.11 --version
# Ожидаемо: Python 3.11.x

# Алиас (опционально):
echo 'alias python3=python3.11' >> ~/.zshrc && source ~/.zshrc

# === Шаг 3: Git ===
# git уже есть (Xcode CLT) или:
brew install git

# === Шаг 4: Клонирование ===
git clone https://github.com/kisslex2013-alt/reefiki
cd reefiki

# === Шаг 5: Первый запуск ===
python3.11 scripts/reefiki.py --project projects/_template status

# === Шаг 6 (опционально): memoir ===
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env   # или перезапусти терминал
export REEFIKI_MEMOIR_STORE="$HOME/.local/share/memoir/reefiki"

# === Шаг 7 (опционально): pre-commit ===
pip3 install pre-commit
pre-commit install
```

**Возможные проблемы:**

| Ошибка | Причина | Решение |
|---|---|---|
| `python` не найден | macOS убрал системный python | Используй `python3` или `python3.11` |
| `ImportError: StrEnum` | macOS системный Python 3.9 | `brew install python@3.11` |
| pre-commit хук падает | `entry: python` не найден | `ln -s $(which python3.11) /usr/local/bin/python` или ждать CROSS-03 фикса |
| `/connect` создаёт симлинк | macOS использует symlink, не junction | Работает корректно ✅ |

---

### 9.3 Ubuntu 22.04 LTS — Python 3.10 из коробки

Ubuntu 22.04 поставляется с Python **3.10.12** — это **ниже требуемого 3.11**.

```bash
# === Шаг 1: Проверка версии ===
python3 --version
# Ubuntu 22.04: Python 3.10.12 — НЕДОСТАТОЧНО

# === Шаг 2A: Установить Python 3.11 через deadsnakes PPA ===
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv

# Проверка:
python3.11 --version
# Ожидаемо: Python 3.11.x

# === Шаг 2B (альтернатива): pyenv ===
curl https://pyenv.run | bash
# добавить в ~/.bashrc: export PATH="$HOME/.pyenv/bin:$PATH" + eval "$(pyenv init -)"
source ~/.bashrc
pyenv install 3.11.9
pyenv global 3.11.9
python --version  # → Python 3.11.9

# === Шаг 3: Git ===
sudo apt install git
git --version

# === Шаг 4: Клонирование ===
git clone https://github.com/kisslex2013-alt/reefiki
cd reefiki

# === Шаг 5: Первый запуск ===
python3.11 scripts/reefiki.py --project projects/_template status

# === Шаг 6: python-is-python3 (fix pre-commit entry: python) ===
sudo apt install python-is-python3
# Теперь `python` → python3

# === Шаг 7 (опционально): memoir ===
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
export REEFIKI_MEMOIR_STORE="$HOME/.local/share/memoir/reefiki"

# === Шаг 8 (опционально): pre-commit ===
pip3 install pre-commit
pre-commit install
```

**Альтернативный путь — без deadsnakes (только Ubuntu 24.04):**
```bash
# Ubuntu 24.04 LTS (Noble) — Python 3.12 из коробки ✅
python3 --version  # Python 3.12.x — всё работает без PPA
```

**Возможные проблемы Ubuntu 22.04:**

| Ошибка | Причина | Решение |
|---|---|---|
| `ImportError: cannot import name 'StrEnum'` | Python 3.10 | `sudo apt install python3.11` (deadsnakes PPA) |
| `python: command not found` | нет `python` алиаса | `sudo apt install python-is-python3` |
| `pre-commit: command not found` | не установлен | `pip3 install --user pre-commit` |
| SQLite FTS5 не работает | `python3.11` без полного sqlite3 | `sudo apt install python3.11-dev libsqlite3-dev` и пересборка через pyenv |

---

### 9.4 Пользователь без git — что доступно

Пользователь клонировал ZIP (без git-истории) или просто скопировал файлы.

```bash
# Скачать архив без git:
curl -L https://github.com/kisslex2013-alt/reefiki/archive/refs/heads/main.zip -o reefiki.zip
unzip reefiki.zip
cd reefiki-main
```

**Команды, работающие без git:**

```bash
python3 scripts/reefiki.py --project projects/_template index
python3 scripts/reefiki.py --project projects/_template status
python3 scripts/reefiki.py --project projects/_template search "python"
python3 scripts/reefiki.py --project projects/_template save "https://example.com/article"
python3 scripts/reefiki.py --project projects/_template dedup "https://example.com/article"
python3 scripts/reefiki.py --project projects/_template privacy
python3 scripts/reefiki.py --project projects/_template plan create "Мой план"
python3 scripts/reefiki.py --project projects/_template timeline
python3 scripts/reefiki.py --project projects/_template review-queues
python3 scripts/reefiki.py --project projects/_template backlinks
python3 scripts/reefiki.py --project projects/_template memory route "Запрос к памяти"
python3 scripts/reefiki.py --project projects/_template memory status
python3 scripts/reefiki.py --project projects/_template memory pack --task "Моя задача"
```

**Команды, НЕ работающие без git (явная ошибка):**

| Команда | Ошибка | Объяснение |
|---|---|---|
| `guard-staged` | `FileNotFoundError: [Errno 2] No such file or directory: 'git'` | Нужен staged index |
| `harvest-commit` | То же | Нужен `git add / commit` |
| `publish-task` | То же | Нужен `git log / push` |
| `cleanup-worktree` | То же | Нужен `git worktree` |
| `memory diff` | То же | Нужен `git log` |

**Важно:** Сейчас ошибка — неинформативный `FileNotFoundError` с traceback. После добавления `shutil.which`-проверок будет:

```
Команда 'guard-staged' требует git.
Установи git: https://git-scm.com

Команды без git: index, search, status, save, dedup, plan,
  timeline, review-queues, backlinks, memory (кроме diff)
```

---

## Краткий action plan

Все изменения — **малые (S)**, не требуют рефакторинга:

| # | Действие | Файл | Сложность | Эффект |
|---|---|---|---|---|
| 1 | StrEnum polyfill (4 строки) | `reefiki_memory/__init__.py` | S | Python 3.9 совместимость |
| 2 | `from __future__ import annotations` | `validate_frontmatter.py` | S | Python 3.9–3.10 совместимость |
| 3 | `shutil.which("git")` guard в 4 функциях | `reefiki.py` | S | Человекочитаемая ошибка без git |
| 4 | `shutil.which("uvx")` guard в `run_memoir` | `reefiki.py` | S | Ясный hint при отсутствии uv |
| 5 | Создать `pyproject.toml` | корень | S | `pipx install`, Python version marker |
| 6 | Создать `QUICKSTART.md` | корень | M | Главный барьер входа |
| 7 | Создать `.gitattributes` | корень | S | CRLF на Windows |
| 8 | `entry: python3` в pre-commit | `.pre-commit-config.yaml` | S | macOS/Linux pre-commit |
| 9 | `scripts/setup.sh` | `scripts/` | S | One-liner установка |
| 10 | Добавить `find`-эквивалент в README | `README.md` | S | Убрать зависимость от `rg` |
