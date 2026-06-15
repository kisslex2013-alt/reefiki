# ROADMAP — когда расширять стек

Принцип: **никаких преждевременных runtime-слоёв**. Новый backend, MCP-daemon, vector/rerank, cloud sync или marketplace work подключается только по объективному триггеру, не «на будущее».

Но roadmap не должен блокировать проверяемое развитие. Если есть маленький local-first slice с тестами, rollback и без смены source of truth, его можно делать как bounded experiment: preflight, benchmark, report, adapter smoke, docs/product packaging или review-queue cleanup.

Источник приоритетов: консенсус 6 независимых исследований (GPT-4o, Claude, DeepSeek, Gemini, Grok, Cascade) — май 2026. Подробности: `projects/reefiki/raw/research-audit-2026-05/`.
Аудит структуры репо: Kiro, май 2026 — выявил расхождения docs ↔ реальность, security-риски, дрейф шаблона.
Полный аудит июня 2026 и нормализованный action plan: [docs/Audit_07.06.26/AUDIT_SYNTHESIS_ACTION_PLAN.md](docs/Audit_07.06.26/AUDIT_SYNTHESIS_ACTION_PLAN.md).
Errata к аудиту: [docs/Audit_07.06.26/REEFIKI_AUDIT_ERRATA.md](docs/Audit_07.06.26/REEFIKI_AUDIT_ERRATA.md).

## Текущий порядок выполнения после аудита 2026-06

До любых новых product/search слоёв порядок такой:

1. Safety foundation
2. CI и verification gates
3. Packaging, installability, legal baseline
4. Concurrency и integrity
5. Markdown-native context/query улучшения
6. Governance UX и health tooling
7. Wizard / dashboard / mobile / Obsidian DX
8. Advanced search / MCP / cloud / ecosystem

Это важнее старой логики "сразу добавлять новый слой по идее". Аудит подтвердил, что текущие реальные блокеры — не недостаток фич, а незакрытые path/publish/CI/concurrency риски.

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

**Skill products / adapter follow-up — июнь 2026:** portable base skills и тонкий read-only adapter layer опубликованы как proof-gated artifacts: `skills/base/*/SKILL.md`, `adapters/*`, adapter proof gates и demo proof tests. Это не live runtime integration: `hooks.json`, Claude commands, Cursor rules, Hermes runtime prompt, global config, marketplace/package install и новый memory runtime остаются вне scope без отдельного explicit approval. Подробности: [base skills](docs/skill-products/BASE_SKILLS.md), [agent adapters](docs/skill-products/AGENT_ADAPTERS.md), [skill products](docs/skill-products/SKILL_PRODUCTS.md). Backlog item: `TASKS.md` T-104 закрыт.

**Agent Readiness / Skill Recommendation — июнь 2026:** read-only repo advisor опубликован как user-facing MVP. `agent-readiness --repo` и alias `skills recommend --repo` делают deterministic scan внешнего git repo и выдают план по четырём блокам: Skills, Rules, Adapters, Hooks. Это всё ещё не auto-install и не runtime integration: target repo mutation, marketplace, paid gating, live hooks/adapters и global runtime config остаются вне scope. Подробности: [Agent Readiness spec](docs/skill-products/AGENT_READINESS_SPEC.md) и [README block reference](docs/skill-products/AGENT_READINESS_README_BLOCK.md). Backlog item: `TASKS.md` T-105 закрыт.

**External tool extension — май 2026:** link triage по code navigation и skill quality зафиксирован как governance registry, без wholesale adoption.

- `codegraph` — installed/disposable code navigation для project-local use. Первый REEFIKI smoke закрыт в T-75; следующий smoke на другом codebase делать только при конкретном code-navigation gap, через `codegraph-evaluation-runbook`, с ignored `.codegraph/` и без `codegraph install`.
- `codebase-memory-mcp` — sandboxed после чистого Windows binary smoke 2026-06-10: manual release zip, checksum, isolated `CBM_CACHE_DIR`, temp repo index/search/architecture JSON output. Не менять REEFIKI runtime, PATH, MCP config или agent hooks под него без отдельного proof gate и конкретного code-navigation gap.
- `SkillOpt` — R&D reference для будущих skill quality gates. Сначала локальные gates, потом tooling.
- `taste-skill` — reference-only для улучшения skill-writing. Не устанавливать без overlap audit.
- `Understand Anything` — sandbox/watch для visual codebase/wiki knowledge graph. Не устанавливать глобально; тестировать только в isolated sandbox, если `graphify`/`codegraph`/dashboards не дают нужного onboarding view.
- Авто-gate для этого watch: `python scripts/reefiki.py tool-trigger Understand-Anything --signal "<observed signal>"`. Агент должен запускать его сам при сигналах visual graph / unknown large codebase / wiki graph / interactive onboarding.
- `ECC` — reference-only agent-operator framework. Не устанавливать и не подключать hooks/MCP/skills wholesale; брать только patterns.
- `Anthropic-Cybersecurity-Skills` — defensive reference для будущего security checklist external tools. Не устанавливать 754-skill pack; брать только schema ideas: When to Use, prerequisites, workflow, verification, mappings к MITRE/NIST/ATLAS/D3FEND/AI RMF.
- `mattpocock/skills` — reference для small/composable skill patterns. Не устанавливать wholesale; локально полезны идеи `diagnose`, `grill-with-docs`, `zoom-out`, `improve-codebase-architecture` как input для `skill-quality-gate`.
- `CloakBrowser` — restricted watch, не обычный dev-tool. Использовать только при легитимном public QA/repro, если обычный browser automation блокируется bot detection и есть явное разрешение; не применять как default для scraping/CAPTCHA/anti-bot bypass.
- `agentmemory` — runtime не внедрять: конфликтует с разделением `memoir` / `REEFIKI` / `graphify`. Брать только benchmark/status ideas, если понадобится улучшать memory UX.

**Codex App tooling watchlist durable layer — июнь 2026:** operational watchlist остаётся в `C:\Users\kissl\.codex\rules\tooling-watchlist.md`, а REEFIKI хранит только durable governance.

Что закрыто:
- ADR `external-tool-adoption-governance` фиксирует правило: watchlist first, REEFIKI durable decisions, без wholesale install и без новых memory/wiki/orchestration runtimes при overlap с `memoir`, REEFIKI, `graphify`, `codegraph`.
- Registry `external-tool-watchlist` хранит durable status/scope/overlap/risk/validation/decision/next_action для известных tools.
- Skill `triage-external-tool` задаёт reusable workflow: primary source check -> overlap/conflict check -> smallest valid form -> validation -> watchlist vs REEFIKI routing.

Начальные registry decisions:
- `codegraph` — installed/disposable code navigation.
- `Odysseus` — dogfood candidate: внешний workspace/behavioral bench для проверки, что REEFIKI работает как portable context control plane. Не dependency, не MCP/server, не runtime. Dogfood brief: `docs/ODYSSEUS_DOGFOOD.md`.
  - 2026-06-12 dogfood status: WSL CI-like diagnostic separated real cross-platform failures from Windows-only portability/env noise. The real pair was fixed in Odysseus PR `pewdiepie-archdaemon/odysseus#4093` from fork branch `kisslex2013-alt:codex/odysseus-cross-platform-fixes`; next step is CI/review follow-up, not a new REEFIKI runtime layer.
  - Windows portability/env cleanup remains a separate trigger-gated Odysseus task. It should start only if PR review/CI or an explicit Windows support decision requires it, and it must not be mixed with REEFIKI MCP/vector/static export work.
- `spec-kit` — useful template source.
- `claude-code-harness`, Claude workflows, `wshobson/agents`, `stop-slop`, `humanizer` — reference/reference-only.
- `markitdown` — use-case install для artifact ingestion.
- `crawl4ai` — sandbox watch для web ingestion pipeline `harvest -> normalize -> save`; запускать только после security gates и concrete batch.
- `btop` — optional utility.
- `headroom` — sandbox watch.
- `vellum-assistant` — reference-only для governance/traceability/operational-boundary ideas.
- `telegram-agent`, `mcp-telegram` — deferred/restricted.
- `ruflo` — ignore for now.

Coverage guard:
- `docs/Audit_07.06.26/AUDIT_RECOMMENDATION_COVERAGE.md` — обязательный checkpoint для audit/report batches: каждая named recommendation должна получить durable destination или explicit rejection.

Что не делать:
- не переносить весь watchlist в REEFIKI;
- не менять Codex global config из REEFIKI-задачи;
- не добавлять MCP servers или global installs без отдельного proof gate;
- не принимать jailbreak/restriction-bypass/social-post ideas как durable governance.

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

**Следующий шаг:** не запускать mutating maintenance, full design runtime или external code-memory runtime автоматически. Любой apply/live runtime требует отдельного handoff/proof gate. Для `codegraph` не нужен новый smoke без конкретного code-navigation gap; если gap появился, разрешён только project-local smoke по runbook с ignored generated database.

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

#### Phase 0j — audit-driven stabilization ⚡ АКТИВНА

Июньский аудит меняет ближайший execution order. До новых больших слоёв нужно закрыть кодовую базу, publish safety и install story.

**2026-06-08 closeout:** P0/P1 stabilization baseline закрыт в `main`: safety, CI, packaging/legal, concurrency/integrity, markdown query L0, governance UX и core docs имеют код/доки и regression gates. Дальше не поднимать новые runtime-слои без триггера; ближайшая работа — только проверяемые P2/backlog slices или точечное hardening по новым findings.

**Product-readiness follow-up — 2026-06-11:** product analysis подтвердил, что после закрытия P0/P1 следующий полезный слой — не новый memory/search runtime, а превращение REEFIKI из личного инструмента в проверяемый portable product. Приоритеты:

1. **CI matrix для реальной целевой среды.** Текущий CI всё ещё `ubuntu-latest`; добавить Windows/macOS lanes и оставить Ubuntu как baseline, чтобы ловить path/newline/symlink/junction regressions до publish.
2. **Agent-flow E2E и conformance.** Проверять не только Python helpers, но и реальные contract flows: `/save`, `/process`, `/query`, `/harvest`, `/status`, publish/guard gates и agent compatibility checklist.
3. **Installability.** Довести `pyproject`/CLI entrypoint до `pipx` или эквивалентного one-command local install, без добавления runtime dependencies и без изменения markdown source-of-truth.
4. **Модульность CLI.** `scripts/reefiki.py` вырос в монолитный control plane; разносить его в пакет `reefiki/` нужно постепенно, сохраняя существующий CLI и import surface. Первый критерий — не “красота”, а снижение review/blast radius: `cli`, `index/search`, `memory`, `publish/guards`, `agent_readiness`.
5. **Onboarding wizard.** Поверх существующих `QUICKSTART.md` и core docs нужен короткий guided path: создать/подключить проект, сохранить источник, разобрать копилку, спросить wiki, выполнить harvest.
6. **MCP/REST entrypoints.** Делать только после installability и conformance gates: минимальный набор `query`, `save`, `status` поверх существующего CLI, без отдельного memory runtime.
7. **Cross-project query/synthesis.** Разрешать только как read-only orchestration поверх project isolation: сначала route/lookup, затем synthesis with provenance; durable writes всё равно идут в явно выбранный project.

Не переносить повторно в backlog уже закрытые claims из анализа: `.gitattributes`/CRLF baseline, publish content scan, `GLOBAL_MEMOIR_STORE` portability, SQLite busy timeout/index lock и Agent Readiness MVP уже закрыты в `main`.

**P0 — закрыть немедленно:**

1. **Safety foundation**
   - Общая containment helper для локальных путей вместо точечных проверок. Закрыто 2026-06-08: `repo_path_in_scope()` централизует repo-relative scope checks для guard/harvest/publish paths.
   - Fail-closed runtime guard для `scripts/public-snapshot.private-projects.txt`: block если файл missing, empty или не покрывает все реальные `projects/*` кроме `_template`. Закрыто 2026-06-08: `publish-task` блокирует missing/empty/incomplete inventory.
   - Исправление `escape_fts()` и FTS crash cases. Закрыто 2026-06-08: keyword tokens quoted, punctuation-only query returns empty results, regression tests added.
   - Content-based secret scan перед `publish-task` и `harvest-commit`. Закрыто 2026-06-08: `publish-task` сканирует changed paths, `harvest-commit` сканирует target wiki paths, а filtered public snapshot сканирует итоговые staged public files в dry-run и перед push/resume.
   - Secret scanning hook в `.pre-commit-config.yaml`. Закрыто 2026-06-08: hook `reefiki-secret-scan` запускает `python scripts/reefiki.py secret-scan`.
   - Timeout для subprocess вызовов. Закрыто 2026-06-08: production `subprocess.run()` вызовы имеют `SUBPROCESS_TIMEOUT_SECONDS`; regression test проверяет отсутствие пропущенных timeout.
   - Portable default для `GLOBAL_MEMOIR_STORE`. Закрыто 2026-06-08: `memoir_store_path()` использует env overrides, существующий Codex store, затем `LOCALAPPDATA`/`XDG_DATA_HOME`.
   - Источники: `docs/Audit_07.06.26/REEFIKI_SECURITY_AUDIT.md`, `docs/Audit_07.06.26/SECURITY-AUDIT.md`, `docs/Audit_07.06.26/REEFIKI_AUDIT_ERRATA.md`.

2. **CI и verification**
   - GitHub Actions для frontmatter validation, pytest, memory golden. Закрыто 2026-06-08: `.github/workflows/ci.yml` запускает validator, `pytest` и `memory golden` на push/PR.
   - Тесты для `escape_fts`, path containment, publish safety, durable apply path. Закрыто 2026-06-08: regression suite покрывает эти flows.
   - Реальные git fixture tests для publish/harvest flows. Закрыто 2026-06-08: tests строят временные git repos для harvest isolated index, publish classification, resume и public snapshot scan.
   - Источники: `docs/Audit_07.06.26/REEFIKI_AUDIT.md`, `docs/Audit_07.06.26/REEFIKI_AUDIT_RU.md`, `docs/Audit_07.06.26/REEFIKI_EXTENDED_AUDITS.md`.

3. **Packaging и legal baseline**
   - `LICENSE`. Закрыто 2026-06-08: Apache License 2.0 добавлен в корень.
   - `pyproject.toml` с `requires-python >= 3.11`. Закрыто 2026-06-08: packaging baseline и dev extras добавлены.
   - Явное разделение прав на code vs wiki content. Закрыто 2026-06-08: README фиксирует Apache 2.0 для кода и ownership пользователя для wiki/raw/inbox/seen content.
   - Источники: `docs/Audit_07.06.26/01_LICENSING.md`, `docs/Audit_07.06.26/ADDITIONAL-AUDIT.md`, `docs/Audit_07.06.26/reefiki-audit.md`.

4. **Concurrency и integrity**
   - `busy_timeout` и context manager для SQLite. Закрыто 2026-06-08: production SQLite connections идут через `sqlite_connection()`.
   - Advisory lock для `build_index()`. Закрыто 2026-06-08: `index_lock()` сериализует rebuild.
   - Атомарное создание inbox/plan/promotion файлов. Закрыто 2026-06-08: new workflow/promotion draft writes используют temp file + replace.
   - Integrity checks и `doctor`/health command. Закрыто 2026-06-08: `doctor` остаётся integrity gate, `health` показывает practical metrics.
   - Источники: `docs/Audit_07.06.26/CONCURRENCY-AUDIT.md`, `docs/Audit_07.06.26/BACKUP-RECOVERY-AUDIT.md`, `docs/Audit_07.06.26/04_DISASTER_RECOVERY.md`, `docs/Audit_07.06.26/10_KNOWLEDGE_HEALTH_METRICS.md`.

**P1 — сразу после P0:**

1. **Markdown-native query improvements**
   - `abstract` как L0 summary field.
   - `_overview.md` для `wiki/<subdir>/`.
   - Обновление `/query`: abstract-first, потом только нужные страницы.
   - 2026-06-08 baseline: `abstract` описан в schema и добавлен в index/search; `_overview.md` добавлены как служебные карты разделов для `_template` и `projects/reefiki`; `/query` docs обновлены на abstract-first flow.
   - 2026-06-10 follow-up: `search --format json --output compact|files` добавлен для progressive disclosure без загрузки полного body, сохраняя full JSON как default для совместимости.
   - Остаток: selectively populate `abstract` у реально используемых страниц и проверить, снижает ли это чтение полных страниц в live `/query`.
   - Источники: `docs/Audit_07.06.26/19_claude_openviking-for-reefiki-1.md`, `docs/Audit_07.06.26/OPENVIKING_IDEAS_FOR_REEFIKI.md`.

2. **Governance UX**
   - `schema_version`.
   - Validator check: `id == filename`.
   - Practical health metrics, а не декоративный score-only слой.
   - 2026-06-08 baseline: `_domain.md` получил `schema_version: "1.0"`; validator проверяет schema_version проекта и блокирует `id`/filename mismatch.
   - 2026-06-08 health baseline: `reefiki.py health` больше не alias `doctor`; он возвращает practical metrics, warnings и recommendations поверх doctor outcome.
   - Остаток: status/lint surfacing и trend snapshots только если появится реальная потребность в динамике.
   - Источники: `docs/Audit_07.06.26/08_SCHEMA_MIGRATIONS.md`, `docs/Audit_07.06.26/10_KNOWLEDGE_HEALTH_METRICS.md`, `docs/Audit_07.06.26/REEFIKI_AUDIT_RU.md`.

3. **Core docs**
   - `QUICKSTART.md`
   - `docs/obsidian-setup.md`
   - `docs/mobile-capture.md`
   - `docs/RECOVERY.md`
   - 2026-06-08 baseline: добавлены четыре user-facing runbook-файла и ссылки из README/COMMANDS; runtime mobile/backup automation не внедрялась.
   - Остаток: `.obsidian/app.json` / `graph.json`, mobile auth implementation и backup command — только отдельными scoped задачами после документационного baseline.
   - Источники: `docs/Audit_07.06.26/05_UX_ACCESSIBILITY.md`, `docs/Audit_07.06.26/06_MOBILE_CAPTURE.md`, `docs/Audit_07.06.26/07_OBSIDIAN.md`, `docs/Audit_07.06.26/04_DISASTER_RECOVERY.md`.

**P2 — только после зелёного P0/P1:**

1. Minimal read-only dashboard.
   - 2026-06-08 first slice: `review-queues --summary` добавлен как компактный read-only governance dashboard для counts, top pages, sample pages и next action перед triage.
   - 2026-06-08 one-way slice: `review-queues` поддерживает `## Intentional one-way inbound links`, чтобы осознанные one-way references не оставались вечным `missing_backlink` шумом.
   - 2026-06-08 detail-output slice: `review-queues --type <queue> --limit N` ограничивает text output и показывает hidden-count hint; full triage остаётся через `--write-report`.
   - 2026-06-08 status-next slice: `memory status --summary` показывает `next_action`, когда open gate требует `review-queues --summary` или promotion inbox review.
   - 2026-06-08 first triage pass: top pages `adopt-skill-adoption-governance` и `reefiki-routing-and-promotion-contract` разобраны bounded-pass style: часть links reciprocal, часть explicit one-way.
   - 2026-06-08 second triage pass: top pages `global-memory-orchestration-cli` и `knowledge-capture-decision-tree` разобраны тем же bounded-pass style.
   - 2026-06-08 dashboard slice: `reefiki.py dashboard` объединяет `health` и `review-queues --summary` в один read-only operator view с `next_action`, не меняя queue semantics.
2. Memory reflection candidate.
   - 2026-06-09 idea review: "dreaming" полезен только как read-only reflection/report поверх существующих gates, не как background daemon или auto-writer.
   - Boundary doc: `docs/MEMORY_REFLECTION.md`.
   - Допустимый первый slice: `memory reflect --project <name> --since <ref-or-date>` собирает `memory diff`, `health`, `review-queues --summary`, `memory status --summary`, `memory pack --strict` и `promotion-inbox` в один report.
   - Write mode только `plans/reflection-YYYY-MM-DD.md`; никаких auto-apply, `raw/sessions/`, cron, IDE API, schema-wide `status`/`expires`, vector DB или нового runtime.
   - Триггер: operator repeatedly вручную склеивает 3+ existing reports, либо `review-queues`/promotion/diff gates дают шумный next-step без единого prioritized report.
   - 2026-06-10 first implementation: `memory reflect` добавлен как read-only CLI report с text/json output, candidate/blocked actions и optional `--write-report` только в `plans/reflection-YYYY-MM-DD.md`; live smoke на `projects/reefiki` показывает следующий safe action `review-queues --type missing_backlink`.
3. Wizard.
4. `_user/` formalization.
5. `context-pack` / `why`.
   - 2026-06-08 routing slice: `memory route/explain/pack` для roadmap/backlog/phase/review-queue intents выбирает REEFIKI как primary layer, а memoir оставляет secondary, чтобы context-pack объяснял durable project-governance scope корректно.
   - 2026-06-08 strict-fallback slice: `memory pack --strict` больше не падает raw traceback при lookup/golden SQLite storage error; pack сохраняет critical context и возвращает structured strict fail reasons.
6. Negative knowledge / `antipattern`.
7. Product-readiness backlog ✅ ГОТОВО
   - 2026-06-12 closeout: Sprint 20 closed the product-readiness slice in `TASKS.md` as T-108..T-116.
   - Closed baseline: CI matrix on Windows/macOS/Linux, agent-flow E2E/conformance, one-command local install, incremental `scripts/reefiki.py` package split, onboarding wizard, local JSON adapter for future MCP/REST wrappers, read-only cross-project query/synthesis with provenance, product-positioning harvest and local Codex Workspace Ops Board.
   - 2026-06-12 product surface pivot: the baseline is now strong enough to build product-facing surfaces without waiting for three external use cases. The next product work should package what already works: public demo/static docs, one-command install landing, local dashboard demo, managed-sync decision/spec and marketplace/GTM readiness pack. This does not authorize cloud accounts, managed sync backend, marketplace submission, vector search or a new runtime.
8. Workflow fail-closed hardening ✅ ГОТОВО
   - Trigger: post-Sprint 20 workflow audit (`docs/AUDIT_WORKFLOW_2026-06-12.md`) plus live `/process` evidence showed that some safety contracts are still markdown-discipline rather than operation-aware machine gates.
   - Accepted findings: broad staging in command docs, missing operation-specific `guard-staged` profiles, append-only `wiki/log.md` not machine-checked, `raw/` immutability not machine-checked, cleanup/publish JSON surfaces need clearer structured evidence.
   - Downgraded findings: `scripts/reefiki.py` is no longer a 200KB monolith after T-111; `privacy` command exists; `--public-snapshot` on private-only is an API clarity issue, not an immediate leak if snapshot guards pass; client-specific Claude hooks are adapter-layer safety, not the primary portable guard.
   - Implementation order: normalize audit into backlog, fix command contracts first, then add `guard-staged --mode process|harvest|docs|code`, then add log/raw guards, then polish publish/cleanup evidence.
   - 2026-06-12 closeout: Sprint 21 closed the batch in T-117..T-122. `guard-staged` now has operation profiles, append-only log and raw immutability checks; publish/cleanup JSON exposes structured evidence; coordination-owner registry is designed but deferred.
   - Non-goals: no new memory/runtime layer, no broad hook install as the first fix, no single mega-refactor of all workflow code.

**Не поднимать как runtime раньше времени:**

- MCP server
- vector/hybrid search
- managed cloud sync/publish
- marketplace / GTM work

Причина:
- эти runtime-слои не нужны, чтобы начать product-facing packaging, demo и install story;
- cloud/sync/vector/marketplace submission могут спрятать local-first value под новой сложностью, если прыгнуть сразу в backend/runtime.

Что разрешено сейчас как product development:
- public demo/static docs surface over existing markdown/docs;
- install landing around the already-smoked `pipx install` / checkout install paths;
- product-facing local dashboard demo over existing `dashboard` / `ops-dashboard`;
- polished website / landing surface over existing README, install docs and mascot assets;
- managed sync decision/spec with threat model and local-first boundaries, without backend implementation;
- marketplace/GTM readiness pack, without marketplace submission or paid-gating work.

**Website / landing slice: июнь 2026.**

Цель: дать REEFIKI публичную product-facing страницу, которая продолжает README, но быстрее объясняет value: chat noise -> distillation gate -> reusable project memory -> handoff next agent.

Research direction:
- open-source landing pages выигрывают, когда сразу дают strong hero, install/docs/GitHub CTA, trust signals, product proof and README continuity;
- для REEFIKI лучше работают mascot-led explanation, animated distillation flow, compact markdown-memory cards and local-first safety proof;
- не подходят generic AI SaaS gradients, stock dashboards, cloud-memory обещания и claims без текущих docs/tests.

Implementation boundary:
- static `site/` surface first, no new frontend build chain;
- use existing `assets/reefiki-hero-mascot.png`, `assets/reefiki-mascot.png`, token economy and architecture assets;
- missing mascot scenes stay as documented prompts/placeholders until dedicated image generation.

2026-06-14 status: first static landing implemented in `site/`, verified locally on desktop/mobile with Chrome/Playwright; deployment/push remains a separate approval step.

**Active backlog unlock — 2026-06-14.**

Landing thread closed and released `ROADMAP.md` / `TASKS.md` ownership. Near-term development should now prefer safe, testable growth over waiting for vague future triggers.

Allowed next slices:
- qmd retrieval preflight and benchmark as sandbox/eval only, comparing against current FTS5/golden before any runtime adoption;
- local adapter and integration smokes over the existing CLI surface, without daemon or public API commitment;
- review-queue and link-confidence reports that improve wiki governance without schema churn first;
- publish/deploy decisions through existing dry-run evidence, without push/deploy unless explicitly approved.

Still blocked without separate explicit approval:
- running qmd as MCP/server runtime in the normal query path;
- vector/rerank/model downloads or semantic search as a default dependency;
- managed cloud sync/backend/account system;
- marketplace submission, paid gating or external analytics;
- global agent config/hooks changes.

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

**Важно после аудита 2026-06:** перед активацией `qmd` сначала закрыть Phase 0j P0/P1. Июньский аудит не подтверждает, что search-layer сейчас главный bottleneck. Он подтверждает, что safety/CI/concurrency ещё не закрыты.

**Current gate after GitHub research slice:** сначала использовать встроенный FTS5 + heading chunks + `memory golden` misses. `qmd`, vectors, rerankers или semantic search подключать только если golden/real `/query` показывают повторяемые misses или latency.

2026-06-14 update: qmd уже не просто абстрактная идея. В wiki есть synthesis `qmd-retrieval-experiment`, а CLI получил preflight path, который различает допустимый sandbox/eval от заблокированного runtime adoption. Это разрешает benchmark work сейчас, но не разрешает автоматом включать qmd в `/query`.

2026-06-14 benchmark: fixed corpus из 9 golden lookup cases показал parity, not uplift. Текущий FTS5 hit 9/9, qmd BM25 hit 9/9, improved 0, regressed 0. Решение: qmd остаётся disabled optional candidate; runtime adoption не нужен без будущих доказанных misses.

**Что подключаем при runtime-активации:** [`qmd`](https://github.com/tobi/qmd) — локальный BM25+вектор-поиск по markdown с MCP-сервером. Бесплатно, локально, рекомендация самого Карпати.

До runtime-активации разрешён только bounded path:

1. `retrieval-preflight qmd` должен показать `experiment-ready` или `runtime-eval-ready`.
2. Fixed-corpus benchmark должен сравнить current FTS5/search/golden и qmd BM25/lex.
3. Generated paths (`.qmd/`, cache, model cache) должны быть ignored/removable.
4. Запрещены MCP daemon, embeddings, rerank и model downloads без отдельного approval.
5. REEFIKI markdown остаётся source of truth; qmd может быть только rebuildable retrieval cache/provider.

**Runtime integration sketch, not current task:**

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
| 0i memory governance | ✅ база готова | promotion/review queue needs | 2 часа | 0 |
| 0j audit stabilization | ✅ P0/P1 baseline готов | новые audit findings / failing gates | batch | 0 |
| 0k workflow fail-closed | ✅ готово | workflow audit / operation guard gap | batch | 0 |
| P2 memory reflection | ⏸ documented candidate | 3+ reports need manual consolidation | низкий | 0 |
| 1 qmd search | ⚡ preflight/benchmark разрешены, runtime отложен | только если FTS5 мало / есть misses | низкий | 0 |
| 2 NotebookLM | ❌ | 30+ PDF / часы видео | средний | 0 |
| 3 Pinecone | ❌ | >10k стр + команда + qmd не тянет | высокий | от $25/мес |

## Принципы при расширении

1. **Сохранять обратную совместимость.** Wiki в markdown не меняется — добавляется только индекс/обёртка.
2. **Один откат-коммит.** Каждое подключение нового слоя — отдельный коммит, чтобы можно было `git revert` если хуже стало.
3. **Замерить ДО.** Перед подключением — снять метрики (`/query` p50/p95, размер index.md). Без метрик неясно, помогло или нет.
4. **MCP-first.** Любой новый слой подключается через MCP-сервер, а не хардкодом в `.claude/commands/*.md`. Это упрощает откат.
5. **Чем выше слой, тем реже трогается.** Pinecone не должен быть в горячем пути локального проекта на одного человека.
6. **Docs ↔ reality sync.** Перед каждым новым спринтом — прогнать `validate_frontmatter.py` на всех индексах. Закрытая задача ≠ закрытая проблема без проверки.
