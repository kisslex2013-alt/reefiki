# REEFIKI — Полный аудит репозитория и план развития

> Дата аудита: 1 июня 2026. Снимок коммита `kisslex2013-alt/reefiki` (main).
> Текущая фаза: **Phase 0i** (базовый слой memory governance готов).
> Живой baseline: `projects/reefiki` — 13/13 golden-запросов проходят, `misses: []`.

---

## Содержание

1. [Резюме](#1-резюме)
2. [Архитектура и качество кода](#2-архитектура-и-качество-кода)
3. [Governance и целостность данных](#3-governance-и-целостность-данных)
4. [Тестовое покрытие](#4-тестовое-покрытие)
5. [Мульти-агент и покрытие IDE](#5-мульти-агент-и-покрытие-ide)
6. [Developer Experience и онбординг](#6-developer-experience-и-онбординг)
7. [Автоматизация и UX — что автоматизировать](#7-автоматизация-и-ux--что-автоматизировать)
8. [Позиционирование](#8-позиционирование)
9. [Предложения (P0→P3)](#9-предложения)
10. [Roadmap зависимостей](#10-roadmap-зависимостей)

---

## 1. Резюме

REEFIKI — хорошо продуманный и философски последовательный персональный knowledge control plane. Ключевая идея — дистилляция вместо архивирования, `useful_when` как обязательное условие сохранения, маршрутизация по слоям memoir/wiki/graphify — разумна и реализована грамотно. Работа по Phase 0 (integrity gate) выполнена тщательно. Проект находится в **здоровой переломной точке**: фундамент прочный, golden-тесты проходят, слой governance на месте.

Основные риски при дальнейшем росте:

1. **Монолитный код** — 3 950 строк и 124 функции в одном файле; сопровождать и тестировать будет всё сложнее.
2. **Пробелы в покрытии агентов** — пять минимальных стабов покрывают меньше половины активно используемых AI-инструментов; несколько крупных инструментов отсутствуют полностью.
3. **Документационная масса** — более 60 КБ документов создают реальный онбординг-барьер.
4. **Пробелы в автоматизации** — многие операции «запусти X вручную» можно превратить в pre-commit хуки, session-starter или cron-задачи.
5. **Нет CI** — golden baseline и frontmatter-валидатор настолько хороши, насколько хорош был последний ручной запуск.

---

## 2. Архитектура и качество кода

### 2.1 `scripts/reefiki.py` — монолит

**Измеренные показатели:**
- 3 950 строк, 124 функции верхнего уровня `def`, ноль классов в production-коде
- 218 вызовов `print()` (правильный паттерн для CLI: stdout — это API)
- 2 аннотации `type: ignore`, 0 `noqa`, 0 `assert` в production-путях
- 0 хардкоженных ссылок на облачные API — genuinely offline-first ✅
- 7 вызовов `subprocess` (git-операции) — все необходимы, инъекций shell не найдено
- Ни одного `TODO/FIXME/HACK` в кодовой базе

**Нужен ли рефакторинг?** Да — но не срочно. При 3 950 строках файл выходит за пределы комфортного одного файла, но внутренняя структура дисциплинированная: функции чистые (без глобального состояния), именование единообразное, мёртвого кода нет. Риск — будущий рост, а не текущие баги.

**Рекомендуемое разделение (целевая структура модулей):**

```
scripts/
  reefiki.py                # тонкий CLI-входной файл: main() + разбор аргументов
  reefiki_core/
    __init__.py
    index.py                # build_index, search, search_existing, FTS5-запросы
    frontmatter.py          # parse_frontmatter, as_text, parse_value (перенести из validate_frontmatter.py)
    graph.py                # build_backlink_index, extract_wiki_links, extract_heading_chunks
    dedup.py                # dedup_check, privacy_scan, file_sha256
    git_ops.py              # harvest_commit_payload, guard_staged, push_public_snapshot, publish_task_payload
    promotion.py            # promotion_dry_run, write_promotion_draft, apply_promotion_draft, review_queue_scan
    memory.py               # memory_route, memory_pack, memory_preflight, memory_explain, memory_status
    project.py              # project_root, repo_root, list_projects, find_project, iter_pages
```

Граница разделения чистая: у каждого предлагаемого модуля единая ответственность и минимальная связанность. `git_ops.py` и `memory.py` — наиболее сложные и наиболее ценные для изоляции.

**Качество аннотаций типов:** хорошее. Функции используют `Path`, `dict[str, object]`, `list[str]`, `str | None` единообразно. Два `type: ignore` — очень мало. Возвращаемые типы `dict[str, object]` во многих функциях можно сузить с помощью `TypedDict` — полезно, но не срочно.

**Обработка ошибок:** голых `raise Exception()` нет. Ошибки передаются через exit-коды и структурированный JSON. Правильный паттерн для CLI-инструмента, потребляемого агентами.

### 2.2 SQLite FTS5 — производительность и масштабируемость

**Текущий подход:** FTS5-индекс в `.reefiki/index.sqlite`, markdown — источник истины, индекс — read-through кэш. Верная архитектура для текущего масштаба.

**Потолок масштабирования:** FTS5 уверенно работает с ~1 млн записей. При Phase 0i (~100–150 страниц) никакого давления нет. Потолок становится актуальным примерно при 10 000 страниц — это далеко в Phase 2+.

**Выявленный пробел:** `build_index` (строка 257) каждый раз полностью пересоздаёт индекс. При текущем масштабе это быстро, но при 1 000+ страниц полная перестройка станет заметной (~100 мс+). **Инкрементальное индексирование** (индексировать только изменённые файлы через `mtime` или git diff) нужно добавить до Phase 1.

### 2.3 `scripts/reefiki_memory/__init__.py`

**Хорошо структурирован.** Везде `@dataclass(frozen=True)`, `StrEnum` для capabilities, чистая сериализация через `to_dict()`. Самая хорошо факторизованная часть кодовой базы.

**Наблюдение:** `PolicySafetyLayer.SECRET_PATTERNS` содержит три хардкоженных паттерна регулярных выражений (общий `api_key`/token/password, `tvly-dev-*`, `sk-*`). Префикс `tvly-dev-` (ключ Tavily API) очень специфичен — судя по всему, пришёл из реального инцидента. Стоит вынести в конфигурационный файл, чтобы паттерны можно было обновлять без изменения кода.

**`build_default_registry`** регистрирует три провайдера (memoir, reefiki, graphify), но `root` у graphify определяется через `project_code_path()` в рантайме и возвращает `None`, если кодовый проект не подключён. Это обрабатывается корректно, но является молчаливым no-op для непривязанных проектов — стоит явно отражать в выводе `memory status`.

### 2.4 `scripts/validate_frontmatter.py`

Добротная реализация в 397 строк. Ключевые наблюдения:

- **`SKIP_FILENAMES`**: `{"_schema.md", "log.md", "_dashboard.md", "_domain.md"}` — правильно. Но `status.md` в списке исключений отсутствует; если у него появится frontmatter, возникнут неожиданные ошибки валидации.
- **Разделение `BODY_WARN` / `BODY_REQUIRED`** — умное решение: страницы `decision` получают неблокирующее предупреждение об отсутствующих ADR-секциях. Это не ломает существующие страницы, но мотивирует использовать правильный формат.
- **Режим `--format json`** возвращает структурированные ошибки с `code`, `line`, `column`, `expected`, `actual` — отлично для диагностики агентом и CI.
- **Пробел:** нет проверки, что поле `id` совпадает с именем файла (в `_schema.md` это правило задекларировано, но в валидаторе не реализовано).
- **Пробел:** `tags` может быть пустым списком (`tags: []`) — схема требует минимум 1 тег, но это не проверяется.

---

## 3. Governance и целостность данных

### 3.1 Frontmatter-схема — полнота

Схема спроектирована хорошо. Условие `useful_when` — лучшее единственное дизайн-решение в проекте: оно заставляет формулировать ценность до сохранения.

**Непокрытые edge-кейсы:**

| Пробел | Влияние | Предложение |
|---|---|---|
| `id` не валидируется относительно имени файла | Молчаливое расхождение id/filename | Добавить проверку `FILENAME_ID_MISMATCH` в валидатор |
| Список `tags` может быть пустым | Проходит валидацию | Добавить проверку на непустой список |
| Формат `date_added` не валидируется (только наличие) | Будущие даты, неверный формат | Добавить проверку по ISO regex |
| Поле `verified` для `skill` принимает любую строку | Несогласованные данные | Добавить проверку date-or-null |
| Уникальность `id` между страницами не проверяется | Возможны дублирующиеся ID | Добавить глобальную проверку уникальности в `/lint` |

### 3.2 Разрешение конфликтов (карантин 30 дней)

Механизм карантина концептуально верный. Наблюдения:

- **Нет автоматического закрытия истёкшего карантина.** Когда `quarantine_until` истекает, элемент появляется в выводе `/status` как просроченный — но действие не форсируется. Это сделано намеренно (ручной просмотр), однако создаёт растущий бэклог из «просроченных» элементов, которые пользователи игнорируют. Стоит добавить счётчик предупреждений в `/status` и отдельную команду `/resolve-quarantine`.
- **30 дней — много** для быстро меняющихся технических знаний (например, решения по версиям фреймворков). Стоит сделать длительность карантина настраиваемой в `_domain.md` (по умолчанию 30, диапазон 7–90).

### 3.3 Dual-remote publishing — оценка безопасности

**Текущий механизм:** `push-public.ps1` + `publish_task_payload()` + `public-snapshot.private-projects.txt`. Гейт `publish-task --dry-run` перед любым пушем — правильная защита.

**Выявленные риски:**

1. **`public-snapshot.private-projects.txt` — плоский список имён приватных проектов.** Если файл неверно настроен (имя отсутствует или опечатка), приватный wiki-контент утечёт в публичный remote без ошибки. Митигация: добавить хэш/чексумму папок приватных проектов для обнаружения расхождения config/реальность перед пушем.
2. **`classify_publish_diff`** (строка 1329) классифицирует пути как `private-only` / `public-safe` / `mixed` на основе сопоставления путей. Если содержимое приватного проекта появится в общем файле (например, имя проекта упоминается в `AGENTS.md`), это не будет поймано. Низкий риск при текущей структуре, но стоит задокументировать.
3. **PowerShell-скрипт `push-public.ps1`** работает только на Windows. Пользователи Linux/macOS вынуждены использовать Python CLI, в котором есть safety gate, но асимметрия создаёт DX-проблему.
4. **Очистка worktree — ручная с подтверждением.** Если команда cleanup пропущена после неудачной публикации, orphaned worktrees накапливаются. `cleanup-worktree` должна быть идемпотентной и запускаться автоматически при следующем `publish-task`.

### 3.4 Предотвращение дрейфа шаблона

Phase 0e закрыла наиболее очевидные векторы дрейфа. Текущий механизм: команда `/sync-template` + охват `_dashboard.md`. Это ручная, выполняемая агентом операция.

**Пробел:** нет машиночитаемого поля «версия шаблона». Если `_template/AGENTS.md` обновился, но `/sync-template` не запускался, проекты молча расходятся. Предложение: добавить `template_version: "0i"` в frontmatter `_domain.md` и валидировать в `/lint`, что версии всех проектов совпадают с шаблоном.

---

## 4. Тестовое покрытие

### 4.1 Что есть

| Файл | Размер | Фреймворк | Тестов | Область покрытия |
|---|---|---|---|---|
| `test_reefiki_memory_contracts.py` | 69,5 КБ | unittest | ~60 методов | Контракты memory layer: registry, route, preflight, status, lookup, promote, golden, pack, diff, publish, promotion-inbox |
| `test_reefiki_memory_governance.py` | 16,7 КБ | unittest | ~15 методов | Governance: review queues, backlinks, orphan detection, conflict review, link health |
| `test_validate_frontmatter.py` | 2,1 КБ | unittest | ~8 методов | Базовая валидация frontmatter |
| `test_reefiki_dedup.py` | 4,9 КБ | unittest | ~10 методов | URL-дедупликация, content hash, inbox dedup |
| `test_public_snapshot_guard.py` | 0,8 КБ | unittest | ~3 метода | Guard-staged payload, фильтрация приватных проектов |

**Качество покрытия:** `test_reefiki_memory_contracts.py` объёмом 69,5 КБ — самый большой файл во всём репозитории, больше самого `reefiki.py`. Покрытие исчерпывающее, но файл стал проблемой для сопровождения: одна упавшая проверка требует прокрутки огромного файла.

### 4.2 Чего не хватает

| Непокрытая область | Риск | Приоритет |
|---|---|---|
| End-to-end CLI-тесты для `/save`, `/process`, `/harvest` | Высокий — пользовательские command-пути | P1 |
| Корректность FTS5-поиска (запрос возвращает ожидаемые страницы) | Средний — golden-тесты покрывают косвенно | P2 |
| `promote-dry-run --apply-draft` (единственный durable write путь) | Высокий — непротестированная мутация | P0 |
| `push_public_snapshot` с реальным git-фикстурой | Высокий — security-sensitive | P1 |
| Обработка Windows-путей (junction, `_wiki/` symlink) | Средний — основная платформа пользователя | P2 |
| Пороги размера/качества `memory_pack --strict` | Средний | P2 |

### 4.3 Проблема архитектуры тестов

`test_reefiki_memory_contracts.py` импортирует `reefiki.py` через `importlib.util.spec_from_file_location`. Это привязывает тесты к монолитной структуре файла. После разделения на модули (§2.1) тесты должны импортировать из `reefiki_core.*` напрямую.

**Рекомендация:** разбить `test_reefiki_memory_contracts.py` на файлы, зеркалирующие структуру `reefiki_core/`. Цель: ни один тестовый файл не превышает 500 строк.

---

## 5. Мульти-агент и покрытие IDE

### 5.1 Существующие стабы — оценка качества

| Файл | Агент | Качество | Проблемы |
|---|---|---|---|
| `CLAUDE.md` | Claude Code | ✅ Хорошо | Есть Claude-специфичные пути slash-команд, sequence старта сессии |
| `.clinerules` | Cline / Roo Cline | ⚠️ Минимально | Перечислены операции, нет Cline-специфичных паттернов (auto-approve, tool confirmation) |
| `.cursorrules` | Cursor | ⚠️ Минимально | Только ссылка + 2-строчное описание. Нет guidance по Cursor Composer/Agent mode |
| `.codex/instructions.md` | Codex CLI | ⚠️ Минимально | Идентичная структура `.cursorrules`. Нет Codex-специфичных флагов |
| `.windsurf/rules/main.md` | Cascade/Windsurf | ⚠️ Минимально | Идентичная структура `.cursorrules`. Нет Cascade-специфичных workflows (flows, rules) |
| `.serena/project.yml` | Serena | ❌ Отсутствует | Упоминается в `AGENTS.md`, но возвращает 404 — файла нет в репозитории |

**Дрейф шаблона в стабах:** `.cursorrules`, `.codex/instructions.md` и `.windsurf/rules/main.md` — копии друг друга. Если структура `AGENTS.md` изменится, стабы не обновятся автоматически — они просто говорят «читай AGENTS.md», что правильно как fallback, но vendor-специфичные подсказки остаются устаревшими.

### 5.2 Пробелы в покрытии агентов

#### Tier 1 — Высокоприоритетные дополнения (широко используются в 2026)

**GitHub Copilot — `.github/copilot-instructions.md`**

GitHub Copilot (Chat, Workspace, Agent mode) читает `.github/copilot-instructions.md` как файл с пользовательскими инструкциями. Сейчас отсутствует. Это наибольший пробел с учётом доли рынка Copilot.

```markdown
<!-- .github/copilot-instructions.md -->
# GitHub Copilot — REEFIKI

This is a multi-project personal knowledge distillation wiki.
Full contract: **AGENTS.md** (repository root).

When working inside `projects/<name>/`:
- Read `projects/<name>/AGENTS.md` — full operation contract.
- Operations: save, process, query, harvest, status, lint, resolve, reindex, help.
- Operation specs live in `.claude/commands/<op>.md` (folder name is historical; content is vendor-neutral).

Key rules:
- Never write to `raw/` (immutable archive).
- Never rewrite `wiki/log.md` entries — append only.
- `useful_when` is mandatory on every wiki page. If you can't articulate it, reject to `seen/`.
```

Сложность: **S**

---

**Aider — `.aider.conf.yml` + `CONVENTIONS.md`**

Aider поддерживает `.aider.conf.yml` для конфигурации CLI и файл соглашений (обычно `CONVENTIONS.md`, указываемый через `--read`). У Aider нет slash-команд; операции запускаются через естественный язык.

```yaml
# .aider.conf.yml
read:
  - AGENTS.md
model: claude-3-5-sonnet-20241022
```

```markdown
# CONVENTIONS.md — REEFIKI (Aider)
Full contract: AGENTS.md

Natural language triggers:
- "save this link" → /save (put in inbox/, no analysis)
- "process inbox" → /process
- "query wiki about X" → /query
- "harvest session" → /harvest at session end
- "check wiki health" → /lint
```

Сложность: **S**

---

**Gemini CLI — `GEMINI.md`**

Google Gemini CLI (2025) читает `GEMINI.md` в корне проекта — аналог `CLAUDE.md`.

```markdown
# GEMINI.md — REEFIKI
Full contract: AGENTS.md (repository root). Read it first.
Project-level work: projects/<name>/AGENTS.md.
```

Сложность: **S** (буквально скопировать структуру CLAUDE.md)

---

**Continue.dev — `.continue/config.json`**

```json
{
  "customCommands": [
    {
      "name": "reefiki-query",
      "description": "Query REEFIKI wiki",
      "prompt": "Using only knowledge in the wiki/ directory, answer: {input}"
    }
  ],
  "systemMessage": "You are working inside a REEFIKI knowledge control plane. Read AGENTS.md before any operation."
}
```

Сложность: **S**

---

#### Tier 2 — Средний приоритет

| Агент | Конфигурационный файл | Примечания |
|---|---|---|
| **Zed AI** | `.zed/settings.json` (`assistant.default_context`) | System prompt injection; ссылка на AGENTS.md |
| **Amazon Q Developer** | `.amazonq/` или `.aws/amazonq/` | Формат ещё развивается |
| **Sourcegraph Cody** | `cody.json` / настройки VS Code | Context fetcher; можно указать на AGENTS.md |
| **JetBrains AI Assistant** | Custom prompt в настройках IDE | Нет file-based конфига; задокументировать обходной путь |

#### Tier 3 — Community contribution или только документация

| Агент | Примечания |
|---|---|
| **OpenHands / SWE-agent** | Автономные агенты; читают `AGENTS.md` через shell. Задокументировать в README. |
| **Локальные модели (Ollama, LM Studio)** | Нет file-based маршрутизации; пользователь вручную вставляет AGENTS.md в контекст. |
| **OpenAI Codex (cloud)** | Веб-интерфейс, нет file-конфига. Документировать: «вставить AGENTS.md как системный контекст». |

### 5.3 Slash-команды — совместимость между агентами

Slash-команды (`.claude/commands/*.md`) нативно поддерживаются только в Claude Code (и частично в Cline). Для остальных агентов:

| Механизм | Агенты | Рекомендация |
|---|---|---|
| Нативные slash-команды | Claude Code, Cline | Уже работает |
| Tool/function calls | Codex CLI (`--functions`) | Определить операции как function-схемы |
| Естественный язык | Все агенты | Всегда указывать NL-триггеры рядом со slash-командами |
| MCP сервер (будущее) | Любой MCP-совместимый агент | По задаче T-40; раскрывает `/save`, `/query` и др. как MCP tools |

**Текущий пробел:** файлы `.claude/commands/` — канонические спецификации операций, но агенты без slash-команд должны читать их как обычный markdown (могут, но это трение). Добавление секции `## Триггеры на естественном языке` в каждый файл спецификации ничего не стоит и улучшает кросс-агентную юзабилити.

### 5.4 Контекстные окна

| Уровень модели | Контекст | Влияние на `memory pack` |
|---|---|---|
| Маленькая локальная (7B–13B) | 4K–8K токенов | Лимит `pack --strict` ≤ 4K; тестировать с флагом `--limit` |
| Средний уровень (GPT-4o, Gemini Pro) | 128K токенов | Текущие значения по умолчанию подходят |
| Большие (Claude 3.5+, Gemini 1.5/2.0) | 200K–1M токенов | Можно упаковать всю вики; но quality gate важнее размера |

**Рекомендация:** добавить `--context-budget <tokens>` в `memory pack`, чтобы агенты могли объявить размер своего окна и пакет учитывал это.

### 5.5 Независимость от провайдера

**Подтверждено offline-first:** ноль хардкоженных ссылок на облачные API в `reefiki.py` или `reefiki_memory/__init__.py`. Весь memory layer (FTS5-поиск, валидация frontmatter, promotion, review queues) работает без сетевого подключения. ✅

**Одно исключение:** mobile capture в Phase 0c использует Telegram бот + Pipedream + GitHub Actions — облачные зависимости, но они изолированы в захвате `inbox/`, не в memory layer. ✅

**Качество следования инструкциям локальных моделей:** контракт AGENTS.md явный и хорошо структурированный, но строгое соблюдение зависит от качества instruction-following модели. 7B–13B модели следуют ~60–70% сложного контракта. Митигация: гейт `memory preflight` — это safety net, не требующий соблюдения контракта моделью — CLI-проверка. Это правильная архитектура. ✅

---

## 6. Developer Experience и онбординг

### 6.1 Объём документации

| Файл | Размер | Назначение |
|---|---|---|
| `COMMANDS.md` | 21,3 КБ | Пользовательский справочник команд |
| `AGENTS.md` | 15,7 КБ | Корневой контракт агента |
| `ROADMAP.md` | 22,7 КБ | Фазовое планирование |
| `TASKS.md` | 23,6 КБ | Отслеживание спринтов |
| `projects/_template/AGENTS.md` | 9,3 КБ | Контракт агента уровня проекта |

**Итого:** ~93 КБ документации для полного понимания системы.

**Слишком ли это много?** Для человека при онбординге — да. Для агента, читающего нужное подмножество — нет: AGENTS.md структурирован для последовательной загрузки («читай это сначала → затем AGENTS.md проекта → затем спецификации команд»). Проблема — опыт онбординга для человека через README.

**Фильтр из 4 вопросов** (упоминается в `process.md` и template AGENTS.md как «4 внутренних вопроса») нигде явно не перечислен ни в одном пользовательском файле. Судя по контексту, это:
1. Это действительно новое по сравнению с тем, что уже в вики?
2. Когда это снова пригодится? (`useful_when`)
3. Какой тип у этого знания? (source/concept/decision/skill/synthesis)
4. Конфликтует ли это с существующей страницей?

Эти вопросы — интеллектуальное ядро системы, и они должны быть явно сформулированы где-то на видном месте.

### 6.2 Путь онбординга (Clone → первый `/save`)

Ожидаемое время для нетехнического пользователя: **45–90 минут**
Ожидаемое время для разработчика: **15–30 минут**

Узкие места:
1. Понимание, какую папку открывать (`REEFIKI/` vs `projects/<name>/`) — различие двух режимов не очевидно
2. Установка pre-commit хука (`pip install pre-commit; pre-commit install`) — не упомянута в быстром старте README
3. `scripts/reefiki.py` требует Python в PATH — нет упоминания о требуемой версии (из type hints — Python 3.10+)
4. Создание Windows junction для `/connect` — требует прав администратора или режима разработчика

**Отсутствует:** `QUICKSTART.md` (путь за 5 минут) отдельно от полного README.

### 6.3 Проблема имени папки `.claude/commands/`

Спецификации команд живут в `.claude/commands/` — соглашение Claude Code. В кодовой базе в нескольких местах корректно написано «имя папки историческое, содержимое vendor-neutral». Но новые пользователи (и агенты, незнакомые с этой историей) будут считать эти файлы Claude-only.

Варианты решения:
- Добавить `README.md` в `.claude/commands/`, объясняющий vendor-neutral природу
- Или переименовать в `.reefiki/commands/` и сделать симлинк `.claude/commands/` → `.reefiki/commands/`

---

## 7. Автоматизация и UX — что автоматизировать

### 7.1 Кандидаты на pipeline (ручные последовательности → одна команда)

| Текущая ручная последовательность | Предлагаемая команда | Уровень | Триггер | Риск полной автоматизации |
|---|---|---|---|---|
| `/process` → reindex → build_index → validate | `/process` уже триггерит reindex; но rebuild после batch — ручной | **Полная авто** | Post-`/process` хук | Нет |
| `memory pack --strict` → `memory golden` → `memory status` | `memory handoff` | **Полная авто** | «продолжи сессию» / «новый тред» | Нет — только чтение |
| `validate_frontmatter.py` → `review-queues` → `backlinks --write` | `reefiki lint-full` | **Полная авто** | Pre-push хук, еженедельный cron | Нет — только сканирование |
| `publish-task --dry-run` → просмотр → `push-public` | Уже гейтовано; UX-проблема — два шага | **Полуавто** | Команда «push» | Публикация: обязателен просмотр dry-run |
| `promote-dry-run --write-draft` → просмотр → `--apply-draft --yes` | Правильно как есть (явное подтверждение) | **Полуавто** | Агент предлагает, пользователь подтверждает | Durable write: явное подтверждение — верно |

### 7.2 Bootstrap-чеклист сессии (что агент должен делать автоматически)

Сейчас частично реализовано в `projects/<name>/AGENTS.md` в разделе «Авто-триггеры». Но:

- ✅ Проверка inbox  
- ✅ Проверка истёкшего карантина
- ✅ Проверка интервала `/lint`
- ✅ Проверка stale-страниц
- ❌ **Отсутствует:** `memory status --summary` для отображения открытых элементов promotion inbox и здоровья провайдеров
- ❌ **Отсутствует:** Проверка, старше ли SQLite-индекс последнего wiki-файла (триггер перестройки)
- ❌ **Отсутствует:** Проверка, превышает ли версия `_template` версию проекта (дрейф шаблона)
- ❌ **Отсутствует:** Предупреждение о возрасте бэкапа, если последний коммит старше N дней

### 7.3 Периодические проверки (кандидаты для cron/CI)

| Проверка | Частота | Уровень | Риск полной автоматизации |
|---|---|---|---|
| `validate_frontmatter.py` для всех wiki-файлов | При каждом git commit | **Полная авто** (pre-commit — уже сделано ✅) | Нет |
| `reefiki.py review-queues` lint-сканирование | Еженедельно | **Полная авто** (cron + write report) | Низкий — только чтение |
| `memory golden` baseline | Еженедельно или после batch `/process` | **Полная авто** (CI job) | Нет — только чтение; алерт на miss |
| `reefiki.py backlinks --write` | После каждого `/harvest` или `/process` | **Полная авто** (post-хук) | Нет — generated артефакт |
| `reefiki.py status --format json` | По требованию (CI health check) | **Полная авто** | Нет |
| Проверка истёкшего карантина | Еженедельно | **Полуавто** (только отчёт, без auto-promote) | Auto-promotion карантинированного контента — рискованно |

### 7.4 Что пользователи забывают делать

На основе анализа структуры команд:

1. **`reindex` после пакетных правок в Obsidian** — правки в Obsidian обходят CLI; FTS5-индекс устаревает. Решение: добавить file watcher или сделать так, чтобы `search` обнаруживал устаревший индекс через сравнение mtime.
2. **`harvest` перед закрытием IDE** — нет механизма напоминания об окончании сессии. Решение: задокументировать как авто-триггер в AGENTS.md (частично уже есть) и добавить в bootstrap-чеклист («последний harvest был N шагов назад»).
3. **`backlinks --write` после `/process`** — кэш backlinks — generated артефакт; устаревает при добавлении новых страниц. Решение: добавить в exit hook `/process`.
4. **`memory golden` после большого batch** — молчаливый дрейф golden baseline. Решение: CI job или post-`/harvest` хук.
5. **`sync-template` после обновлений REEFIKI** — проекты молча расходятся с шаблоном. Решение: поле версии шаблона в `_domain.md` + lint-проверка.

### 7.5 Возможности полной безопасной автоматизации

| Операция | Реализация |
|---|---|
| CI: `validate_frontmatter.py` на PR | GitHub Actions `.github/workflows/ci.yml` — запуск при push/PR в `projects/*/wiki/**` |
| CI: `memory golden` baseline | Тот же workflow — запуск и сравнение с сохранённым baseline; fail при регрессии |
| Post-commit хук: `backlinks --write` | `.git/hooks/post-commit` — быстрый, идемпотентный |
| Cron: еженедельный `review-queues --write-report` | GitHub Actions scheduled workflow — создаёт report-артефакт без durable-изменений |
| mtime-based rebuild индекса | В `search()` — сравнивать `max(wiki_file.mtime)` с `index.sqlite mtime`; перестраивать если устарел |

---

## 8. Позиционирование

### 8.1 Уникальное value proposition

Наиболее чёткий дифференциатор REEFIKI: **локальный governance layer, работающий одинаково в любом LLM-агенте или IDE, с явной маршрутизацией знаний, карантином и типизированной таксономией** — без сервера, подписки или API-ключа.

Ближайшие аналоги и отличия REEFIKI:

| Аналог | Что делают | Отличие REEFIKI |
|---|---|---|
| **Mem0 / Zep** | Облачный memory-сервис; хранит и извлекает факты | Локальный, markdown-нативный, agent-agnostic; не нужен API |
| **Karpathy LLM Wiki** | Простой markdown wiki gist | REEFIKI добавляет governance (карантин, типы, валидация, FTS5) |
| **Obsidian + AI плагин** | Graph knowledge base с AI | REEFIKI использует Obsidian только как viewer; control plane — CLI-нативный |
| **Honcho** | Персонализация на уровне пользователя для агентов | REEFIKI — по проекту/домену, а не по профилю пользователя |
| **LangChain Memory** | Память сессии внутри chain | REEFIKI — durable между сессиями, не внутри chain |

**Что усиливает проект:**
- Условие `useful_when` интеллектуально честно и создаёт реальное трение против накопительства знаний
- Слоёная архитектура (memoir / REEFIKI / graphify) чётко соответствует когнитивным уровням памяти
- Типизированная таксономия страниц (`source/entity/concept/synthesis/decision/skill`) даёт структуру без переусложнения
- Local-first + markdown = работает офлайн, инспектируемо, Git-backed, без vendor lock-in

**Что ослабляет проект:**
- Высокая стоимость онбординга (93 КБ документов до первого `/save`)
- Windows-ориентированные допущения (junction симлинки, PowerShell-скрипты) без эквивалентов для Linux/macOS в ряде операций
- UX «агент делает сам» — аспирационный; без session-start хуков в IDE пользователи должны помнить о запуске операций
- Нет CI — golden baseline доказывает качество только на момент последнего ручного запуска

### 8.2 Риск open-source adoption

Проект сейчас структурирован для персонального использования опытным техническим пользователем. Для принятия сообществом:
- Основной README на русском (EN и ZH версии существуют, но менее полные)
- Нет `CONTRIBUTING.md`
- Нет `QUICKSTART.md` (15-минутный путь)
- Стабы агентов покрывают ~40% активно используемых инструментов

---

## 9. Предложения

### Ядро (P0)

---

**CORE-01 — CI pipeline: validate_frontmatter + golden baseline**
- **Проблема:** Pre-commit хук защищает коммитируемые файлы, но нет CI-задачи для отлова регрессий по всем проектам, особенно после обновлений шаблона или пакетных правок в Obsidian. Golden baseline (`13/13`) существует, но проверяется только вручную.
- **Решение:**
```yaml
# .github/workflows/ci.yml
name: REEFIKI CI
on:
  push:
    paths: ['projects/*/wiki/**', 'scripts/**', 'tests/**']
  pull_request:
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install pre-commit
      - run: python scripts/validate_frontmatter.py $(find projects -path "*/wiki/*.md" -not -name "_*" -not -name "log.md")
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: python -m pytest tests/ -v
  golden:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: python scripts/reefiki.py memory golden --project reefiki --format json | python -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if not d.get('misses') else 1)"
```
- **Ценность:** Регрессии отлавливаются автоматически; новые контрибьюторы могут доверять baseline.
- **Сложность:** S (1–2 дня)
- **Приоритет:** P0

---

**CORE-02 — Исправить отсутствующий `.serena/project.yml`**
- **Проблема:** `AGENTS.md` перечисляет `.serena/project.yml` как файл-стаб, но файл возвращает 404 — его нет в репозитории. Это нарушенное обещание в agent-agnostic заявлении.
- **Решение:** Создать файл:
```yaml
# .serena/project.yml
initial_prompt: |
  Read AGENTS.md in the repository root. It contains the full operating contract for REEFIKI.
  When working inside a project folder (projects/<name>/), read projects/<name>/AGENTS.md instead.
  Slash commands are defined in .claude/commands/ (vendor-neutral despite the folder name).
```
- **Ценность:** Пользователи Serena получают работающую интеграцию.
- **Сложность:** S (< 1 часа)
- **Приоритет:** P0

---

**CORE-03 — Добавить проверку `id`/filename в валидатор**
- **Проблема:** `_schema.md` гласит «`id` == имя файла без `.md`», но `validate_frontmatter.py` это не проверяет. Файл `wiki/decisions/use-sqlite.md` с `id: use-postgres` проходит валидацию молча.
- **Решение:**
```python
# в validate_file_report()
if "id" in fm and fm["id"] != path.stem:
    errors.append(error(
        path, "ID_FILENAME_MISMATCH",
        f"id field '{fm['id']}' does not match filename '{path.stem}'",
        expected=path.stem, actual=fm["id"]
    ))
```
- **Ценность:** Предотвращает битые wiki-ссылки (`[[slug]]` зависят от `id == filename`).
- **Сложность:** S
- **Приоритет:** P0

---

**CORE-06 — Тестовое покрытие `--apply-draft`**
- **Проблема:** `promote-dry-run --apply-draft <path> --yes` — единственный durable write путь в `reefiki.py` вне slash-команд. Тестового покрытия нет (подтверждено — в `test_reefiki_memory_contracts.py` нет теста для `apply_promotion_draft`).
- **Решение:** Добавить интеграционный тест с временной фикстурой проекта.
- **Ценность:** Предотвращает молчаливые регрессии в единственном durable write пути.
- **Сложность:** M
- **Приоритет:** P0 (security-adjacent)

---

### Ядро (P1)

---

**CORE-04 — Инкрементальная перестройка FTS5 индекса (mtime-based)**
- **Проблема:** `build_index()` полностью пересоздаёт индекс при каждом вызове. При 100 страницах это ~20 мс. При 1 000+ страниц (Phase 1) становится заметным.
- **Решение:** Сравнивать `max(page.stat().st_mtime)` по wiki-файлам с mtime `index.sqlite`. Перестраивать только если вики новее.
```python
def build_index(project: Path) -> int:
    db = db_path(project)
    pages = iter_pages(project)
    if db.exists():
        db_mtime = db.stat().st_mtime
        if all(p.stat().st_mtime <= db_mtime for p in pages):
            return 0  # индекс актуален
    # ... существующая логика перестройки
```
- **Ценность:** `/query` и `search` становятся практически мгновенными после первой сборки.
- **Сложность:** M
- **Приоритет:** P1

---

**CORE-05 — Составная команда `reefiki lint-full`**
- **Проблема:** Полная проверка здоровья вики требует четырёх отдельных команд: `validate_frontmatter.py`, `review-queues`, `backlinks --write`, `memory golden`. Пользователи запускают их по очереди вручную; часто запускается только одна.
- **Решение:** Добавить `reefiki.py lint-full` — запускает все четыре последовательно, возвращает 0 только если все прошли, выдаёт структурированный JSON-summary.
- **Ценность:** Одна команда для CI, pre-push хуков и проверок здоровья сессии.
- **Сложность:** M
- **Приоритет:** P1

---

### Качество кода (P1)

---

**CQ-01 — Разделить `reefiki.py` на пакет `reefiki_core/`**
- **Проблема:** 3 950 строк, 124 функции в одном файле. Логические группы существуют (FTS5-запросы, git-операции, promotion, memory layer), но перемешаны.
- **Решение:** Вынести в `scripts/reefiki_core/` по структуре из §2.1. Оставить `reefiki.py` тонкой CLI-оберткой (~600 строк).
- **Ценность:** Быстрее тесты (импорт только нужного модуля), чётче ответственность, проще добавлять контрибьюторов.
- **Сложность:** L (1–2 недели, осторожно с импортами)
- **Приоритет:** P1

---

**CQ-02 — Разбить `test_reefiki_memory_contracts.py`**
- **Проблема:** 69,5 КБ тестового файла — больше production-кода. Сообщение о падении показывает номер строки в 2 200-строчном файле.
- **Решение:** Разбить на `test_memory_route.py`, `test_memory_status.py`, `test_memory_pack.py`, `test_memory_promote.py`, `test_memory_golden.py`. Каждый < 300 строк.
- **Сложность:** M
- **Приоритет:** P1

---

**CQ-03 — Добавить `QUICKSTART.md`**
- **Проблема:** Новый пользователь сталкивается с 15,7 КБ AGENTS.md до понимания, что вводить. README содержит правильную информацию, но вперемешку с архитектурными диаграммами и философией.
- **Решение:** Создать `QUICKSTART.md` со строгим 5-минутным путём:
  1. Требования (Python 3.10+, pre-commit)
  2. `pre-commit install`
  3. Открыть `REEFIKI/` в Claude Code / Cursor / Windsurf
  4. Сказать: «Создай новый проект `test` про Python»
  5. Сказать: «Сохрани https://peps.python.org/pep-0008/»
  6. Сказать: «Разбери копилку»
  7. Сказать: «Что мы знаем про code style?»
- **Сложность:** S
- **Приоритет:** P1

---

**CQ-04 — Явно перечислить фильтр из 4 вопросов**
- **Проблема:** «4 внутренних вопроса» для `/process` упоминаются, но нигде не показываются пользователю. Новым агентам нужно реконструировать их из контекста.
- **Решение:** Добавить раздел `## Фильтр дистилляции` в `_schema.md` и `COMMANDS.md`:
  1. **Дельта:** Это действительно новое по сравнению с существующими wiki-страницами?
  2. **Сценарий:** Могу ли я написать конкретный `useful_when`? (если нет → в `seen/`)
  3. **Тип:** Какой тип знания? (source/concept/decision/skill/synthesis)
  4. **Конфликт:** Противоречит ли это существующей странице? (→ `## Conflicting claims`)
- **Сложность:** S
- **Приоритет:** P1

---

### Интеграции (P1)

---

**INT-01 — Стаб GitHub Copilot**
- **Проблема:** Нет `.github/copilot-instructions.md`. Copilot (Chat, Workspace, Agent mode) не знает о REEFIKI.
- **Решение:** Файл из §5.2 Tier 1 выше.
- **Сложность:** S
- **Приоритет:** P1

---

**INT-02 — `.aider.conf.yml` + `CONVENTIONS.md` для Aider**
- **Решение:** Файлы из §5.2 Tier 1 выше.
- **Сложность:** S
- **Приоритет:** P1

---

**INT-03 — `GEMINI.md` для Gemini CLI**
- **Решение:** Зеркалить структуру `CLAUDE.md`.
- **Сложность:** S
- **Приоритет:** P1

---

**INT-04 — `.continue/config.json` для Continue.dev**
- **Решение:** Конфиг из §5.2 Tier 1 выше.
- **Сложность:** S
- **Приоритет:** P2

---

**INT-05 — MCP сервер для memory-операций**
- **Проблема:** По мере того как MCP становится стандартом для tool calls агентов, агенты с поддержкой MCP (Claude Desktop, Cline с MCP) могут вызывать операции REEFIKI как структурированные инструменты.
- **Решение:** Минимальный MCP сервер, раскрывающий: `reefiki_save`, `reefiki_query`, `reefiki_status`, `reefiki_memory_pack`. Python MCP SDK как тонкая обёртка над существующими функциями `reefiki.py`.
- **Сложность:** L
- **Приоритет:** P2 (после стабилизации Phase 0j)

---

### Developer Experience (P2)

---

**DX-01 — Поле версии шаблона для обнаружения дрейфа**
- **Проблема:** Нет машиночитаемого подтверждения синхронизации шаблона с проектами.
- **Решение:** Добавить `template_version: "0i"` в `_template/_domain.md`. Добавить в `/lint` проверку: сравнивать `_domain.md` проекта с текущим шаблоном.
- **Сложность:** S
- **Приоритет:** P2

---

**DX-02 — `--context-budget <tokens>` для `memory pack`**
- **Проблема:** Размер pack контролируется `--limit` (количество страниц), но у агентов разный размер контекстного окна. 7B локальная модель с 4K токенами требует радикально другого pack, чем Claude с 200K.
- **Решение:** Флаг `--context-budget 4000`. Оценивать количество токенов (грубо: `len(text) / 4`) и обрезать/приоритизировать под бюджет.
- **Сложность:** M
- **Приоритет:** P2

---

**DX-03 — Составная команда `reefiki session-start`**
- **Описание:** Объединяет авто-триггеры из AGENTS.md в одну CLI-команду, которую агенты могут вызывать механически. Возвращает: inbox count, истёкший карантин, stale pages, overdue lint, открытые элементы promotion inbox, freshness индекса, совпадение версий шаблона.
- **Сложность:** M
- **Приоритет:** P2

---

**DX-04 — `scripts/push-public.sh` для Linux/macOS**
- **Проблема:** `push-public.ps1` — только PowerShell/Windows. Пользователи Linux/macOS вынуждены использовать Python CLI.
- **Решение:** Создать `scripts/push-public.sh` с идентичной логикой (bash).
- **Сложность:** S
- **Приоритет:** P2

---

### Экосистема (P3)

---

**ECO-01 — `CONTRIBUTING.md`**
- Краткий гайд для внешних контрибьюторов: философия проекта, как добавить wiki-проект, как запустить тесты, как добавить стаб нового агента.
- **Сложность:** S
- **Приоритет:** P3

---

**ECO-02 — Английский README как первичный**
- `README.md` — русскоязычный. `README.en.md` существует, но вторичен. Для open-source adoption: либо сделать EN первичным, либо явно пометить RU как основной с примечанием.
- **Сложность:** M (контент, не код)
- **Приоритет:** P3

---

**ECO-03 — Стаб `.zed/settings.json` для Zed AI**
- **Сложность:** S
- **Приоритет:** P3

---

## 10. Roadmap зависимостей

```
Phase 0i (сейчас)
     │
     ├─── CORE-02 [S, P0] Создать .serena/project.yml  ──── разблокирует: пользователей Serena
     ├─── CORE-03 [S, P0] Валидатор id/filename         ──── разблокирует: CORE-01 CI
     ├─── CORE-06 [M, P0] Тест apply-draft              ──── нет зависимостей
     │
     ├─── CORE-01 [S, P0] CI pipeline                   ──── требует: CORE-03
     │         зависит от прохождения тестов ────────────── требует: текущие тесты OK
     │
     ├─── INT-01..03 [S, P1] Стабы агентов              ──── независимы, распараллелить
     ├─── CQ-03 [S, P1] QUICKSTART.md                   ──── независимо
     ├─── CQ-04 [S, P1] Перечислить 4 вопроса           ──── независимо
     │
     ├─── CORE-05 [M, P1] Команда lint-full             ──── требует: CORE-01 (для CI)
     ├─── CORE-04 [M, P1] Инкрементальный индекс        ──── независимо
     │
     ▼
Phase 0j (стабилизация)
     │
     ├─── CQ-01 [L, P1] Разделить reefiki_core/         ──── требует: CORE-01 (CI поймает регрессии)
     ├─── CQ-02 [M, P1] Разбить тестовый файл           ──── до: CQ-01 (мигрировать тесты вместе)
     ├─── DX-01 [S, P2] Поле версии шаблона             ──── требует: CORE-05
     ├─── DX-03 [M, P2] Команда session-start           ──── требует: CORE-05
     ├─── DX-04 [S, P2] push-public.sh                  ──── независимо
     │
     ▼
Phase 1 (триггер: >200 страниц или >3 промахов query/месяц)
     │
     ├─── DX-02 [M, P2] --context-budget для pack       ──── требует: CQ-01 (рефакторинг)
     ├─── INT-04 [S, P2] Стаб Continue.dev              ──── независимо
     ├─── INT-05 [L, P2] MCP сервер                     ──── требует: CQ-01, стабильный CLI API
     │
     ├─── T-21 Confidence tagging                       ──── по существующему TASKS.md
     ├─── T-20 Static site export                       ──── по существующему TASKS.md
     │
     ▼
Phase 2+ (триггер: мульти-пользователь или >1000 страниц)
     ├─── T-40 MCP/REST API (расширяет INT-05)
     ├─── T-41 Vector/graph search layer
```

### Немедленный параллелизуемый спринт (~8 часов, всё независимо):

| Задача | Время |
|---|---|
| CORE-02 — создать `.serena/project.yml` | 30 мин |
| CORE-03 — добавить проверку id/filename | 2 ч |
| INT-01 — `.github/copilot-instructions.md` | 30 мин |
| INT-02 — `.aider.conf.yml` + `CONVENTIONS.md` | 1 ч |
| INT-03 — `GEMINI.md` | 30 мин |
| CQ-03 — `QUICKSTART.md` | 2 ч |
| CQ-04 — перечислить фильтр из 4 вопросов | 1 ч |

---

## Итоговая scorecard

| Категория | Текущее состояние | Цель |
|---|---|---|
| Архитектура | Монолит, хорошо структурированный | Модульный пакет `reefiki_core/` |
| Типобезопасность | Хорошая (`dict[str, object]`) | TypedDict-сужение для ключевых return types |
| Тестовое покрытие | Исчерпывающее для memory layer; пробелы в durable write, CLI flows | Все durable write пути покрыты; CI зелёный |
| Покрытие агентов | 5 стабов (~40% инструментов) | 9 стабов + документация для остальных |
| CI/CD | Отсутствует | GitHub Actions: validate + tests + golden |
| Онбординг | 45–90 мин; сложный | 15 мин с QUICKSTART.md |
| Автоматизация | Много ручных последовательностей | `lint-full`, `session-start`, post-commit хуки |
| Документация | Исчерпывающая, но перегруженная | Уровневая: QUICKSTART → COMMANDS → AGENTS |
| Позиционирование | Чёткое и защищаемое | Усилить EN README + CONTRIBUTING |
