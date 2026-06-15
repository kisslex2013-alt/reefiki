# 🚀 REEFIKI: Стратегия развития, оптимизация и уникальность

**Дата:** 2026-06-02
**Репозиторий:** https://github.com/kisslex2013-alt/reefiki
**Контекст:** Стратегический анализ после полного аудита безопасности (64 findings)

---

## Содержание

1. [Уникальность на рынке](#1-уникальность-на-рынке)
2. [Конкурентный ландшафт](#2-конкурентный-ландшафт)
3. [Стратегические возможности развития](#3-стратегические-возможности-развития)
4. [Оптимизация архитектуры](#4-оптимизация-архитектуры)
5. [Roadmap](#5-roadmap)

---

## 1. Уникальность на рынке

### 1.1 Единственный agent-agnostic knowledge control plane

REEFIKI — не привязан к конкретному AI-агенту. Работает через markdown + git + CLI, что делает его совместимым с любым агентом: Claude, Codex, Hermes, Cursor, Windsurf, Cline, ChatGPT.

**Почему это важно:**
- Организации используют 3-5 разных AI-агентов одновременно
- Knowledge не должен быть заложником одного вендора
- Markdown + git — lingua franca разработки, понятна всем

**Ни один конкурент не делает это:**
- Mem0: cloud-only, API-locked, Python SDK
- Zep: cloud-first, LangChain-integrated
- MemGPT/Letta: single-agent, proprietary storage
- Obsidian: не agent-aware, ручное управление
- Notion: cloud, API rate limits, vendor lock-in

### 1.2 Markdown как source of truth

Инновационная архитектурная идея: **markdown = durable storage, SQLite = disposable cache**.

**Что это даёт:**
- Knowledge portable: скопировал папку — перенёс всё
- Knowledge diffable: `git diff` показывает что изменилось
- Knowledge reviewable: PR-based workflow для знаний
- Knowledge versionable: полная история через git
- Knowledge searchable даже без REEFIKI: `grep -r "pattern" wiki/`

**Сравнение:**
| Подход | Portability | Versioning | Search | Agent-agnostic |
|---|---|---|---|---|
| Markdown + git (REEFIKI) | ✅ | ✅ (git) | ✅ (FTS5 + grep) | ✅ |
| SQLite-only | ❌ | ❌ | ✅ | ❌ |
| Cloud API (Mem0/Zep) | ❌ | ❌ (vendor) | ✅ | ❌ |
| Obsidian vault | ✅ | ⚠️ (git plugin) | ⚠️ | ❌ |

### 1.3 Privacy-first архитектура

- Local-first: данные не покидают машину
- Нет cloud calls (кроме опционального memoir-ai)
- Dual-remote publishing: private → filtered → public
- Нет телеметрии, analytics, phone-home

**Для кого критично:**
- Enterprise с compliance требованиями (SOC2, HIPAA, GDPR)
- Разработчики с чувствительными проектами (финтех, healthtech, defense)
- Компании с политикой "no external AI services"

### 1.4 Dual-remote publishing — уникальная модель

Ни один инструмент знаний не предлагает:
1. Private knowledge base (local + private GitHub)
2. Privacy filter (удаляет private пути, секреты)
3. Public snapshot (filtered копия на public GitHub)

**Use cases:**
- Команда: внутренняя wiki → публичная документация
- Open source: приватные заметки → публичные guides
- Research: рабочие гипотезы → опубликованные результаты

---

## 2. Конкурентный ландшафт

### 2.1 Прямые конкуренты

| Проект | Подход | Слабые стороны vs REEFIKI |
|---|---|---|
| **Mem0** | Cloud memory layer for AI | Vendor lock-in, cloud-only, не portable |
| **Zep** | Long-term memory for AI agents | Cloud-first, LangChain dependency |
| **MemGPT/Letta** | Self-editing memory for LLMs | Single-agent, proprietary format |
| **Memind** | Memory management for LLMs | Cloud-only, API-locked |
| **Cognee** | Knowledge graph for AI | Complex setup, graph DB dependency |

### 2.2 Соседние инструменты

| Инструмент | Пересечение | Что REEFIKI делает лучше |
|---|---|---|
| **Obsidian** | Markdown knowledge base | Agent-aware, programmatic access, publish pipeline |
| **Notion** | Team wiki | Local-first, no rate limits, git-native |
| **Logseq** | Outliner + knowledge graph | CLI-first, agent-compatible, privacy |
| **SiYuan** | Local knowledge base | Agent-agnostic, dual-remote, multi-vendor |

### 2.3 Белые пятна рынка

REEFIKI занимает уникальную нишу: **Agent-Native Knowledge Infrastructure**

Это пересечение:
- Knowledge Management (wiki, notes, docs)
- AI Agent Memory (persistent context, retrieval)
- Developer Tools (git, CLI, markdown)
- Privacy Engineering (local-first, filtered publish)

**Ни один продукт не покрывает все 4 области одновременно.**

---

## 3. Стратегические возможности развития

### 3.1 Knowledge Graph поверх FTS5

**Текущее состояние:** Pages связаны через `[[wiki links]]` и backlinks, но нет graph queries.

**Возможности:**
- Визуализация связей между знаниями (как Obsidian Graph View)
- Graph-based retrieval: "найди все страницы, связанные с X через 2 hops"
- Cluster detection: автоматическое обнаружение тематических кластеров
- Orphan detection: страницы без связей (потенциальные кандидаты на удаление/связывание)

**Реализация:**
- Лёгкий вариант: adjacency list в SQLite (уже есть extract_wiki_links)
- Тяжёлый вариант: graph database (networkx для in-memory, neo4j для persistence)

**Приоритет:** HIGH — это дифференциатор от Mem0/Zep

### 3.2 Cross-project Knowledge Discovery

**Текущее состояние:** Проекты изолированы. Knowledge из проекта A не видна из проекта B.

**Проблема:** Разработчик работает над 3 проектами. Ошибка, решённая в проекте A, повторяется в проекте C, потому что знание не было обнаружено.

**Возможности:**
- Global search: `/query --all "как настроить CI для monorepo"`
- Knowledge reuse: "эта страница похожа на страницу из другого проекта"
- Cross-project backlinks: "проект B ссылается на знание из проекта A"
- Shared knowledge layer: общие знания (паттерны, best practices) доступны всем проектам

**Реализация:**
- `memory_global_lookup()` уже существует, но не использует cross-project FTS
- Добавить `--scope global` в search
- Shared wiki layer: `projects/_shared/wiki/`

**Приоритет:** HIGH — значительно повышает ценность для multi-project teams

### 3.3 Temporal Knowledge (Knowledge Decay)

**Текущее состояние:** Страницы не имеют срока годности. Knowledge, написанная 2 года назад, считается такой же актуальной, как вчерашняя.

**Проблема:** "Как развернуть проект" — инструкция для v1.0. Сейчас v3.0, инструкция не работает. Агент находит её и даёт устаревший ответ.

**Возможности:**
- `last_verified: 2026-01-15` — когда кто-то подтвердил актуальность
- `applies_to: "v1.x"` — к какой версии относится
- `staleness_score` — формула: days_since_verified / expected_lifetime
- Auto-stale detection: если linked page обновилась, linked pages тоже могут быть stale
- `/stale` command: показать все potentially outdated pages

**Реализация:**
- Добавить поля в frontmatter schema
- Добавить staleness scoring в search ranking
- Добавить `/verify` command для ручного подтверждения

**Приоритет:** MEDIUM — важно для long-lived projects

### 3.4 Agent Feedback Loop (Adaptive Relevance)

**Текущее состояние:** `useful_when` — статичная строка. `use_count` увеличивается при каждом использовании, но не различает полезное и бесполезное использование.

**Возможности:**
- Implicit feedback: агент нашёл страницу → использовал → пользователь не поправил → positive signal
- Explicit feedback: thumbs up/down после ответа
- Relevance decay: страница не использовалась N месяцев → понизить в поиске
- Auto-suggest: "вы искали X, возможно вам нужна страница Y (similar, but more recent)"
- Negative feedback: агент дал ответ на основе страницы, пользователь сказал "нет" → понизить релевантность

**Реализация:**
- Добавить `feedback_score` в SQLite (float, -1.0 .. +1.0)
- Комбинировать с FTS5 relevance: `final_score = fts_score * (1 + feedback_score)`
- Добавить CLI: `reefiki feedback <page> --positive|--negative`

**Приоритет:** MEDIUM — делает REEFIKI "умнее" со временем

### 3.5 Knowledge Quality Metrics

**Текущее состояние:** Нет метрик качества knowledge base.

**Возможности:**
- **Coverage:** сколько тем проекта задокументировано? (сравнить с файлами кода, issues, PRs)
- **Freshness:** средний возраст страниц, % stale
- **Usage:** топ-N самых читаемых/полезных страниц
- **Gaps:** темы, по которым агент не нашёл ответ (search → empty result)
- **Consistency:** противоречат ли страницы друг другу?

**Реализация:**
- `/knowledge-health` command
- Dashboard в markdown (auto-generated report)
- Добавить `search_empty_queries.log` для gap detection

**Приоритет:** MEDIUM — важно для adoption в командах

### 3.6 MCP Server (Model Context Protocol)

**Текущее состояние:** REEFIKI доступен только через CLI. Агенты должны вызывать `python scripts/reefiki.py` через subprocess.

**Возможности:**
- MCP-сервер, exposing REEFIKI как tool для любого MCP-совместимого агента
- Zero-install: агент подключается по HTTP/stdio
- Standard interface: `search`, `read`, `write`, `publish` как MCP tools
- Discovery: агент автоматически находит REEFIKI при подключении

**Реализация:**
- MCP SDK для Python
- Expose существующие CLI commands как MCP tools
- Config: `reefiki mcp --port 8080` или stdio mode

**Приоритет:** HIGH — это unlock для ecosystem adoption

### 3.7 Multi-modal Knowledge

**Текущее состояние:** Только текст (markdown).

**Возможности:**
- Image support: скриншоты, диаграммы, архитектурные схемы в wiki
- Audio notes: голосовые заметки → transcription → wiki page
- Code snippets: syntax-highlighted код с возможностью запуска
- Video summaries: ссылки на видео с auto-generated summary

**Реализация:**
- Markdown уже поддерживает images (`![]()`)
- Добавить `media/` directory с auto-linking
- FTS5 не индексирует изображения → нужен separate index (CLIP, BLIP)

**Приоритет:** LOW — nice to have, markdown уже покрывает базовые needs

---

## 4. Оптимизация архитектуры

### 4.1 FTS5 → Гибридный поиск (Keyword + Semantic)

**Текущее состояние:** FTS5 — keyword-based search. Не понимает синонимы, контекст, намерения.

**Проблема:** Пользователь ищет "как сделать деплой". FTS5 не найдёт страницу "развертывание на сервере" (синоним).

**Возможности:**
- FTS5 для keyword search (быстро, точно)
- Embedding-based search для semantic similarity
- Hybrid scoring: `final = α * fts_score + (1-α) * cosine_similarity`
- Local embeddings: sentence-transformers (нет cloud dependency)

**Реализация:**
- Добавить embedding column в SQLite (BLOB)
- `pip install sentence-transformers` (опциональная зависимость)
- `build_index --embeddings` flag
- Fallback на FTS5 если embeddings не установлены

**Приоритет:** HIGH — значительно улучшает search quality

### 4.2 Incremental Index

**Текущее состояние:** `build_index()` перестраивает ВСЮ базу каждый раз. Для large wiki (>100 pages) это медленно.

**Возможности:**
- Diff-based: проиндексировать только изменённые файлы
- File hash tracking: `mtime` + `sha256` для каждого файла
- Partial rebuild: `build_index --changed` (только modified/added/deleted)
- Background indexing: watch mode для auto-reindex при изменении файлов

**Реализация:**
- Добавить `file_meta` таблицу: `path, mtime, sha256, indexed_at`
- При `build_index`: сравнить текущие hashes с сохранёнными
- Re-index только различающиеся файлы

**Приоритет:** MEDIUM — важно для large projects (>50 pages)

### 4.3 Streaming Publish

**Текущее состояние:** Public snapshot — полная копия private repo с фильтрацией. Для large repos это дорого.

**Возможности:**
- Incremental publish: push только изменённых файлов
- Differential snapshot: `rsync`-like sync между private и public
- Selective publish: publish только конкретных pages (не всего проекта)

**Реализация:**
- Добавить `--pages` flag: `reefiki publish-task --pages "setup,deployment"`
- Incremental: сравнивать public worktree с private, push только diffs

**Приоритет:** LOW — текущий подход работает, optimization при необходимости

### 4.4 Modular Architecture (Code Quality)

**Текущее состояние:** 3949 строк в одном файле, 126 функций.

**Предлагаемая декомпозиция:**

```
scripts/
├── reefiki.py          # CLI entry point + main() (~200 lines)
├── reefiki/
│   ├── __init__.py
│   ├── git_ops.py      # run_git, staged_paths, etc. (~200 lines)
│   ├── index.py         # build_index, extract_wiki_links (~300 lines)
│   ├── search.py        # search, escape_fts, best_chunk (~200 lines)
│   ├── publish.py       # publish_task, push_snapshot (~200 lines)
│   ├── memory.py        # memory_route, pack, status (~400 lines)
│   ├── promotion.py     # promotion workflow (~300 lines)
│   ├── review.py        # review_queue_scan, backlinks (~300 lines)
│   ├── guards.py        # privacy_scan, path_containment (~200 lines)
│   ├── utils.py         # parse_frontmatter, slugify, etc. (~200 lines)
│   └── cli.py           # print_* functions, formatting (~400 lines)
├── reefiki_memory/
│   └── __init__.py      # (keep as is)
└── validate_frontmatter.py  # (keep as is)
```

**Приоритет:** HIGH — prerequisite для всех остальных improvements

---

## 5. Roadmap

### Phase 1: Quick Wins (1-2 недели)
- [ ] Разбить reefiki.py на модули (modular architecture)
- [ ] Создать .gitignore
- [ ] Исправить security findings (Phase 1 из MEGA-AUDIT)
- [ ] Добавить CI workflow для тестов
- [ ] Добавить MCP server (stdio mode)

### Phase 2: Search & Discovery (2-4 недели)
- [ ] Гибридный поиск (FTS5 + embeddings)
- [ ] Incremental index
- [ ] Cross-project knowledge discovery
- [ ] Knowledge graph (adjacency list + basic queries)

### Phase 3: Intelligence (1-2 месяца)
- [ ] Agent feedback loop (adaptive relevance)
- [ ] Temporal knowledge (staleness detection)
- [ ] Knowledge quality metrics dashboard
- [ ] Auto-gap detection (empty search queries)

### Phase 4: Ecosystem (2-3 месяца)
- [ ] MCP server (full HTTP mode)
- [ ] VS Code extension (browse wiki inline)
- [ ] GitHub Action (auto-publish on merge)
- [ ] Plugin system (custom guards, custom search providers)
- [ ] Multi-modal support (images, diagrams)

### Phase 5: Scale (ongoing)
- [ ] Large repo support (>500 pages)
- [ ] Multi-user concurrent access (proper locking)
- [ ] Team features (shared knowledge, permissions)
- [ ] Enterprise features (audit log, compliance reports)

---

## 6. Уникальные фишки (post-audit innovations)

> Предпосылка: все 64 проблемы аудита исправлены. База надёжна, guards работают,
> код модульный. Что строить поверх?

### 6.1 Knowledge Fork & Branch

**Идея:** Как git branch, но для знаний. Wiki-ветки для экспериментов.

**Сценарий:**
- "Попробовать другой подход к деплою" → `reefiki branch deploy-experiment`
- Писать в ветке, не затрагивая основную wiki
- Эксперимент удался → `reefiki merge deploy-experiment`
- Не удался → `reefiki branch -d deploy-experiment`

**Почему уникально:** Ни один инструмент знаний (Obsidian, Notion, Mem0) не поддерживает branching. Git даёт это для кода, REEFIKI — для знаний.

**Реализация:** Git branches + working tree isolation. CLI: `reefiki branch`, `reefiki merge`, `reefiki switch`.

**Приоритет:** MEDIUM — мощный дифференциатор, но требует mature git integration.

---

### 6.2 Agent-as-Author с Blame

**Идея:** Каждая wiki-страница помечена: кто написал (Claude, Codex, Hermes, человек), когда, в каком контексте.

**Сценарий:**
- "Кто добавил этот паттерн и почему?" → `reefiki blame setup.md`
- Ответ: "Claude, 2026-05-15, сессия #abc123, контекст: настройка CI для monorepo"
- Git blame уже хранит автора коммита → расширить на agent metadata

**Почему уникально:** Git blame показывает email автора. REEFIKI покажет: какой AI-агент, какая сессия, какая задача. Knowledge provenance для multi-agent среды.

**Реализация:**
- Frontmatter: `author_agent: claude`, `session_id: abc123`, `created_from: "setup CI task"`
- `reefiki blame <page>` — агрегирует git blame + frontmatter metadata
- `reefiki history <page>` — timeline всех правок с agent attribution

**Приоритет:** HIGH — критично для multi-agent accountability.

---

### 6.3 Cross-Agent Knowledge Transfer

**Идея:** Claude решил проблему → записал в wiki → Codex нашёл через FTS5 → применил. Knowledge flow между агентами без cloud, без API.

**Сценарий:**
1. Claude работает над проектом, решает проблему с Docker networking
2. Автоматически создаёт wiki-страницу "docker-networking-fix.md"
3. Через неделю Codex работает над другим проектом, ищет "docker networking"
4. FTS5 находит страницу Claude → Codex применяет решение
5. Codex отмечает: `useful_when: "Docker bridge network issues"` + `use_count++`

**Почему уникально:** Сейчас каждый AI-агент работает в изоляции. REEFIKI становится **shared memory layer** для всех агентов. Не cloud API, не vendor lock-in — просто markdown + git + FTS5.

**Реализация:**
- Already works via `/query --global` и `memory_global_lookup()`
- Улучшить: agent metadata в frontmatter → фильтрация "знания от Claude" vs "знания от Codex"
- Улучшить: cross-project relevance scoring

**Приоритет:** HIGH — это core value proposition.

---

### 6.4 Staleness Radar

**Идея:** Связать wiki-страницы с git commits. Автоматическое обнаружение устаревших знаний.

**Сценарий:**
- Wiki-страница "как деплоить" написана для v1.0
- В git 200 коммитов с изменениями в deploy-скриптах
- REEFIKI: "⚠️ Страница deploy.md не обновлялась 90 дней. Изменённые файлы: Dockerfile, docker-compose.yml, scripts/deploy.sh. Возможно, устарела."

**Почему уникально:** Ни один инструмент не связывает knowledge freshness с code changes. Obsidian — нет. Notion — нет. Mem0 — нет.

**Реализация:**
- `file_watch` table: `wiki_page, watched_files[], last_verified, last_code_change`
- Git hook: при коммите → проверить, связаны ли изменённые файлы с wiki-страницами
- `reefiki stale` command: показать все potentially outdated pages
- Scoring: `staleness = days_since_verified / expected_lifetime`
- Frontmatter: `last_verified: 2026-01-15`, `applies_to: "v1.x"`

**Приоритет:** HIGH — решает реальную боль "документация устарела и никто не знает".

---

### 6.5 Knowledge Gaps Detector

**Идея:** Логировать каждый поиск с пустым результатом. Автоматическое обнаружение пробелов в документации.

**Сценарий:**
- Агент ищет "как настроить мониторинг" → 0 результатов (7 раз за неделю)
- REEFIKI: "🔍 Агенты искали 'мониторинг' 7 раз без результата. Создать страницу?"
- Автоматический issue/task: "Требуется wiki-страница про мониторинг"

**Почему уникально:** Documentation coverage на основе реальных запросов, а не предположений. Data-driven documentation strategy.

**Реализация:**
- `search_log` table: `query, timestamp, results_count, agent`
- Cron job: агрегирует пустые запросы за неделю
- `reefiki gaps` command: топ-N неотвеченных запросов
- Интеграция с kanban: автоматическое создание task

**Приоритет:** MEDIUM — полезно для команд, которые хотят расти knowledge base целенаправленно.

---

### 6.6 Publish Approval Queue

**Идея:** Не publish-all-or-nothing, а очередь с ревью.

**Сценарий:**
- 5 страниц готовы к публикации
- `reefiki publish-queue`:
  - ✅ `setup.md` — auto-publish (safe, no secrets detected)
  - ⏳ `architecture.md` — pending review (содержит internal API endpoints)
  - ⏳ `troubleshooting.md` — pending review (содержит internal error codes)
  - 🚫 `credentials-guide.md` — blocked (detected secret patterns)
  - ✅ `changelog.md` — auto-publish (public content)
- Человек одобряет → публикация

**Почему уникально:** Publish workflow с approval, как в CI/CD, но для знаний. Ни один knowledge tool этого не делает.

**Реализация:**
- `publish_queue` table: `page, status (auto/pending/blocked), reason, approved_by, approved_at`
- Privacy scan при добавлении в очередь (уже есть `privacy_scan()`)
- `reefiki publish-queue approve <page>` / `reefiki publish-queue reject <page>`
- Auto-publish: если privacy_scan чист + content confidence > threshold

**Приоритет:** HIGH — критично для команд, публикующих knowledge externally.

---

### 6.7 Privacy-Aware RAG

**Идея:** Один и тот же вопрос → разный ответ в зависимости от контекста аудитории.

**Сценарий:**
- Вопрос: "Как устроен auth?"
- Internal-чат (команда): полный ответ с private деталями, internal endpoints, secret rotation policy
- Public-чат (документация): filtered версия — только public-facing auth flow
- Один источник знаний, разные уровни детализации

**Почему уникально:** Текущие RAG-системы не различают audience. REEFIKI уже имеет privacy tiers (private/project/public) → использовать их при retrieval.

**Реализация:**
- `/query --tier internal "как устроен auth"` → полный ответ
- `/query --tier public "как устроен auth"` → filtered ответ
- FTS5 filter: `WHERE privacy_tier <= requested_tier`
- Agent instruction: "если вопрос из public-канала, используй --tier public"

**Приоритет:** MEDIUM — важно для компаний с mixed audience.

---

### 6.8 Knowledge Conflict Detection

**Идея:** Два агента написали противоположные вещи. Автоматическое обнаружение противоречий.

**Сценарий:**
- Claude написал: "Используй PostgreSQL для основной БД" (project A wiki)
- Codex написал: "Используй SQLite для основной БД" (project B wiki)
- REEFIKI: "⚠️ Конфликт: 'database-setup.md' (project A) рекомендует PostgreSQL, 'architecture.md' (project B) рекомендует SQLite. Какой источник актуален?"

**Почему уникально:** Conflict detection в distributed knowledge base. Ни один инструмент знаний не проверяет консистентность между страницами/проектами.

**Реализация:**
- Semantic similarity: найти страницы с похожими темами, но разными рекомендациями
- Keyword extraction: "PostgreSQL" vs "SQLite" на одной теме
- `reefiki conflicts` command: показать потенциальные противоречия
- Manual resolution: человек отмечает "canonical source"

**Приоритет:** LOW — сложно реализовать хорошо, но мощный дифференциатор.

---

### 6.9 Auto-ADR из Решений

**Идея:** Агент принял решение → автоматически создаётся ADR (Architecture Decision Record).

**Сценарий:**
- Codex выбирает библиотеку для HTTP: "Используем httpx вместо requests"
- Автоматически создаётся `decisions/001-use-httpx.md`:
  ```
  ---
  title: "Use httpx instead of requests"
  status: accepted
  decided_by: codex
  date: 2026-06-02
  context: "Need async HTTP support for webhook delivery"
  ---
  # Decision: Use httpx
  ## Context
  We need async HTTP for webhook delivery.
  ## Decision
  Use httpx (async-native, HTTP/2, connection pooling).
  ## Consequences
  - Migrate existing requests calls
  - Update requirements.txt
  ```
- Решения накапливаются, не теряются. Новый агент может спросить "почему httpx?" и получить ответ.

**Почему уникально:** ADR — стандартная практика, но ручная. REEFIKI делает её автоматической через agent actions. Ни один инструмент не генерирует ADR из AI-сессий.

**Реализация:**
- Detect decision patterns в agent output: "let's use X", "I'll go with X because Y"
- Template: ADR frontmatter + context + decision + consequences
- `reefiki adr create "title" --context "..." --decision "..."`
- Or: agent self-report: "I decided X because Y" → auto-ADR

**Приоритет:** MEDIUM — полезно для long-lived projects с множеством агентов.

---

### 6.10 Live Documentation Sync

**Идея:** Wiki "прилипает" к коду. Изменения в коде → предупреждение о расхождении с документацией.

**Сценарий:**
- Разработчик изменил `docker-compose.yml` (добавил новую зависимость)
- Git hook: "📄 Изменён docker-compose.yml. Связанная wiki-страница: 'docker-setup.md'. Проверьте актуальность."
- Или: `pyproject.toml` изменился → "📄 Страница 'dependencies.md' может быть устаревшей."

**Почему уникально:** Documentation-code drift — одна из главных болей разработки. Ни один инструмент не мониторит связь "файл кода ↔ wiki-страница" автоматически.

**Реализация:**
- Frontmatter: `watches: ["docker-compose.yml", "Dockerfile"]`
- Git hook `post-commit`: diff → check watched files → alert if changed
- `reefiki watch` command: показать все file→page связи
- Cron job: еженедельный отчёт "10 wiki-страниц потенциально устарели (код изменился)"

**Приоритет:** HIGH — решает фундаментальную проблему "документация всегда отстаёт от кода".

---

### 6.11 Knowledge Harvesting from AI Conversations

**Идея:** Импорт переписок с AI-агентами (ChatGPT, Claude, Hermes, OpenClaw, Codex) → автоматическое извлечение решений, идей, паттернов → wiki-страницы.

**Контекст:** У каждого разработчика накапливаются десятки/сотни переписок с AI. В них — решения архитектурных проблем, обходные пути, объяснения сложных концепций, code review feedback. Сейчас всё это **теряется** после закрытия чата.

**Сценарий:**
1. Экспорт переписки из ChatGPT (JSON) / Claude (copy) / Hermes (markdown)
2. `reefiki harvest chatgpt-export.json --agent chatgpt --project myproject`
3. REEFIKI парсит → извлекает:
   - **Решения**: "используй httpx вместо requests" → wiki-страница или ADR
   - **Паттерны**: "для retry всегда используй exponential backoff" → best practice
   - **Обходные пути**: "ошибка X решается через Y" → troubleshooting
   - **Архитектурные инсайты**: "microservices лучше чем monolith для этого кейса" → decision
   - **Code snippets**: рабочий код с объяснением → reference page
4. Deduplication: если идея уже есть в wiki → skip или обновить `use_count`
5. Provenance: каждая страница помечена `source: "chatgpt session 2026-05-15"`, `source_agent: chatgpt`

**Поддерживаемые форматы:**

| Источник | Формат | Метод импорта |
|---|---|---|
| ChatGPT | JSON export | `reefiki harvest --format chatgpt` |
| Claude | Markdown (copy) | `reefiki harvest --format claude` |
| Hermes | Markdown | `reefiki harvest --format hermes` |
| OpenClaw | Markdown/JSON | `reefiki harvest --format openclaw` |
| Любой | Plain text | `reefiki harvest --format generic` |

**Pipeline:**

```
Переписка → Parse → Classify → Extract → Deduplicate → Wiki page
                ↓         ↓          ↓            ↓
           Убрать шум  Тип:       Frontmatter   Уже есть?
           (90% текста) decision   + body        → skip/merge
                       /pattern
                       /fix
                       /insight
```

**Промт для извлечения (inbox-processing):**

```
Ты — knowledge extractor. Прочитай переписку с AI-агентом и извлеки:
1. Конкретные РЕШЕНИЯ (что выбрали и почему)
2. ПАТТЕРНЫ и best practices (повторяющиеся подходы)
3. ОБХОДНЫЕ ПУТИ (как решили конкретную ошибку)
4. АРХИТЕКТУРНЫЕ ИНСАЙТЫ (почему сделали так, а не иначе)
5. ПОЛЕЗНЫЙ КОД (рабочие snippets с контекстом)

НЕ извлекай:
- Рассуждения без вывода
- Повторные попытки (retry лог)
- Приветствия и формальности
- Один и тот же совет несколько раз (только финальную версию)

Для каждого извлечённого элемента:
- title: краткий заголовок
- type: decision | pattern | fix | insight | reference
- body: markdown с деталями
- source_agent: имя агента
- source_date: дата сессии
- useful_when: когда это знание пригодится
```

**Батчевый режим:**

```bash
# Один файл
reefiki harvest session.json --agent chatgpt --project reefiki

# Папка с экспортами
reefiki harvest ~/ai-exports/ --agent chatgpt --batch --project reefiki

# Только извлечь, не создавать страницы (dry run)
reefiki harvest session.json --dry-run --agent claude
```

**Почему уникально:** Ни один инструмент знаний не предлагает импорт из AI-переписок с автоматическим извлечением. Obsidian — ручное копирование. Notion — нет. Mem0 — cloud-only, не импортирует переписки. REEFIKI превращает **забытые чаты в структурированные знания**.

**Реализация:**
- `scripts/harvest_conversations.py` — парсинг + классификация
- Поддержка форматов: ChatGPT JSON, Claude markdown, generic text
- Классификация через LLM (опционально) или rule-based (regex на паттерны решений)
- Deduplication: FTS5 similarity search на существующие страницы
- Frontmatter: `source_type: "ai_conversation"`, `source_agent: "chatgpt"`, `source_session_id: "..."`

**Приоритет:** HIGH — это **killer feature для adoption**. Каждый разработчик имеет сотни переписок. Один скрипт превращает их в wiki.

---

## 7. Сводная таблица уникальных фишек

| # | Фишка | Уникальность | Приоритет | Сложность |
|---|---|---|---|---|
| 6.1 | Knowledge Fork & Branch | Нет аналогов | MEDIUM | L |
| 6.2 | Agent-as-Author с Blame | Нет аналогов | HIGH | M |
| 6.3 | Cross-Agent Knowledge Transfer | Core differentiator | HIGH | S |
| 6.4 | Staleness Radar | Нет аналогов | HIGH | M |
| 6.5 | Knowledge Gaps Detector | Нет аналогов | MEDIUM | S |
| 6.6 | Publish Approval Queue | CI/CD for knowledge | HIGH | M |
| 6.7 | Privacy-Aware RAG | Нет аналогов | MEDIUM | M |
| 6.8 | Knowledge Conflict Detection | Нет аналогов | LOW | L |
| 6.9 | Auto-ADR из Решений | Нет аналогов | MEDIUM | S |
| 6.10 | Live Documentation Sync | Нет аналогов | HIGH | M |
| 6.11 | Knowledge Harvesting from AI Conversations | Нет аналогов | HIGH | M |

**Топ-4 для немедленной реализации:**
1. **Cross-Agent Knowledge Transfer** (S) — уже почти работает, нужно доработать
2. **Knowledge Harvesting** (M) — killer feature для adoption, каждый имеет сотни переписок
3. **Agent-as-Author с Blame** (M) — критично для multi-agent accountability
4. **Live Documentation Sync** (M) — решает главную боль документации

---

## Ключевой инсайт

REEFIKI — это **не просто инструмент для заметок**. Это **knowledge infrastructure для эпохи AI-агентов**.

Когда у вас 5 разных AI-агентов, работающих с одним кодом, им всем нужно:
- Понимать проект (knowledge)
- Запоминать решения (memory)
- Не терять контекст (persistence)
- Не утекать данные (privacy)
- Работать вместе (multi-agent)

REEFIKI — единственный инструмент, который решает все 5 проблем одновременно, оставаясь local-first и vendor-agnostic.

**Это не Obsidian для агентов. Это git для знаний агентов.**

---

## 8. Монетизация (Freemium)

> Принцип: **core всегда бесплатный и open-source**. CLI, markdown, git, FTS5, local publish — навсегда.
> Монетизация через дополнительную ценность, а не ограничение базового функционала.

### 8.1 Принципы

**Бесплатно навсегда (Core):**
- CLI (`reefiki` command)
- Markdown + YAML frontmatter
- SQLite FTS5 поиск
- Git-based versioning
- Dual-remote publish (private → public)
- Pre-commit hooks, guards
- Inbox, source, classify
- Wiki link graph (базовый)
- Все текущие commands

**Платно (所提供之 поверх core):**
- Всё, что требует hosting/infrastructure
- Всё, что требует compute (LLM, embeddings)
- Всё, что экономит время команды (collaboration, automation)
- Всё, что нужно для compliance (enterprise)

---

### 8.2 REEFIKI Cloud ($0 / $12 / $29 / custom)

**Идея:** Hosted версия REEFIKI без необходимости локальной установки.

**Free tier:**
- 1 проект, 50 страниц
- Web UI (read-only browse)
- Public wiki hosting (*.reefiki.dev)
- Basic FTS5 search

**Pro ($12/мес):**
- Безлимит проектов и страниц
- Web UI (read + write)
- Custom domain для public wiki
- Semantic search (embeddings-based)
- Knowledge graph visualization
- Export/backup

**Team ($29/мес, за пользователя):**
- Multi-user access
- Roles: viewer / editor / admin
- Real-time collaboration
- Publish approval workflow
- Activity feed (кто что изменил)
- Slack/Discord интеграция

**Enterprise (custom):**
- SSO (SAML, OIDC)
- Audit log (compliance)
- On-premise option
- SLA, priority support
- Custom integrations

**Почему работает:** Большинство команд не хотят управлять локальной установкой. Cloud = zero setup + collaboration.

---

### 8.3 REEFIKI Pro License ($99/год, per-seat)

**Идея:** Премиум фичи для локальной установки. Не cloud — остаётся local-first.

**Включает:**
- Semantic search (embeddings, гибридный FTS5 + cosine)
- Knowledge graph visualization (web UI, localhost)
- Knowledge Harvesting (import из ChatGPT, Claude, Hermes)
- Staleness Radar (auto-detect outdated pages)
- Knowledge Gaps Detector
- Auto-ADR generation
- Live Documentation Sync (git hooks)
- Conflict Detection
- Privacy-Aware RAG (multi-tier retrieval)
- Priority email support

**Почему работает:** Power users и команды заплатят за фичи, которые экономят часы работы. $99/год — дешевле одного часа разработчика.

---

### 8.4 REEFIKI Managed Publish ($5/мес за домен)

**Идея:** Хостинг public wiki с кастомным доменом и красивым UI.

**Сценарий:**
- У тебя есть private REEFIKI с knowledge base
- `reefiki publish-task` → filtered snapshot
- Managed Publish хостит его на `docs.yourcompany.com`
- Автоматический SSL, CDN, поиск, навигация
- Обновляется при каждом `publish-task`

**Ценообразование:**
- $5/мес за домен (1 project)
- $2/мес за каждый additional project
- Free: *.reefiki.pages.dev subdomain

**Почему работает:** Компании тратят $50-200/мес на hosted docs (GitBook, ReadMe, Docusaurus Cloud). REEFIKI дешевле в 10-40 раз + данные остаются в markdown/git.

---

### 8.5 REEFIKI Templates & Plugins Marketplace

**Идея:** Экосистема шаблонов и плагинов от сообщества.

**Шаблоны (free + paid):**
- Project templates: React app wiki, Python library docs, SaaS runbook, API reference
- Wiki templates: troubleshooting, ADR, onboarding, postmortem
- Deep Research templates: market analysis, competitive analysis, tech evaluation

**Плагины (free + paid):**
- Source connectors: Notion import, Confluence import, Obsidian vault import
- Search providers: Elasticsearch backend, Algolia integration
- Publish targets: Vercel, Netlify, GitHub Pages, S3
- Integrations: Linear, Jira, Slack bot, Discord bot

**Модель:**
- Free плагины: community-built, open-source
- Paid плагины: REEFIKI team или verified partners, 70/30 split
- REEFIKI берёт 30% комиссии

**Почему работает:** Marketplace = ecosystem lock-in (положительный). Плагины делают REEFIKI незаменимым.

---

### 8.6 REEFIKI API ($0 / $49 / $199)

**Идея:** REST/GraphQL API для программного доступа к REEFIKI.

**Free tier:**
- 1000 запросов/мес
- Read-only endpoints: search, get page, list pages
- Webhook: page created, page updated

**Growth ($49/мес):**
- 50,000 запросов/мес
- Read + Write endpoints
- Batch operations
- Webhook: all events

**Scale ($199/мес):**
- Безлимит запросов
- Priority rate limits
- Dedicated endpoint
- Custom webhooks
- SLA

**Use cases:**
- CI/CD пайплайны: "обновить wiki при merge"
- Slack бот: "найди мне страницу про X"
- Dashboard: knowledge base metrics
- Custom integrations

**Почему работает:** API = developer platform. Когда другие строят на REEFIKI, он становится стандартом.

---

### 8.7 REEFIKI Consulting & Training

**Идея:** Professional services для enterprise adoption.

**Услуги:**
- **Setup & Migration** ($500-2000): установка, миграция из Notion/Confluence/Obsidian, настройка publish pipeline
- **Knowledge Audit** ($1000-3000): аудит existing knowledge base, рекомендации по структуре
- **Team Training** ($2000-5000): воркшоп для команды "как использовать REEFIKI эффективно"
- **Custom Development** ($150/час): кастомные плагины, интеграции, automation

**Почему работает:** Enterprise не купит инструмент без professional services. Consulting = доверие + revenue.

---

### 8.8 Сводная таблица монетизации

| Продукт | Цена | Целевая аудитория | MRR potential |
|---|---|---|---|
| REEFIKI Cloud Free | $0 | Solo developers | — |
| REEFIKI Cloud Pro | $12/мес | Power users | ARR: $12 × users |
| REEFIKI Cloud Team | $29/мес/user | Команды 5-50 | ARR: $29 × users |
| REEFIKI Cloud Enterprise | Custom | Enterprise 50+ | ARR: $500-5000/deal |
| REEFIKI Pro License | $99/год | Local power users | ARR: $99 × seats |
| Managed Publish | $5/мес/domain | Open-source projects | ARR: $5 × domains |
| Marketplace | 30% commission | Developers | Varies |
| API Growth | $49/мес | SaaS companies | ARR: $49 × subs |
| API Scale | $199/мес | Enterprise integrations | ARR: $199 × subs |
| Consulting | $500-5000/project | Enterprise | Project-based |

### 8.9 Стратегия запуска

**Phase 0 (сейчас):** Open-source, бесплатный CLI. Build community.

**Phase 1 (через 3 месяца):** REEFIKI Pro License ($99/год). Премиум фичи для локальной установки. Первый revenue.

**Phase 2 (через 6 месяцев):** Managed Publish ($5/мес). Хостинг public wiki. Low-touch revenue.

**Phase 3 (через 9 месяцев):** REEFIKI Cloud (Free + Pro + Team). Hosted версия. Scale revenue.

**Phase 4 (через 12 месяцев):** Marketplace + API. Developer ecosystem. Platform revenue.

**Phase 5 (ongoing):** Consulting + Enterprise. High-touch revenue.

**Ключевой принцип:** Никогда не paywall core функционал. Бесплатный CLI должен быть достаточно мощным, чтобы разработчик влюбился. Платные фичи — это "я хочу больше", а не "я должен заплатить чтобы пользоваться".

---

## 9. Go-to-Market стратегия

### 9.1 Hacker News — главный канал запуска

**Формат:** Show HN: REEFIKI — local-first knowledge control plane for AI agents

**Тактика:**
- Вторник–четверг, 9–11 AM EST (максимальный трафик)
- Первые 30 минут критичны: нужны 5-10 ранних пользователей для начальных апвоутов
- Заголовок: pain point + technical insight + demo link
- Антипаттерны: buzzwords, вейпворк, отсутствие демо

**Месседж для HN:**
> "Stop re-explaining your project to every AI agent. REEFIKI gives your agents a shared, local-first knowledge base — markdown + git + full-text search. Switch between Claude, Codex, and Hermes without losing context."

**Контент-стратегия для HN (помимо Show HN):**
- "How we built SQLite FTS5-based knowledge graph for AI agents"
- "Why AI agents lose context between sessions and how to fix it"
- Экспертные комментарии к постам об AI agent tooling

### 9.2 Product Hunt

**Подготовка (за 2-4 недели):**
- Собрать 500-1000 followers (Twitter, Discord, newsletter)
- Найти hunters из топ-100 с релевантной аудиторией
- Подготовить assets: screenshots, demo video, описание

**День запуска:**
- 12:01 AM PST (первый на платформе)
- Первый комментарий от основателя: история создания
- "Ранние пользователи получают badge в репозитории"

**Позиционирование:** "The Git for your AI agents' knowledge"

### 9.3 Reddit и Dev-сообщества

**Субреддиты:**
- r/programming, r/opensource, r/devtools
- r/LocalLLaMA (ключевой для agent-agnostic positioning)
- r/selfhosted (local-first narrative)
- r/ClaudeAI, r/ChatGPTPro (agent-specific communities)

**Формат:** Не "я сделал X", а "I was frustrated with X, so I built Y. Here's what I learned"

**Другие площадки:**
- Dev.to / Hashnode — SEO-дружелюбные статьи
- Lobste.rs — технически подкованная аудитория, любит deep-dive
- Twitter/X — threads с техническими инсайтами, не промо

### 9.4 Месседжевая матрица

| Аудитория | Боль | Месседж |
|---|---|---|
| AI power users | Контекст теряется между агентами | "One knowledge base, any agent" |
| Privacy-conscious devs | Данные уходят в облака | "Your knowledge stays local. Git-first." |
| Team leads | Knowledge silos | "Private → public docs with one push" |
| OSS contributors | Любят простые инструменты | "Markdown + SQLite + Git. No magic." |

### 9.5 Timeline запуска

| Неделя | Действие |
|---|---|
| -4 | Подготовка README, demo, screenshots |
| -3 | Twitter/X: серия постов о проблеме |
| -2 | Dev.to статья "Why AI agents need shared memory" |
| -1 | Show HN + Reddit посты |
| 0 | Product Hunt запуск |
| +1 | Follow-up статья "What we learned from launch" |
| +2 | Discord community open |

---

## 10. Community Flywheel

### 10.1 Три фазы роста

**Phase 1 — "Вирусное ядро" (0 → 1000 users):**
- Extreme developer experience: `pip install reefiki && reefiki init` — работает за 30 секунд
- "Wow moment": агент находит знание из другой сессии → пользователь понимает ценность
- Личные invite в Discord каждого раннего пользователя
- KPI: GitHub stars, Discord members

**Phase 1.5 — "Contributor flywheel" (1000 → 10000 users):**
- 10+ `good first issue` всегда открыты
- CONTRIBUTING.md: как начать за 5 минут
- Документация лучше, чем у любого конкурента
- Fast response на issues: < 1 час в первые месяцы
- KPI: PRs merged, contributors count, issue response time

**Phase 2 — "Community scale" (10000+ users):**
- Ambassador program: активные пользователи → special role
- Community plugins/templates от пользователей
- Monthly community calls
- KPI: community plugins, ambassador count, NPS

### 10.2 Discord сервер

**Структура:**
```
#announcements       — релизы, обновления
#getting-started     — помощь новичкам
#show-and-tell       — пользователи делятся wiki
#plugins             — разработка плагинов
#feature-requests    — голосование за фичи
#bug-reports         — быстрый triage
#off-topic           — community building
```

**Правила:**
- Ответ на каждый вопрос < 1 час (первые месяцы)
- Еженедельный "community spotlight" — лучшие wiki от пользователей
- Monthly "office hours" с основателем

### 10.3 Contributor Recognition

- Contributors page на сайте с avatar и link
- Special Discord roles: "Core Contributor", "Plugin Author", "Early Adopter"
- Swag для top contributors (stickers, t-shirts)
- Annual "REEFIKI Awards": лучший плагин, лучший wiki, лучший PR

---

## 11. Competitive Moat (защитимость)

### 11.1 Естественные рвы

**Data Gravity:**
- Wiki pages накапливаются со временем → switching cost растёт
- Git history = бесценный контекст решений
- FTS5 index = "мозг" проекта, нельзя перенести в другой инструмент

**Ecosystem Lock-in:**
- Каждый плагин увеличивает стоимость миграции
- Community templates = стандарт де-факто для wiki структуры
- API integrations (Slack, CI/CD, IDE) = "приклеенные" workflows

**Network Effects:**
- Cross-agent knowledge transfer: больше агентов используют → больше знаний → ценнее для каждого
- Marketplace: больше плагинов → больше пользователей → больше разработчиков плагинов
- Public wiki hosting: больше проектов на *.reefiki.dev → узнаваемость бренда

### 11.2 Почему конкуренты не скопируют

| Конкурент | Почему не скопирует |
|---|---|
| Mem0/Zep | Cloud-first DNA. Не могут сделать local-first без переписывания |
| Obsidian | Markdown-first, но не agent-aware. Нет CLI, нет publish pipeline |
| Notion | Cloud-only, proprietary format. Не могут сделать git-native |
| Cursor/Windsurf | Vendor-locked. Не могут сделать agent-agnostic |
| GitBook | Hosted docs company. Не могут сделать local-first |

### 11.3 Временное окно

REEFIKI нужно занять нишу в ближайшие 12-18 месяцев. После этого:
- Крупные игроки начнут копировать (Obsidian добавит agent features)
- Появятся конкуренты с бо́льшим funding
- Network effects начнут работать только после ~10000 активных пользователей

**Действие:** Быстро → community → ecosystem → moat.

---

## 12. Migration Playbook

### 12.1 Из Notion

**Экспорт:** Notion → Export as Markdown (zip)
**Импорт:**
```bash
reefiki import notion-export.zip --format notion --project myproject
```
**Что нужно обработать:**
- Notion blocks → markdown (таблицы, callouts, toggles)
- Notion database → frontmatter metadata
- Nested pages → flat wiki structure с wiki links
- Images: Notion export хранит в /images/ → перенести в wiki

**Сложность:** MEDIUM. Notion API позволяет экспортировать программно.

### 12.2 Из Confluence

**Экспорт:** Confluence → Space export (XML/HTML)
**Импорт:**
```bash
reefiki import confluence-export.zip --format confluence --project myproject
```
**Что нужно обработать:**
- Confluence storage format (XHTML) → markdown
- Macro expansion (code blocks, panels, table of contents)
- Attachments → wiki media
- Page hierarchy → wiki links

**Сложность:** HIGH. Confluence storage format сложный, нужен parser.

### 12.3 Из Obsidian

**Экспорт:** Просто скопировать vault
**Импорт:**
```bash
reefiki import ~/obsidian-vault/ --format obsidian --project myproject
```
**Что нужно обработать:**
- Obsidian markdown ≈ REEFIKI markdown (почти совместимы)
- Obsidian frontmatter → REEFIKI frontmatter (маппинг полей)
- Obsidian plugins data → игнорировать
- Obsidian internal links `[[page]]` → REEFIKI wiki links (совместимы!)
- Obsidian graph view metadata → не переносить (REEFIKI строит свой)

**Сложность:** LOW. Почти 1:1 совместимость.

### 12.4 Из Roam Research

**Экспорт:** Roam → JSON export
**Импорт:**
```bash
reefiki import roam-export.json --format roam --project myproject
```
**Что нужно обработать:**
- Roam blocks (bullet-based) → markdown paragraphs
- `((page references))` → `[[wiki links]]`
- Daily notes → log pages
- Block references → inline quotes

**Сложность:** MEDIUM. Roam JSON format хорошо документирован.

### 12.5 Из Generic Markdown

```bash
reefiki import ~/my-notes/ --format generic --project myproject
```
- Рекурсивный обход директории
- .md файлы → wiki pages
- Directory structure → wiki hierarchy через links
- YAML frontmatter: если есть → использовать, если нет → сгенерировать

**Сложность:** LOW.

---

## 13. Content Strategy

### 13.1 Контент-воронка

```
Awareness → Understanding → Adoption → Retention
   ↓              ↓             ↓           ↓
 Twitter      Blog posts     Tutorials    Community
 HN/Reddit    Comparison     Quickstart   Discord
 Podcasts     Deep dives     Examples     Newsletter
```

### 13.2 Контент-план (первые 3 месяца)

**Week 1-2: Awareness**
- "Why AI agents lose context between sessions" (blog + HN + Twitter thread)
- "REEFIKI: git for your AI agents' knowledge" (Show HN)

**Week 3-4: Understanding**
- "REEFIKI vs Mem0 vs Zep: local-first vs cloud" (comparison article)
- "How dual-remote publishing works" (technical deep dive)

**Week 5-6: Adoption**
- "5-minute setup: shared knowledge for Claude and Codex" (tutorial)
- "Migrating from Obsidian to REEFIKI" (migration guide)

**Week 7-8: Retention**
- "Building a knowledge base that grows with your project" (best practices)
- "REEFIKI plugin development guide" (ecosystem building)

**Week 9-12: Scale**
- "How we use REEFIKI to manage knowledge across 5 AI agents" (case study)
- "REEFIKI at scale: 1000+ pages, 10+ projects" (performance article)
- Video tutorial series on YouTube

### 13.3 SEO-ключевые запросы

- "AI agent memory" / "AI agent knowledge base"
- "local-first knowledge management"
- "markdown knowledge base for developers"
- "alternative to Notion for developers"
- "AI agent context management"
- "shared memory for AI agents"

---

## 14. Partnerships

### 14.1 AI Agent Companies

| Партнёр | Интеграция | Ценность |
|---|---|---|
| **Cursor** | Plugin: REEFIKI as memory backend | Cursor users → REEFIKI adoption |
| **Windsurf** | MCP server integration | Same |
| **Cline** | CLI integration | Same |
| **Anthropic** | Claude projects + REEFIKI wiki | Enterprise credibility |
| **OpenAI** | Custom GPTs + REEFIKI knowledge | Scale |

### 14.2 Dev Tool Companies

| Партнёр | Интеграция | Ценность |
|---|---|---|
| **GitHub** | GitHub Actions для auto-publish | Workflow integration |
| **Linear** | Issues → wiki pages | Project management bridge |
| **Vercel** | Deploy public wiki as site | Hosting partnership |
| **Railway** | One-click REEFIKI Cloud deploy | Easy hosting |

### 14.3 AI Infrastructure

| Партнёр | Интеграция | Ценность |
|---|---|---|
| **LangChain** | REEFIKI as memory provider | Framework ecosystem |
| **LlamaIndex** | REEFIKI as data connector | Same |
| **Hugging Face** | REEFIKI + local models | Open-source credibility |

### 14.4 Partnership Strategy

**Phase 1:** MCP server → автоматическая совместимость с Cursor, Windsurf, Cline
**Phase 2:** GitHub Action → workflow integration
**Phase 3:** LangChain/LlamaIndex connectors → framework ecosystem
**Phase 4:** Direct partnerships с Anthropic, OpenAI → enterprise credibility

---

## 15. Offline-first и Conflict Resolution

### 15.1 Проблема

Агент работает offline (или на другой машине). Потом синхронизация. Конфликты:
- Два агента отредактировали одну страницу
- Агент удалил страницу, которую человек дополнил
- Wiki link指向 страницу, которую другой агент переименовал

### 15.2 Решения

**Уровень 1: Git merge (текущий)**
- Git already handles merges
- Wiki pages — простой текст, merge conflicts редки
- `git mergetool` для ручного разрешения

**Уровень 2: Auto-merge для wiki content**
- Если оба изменили разные секции → auto-merge
- Если оба изменили одну секцию → conflict marker + alert
- Примитивный 3-way merge для markdown sections

**Уровень 3: Conflict resolution UI (future)**
- `reefiki conflicts` command: показать все конфликты
- Side-by-side diff в terminal
- "Принять мой / принять их / ручное合并"

### 15.3 Offline workflow

```
1. Агент работает offline → создаёт/редактирует pages
2. Коммитит локально (git commit)
3. При появлении сети → git pull --rebase
4. Если конфликты → reefiki conflicts → ручное разрешение
5. git push
```

### 15.4 Ключевой принцип

REEFIKI уже offline-first (local files + git). Нужно только:
- Хороший merge strategy для wiki content
- Conflict detection и resolution tooling
- Documentation: "how to work offline with REEFIKI"

---

## 16. License Strategy

### 16.1 Варианты

| Лицензия | Плюсы | Минусы | Примеры |
|---|---|---|---|
| **MIT** | Максималь adoption, разрешает всё | Конкуренты могут забрать код | React, Vue, Rails |
| **Apache 2.0** | MIT + patent protection | Сложнее для восприятия | Kubernetes, TensorFlow |
| **AGPL** | Защита от SaaS-клонирования | Отпугивает enterprise | MongoDB (был), Grafana |
| **BSL** | Source available, через N лет → open | Сложная лицензия, путаница | MariaDB, Sentry, HashiCorp |

### 16.2 Рекомендация для REEFIKI

**Core (CLI + markdown processing + FTS5):** MIT или Apache 2.0
- Максималь adoption
- Разрешает использование в enterprise
- Разрешает fork (конкуренты могут скопировать, но не ecosystem)

**Premium features (semantic search, harvesting, etc.):** Proprietary license
- Закрытый код для премиум фичей
- Или BSL: source available, но нельзя использовать как SaaS

**Plugins/Marketplace:** MIT
- Разработчики плагинов выбирают свою лицензию
- Рекомендация: MIT для ecosystem growth

### 16.3 Почему не AGPL

- Отпугивает enterprise (юридические отделы боятся AGPL)
- Сложно определить границу: CLI tool = distribution? HTTP server = distribution?
- MongoDB перешёл с AGPL на SSPL из-за проблем с cloud провайдерами
- REEFIKI не SaaS-продукт → AGPL не даёт преимуществ

### 16.4 Рекомендация

**Apache 2.0 для core** — баланс между adoption и protection.
**Proprietary для premium** — монетизация через closed-source фичи.

---

## 17. Non-technical Users

### 17.1 Проблема

REEFIKI — developer tool. CLI, markdown, git — intimidating для PM, дизайнера, руководителя.

### 17.2 Решения

**Уровень 1: CLI (для разработчиков)**
- Текущий подход. `reefiki` command. Полная мощность.

**Уровень 2: Web UI (для всех)**
- Read-only browse: любой может читать wiki через браузер
- Search: простой search bar, как Google
- Навигация: sidebar с деревом страниц, breadcrumbs
- Без login для public wiki, с login для internal

**Уровень 3: Visual Editor (для не-разработчиков)**
- WYSIWYG markdown editor (как Notion)
- Drag-and-drop для изображений
- Auto-save (без "commit" кнопки)
- Frontmatter editor: dropdown для тегов, date picker для дат

**Уровень 4: Templates (для быстрого старта)**
- "Создать страницу" → шаблоны: Meeting Notes, Decision, Troubleshooting, How-To
- Заполнить поля → markdown генерируется автоматически
- Без знания markdown syntax

### 17.3 Принцип

> "CLI для power, Web UI для reach, Templates для adoption"

REEFIKI должен быть:
- **Мощным** через CLI (для разработчиков)
- **Доступным** через Web UI (для всех)
- **Простым** через Templates (для новичков)

---

## 18. Metrics & KPIs

### 18.1 Product Metrics

| Метрика | Описание | Цель (6 мес) | Цель (12 мес) |
|---|---|---|---|
| GitHub Stars | Interest/awareness | 500 | 2000 |
| Active Installations | `reefiki status` pings | 100 | 1000 |
| Wiki Pages Created | Content growth | 5000 | 50000 |
| Search Queries/Day | Usage intensity | 200 | 2000 |
| Publish Operations | Content sharing | 50 | 500 |

### 18.2 Community Metrics

| Метрика | Описание | Цель (6 мес) | Цель (12 мес) |
|---|---|---|---|
| Discord Members | Community size | 200 | 1000 |
| Contributors | OSS health | 10 | 50 |
| PRs Merged/Month | Development velocity | 10 | 30 |
| Issue Response Time | Support quality | < 2 hours | < 1 hour |
| Community Plugins | Ecosystem growth | 5 | 20 |

### 18.3 Business Metrics

| Метрика | Описание | Цель (6 мес) | Цель (12 мес) |
|---|---|---|---|
| MRR | Revenue | $0 | $2000 |
| Paid Users | Monetization | 0 | 50 |
| Churn Rate | Retention | N/A | < 5% |
| NPS | Satisfaction | N/A | > 50 |
| Conversion Rate | Free → Paid | N/A | 3-5% |

### 18.4 Knowledge Quality Metrics

| Метрика | Описание | Измерение |
|---|---|---|
| Coverage | % тем задокументировано | wiki pages / code modules |
| Freshness | Средний возраст страниц | days since last edit |
| Usage | Топ-N читаемых страниц | search click-through |
| Gaps | Неотвеченные запросы | empty search results |
| Conflicts | Противоречия между страницами | conflict detection |

### 18.5 Tracking

- **GitHub:** stars, forks, issues, PRs (built-in)
- **Discord:** member count, message volume (Discord analytics)
- **Product:** anonymous telemetry (opt-in): `reefiki status --telemetry`
  - What: command used, pages count, search queries (no content)
  - Why: understand usage patterns, prioritize features
  - Privacy: opt-in, anonymized, no content, no paths
- **Revenue:** Stripe dashboard

---

## 19. Сводная карта всего проекта

```
REEFIKI Project Map
├── 📦 Core (бесплатно, open-source)
│   ├── CLI (reefiki command)
│   ├── Markdown + YAML frontmatter
│   ├── SQLite FTS5 search
│   ├── Git-based versioning
│   ├── Dual-remote publish
│   ├── Guards & hooks
│   └── Inbox, source, classify
│
├── 🔒 Security (64 findings → fix)
│   ├── MEGA-AUDIT.md
│   ├── 19 направлений
│   └── 4-фазный remediation
│
├── 🚀 Features (11 unique innovations)
│   ├── Cross-Agent Knowledge Transfer
│   ├── Knowledge Harvesting
│   ├── Staleness Radar
│   ├── Agent-as-Author
│   └── ... (7 more)
│
├── 💰 Monetization (8 revenue streams)
│   ├── Cloud ($0/$12/$29)
│   ├── Pro License ($99/yr)
│   ├── Managed Publish ($5/mo)
│   ├── Marketplace (70/30)
│   ├── API ($0/$49/$199)
│   └── Consulting ($500-5000)
│
├── 📣 Go-to-Market
│   ├── HN + Product Hunt + Reddit
│   ├── Content strategy
│   └── Partnership pipeline
│
├── 👥 Community
│   ├── Discord server
│   ├── Contributor program
│   └── Ambassador network
│
├── 🏗️ Infrastructure
│   ├── Migration from competitors
│   ├── Offline-first + conflict resolution
│   ├── Non-technical user access
│   └── License: Apache 2.0 core
│
└── 📊 Metrics & KPIs
    ├── Product (stars, pages, queries)
    ├── Community (discord, contributors)
    ├── Business (MRR, NPS, churn)
    └── Knowledge quality (coverage, freshness)
```

---

*Сгенерировано Hermes Agent, 2026-06-02*
*Обновлено: добавлены разделы 9-19 (GTM, community, moat, migration, content, partnerships, offline, license, non-tech users, metrics, project map)*
