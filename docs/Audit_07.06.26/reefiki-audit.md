# REEFIKI — Полный аудит и план развития

> **Версия:** 1.0 | **Дата:** 2026-06-04
> **Охват:** Архитектура, governance, DX, skills system, автоматизация, оптимизация токенов.
> **Основано на:** README.md, AGENTS.md, COMMANDS.md, CLAUDE.md, файловое дерево репозитория,
> архитектурное описание проекта.

---

## Содержание

1. [Обзор архитектуры](#1-обзор-архитектуры)
2. [Анализ по категориям](#2-анализ-по-категориям)
3. [Предложения и рекомендации](#3-предложения-и-рекомендации)
4. [Skills system — расширение](#4-skills-system--расширение)
5. [Автоматизация](#5-автоматизация)
6. [Оптимизация токенов](#6-оптимизация-токенов)
7. [Roadmap](#7-roadmap)
8. [Сводная таблица предложений](#8-сводная-таблица-предложений)

---

## 1. Обзор архитектуры

REEFIKI — markdown-native knowledge control plane с чёткой трёхслойной архитектурой:

```
Control plane (Python)
  ├── reefiki.py              — монолитный CLI (~3949 LOC)
  ├── reefiki_memory/         — модуль памяти (285 LOC)
  └── validate_frontmatter.py — валидатор governance (397 LOC)

Knowledge store (markdown + SQLite FTS5)
  └── projects/<name>/wiki/** — типизированные страницы с обязательным frontmatter

Agent contracts (vendor-neutral markdown)
  ├── AGENTS.md               — корневой контракт (source of truth)
  ├── projects/<name>/AGENTS.md
  └── Stubs: CLAUDE.md, .cursorrules, .windsurf/, .codex/

Operations (slash-commands)
  └── .claude/commands/*.md   — save, process, query, harvest, lint, ...
```

**Ключевые сильные стороны архитектуры:**
- Один source of truth (AGENTS.md) с тонкими IDE-специфичными заглушками
- Типизированное знание (6 типов страниц) с обязательным `useful_when`
- Dual-remote publish с классификацией `private-only / public-safe / mixed`
- Агент-нейтральный дизайн: работает с любым IDE/агентом

---

## 2. Анализ по категориям

### 2.1 Архитектура и код

**Монолит reefiki.py (3949 LOC)**

Единственный файл содержит логически независимые подсистемы: CLI-парсинг, FTS5-индекс,
frontmatter CRUD, git-операции, dual-remote publish, memory routing/lookup/promote,
граф обратных ссылок, управление review queue. Проблема — не сложность, а
обнаруживаемость и тестируемость.

`reefiki_memory/` уже вынесен в отдельный модуль (285 LOC) — паттерн работает,
нужно распространить на весь codebase.

**Тесты (5 suites, ~2800 LOC)**

Соотношение 2800/4632 LOC (~60%) — здоровое. Риск: неизвестно покрыты ли git-операции
(`guard-staged`, `harvest-commit`, `publish-task`) реальными интеграционными тестами
или только mock-объектами.

**SQLite FTS5**

Отличный выбор для Phase 0i (~100 страниц). Rebuild тривиален, нет внешних зависимостей.
Проблема: `reindex` помечен как "emergency" — значит индекс может дрейфовать от
состояния диска. Дрейф должен быть невозможен при нормальном использовании.

### 2.2 Governance и data integrity

**Frontmatter schema**

`useful_when` как обязательное поле с "отказом при отсутствии" — сильнейшее дизайнерское
решение. Принудительная дистилляция при записи формирует качественный корпус.

Слабость: enforcement поведенческий (LLM отказывает), не механический (коммит блокируется).
Pre-commit hooks — необходимый backstop.

**30-дневный карантин**

`seen/` с `quarantine_until` — хорошо спроектирован. Риск: `/resolve` используется редко,
старые `## Conflicting claims` могут накапливаться незаметно. Без CI-счётчика
неразрешённых конфликтов дрейф невидим до следующего ручного `/lint`.

**Dual-remote publish**

Архитектурно корректен. Критический риск: если пользователь делает `git push` из
терминала минуя агент-сессию — pre-push проверка не срабатывает. Нужен механический guard.

### 2.3 Developer Experience

**Объём документации**

AGENTS.md (23 KB) + COMMANDS.md (32 KB) = 55 KB обязательного чтения. Для contributing
в Python-код — уместно. Для нового пользователя пытающегося сохранить первую страницу — избыточно.

**Время от clone до первого /save**

~10 минут при условии открытия папки в IDE с агентом. Точка трения: пользователи без
IDE+агент среды не видят точки входа. Нет `make setup` или `python -only` entrypoint.

**COMMANDS.md vs usability**

293-строчный COMMANDS.md — полный reference, не введение. Читкод в конце ("90% случаев
хватает `/save` и `/query`") частично помогает. Нужен отдельный QUICKSTART.md (1 страница, 5 команд).

### 2.4 Позиционирование

**Уникальное value proposition**

REEFIKI занимает реальную нишу между "личным markdown-vault" и "production memory service".
Ближайшие аналоги (Karpathy LLM wiki, Obsidian + AI plugin) не имеют governance.
Mem0/Zep/LangChain Memory — не аналоги: другой уровень абстракции.

**Что усиливает проект:**
- Vendor-neutral agent contract (AGENTS.md) совместим с любым будущим runtime
- Типизированная схема страниц делает retrieval осмысленным
- `useful_when` как обязательный gate формирует самоотбирающийся качественный корпус
- Dual-remote publish решает реальную задачу "поделиться частью знаний публично"

**Что ослабляет проект:**
- Нет `pip install` / `brew install` — friction для не-разработчиков
- Монолит ограничивает contributors
- Нет GitHub Actions CI в публичном дереве
- Публичный снапшот без demo-проекта выглядит пустым для новых пользователей

---

## 3. Предложения и рекомендации

### Категория Core

---

**C1 — Авто-reindex после /process и /harvest**

- **Проблема:** `/reindex` помечен "emergency" но `/process` и `/harvest` пишут новые
  страницы. Если обновление индекса упало (исключение, обрыв, усечение контекста агента)
  — индекс устарел до следующего ручного `/reindex`.
- **Решение:** Сделать обновление индекса обязательным логируемым шагом пайплайна записи:
  write page → append log → update index → git add → git commit. Post-write assertion:
  страница появляется в `index.md`.
- **Ценность:** Устраняет класс багов "orphaned page" которые накапливаются незаметно.
- **Сложность:** S (1–2 дня) | **Приоритет:** P0

---

**C2 — Pre-push git hook для dual-remote safety**

- **Проблема:** `publish-task --dry-run` требует чтобы агент добровольно запустил проверку
  перед `git push`. Push из терминала минует эту проверку.
- **Решение:** `.git/hooks/pre-push` (или `scripts/install-hooks.sh`) запускает
  `python scripts/reefiki.py publish-task --dry-run --format json` и блокирует push
  при вердикте `block`. Escape через `--skip-hook` с явным подтверждением.
- **Ценность:** Dual-remote safety становится механической гарантией, не поведенческой.
- **Сложность:** S (1–2 дня) | **Приоритет:** P0

---

**C3 — Идемпотентность /reindex**

- **Проблема:** При двойном запуске `/reindex` файл `index.md.bak` перезаписывается
  молча — теряется предыдущий бэкап.
- **Решение:** Бэкапы как `index.md.bak.<timestamp>` с configurable retention (default: 3).
  Флаг `--verify` сравнивает новый индекс с состоянием диска без записи — пригоден для CI.
- **Сложность:** S (1–2 дня) | **Приоритет:** P1

---

**C4 — CI-проверка истёкшего карантина**

- **Проблема:** `seen/` файлы с `quarantine_until` не проверяются механически.
  Страница может быть готова к re-evaluation месяцами без уведомления.
- **Решение:** Еженедельный GitHub Actions job или локальный cron:
  `python scripts/reefiki.py review-queues --type quarantine_expired --format json`
  → запись в `plans/quarantine-report-YYYY-MM-DD.md`. Без авто-удаления — только видимость.
- **Сложность:** S для скрипта, M для CI | **Приоритет:** P1

---

### Категория Code Quality

---

**Q1 — Разбивка reefiki.py на пакет**

- **Проблема:** 3949 LOC в одном файле. Contributor не знает где искать логику бэклинков
  vs логику git-операций vs FTS5 vs frontmatter.
- **Решение:**
  ```
  scripts/reefiki/
  ├── __main__.py          # тонкий CLI dispatch
  ├── commands/
  │   ├── save.py
  │   ├── process.py
  │   ├── query.py
  │   ├── harvest.py
  │   └── lint.py
  ├── memory/              # существующий reefiki_memory/ → сюда
  ├── git_ops.py           # guard_staged, harvest_commit, publish_task
  ├── frontmatter.py       # schema, validation, parsing
  ├── index.py             # index read/write/verify
  └── fts.py               # SQLite FTS5 interface
  ```
  Публичный API (`reefiki.py <command>`) не меняется.
- **Сложность:** L (1–2 недели) — механический рефакторинг. Требует Q3 как предусловие.
- **Приоритет:** P1

---

**Q2 — Типизация Python codebase**

- **Проблема:** Кастомный frontmatter-парсер без Pydantic/dataclasses → нарушения схемы
  проявляются как `KeyError` в runtime, не при парсинге.
- **Решение:** Typed dataclasses или Pydantic модели для каждого типа страницы.
  `mypy --strict` в CI. Начать с `frontmatter.py` и `index.py` — наибольший риск.
- **Сложность:** M (3–5 дней) | **Приоритет:** P1

---

**Q3 — Интеграционные тесты git-операций**

- **Проблема:** `guard-staged`, `harvest-commit`, `publish-task` зависят от реального
  git-состояния. Mock-тесты не покрывают конфликты при параллельных агент-потоках.
- **Решение:** `tests/test_git_integration.py` — временный git repo с двумя remote,
  различные сценарии staging, проверка вердиктов `block`/`pass`.
  `@pytest.mark.integration` — запускается в CI при push, не локально по умолчанию.
- **Сложность:** M (3–5 дней) | **Приоритет:** P0

---

**Q4 — GitHub Actions CI**

- **Проблема:** Нет `.github/workflows/`. Пользователи которые форкают репо не получают
  автоматическую проверку качества.
- **Решение:**
  ```yaml
  # .github/workflows/ci.yml
  on: [push, pull_request]
  jobs:
    lint-and-test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: { python-version: "3.11" }
        - run: pip install -r requirements.txt
        - run: python -m pytest tests/ -x --timeout=30
        - run: python scripts/validate_frontmatter.py --format json projects/_template/wiki/
        - run: python scripts/reefiki.py memory golden --project _template
  ```
- **Сложность:** S (1–2 дня) | **Приоритет:** P0

---

### Категория Integrations

---

**I1 — Gemini CLI stub**

- **Проблема:** README упоминает Gemini CLI как "add by template" — заглушки нет.
- **Решение:** `GEMINI.md` по паттерну CLAUDE.md: одна строка → AGENTS.md + Gemini-specific notes.
- **Сложность:** S (< 1 дня) | **Приоритет:** P2

---

**I2 — VS Code Copilot stub**

- **Решение:** `.github/copilot-instructions.md`:
  `Follow the instructions in AGENTS.md at the root of this repository.`
- **Сложность:** S (< 1 дня) | **Приоритет:** P2

---

**I3 — Руководство по Web Clipper**

- **Проблема:** COMMANDS.md упоминает Web Clipper для сохранения URL но без guidance
  по выбору инструмента, конфигурации, формату имён файлов.
- **Решение:** `docs/web-clipper.md`: рекомендуемые clippers (MarkDownload, Omnivore,
  Obsidian Web Clipper), target folder = `projects/<name>/inbox/`,
  конвенция имён `YYYY-MM-DD-<slug>.md`, минимальный frontmatter stub для `/process`.
- **Сложность:** S (1–2 дня) | **Приоритет:** P1

---

**I4 — Obsidian vault config**

- **Проблема:** `.obsidian/` существует но не задокументирован. Пользователи получают
  дефолтные настройки конфликтующие с архитектурой (граф показывает `raw/`, `seen/`).
- **Решение:** `docs/obsidian-setup.md` + готовые `.obsidian/app.json` и `graph.json`:
  фильтр графа `-path:raw -path:seen -path:inbox`, рекомендуемые плагины (Dataview, Tag Wrangler).
- **Сложность:** S (1–2 дня) | **Приоритет:** P1

---

### Категория Developer Experience

---

**D1 — QUICKSTART.md (5 команд, 1 страница)**

- **Проблема:** Новый пользователь: README → AGENTS.md → COMMANDS.md до первого действия.
- **Решение:** `QUICKSTART.md` (max 1 страница, EN + RU):
  ```
  1. git clone → открой папку в Claude Code / Cursor / Windsurf
  2. Агент: "Проектов нет. Создать?"
     → "Create project myproject about <тема>"
  3. /save https://example.com/interesting-article
  4. /process
  5. /query что мы решили про X?
  Всё остальное — опциональное обслуживание.
  ```
- **Сложность:** S (< 1 дня) | **Приоритет:** P1

---

**D2 — CONTRIBUTING.md**

- **Проблема:** Python-contributors не знают: где тесты, как запускать, что значит
  golden-test requirement, как организован монолит.
- **Решение:** `CONTRIBUTING.md` с: setup, запуск тестов, golden-test gate,
  файловая карта codebase.
- **Сложность:** S (1 день) | **Приоритет:** P2

---

**D3 — requirements.txt + pyproject.toml**

- **Проблема:** Нет `requirements.txt` в публичном дереве. `python scripts/reefiki.py`
  → import errors без guidance.
- **Решение:** `requirements.txt` + `pyproject.toml`:
  ```toml
  [project.scripts]
  reefiki = "scripts.reefiki:main"
  ```
  Установка: `pip install -e .`, вызов: `reefiki <command>`.
- **Сложность:** S (1–2 дня) | **Приоритет:** P0

---

**D4 — Bootstrap status command**

- **Проблема:** Startup contract описан прозой в AGENTS.md. Агенты при неполном парсинге
  пропускают шаги. Нет machine-readable checklist.
- **Решение:** `python scripts/reefiki.py status --bootstrap --format json`:
  ```json
  {
    "projects": ["myapp", "notes"],
    "inbox_sizes": {"myapp": 3},
    "lint_age_days": {"myapp": 45},
    "unresolved_conflicts": {"myapp": 2},
    "quarantine_expired": {"myapp": 1},
    "backup_age_days": 12
  }
  ```
- **Сложность:** M (3–5 дней) | **Приоритет:** P1

---

### Категория Ecosystem

---

**E1 — GitHub Topics + README badges**

- **Проблема:** 0 stars, 0 forks, нет GitHub Topics. Нулевая discoverability.
- **Решение:** Topics: `knowledge-management`, `llm`, `ai-agent`, `obsidian`,
  `personal-knowledge-base`, `claude`, `cursor`, `markdown`.
  Badges: Python version, license, CI status.
- **Сложность:** S (< 1 дня) | **Приоритет:** P2

---

**E2 — Публичный demo-проект**

- **Проблема:** Dual-remote дизайн означает что visitor видит template без реальных страниц.
  Непонятно как выглядит зрелый REEFIKI-проект.
- **Решение:** `projects/demo/` с `public: true` в `_domain.md` — 10–15 страниц
  по нейтральной теме (например, как использовать SQLite FTS5) со всеми 6 типами страниц
  и реальными `useful_when`.
- **Сложность:** M (3–5 дней) | **Приоритет:** P2

---

## 4. Skills System — расширение

### 4.1 Проблема: skills tied to IDE-projects без portability layer

При хранении skills в отдельном проекте на каждую IDE возникают три проблемы одновременно:

- **Дублирование без синхронизации** — один паттерн живёт в 5 проектах в разных стадиях зрелости
- **Слепота при адаптации** — нет явного разделения "идея (universal)" vs "реализация (IDE-specific)"
- **Нет сигнала о портируемости** — непонятно есть ли skill в других IDE и насколько они расходятся

### 4.2 Решение: двухслойная модель

```
projects/
├── skills-core/          ← НОВЫЙ: агент-нейтральный слой (паттерны)
│   └── wiki/
│       ├── skills/       ← universal patterns
│       └── sources/      ← источники с трассировкой
├── claude-code/
│   └── wiki/skills/      ← конкретные инструкции для Claude Code
├── codex/
│   └── wiki/skills/      ← конкретные инструкции для Codex
└── cursor/ windsurf/ ...
```

### 4.3 Новые поля frontmatter

**Для `type: skill` в skills-core:**

```yaml
portability: full | partial | ide-only
  # full     — паттерн работает везде без адаптации
  # partial  — нужна адаптация реализации (идея та же)
  # ide-only — принципиально непортируемый

implementations:
  claude-code: implemented | idea-only | missing | blocked
  codex: implemented | idea-only | missing | blocked
  cursor: implemented | idea-only | missing | blocked
  windsurf: implemented | idea-only | missing | blocked
  aider: implemented | idea-only | missing | blocked
```

**Для `type: skill` в IDE-проектах:**

```yaml
core_skill: <slug>                   # ссылка на skills-core
ide: claude-code | codex | cursor | windsurf | aider
portability_status: implemented | idea-only | diverged | deprecated
last_synced_with_core: YYYY-MM-DD
```

**Для `type: source` в skills-core:**

```yaml
url: https://...
archived_at: raw/<slug>.md
ide: claude-code | codex | cursor | windsurf | aider | universal
source_type: docs | changelog | post | video | experiment
source_nature: static | living
  # static  — конкретный пост/релиз. Не меняется.
  # living  — docs сайт, changelog, GitHub issue. Обновляется.
check_interval: 7d | 14d | 30d | 90d | never
last_checked: YYYY-MM-DD
skills_derived: [slug, slug]
portability_signal: full | partial | ide-only | unknown
```

**Для `type: skill` — трассировка к источнику:**

```yaml
derived_from:
  - source: <slug>
    what_used: "краткое описание что именно взято"
    confidence: high | medium | low

source_conflicts:
  - between: [source-slug-1, source-slug-2]
    on: "по какому вопросу противоречие"
    resolution: source-slug-1 | source-slug-2 | experiment | unknown
    resolved_date: YYYY-MM-DD
    review_trigger: "при каком событии перепроверить"

skill_version: "1.2"
breaking_change_in: "1.2"    # IDE-проекты должны обновить реализацию
```

### 4.4 Новые команды

**`/skill-port <slug> --from <ide> --to <ide>`**

```markdown
Готовит адаптацию skill из одной IDE в другую.

Что делает агент:
1. Читает skills-core/<slug>.md — core_pattern и adaptation notes
2. Читает projects/<from>/wiki/skills/<slug>.md — рабочую реализацию
3. Проверяет implementations[<to>] — idea-only или missing?
4. Показывает что в <from> завязано на IDE, что универсально
5. Предлагает черновик для <to> с явными TODO на IDE-специфичные части
6. После подтверждения — создаёт страницу в projects/<to>/wiki/skills/
7. Обновляет implementations[<to>] = implemented в skills-core
```

**`/source-check [--ide <name>] [--overdue] [--skill <slug>]`**

```markdown
Проверяет источники у которых истёк check_interval.

Что делает агент:
1. Находит source-страницы где (today - last_checked) > check_interval
2. Для каждой: url, skills_derived, что искать в новой версии
3. Пользователь проверяет оригинал, сообщает что изменилось
4. Агент обновляет last_checked и предлагает правки в skills_derived
```

**`/source-analogies`**

```markdown
Находит skill gaps на основе накопленных источников.

Логика: если source с portability_signal: partial описывает ограничение
которое есть и в другой IDE — но skills_derived для той IDE пустой —
это gap. Агент показывает список gaps и предлагает создать заготовки.

Имеет смысл при 20+ source страницах в skills-core.
```

**`/skill-sync <slug>`**

```markdown
Синхронизирует metadata skill во всех IDE-проектах за один проход.

Читает core skill один раз. Обходит все IDE-проекты с implementations: implemented.
Обновляет только frontmatter: last_synced_with_core, skill_version, breaking_change_in.
```

### 4.5 Страница source — целевой формат

```yaml
---
type: source
title: "Codex CLI — Tool Use & Memory, Changelog May 2026"
slug: codex-changelog-v2-may2026
url: https://github.com/openai/codex/releases/tag/v2.0-may2026
archived_at: raw/codex-changelog-v2-may2026.md
ide: codex
source_type: changelog
source_nature: living
check_interval: 30d
last_checked: 2026-05-15
skills_derived:
  - iterative-code-review
  - context-handoff-between-sessions
portability_signal: partial
useful_when: >
  Когда нужно проверить изменилось ли поведение Codex
  при передаче контекста — и обновить соответствующие skills.
---

## Что важно для skills (навигация, не пересказ)

- §3 "Persistent context" — почему контекст не переживает сессию
  → основа для skills про context handoff
- §7 "Tool call limits" — ограничение 10 вызовов за ход
  → влияет на iterative-review skill

## Сигналы для других IDE

Проблема persistent context в Codex аналогична Cursor Composer.
Claude Code решает через Memory layer. Windsurf — через Rules.
→ Этот источник полезен как аналогия для любого skill про multi-pass workflows.

## Триггер обновления skills

Если в следующем changelog: "persistent context" или "session memory" —
перечитать и обновить: iterative-code-review, context-handoff-between-sessions.
```

> **Ограничение размера:** source страница в skills-core — **300–500 токенов**.
> Если растёт до 1500+ — контент уходит в `raw/`, здесь остаётся только навигация.

---

## 5. Автоматизация

### 5.1 Принцип безопасной автоматизации

```
Обратимо без потерь  → агент делает сам, сообщает кратко
Обратимо с усилием   → агент делает, явно называет что изменил
Необратимо           → агент предлагает, пользователь говорит "да"
```

**Граница:** агент управляет метаданными и черновиками. Пользователь управляет контентом.

### 5.2 Полная автоматизация (агент делает + кратко сообщает)

---

**A1 — Drift detection при старте сессии**

- **Триггер:** открытие любого IDE-проекта или skills-core
- **Что делает агент:** считает drift score для source страниц → просроченные помечает
  тегом `needs-check` во frontmatter → запись в `wiki/log.md`
- **Сообщение:**
  ```
  Помечено 3 источника как needs-check:
  codex-changelog-v2 (45д), anthropic-tool-use (32д), cursor-docs-mar (31д).
  Запусти /source-check когда готов.
  ```
- **Почему безопасно:** только добавляет тег, контент не меняется

---

**A2 — Авто-пометка skills при обновлении source**

- **Триггер:** завершение `/source-check` для источника
- **Что делает агент:** проходит по skills с этим source в `derived_from` →
  `confidence: high` → `needs-review`, `confidence: medium` → `watch`, `low` → только лог
- **Сообщение:**
  ```
  Source обновлён. Затронуто skills:
  → needs-review: iterative-code-review, context-handoff
  → watch: session-memory-pattern
  ```

---

**A3 — Gap injection в черновик при /skill-port**

- **Триггер:** запуск `/skill-port <slug> --from X --to Y`
- **Что делает агент:** проверяет source страницы из `derived_from` →
  извлекает адаптационные заметки для целевой IDE → включает в черновик
- **Сообщение:**
  ```
  Создан черновик для cursor.
  Включены адаптационные заметки из 2 источников.
  Требует проверки: TODO в §2 (cursor-specific context persistence).
  ```
- **Черновик в `plans/`, не в `wiki/` — apply только явно**

---

**A4 — Авто-индексация новых implementations**

- **Триггер:** создание skill страницы в IDE-проекте (`/skill-port --apply` или вручную)
- **Что делает агент:** находит страницу в skills-core по `core_skill` →
  обновляет `implementations[ide]` → `implemented` → обновляет `wiki/index.md`
- **Сообщение:**
  ```
  implementations обновлён в skills-core:
  iterative-code-review → cursor: implemented
  ```

---

**A5 — Авто-обнаружение gaps при накоплении источников**

- **Триггер:** количество source страниц пересекает порог (конфиг в `_domain.md`, default: 20)
- **Что делает агент:** тихий скан → для каждого `portability_signal: partial` source →
  ищет IDE где ограничение то же но skill отсутствует → отчёт в `plans/`
- **Сообщение:**
  ```
  Обнаружено 4 потенциальных skill gap.
  Отчёт: plans/source-analogies-2026-06-03.md
  ```

---

### 5.3 Частичная автоматизация (агент делает, явно называет изменения)

---

**B1 — Обновление last_synced_with_core в IDE-проектах**

- **Триггер:** изменение `skill_version` в skills-core
- **Что делает агент:** обновляет только `last_synced_with_core` в IDE-проектах →
  если `breaking_change_in` — добавляет тег `breaking-change-pending`
- **Сообщение:**
  ```
  Обновлён last_synced_with_core в 3 IDE-проектах:
  claude-code, codex, windsurf → 2026-06-04
  cursor → помечен breaking-change-pending (требует адаптации §2)
  ```

---

**B2 — Архивация просроченных черновиков**

- **Триггер:** `/source-check` или старт сессии, черновики в `plans/` старше 30 дней
  со статусом `idea-only`
- **Что делает агент:** перемещает в `plans/closed/` с `reason: expired` →
  обновляет `implementations` → `missing`
- **Сообщение:**
  ```
  Архивировано 2 устаревших черновика (>30д):
  plans/closed/skill-port-aider-20260503.md
  plans/closed/skill-port-gemini-20260501.md
  implementations → missing
  ```

---

### 5.4 Никогда не автоматизировать

| Операция | Причина |
|---|---|
| Изменение контента существующей skill страницы | Даже при изменении source — только `needs-review` тег |
| Удаление/перемещение из `wiki/` в `seen/` | `use_count=0` не означает бесполезность |
| Разрешение `source_conflicts` | Выбор чему доверять — суждение пользователя |
| Apply `/skill-port` черновика | Адаптация под IDE — интеллектуальное решение |
| Запись в `wiki/` из CI или cron | CI читает и проверяет, но не пишет |

### 5.5 Где живут правила автоматизации

```yaml
# projects/skills-core/AGENTS.md — секция "Automation rules"
# Логика: что делать при каком триггере (A1–A5, B1–B2)

# projects/skills-core/_domain.md — параметры
automation_thresholds:
  source_analogies_trigger: 20   # кол-во sources для запуска A5
  drift_score_needs_review: 2.0
  draft_expiry_days: 30
  breaking_change_pending_tag: "breaking-change-pending"
```

Логика отдельно от параметров: правила в AGENTS.md, пороги в `_domain.md` — меняешь без правки контракта.

---

## 6. Оптимизация токенов

### 6.1 Откуда берётся расход

| Операция | Без оптимизации | С оптимизацией |
|---|---|---|
| Bootstrap (старт сессии) | 15–20K токенов | 1–2K токенов |
| /source-check (1 источник) | 8–12K токенов | 4–6K токенов |
| /skill-port (1 skill) | 20–40K токенов | 12–20K токенов |
| /skill-sync (1 skill, 5 IDE) | 15–25K токенов | 5–8K токенов |
| Типичная сессия | 50–80K токенов | 15–30K токенов |

Главная проблема — **drift detection при каждом старте**. Читать все source страницы
каждую сессию — расход который растёт линейно с корпусом.

### 6.2 Оптимизация 1 — Внешний drift cache (наибольшая отдача)

```
projects/skills-core/.drift-cache.json   ← в .gitignore
```

```json
{
  "generated": "2026-06-04T09:00:00",
  "overdue": [
    {"slug": "codex-changelog-v2", "days": 45,
     "affects": ["iterative-code-review"]},
    {"slug": "anthropic-tool-use", "days": 32,
     "affects": ["context-handoff"]}
  ],
  "ok_count": 24,
  "next_check": "2026-06-05"
}
```

Агент при старте читает только этот файл — **200 токенов вместо 15K**.
Скрипт пересчитывает кэш: git post-commit hook или cron раз в день.

```bash
python scripts/reefiki.py skills drift-cache --project skills-core
```

**Экономия:** ~75x на операции bootstrap при 30 источниках.

### 6.3 Оптимизация 2 — Lazy loading

Правило в `skills-core/AGENTS.md`:

```markdown
## Lazy loading rule

При старте: читай только .drift-cache.json и wiki/index.md
При /source-check: читай конкретный source slug
При /skill-port: читай core skill + source из derived_from + target IDE реализацию
НЕ читай все skill страницы при старте сессии
```

**Экономия:** 10–20x на типичной сессии где нужно 2–3 страницы из 50.

### 6.4 Оптимизация 3 — Компактный machine-readable index

```
projects/skills-core/wiki/index.min.json   ← генерируется автоматически
```

```json
[
  {
    "slug": "iterative-code-review",
    "portability": "partial",
    "impl": {"claude-code": "ok", "codex": "ok", "cursor": "gap"},
    "needs_review": false,
    "drift": 0.3
  },
  {
    "slug": "context-handoff",
    "portability": "full",
    "impl": {"claude-code": "ok", "codex": "idea-only"},
    "needs_review": true,
    "drift": 1.8
  }
]
```

Полная картина всех skills — **~1K токенов** вместо развёрнутого markdown индекса.
Генерируется после каждого `/process` или `/harvest`.

### 6.5 Оптимизация 4 — Батчинг /skill-sync

Вместо обхода IDE-проектов по одному:

```python
def skill_sync(slug, projects):
    core = read_once(f"skills-core/wiki/skills/{slug}.md")  # одно чтение
    for project in projects:
        path = f"{project}/wiki/skills/{slug}.md"
        update_frontmatter_only(path, {
            "last_synced_with_core": today(),
            "skill_version": core["skill_version"]
        })
    log_once(f"Synced {slug} across {len(projects)} projects")
```

**Экономия:** ~4x при 5 IDE-проектах.

### 6.6 Оптимизация 5 — Source страницы: лимит размера

Целевой размер source страницы в skills-core: **300–500 токенов**.
Полный текст → в `raw/`, в source-странице только навигация.

Добавить в `_schema.md`:
```yaml
max_tokens_guideline: 500
# /lint предупреждает если source страница > 600 токенов
```

### 6.7 Когда внедрять каждую оптимизацию

| Оптимизация | Когда нужна | Что делать прямо сейчас |
|---|---|---|
| Lazy loading rule | Сразу | Добавить текстовое правило в AGENTS.md |
| Drift cache | 10+ source страниц | Написать скрипт + hook |
| index.min.json | 30+ skills | Добавить в /process pipeline |
| Батчинг skill-sync | Регулярное использование | При первых жалобах на время |
| Source size limit | Сразу | Добавить в _schema.md как guideline |

---

## 7. Roadmap

### Сейчас — Stability foundations (Недели 1–2)

Разблокированы немедленно, дают safety/reliability:

```
D3  requirements.txt + pyproject.toml   [P0, S] — разблокирует всё остальное
Q4  GitHub Actions CI                   [P0, S] — требует D3
Q3  Git integration tests               [P0, M] — разблокирует уверенность для Q1
C1  Auto-reindex в process/harvest      [P0, S]
C2  Pre-push dual-remote hook           [P0, S]
```

### Недели 3–4 — DX и discoverability

```
D1  QUICKSTART.md                       [P1, S]
I3  Web Clipper guide                   [P1, S]
I4  Obsidian setup docs                 [P1, S]
D4  Bootstrap status command            [P1, M] — основа для agent automation
D2  CONTRIBUTING.md                     [P2, S]
I1  Gemini CLI stub                     [P2, S]
I2  VS Code Copilot stub                [P2, S]
E1  GitHub topics + badges              [P2, S]
```

### Месяц 2 — Skills system foundation

```
skills-core проект — создать + 1 skill как пример   [P1, S]
Ретроспективная разметка существующих skills         [P1, M]
/skill-port команда                                  [P1, M]
Lazy loading rule в AGENTS.md                        [P1, S]  ← токены
```

### Месяц 2–3 — Code quality (после Q3)

```
Q2  Type annotation pass                [P1, M]
Q1  Package refactor                    [P1, L] — только после Q3 зелёные
```

### Месяц 3 — Governance automation + Source layer

```
C4  Quarantine expiry CI                [P1, M]
C3  Reindex idempotency                 [P1, S]
/source-check команда                   [P1, M]
Drift cache скрипт + hook               [P1, S]  ← токены, при 10+ sources
```

### Месяц 4+ — Ecosystem + Advanced skills

```
E2  Public demo project                 [P2, M]
/source-analogies                       [P2, M] — при 20+ sources
index.min.json                          [P2, S] — при 30+ skills
Батчинг /skill-sync                     [P2, S]
```

### Граф зависимостей

```
D3 (packaging)
  └─→ Q4 (CI)
        └─→ Q3 (git integration tests)
              └─→ Q1 (package refactor)
                    └─→ Q2 (typing)

C2 (pre-push hook)  ──── независимо
C1 (auto-reindex)   ──── независимо

D4 (bootstrap status command)
  └─→ Agent bootstrap checklist
        └─→ A1 drift detection (автоматизация)
              └─→ Drift cache (оптимизация токенов)

skills-core (новый проект)
  └─→ /skill-port
        └─→ /source-check
              └─→ /source-analogies
```

---

## 8. Сводная таблица предложений

| ID | Предложение | Приоритет | Сложность | Категория |
|---|---|---|---|---|
| D3 | requirements.txt + pyproject.toml | P0 | S | DX |
| Q4 | GitHub Actions CI | P0 | S | Code |
| Q3 | Git integration tests | P0 | M | Code |
| C1 | Auto-reindex в /process и /harvest | P0 | S | Core |
| C2 | Pre-push dual-remote hook | P0 | S | Core |
| D1 | QUICKSTART.md | P1 | S | DX |
| D4 | Bootstrap status command | P1 | M | DX |
| I3 | Web Clipper guide | P1 | S | Integration |
| I4 | Obsidian setup docs + config | P1 | S | Integration |
| C4 | Quarantine expiry CI | P1 | M | Core |
| C3 | Reindex idempotency | P1 | S | Core |
| Q2 | Type annotation pass | P1 | M | Code |
| Q1 | Package refactor (reefiki.py split) | P1 | L | Code |
| SK1 | skills-core проект + двухслойная модель | P1 | M | Skills |
| SK2 | /skill-port команда | P1 | M | Skills |
| SK3 | Source страницы с трассировкой | P1 | M | Skills |
| SK4 | /source-check команда | P1 | M | Skills |
| AU1 | A1–A5: полная автоматизация (теги, drift, gaps) | P1 | M | Automation |
| AU2 | B1–B2: частичная автоматизация (sync, архив) | P2 | M | Automation |
| TK1 | Lazy loading rule в AGENTS.md | P1 | S | Tokens |
| TK2 | Drift cache скрипт + hook | P1 | S | Tokens |
| TK3 | index.min.json | P2 | S | Tokens |
| TK4 | Батчинг /skill-sync | P2 | S | Tokens |
| TK5 | Source size limit в _schema.md | P1 | S | Tokens |
| SK5 | /source-analogies | P2 | M | Skills |
| D2 | CONTRIBUTING.md | P2 | S | DX |
| I1 | Gemini CLI stub | P2 | S | Integration |
| I2 | VS Code Copilot stub | P2 | S | Integration |
| E1 | GitHub topics + badges | P2 | S | Ecosystem |
| E2 | Public demo project | P2 | M | Ecosystem |

---

*Аудит подготовлен на основе публично доступных документов репозитория REEFIKI.
Наблюдения по коду (reefiki.py, tests/) основаны на метаданных (LOC, имена модулей)
и архитектурном описании — прямой доступ к скриптам в публичном снапшоте отсутствовал.*
