# ROADMAP — когда расширять стек

Принцип: **никаких преждевременных оптимизаций**. Каждый следующий слой подключается только по объективному триггеру, не «на будущее».

Источник приоритетов: консенсус 6 независимых исследований (GPT-4o, Claude, DeepSeek, Gemini, Grok, Cascade) — май 2026. Подробности: `projects/reefiki/raw/research-audit-2026-05/`.
Аудит структуры репо: Kiro, май 2026 — выявил расхождения docs ↔ реальность, security-риски, дрейф шаблона.

## Фазы роста

### Phase 0 — bootstrap (сейчас)

- 0–~50 страниц wiki, до ~10 источников в `raw/`.
- Стек: только встроенный `index.md` + `wiki/<subdir>/*.md` + любой LLM-агент.
- Workflow: `/save` → `/process` → `/query` → `/harvest` → `/lint`.
- **Достаточно для одного человека и одного проекта.** Это подтверждает [гист Карпати](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Phase 0 включает обязательные улучшения, без которых дальнейший рост рискован:

#### Phase 0a — integrity gate ✅ ГОТОВО

Защита целостности данных. Obsidian используется ежедневно, одна поломка frontmatter ломает цепочку обработки.

**Что внедрено:**

1. **Pre-commit hook** — `scripts/validate_frontmatter.py` + `.pre-commit-config.yaml`.
   - Обязательные поля: `id`, `type`, `title`, `tags`, `useful_when`, `date_added`.
   - Допустимые типы: `source`, `entity`, `concept`, `synthesis`, `decision`, `skill`.
   - Запрет устаревших полей (`importance`).
   - Проверка body: `skill` содержит `## Шаги`; `decision` получает non-blocking `BODY_WARN` при отсутствии ADR-секций.
   - Проверка `index.md`: `Total pages`, `importance`, рассинхрон файлов.

2. **Obsidian Linter plugin** — lint-on-save, сортировка frontmatter.

3. **Дедупликация на save** — URL-дубликат, совпадение имени в `inbox/` и exact content hash проверяются через `scripts/reefiki.py dedup`.

4. **`.gitignore`** — workspace*.json, cache/, .trash/, *.tmp.

**Закрыто по аудиту май 2026:**
- `projects/reefiki` и `projects/metrica` прошли reality check: индексы синхронизированы, `importance` убран, `skills` учитываются.
- 17 synthesis-страниц в metrica получили валидный frontmatter.
- `.obsidian/plugins/**/main.js` убраны из git; runtime-файлы плагинов больше не тащатся в репо.

#### Phase 0b — agent metrics ✅ ГОТОВО

Сбор данных об эффективности агента.

**Что внедрено:**
1. Trigger acceptance logging в `log.md`: `trigger: harvest-proposed | accepted/declined`.
2. Query relevance tracking: `query: "..." | found: N | relevant: Y/N`.
3. Root-level и project-level `AGENTS.md` реструктурированы (критические правила в начале).

#### Phase 0c — mobile capture ✅ ГОТОВО

Telegram бот → Pipedream → GitHub Actions `inbox-capture.yml`. iOS Shortcuts как альтернатива.

Security-аудит закрыт: `inbox-capture.yml` больше не интерполирует payload напрямую в shell-строку commit message.

#### Phase 0d — reality checks ✅ ГОТОВО, повторять по триггеру

Регулярная проверка, что документы совпадают с реальностью.

**Что проверяем:**
1. `wiki/index.md` не содержит устаревших полей и совпадает с реальными файлами.
2. `Total pages` равен числу wiki-страниц.
3. `/lint` и `/reindex` учитывают `wiki/skills/*.md`.
4. Перед новыми фичами — закрыть рассинхроны docs ↔ files.

**Триггер:** перед Phase 0.5/1, после batch-импорта, после ручных правок в Obsidian.

**Статус:** `projects/reefiki` и `projects/metrica` закрыты по текущему audit pass. Повторять перед новыми фазами, batch-импортом и ручными массовыми правками.

#### Phase 0d extension — wiki health dashboard ✅ ГОТОВО

Phase 1 prep для проектов с растущей wiki: `_dashboard.md` теперь показывает backlinks count, cross-reference density и content freshness. Обновлены `_template`, `projects/reefiki` и `projects/metrica`.

#### Phase 0e — template drift prevention ✅ ГОТОВО

Выявлен аудитом май 2026. Шаблон и живые проекты расходятся при каждом обновлении шаблона.

**Что закрыто:**
- `projects/metrica/AGENTS.md` и `projects/reefiki/AGENTS.md` синхронизированы с шаблоном.
- `_dashboard.md` включён в scope `/new` и `/sync-template`.
- `.agents/skills/source-command-*` исправлены.
- `_template/wiki/index.md` и `status.md` учитывают `skills`.

#### Phase 0f — synthesis discipline ✅ ГОТОВО как gate, stale-процедура отдельно

Выявлен аудитом май 2026. В `projects/metrica` 55 synthesis + 26 skills = 81 из 108 страниц. Признак «архивации вместо дистилляции».

**Симптомы:**
- Большинство synthesis-страниц — снимки одной отладочной сессии, `use_count: 0`.
- 17 страниц без frontmatter — созданы вне контракта.
- Названия вида `*-coverage-uplift`, `*-antiflake-proof` — проектные артефакты, не переиспользуемые знания.

**Что закрыто:**
1. `/harvest` получил acceptance check для synthesis: «чем эта страница будет полезна через 3 месяца? если только как снимок — в `seen/` или `deep-research/`».
2. Старые metrica synthesis без frontmatter доведены до валидного состояния.
3. Полная stale-процедура остаётся отдельной Phase 0.6 задачей.

#### Phase 0g — memory/search/planning layer ✅ ГОТОВО

Внедрено после разбора `claude-mem`, `planning-with-files` и `agentmemory`.

**Что внедрено:**

1. `scripts/reefiki.py` — локальный CLI без внешних зависимостей.
2. SQLite FTS5 индекс `.reefiki/index.sqlite` поверх `wiki/*.md`; markdown остаётся источником истины.
3. `/query` переведён на progressive disclosure + provenance: сначала top-K, затем нужные страницы, затем timeline.
4. Privacy guard для `/save` и `/process`: секреты, бинарники, forbidden dirs, большие файлы.
5. `/status` получил машинный summary: inbox, seen, типы wiki, stale, last lint.
6. План-файлы `plans/<task>.md` для длинных задач + checksum recovery.
7. Timeline/replay через последние записи `wiki/log.md`.
8. GitHub research 2026-05-31 внедрён как безопасный local-first slice без новых dependencies:
   - `reefiki.py backlinks` строит generated backlink index: incoming/outgoing links, orphans, broken links.
   - `search` получил frontmatter/link filters: `--type`, `--tag`, `--link-to`, `--linked-by`, `--orphan`.
   - `search --chunks` добавил heading-aware FTS5 chunks с `heading_path` и snippet.
   - `review-queues --type` фильтрует конкретные очереди; link-health очереди включают `placeholder_link` и `missing_backlink`.
   - `memory golden` возвращает `misses` и `eval` как retrieval eval harness.
   - `validate_frontmatter.py --format json` возвращает `code`, `line`, `column`, `expected`, `actual` для agent/CI diagnostics.

**Отложено:**
- MCP/REST API — только после стабильного локального `/query`.
- Vector/graph слой — только если FTS5/golden дают реальные промахи; текущий live baseline `projects/reefiki` = 13/13, `misses: []`.
- Team/shared memory — только при multi-user сценарии.
- Auto-forgetting/decay — не внедрять без отдельного решения.

#### Phase 0h — agent skills governance ⚡ АКТИВНА

Внешние agent skills полезны как ускоритель, но marketplace/repo-контент не считается доверенным до аудита.

**Что внедрено:**

1. `wiki/_schema.md` описывает governance-поля для adopted skills: `source_url`, `license`, `status`, `scope`, `validation`, `risks`.
2. `validate_frontmatter.py` проверяет, что эти поля используются только у `type: skill`, а `status` входит в allowlist.
3. ADR `adopt-skill-adoption-governance` фиксирует audit-first policy.

**Текущий статус:** первые entries созданы. `keep-codex-fast` установлен как sandboxed Codex skill с `ADOPTION.md`; `agentic-delivery-gates` принят как локальный REEFIKI-native skill; `open-design` оставлен sandbox/reference/static proof only, без product runtime integration.

**External tool extension — май 2026:** link triage по code navigation и skill quality зафиксирован как governance registry, без wholesale adoption.

- `codegraph` — sandboxed candidate для project-local code navigation. Следующий допустимый шаг: выполнить `codegraph-evaluation-runbook` на 1-2 реальных codebase и записать evidence.
- `codebase-memory-mcp` — watch/deferred до чистого Windows smoke. Не менять REEFIKI runtime под него.
- `SkillOpt` — R&D reference для будущих skill quality gates. Сначала локальные gates, потом tooling.
- `taste-skill` — reference-only для улучшения skill-writing. Не устанавливать без overlap audit.
- `Understand Anything` — sandbox/watch для visual codebase/wiki knowledge graph. Не устанавливать глобально; тестировать только в isolated sandbox, если `graphify`/`codegraph`/dashboards не дают нужного onboarding view.
- Авто-gate для этого watch: `python scripts/reefiki.py tool-trigger Understand-Anything --signal "<observed signal>"`. Агент должен запускать его сам при сигналах visual graph / unknown large codebase / wiki graph / interactive onboarding.
- `ECC` — reference-only agent-operator framework. Не устанавливать и не подключать hooks/MCP/skills wholesale; брать только patterns.
- `Anthropic-Cybersecurity-Skills` — defensive reference для будущего security checklist external tools. Не устанавливать 754-skill pack; брать только schema ideas: When to Use, prerequisites, workflow, verification, mappings к MITRE/NIST/ATLAS/D3FEND/AI RMF.
- `mattpocock/skills` — reference для small/composable skill patterns. Не устанавливать wholesale; локально полезны идеи `diagnose`, `grill-with-docs`, `zoom-out`, `improve-codebase-architecture` как input для `skill-quality-gate`.
- `CloakBrowser` — restricted watch, не обычный dev-tool. Использовать только при легитимном public QA/repro, если обычный browser automation блокируется bot detection и есть явное разрешение; не применять как default для scraping/CAPTCHA/anti-bot bypass.
- `agentmemory` — runtime не внедрять: конфликтует с разделением `memoir` / `REEFIKI` / `graphify`. Брать только benchmark/status ideas, если понадобится улучшать memory UX.

**ECC patterns — когда применять.**

Полезные идеи:
- trigger gates / instincts → развивать локальный `tool-trigger`, когда external-tool candidates начинают повторяться;
- status snapshots / readiness gates → развивать `memory status --summary` и `review-queues`, если нужен portable handoff/status artifact;
- security checklist / AgentShield ideas → использовать как reference при будущем external-skill/tool security checklist;
- selective install / manifest-driven install → reference для governance, если когда-нибудь появится локальный plugin/skill installer;
- continuous learning → только как comparison point; REEFIKI остаётся `/harvest` review-first, без auto-capture.

Триггеры возврата к ECC:
- 3+ повторяющихся external-tool triage cases, где нужен общий gate вместо ручного решения;
- нужно машинно проваливать automation по readiness/status, а не только показывать отчёт;
- нужен formal security checklist перед sandbox/install внешнего tool;
- появляется задача selective install для локальных skills/plugins.

Что не делать:
- не ставить ECC в REEFIKI;
- не включать hooks/continuous learning/session memory;
- не заменять `AGENTS.md`, REEFIKI wiki, memoir, graphify или codegraph;
- не тащить большой operator framework ради 1-2 паттернов.

**Second-brain / Obsidian + Claude Code prompt — reference-only.**

Промт про “AI-augmented second brain” полезен как источник идей, но не как план немедленного внедрения. REEFIKI уже выполняет роль durable wiki/governance layer; Obsidian остаётся viewer/editor, а не отдельным memory layer.

Что можно забрать:
- preflight checklist для новых машин: Obsidian, vault path, Node/npm, Python, Ollama;
- decision matrix для будущего выбора: MCP + Smart Connections / Karpathy Wiki / full RAG;
- note-template ideas для будущего `deep-research/` и conversation/decision/insight/pattern templates;
- правила archive-not-delete, `updated`, cross-links — они совместимы с текущей governance-моделью.

Что не внедрять сейчас:
- automatic capture из каждого разговора Claude Code: это создаёт memory spam; текущий `/harvest` остаётся review-first;
- новый Obsidian/MCP/Smart Connections слой поверх REEFIKI: это дублирует `memoir`/`REEFIKI`/`graphify`;
- LanceDB/Ollama/full RAG без доказанных FTS5 misses или latency problem;
- отдельный `.claude/CLAUDE.md` как источник истины внутри vault: текущий контракт живёт в `AGENTS.md` и project command docs.

Когда возвращаться к реализации:
- при новом workspace/bootstrap — использовать только preflight checklist;
- при первом материале >5 источников — адаптировать template ideas в Phase 0.5 `deep-research/`;
- при 3+ подтверждённых `/query` misses или `/query` >8 секунд — сравнить `qmd` с Smart Connections/MCP как Phase 1 search option;
- при явной потребности в semantic search по большим архивам — сначала локальный `qmd`, full RAG только после провала более простого слоя.

**Следующий шаг:** не запускать mutating maintenance, full design runtime или external code-memory runtime автоматически. Любой apply/live runtime требует отдельного handoff/proof gate. Для `codegraph` разрешён только project-local smoke по runbook с ignored generated database.

#### Phase 0i — memory governance layer ✅ БАЗА ГОТОВА

Внедрено после узкого GitHub research по теме: как усилить REEFIKI как durable governance layer поверх уже работающих `memoir` и `graphify`, не добавляя четвёртый memory layer.

**Что закрыто:**

1. ADR `reefiki-routing-and-promotion-contract` фиксирует роли слоёв:
   - `memoir` = short working memory
   - `graphify` = structure map
   - `REEFIKI` = durable knowledge/governance
2. Concept `memoir-to-reefiki-promotion-gate` фиксирует typed promotion `memoir -> REEFIKI`.
3. Concept `reefiki-review-queue-contract` фиксирует review queues и их semantics.
4. Synthesis `reefiki-memory-governance-first-automation-steps` фиксирует первые automation steps.
5. `scripts/reefiki.py` получил working read-only helpers:
   - `promote-dry-run`
   - `review-queues`
   - `review-queues --write-report`
   - `promote-dry-run --write-draft`
6. Confirm-only apply layer добавлен:
   - `promote-dry-run --apply-draft <path> --yes`
7. Первый pass по false positives уже сделан:
   - prose `[[wikilinks]]` больше не даёт fake `conflict_review`
   - `duplicate_candidate` стал консервативнее по типам страниц
8. Второй pass по `duplicate_candidate` закрыт:
   - shared-source overlap больше не считается high-confidence duplicate при широком title overlap вроде governance/adoption.
9. `conflict_review` расширен beyond missing related pages:
   - явные секции `## Conflicting claims` / `## Conflict` с wikilinks попадают в review queue без LLM и auto-merge.
10. Link-health очереди закрыты как безопасный governance slice:
   - `placeholder_link` для wikilinks на отсутствующие страницы
   - `missing_backlink` для входящих ссылок без обратной связи
   - `review-queues --type <queue>` для точечного triage

**Что дальше:**

- не строить новый memory layer;
- не включать auto-promotion и auto-merge;
- сначала чистить только доказанный noise/backlog:
  - `needs_verification`
  - `orphan_review`
  - `placeholder_link`
  - `missing_backlink`
- дальше улучшать governance UX и не добавлять semantic conflict detection без явных markers/evidence.

---

### Phase 0.5 — deep-research/ (отдельный тир для больших исследований)

**Триггер любой из:**
- Материал не помещается в одну wiki-страницу (>5 источников, развёрнутое сравнение).
- Нужен архив хода исследования (промежуточные выводы, отброшенные варианты).
- Результат слишком сырой для wiki, но слишком ценный для `seen/`.
- Synthesis-страниц типа «снимок сессии» накопилось >10 — лучше в `deep-research/`.

**Что подключаем:** папку `deep-research/` в каждом проекте. Структура:

```
deep-research/<topic-slug>/
  brief.md          # вопрос, scope, useful_when
  sources.md        # список источников + статус (прочитано/нет)
  report.md         # structured synthesis
  _meta.yaml        # дата, тема, статус (open/closed)
```

**Связь с wiki:** по завершении (статус `closed`) — дистиллировать итог в wiki-страницу (concept/decision/synthesis) и сослаться на `deep-research/<slug>/` как источник.

**Статус:** шаблон `_template` создан 2026-05-31 и применён к `projects/reefiki`. Existing проекты вне текущего scope не менялись автоматически.

**Стоимость:** 0. Просто папка и конвенция.

---

### Phase 0.6 — stale pages + log rotation

**Триггер:** wiki > 50 страниц ИЛИ `log.md` > 500 строк ИЛИ stale pages > 5 штук.

> ⚠ `projects/metrica` уже на 108 страницах — триггер активен. Проверить log.md на объём.

**Stale page procedure** (3 исхода):
1. `use_count=0` + нет входящих ссылок → `seen/` с `reason: stale`.
2. `use_count=0` + есть входящие → переформулировать `useful_when`.
3. `use_count>0` + не менялась >90 дней → skill verification.

**Статус:** процедура зафиксирована в `/review-queues` command docs; live `review-queues` по `projects/reefiki` и `projects/metrica` на 2026-05-31 пустой. Массового cleanup сейчас нет.

**Log rotation:** при достижении порога — `git mv log.md logs/log-YYYY-MM.md`, новый `log.md` со ссылкой на архив. Append-only сохраняется.

**Стоимость:** 0.

---

### Phase 1 — local search (`qmd`)

**Триггер любой из:**
- `wiki/index.md` > **100 страниц** ИЛИ wiki содержит >**120 страниц** (снижен с 150/800 строк — `metrica` уже на 108).
- `/query` стабильно отвечает дольше 8 секунд (по log.md).
- 3+ ложных промаха подряд (`/query` отвечает «нет в базе», а нужная страница в wiki есть).
- Домен с сильной синонимией (русский+английский+транслит).

> ⚠ `projects/metrica` приближается к триггеру. Рекомендуется запустить golden query pack (T-18) для замера до активации.

**Current gate after GitHub research slice:** сначала использовать встроенный FTS5 + heading chunks + `memory golden` misses. `qmd`, vectors, rerankers или semantic search подключать только если golden/real `/query` показывают повторяемые misses или latency.

**Что подключаем:** [`qmd`](https://github.com/tobi/qmd) — локальный BM25+вектор-поиск по markdown с MCP-сервером. Бесплатно, локально, рекомендация самого Карпати.

**Шаги интеграции:**

```pwsh
cargo install qmd                              # либо winget install qmd
qmd serve --root wiki --port 7300              # внутри проекта
```

Затем в `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "qmd": { "command": "qmd", "args": ["mcp", "--root", "wiki"] }
  }
}
```

В `.claude/commands/query.md` шаг 1 заменить:

> ~~Прочитать `wiki/index.md`. Оценить каждую запись...~~
> Вызвать MCP-инструмент `qmd.search "<запрос>"`. Получить топ 5–10 кандидатов с relevance score.

Остальные шаги без изменений. Агент продолжает читать полные файлы и синтезировать.

**Стоимость:** 0. **Откат:** удалить MCP-блок, инструкция в `query.md` есть откатиться на index.md.

**Опция при активации Phase 1:** confidence tagging для связей между страницами (по образцу [graphify](https://github.com/safishamsi/graphify)): `EXTRACTED` / `INFERRED` / `AMBIGUOUS`. Добавить в `_schema.md` если появятся cross-reference edges. Анализ: май 2026, `seen/`.

### Phase 2 — cold storage для тяжёлых архивов (NotebookLM)

**Триггер любой из:**
- В `raw/` 30+ PDF, или транскрипты часовых видео общим объёмом >5 MB текста.
- `/process` начинает читать одиночный файл из `raw/` дольше 20 секунд (большие токены).
- Хочешь генерировать инфографики/подкасты по материалам — это native-фича NotebookLM.

**Что подключаем:** Google NotebookLM как «холодное хранилище» + ресерч-движок. Бесплатно, требует Google-аккаунт.

**Шаги интеграции** (по [cheatsheet-notebooklm](https://gomymy64.github.io/cheatsheet-notebooklm/)):

1. Скачать NotebookLM-skill (CLI) с Google Drive автора шпаргалки.
2. `nlm login` → авторизация в Google.
3. Создать в NotebookLM notebook на проект (например, `reef`), загрузить туда тяжёлые источники из `raw/`.
4. В `.claude/commands/` добавить новую команду `/enrich <тема>`:
   - вызывает skill: `nlm query <notebook-id> "<тема>"`,
   - получает выжимку,
   - кладёт в `wiki/synthesis/<slug>.md` с frontmatter `sources: [notebooklm:<notebook-id>]`,
   - обновляет `index.md`.
5. В `_schema.md` дополнить тип `source` поддержкой URI `notebooklm:...`.

**Стоимость:** 0 (бесплатно для личного), но веб-доступ обязателен.

### Phase 3 — managed vector DB (Pinecone) — почти наверняка не нужно

**Триггер ВСЕХ ОДНОВРЕМЕННО:**
- >10 000 страниц wiki ИЛИ >5 проектов с переплетающимися темами.
- Командное использование (>3 человек), нужна низкая латентность для concurrent queries.
- `qmd` локально не справляется (профилировано: latency >5s на p95, не помогает шардинг).
- Готов платить $25–$70/мес минимум.

**Что подключаем:** Pinecone serverless (либо Weaviate Cloud / Qdrant Cloud — выбирается под бюджет).

**Шаги интеграции (схематично):**

1. Pinecone account, API key.
2. Скрипт ingest: `wiki/**/*.md` → embedding (OpenAI `text-embedding-3-large` или Voyage `voyage-3`) → upsert в индекс.
3. Embedding-pipeline в `/process`: после создания страницы автоматически embed + upsert.
4. MCP-сервер-обёртка над Pinecone (есть готовые в комьюнити).
5. В `query.md` шаг 1 — `pinecone.query` вместо `qmd.search`.

**Стоимость:** Pinecone serverless ~$25/мес минимум + embeddings $0.02–$0.13 за миллион токенов. Для wiki из 1000 страниц по 2k токенов — $0.04–$0.26 разово на индексацию + ~$5/мес запросов.

**Альтернативы перед прыжком на Pinecone:**
- Раздробить большой проект на несколько мелких в `projects/<name>/` (изоляция = меньше индекс на проект).
- Локальный SQLite-vec (`sqlite-vss`, `chromadb` локально) — вектор-поиск без облака.

## Сводная таблица фаз

| Фаза | Статус | Триггер | Effort | Стоимость |
|---|---|---|---|---|
| 0 bootstrap | ✅ активна | — | — | 0 |
| 0a integrity gate | ✅ готово | Obsidian ежедневно | 2 часа | 0 |
| 0b agent metrics | ✅ готово | Нет данных об эффективности | 1 час | 0 |
| 0c mobile capture | ✅ готово | 3+ захватов/неделю | 3 часа | 0 |
| 0d reality checks | ✅ готово, повторять | перед новыми фазами/массовыми правками | 1 час | 0 |
| 0e template drift | ✅ готово | шаблон и проекты разошлись | 1 час | 0 |
| 0f synthesis discipline | ✅ gate готов | 81/108 страниц metrica — архивация | 2 часа | 0 |
| 0.5 deep-research | ✅ шаблон готов, применять по триггеру | >5 источников / >10 session-synthesis | 30 мин | 0 |
| 0.6 stale + log rotation | ✅ процедура готова, повторять по триггеру | metrica >50 страниц уже | 1 час | 0 |
| 0g memory/search/planning | ✅ готово | external memory audit | 2 часа | 0 |
| 0h skills governance | ⚡ активна | внешний skill предлагается к внедрению | 1 час | 0 |
| 1 qmd search | ⏸ отложено | только если FTS5 мало | низкий | 0 |
| 2 NotebookLM | ❌ | 30+ PDF / часы видео | средний | 0 |
| 3 Pinecone | ❌ | >10k стр + команда + qmd не тянет | высокий | от $25/мес |

## Принципы при расширении

1. **Сохранять обратную совместимость.** Wiki в markdown не меняется — добавляется только индекс/обёртка.
2. **Один откат-коммит.** Каждое подключение нового слоя — отдельный коммит, чтобы можно было `git revert` если хуже стало.
3. **Замерить ДО.** Перед подключением — снять метрики (`/query` p50/p95, размер index.md). Без метрик неясно, помогло или нет.
4. **MCP-first.** Любой новый слой подключается через MCP-сервер, а не хардкодом в `.claude/commands/*.md`. Это упрощает откат.
5. **Чем выше слой, тем реже трогается.** Pinecone не должен быть в горячем пути локального проекта на одного человека.
6. **Docs ↔ reality sync.** Перед каждым новым спринтом — прогнать `validate_frontmatter.py` на всех индексах. Закрытая задача ≠ закрытая проблема без проверки.
