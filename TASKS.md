# TASKS — план внедрения

Привязка к `ROADMAP.md`. Каждая задача ссылается на фазу. Статусы: `[ ]` todo, `[~]` в работе, `[x]` готово.

Источник: консенсус 6 исследований (GPT-4o, Claude, DeepSeek, Gemini, Grok, Cascade) — май 2026.

---

## Sprint 1 — Integrity Gate (Phase 0a)

Цель: защитить frontmatter от поломки при ручном редактировании в Obsidian.

- [x] **T-01** Написать `scripts/validate_frontmatter.py`
  - Парсить YAML frontmatter из `wiki/**/*.md`
  - Проверять обязательные поля: `id`, `type`, `title`, `tags`, `useful_when`, `date_added`
  - Проверять допустимые типы: source, entity, concept, synthesis, decision, skill
  - Запрещать поле `importance` (устаревшее)
  - Проверять body: decision → `## Контекст` + `## Решение`, skill → `## Шаги`
  - Exit code 1 при ошибке → блокирует коммит

- [x] **T-02** Создать `.pre-commit-config.yaml`
  - `check-yaml` из pre-commit-hooks
  - Local hook: `validate_frontmatter.py` на файлы `projects/*/wiki/**/*.md`

- [x] **T-03** Настроить `.gitignore`
  - `.DS_Store`, `.obsidian/workspace*.json`, `.obsidian/cache/`, `.trash/`, `*.tmp`

- [x] **T-04** Добавить дедупликацию в спецификацию `/save`
  - Перед записью в inbox: проверять URL и content hash против `wiki/index.md` и `seen/`
  - При совпадении: отказ с сообщением «Уже есть: <существующая страница>»
  - Обновить `.claude/commands/save.md`
  - Реализация уточнена: `scripts/reefiki.py dedup <source>` проверяет URL по `wiki/`, `inbox/`, `seen/`, а файлы — по имени в `inbox/` и exact `sha256`.

- [x] **T-05** Настроить Obsidian Linter plugin
  - Включить lint-on-save
  - Задать порядок ключей frontmatter
  - YAML array format: оставить multi-line (осторожно с переформатированием)

- [x] **T-06** Мигрировать старые страницы: убрать поле `importance`
  - Найти все страницы с `importance:` через grep
  - Удалить поле, проверить что остальной frontmatter валиден

---

## Sprint 2 — Agent Metrics (Phase 0b)

Цель: собирать данные об эффективности агента для обоснованных решений.

- [x] **T-07** Обновить спецификацию `/harvest` — логировать trigger events
  - Формат в log.md: `trigger: harvest-proposed | accepted/declined`
  - Обновить `.claude/commands/harvest.md`

- [x] **T-08** Обновить спецификацию `/query` — логировать релевантность
  - Формат в log.md: `query: "<вопрос>" | found: N | relevant: Y/N`
  - Обновить `.claude/commands/query.md`

- [x] **T-09** Реструктурировать project-level `AGENTS.md`
  - Критические правила и запреты → первые 30 строк
  - Процедуры → середина
  - Примеры → конец
  - Не сокращать, только переставить блоки

- [x] **T-10** Усилить resolve: добавить supersession
  - При `/resolve` старое утверждение помечается `[superseded by: <new claim>]`
  - Обновить `.claude/commands/resolve.md`

---

## Sprint 3 — Obsidian UX

Цель: улучшить повседневный опыт работы с вики через Obsidian.

- [x] **T-11** Создать `wiki/_dashboard.md` с Dataview-запросами
  - Все страницы без `useful_when` (баг)
  - Все страницы с `use_count: 0` старше 60 дней (stale candidates)
  - Все skills с `verified: null` (нужна проверка)
  - Orphan pages (0 входящих ссылок)
  - Thin pages (<100 слов)

- [x] **T-12** Настроить Obsidian Dataview plugin
  - Установить, проверить что frontmatter индексируется

---

## Sprint 4 — Mobile Capture (Phase 0c)

Цель: сохранять ссылки с телефона в inbox/ без IDE.

Триггер: 3+ отложенных захватов в неделю.

- [x] **T-13** Выбрать способ: Telegram бот / iOS Shortcuts / Web Clipper
  - Telegram бот — рекомендация 5/6 исследований, cross-platform
  - iOS Shortcuts — бесплатно, без сервера, только Apple
  - Web Clipper — browser capture, не для произвольных заметок

- [x] **T-14** Реализовать выбранный способ
  - Бот/shortcut создаёт файл в `projects/<name>/inbox/<timestamp>.md`
  - Формат: `# <url или заголовок>\n\n<текст если есть>`
  - Монорепо сохраняется

---

## Backlog — при росте (Phase 0.5, 0.6, 1+)

Не начинать без объективного триггера.

- [x] **T-22** Integrity reality check — all projects (переоткрыт, скоуп расширен)
  - `projects/reefiki` — закрыт: index.md валиден, `Total pages: 19`.
  - `projects/metrica` — закрыт: `importance` не найден, `Total pages: 113` совпадает с реальными wiki-страницами.
  - `validate_frontmatter.py` проверяет все wiki-файлы: 143 OK.
  - Остаток не блокирует integrity gate: 5 старых `decision`-страниц в metrica предупреждают о желательной миграции к ADR-секциям.

- [x] **T-15** Создать шаблон `deep-research/` (Phase 0.5)
  - Триггер: первый материал >5 источников
  - Структура: `brief.md`, `sources.md`, `report.md`, `_meta.yaml`
  - Закрыто 2026-05-31: шаблон добавлен в `_template` и `projects/reefiki`; существующие проекты вне текущего scope не тронуты.

- [x] **T-16** Процедура stale pages (Phase 0.6)
  - Триггер: stale pages > 5 штук
  - 3 исхода: seen/ | refresh useful_when | skill verification
  - Закрыто 2026-05-31: процедура добавлена в `/review-queues`; live `projects/reefiki` и `projects/metrica` queues пустые, массовых stale-правок нет.

- [x] **T-17** Ротация log.md (Phase 0.6)
  - Триггер: log.md > 500 строк
  - `git mv log.md logs/log-YYYY-MM.md`, новый log.md со ссылкой
  - Закрыто 2026-05-30 для `projects/reefiki`: старый журнал перенесён в `wiki/logs/log-2026-04-to-2026-05.md`, новый `wiki/log.md` содержит ссылку на архив.

- [x] **T-18** Golden query pack (Phase 1 prep)
  - Триггер: после первого integrity reality check ИЛИ >50 страниц ИЛИ 3+ query miss/месяц
  - 10-15 реальных вопросов с expected_pages
  - Метрики: Recall@5, MRR
  - Закрыто 2026-05-30 для `projects/reefiki`: 13 golden cases covering lookup/promote/pack; current baseline 13/13 passed.

- [x] **T-19** Wiki health dashboard расширенный (Phase 1 prep)
  - Триггер: >50 страниц
  - Backlinks count, cross-reference density, content freshness
  - Закрыто 2026-05-31: `_dashboard.md` расширен в `_template`, `reefiki`, `metrica`; добавлены backlinks count, outlinks/size density и freshness queries.

- [ ] **T-20** Static site export (Phase 2+)
  - Триггер: 3+ внешних readonly use cases
  - Инструмент: Quartz (Obsidian-совместимый) или MkDocs
  - 2026-06-14 status: product-facing public surface is no longer blocked by this item; Sprint 24 delivered the static landing in `site/`.
  - Keep this only for future wiki export of selected public-safe knowledge, after private/public boundary review. Do not use it as the next default growth task.

- [ ] **T-21** Confidence tagging для cross-reference edges в `_schema.md` (Phase 1)
  - Триггер: активация Phase 1 (qmd search)
  - Паттерн: `EXTRACTED` / `INFERRED` / `AMBIGUOUS` по образцу [graphify](https://github.com/safishamsi/graphify)
  - Применять к связям `[[wikilinks]]` между страницами когда их станет достаточно
  - Источник отложен в `seen/`, май 2026
  - 2026-06-14 status: schema change is not the first step. Next safe slice is a read-only link-confidence report over existing wikilinks/review-queues; update schema only if the report shows repeated ambiguity.
  - 2026-06-14 T-21a closeout: T-140 found 8 ambiguous-looking links, so `_schema.md` now allows optional `## Related` markers and `link-confidence` reports explicit marker counts. Existing wiki pages were not rewritten. T-21 remains open for future manual triage/adoption.

---

---

## Sprint 5 — Audit Fixes (Phase 0d/0e/0f, Security)

Источник: аудит Kiro, май 2026. Исправляем расхождения docs ↔ реальность, security-риски, дрейф шаблона.

- [x] **T-23** Добавить `decision` body-check в `validate_frontmatter.py` (Phase 0a)
  - Добавить non-blocking `BODY_WARN` для `decision`: ADR-секции `## Контекст` / `## Решение` / `## Варианты`.
  - `source` body-check оставлен опциональным, не блокирующим.
  - Статус: **выполнено** в этом спринте.

- [x] **T-24** Починить 17 synthesis-страниц без frontmatter в metrica (Phase 0d)
  - Файлы: `preview-otp-delivery-gap-vs-production-control.md`, `first-upload-*`, `live-*`, `*-coverage-uplift`, `sync-conflict-error-branches-*`, `settings-*`
  - Для каждой: добавить frontmatter (`id`, `type: synthesis`, `title`, `tags`, `useful_when`, `date_added`, `use_count: 0`, `last_used: null`)
  - Статус: **выполнено** в этом спринте.

- [x] **T-25** Убрать `.obsidian/plugins/**/main.js` из git (Phase 0a)
  - `git rm --cached .obsidian/plugins/dataview/main.js .obsidian/plugins/obsidian-linter/main.js`
  - Добавить в `.gitignore`: `.obsidian/plugins/**/main.js`, `.obsidian/plugins/**/styles.css`
  - Плагины ставятся через community plugins ID, не через репо.
  - Триггер: сейчас (раздувают репо, вопрос лицензий при public push).

- [x] **T-26** Реструктурировать root-level `AGENTS.md` (Phase 0b)
  - Критические правила (режимы работы, запреты) → первые 30 строк
  - Статус: **выполнено** в этом спринте.

- [x] **T-27** Исправить command injection в `.github/workflows/inbox-capture.yml` (Phase 0c — Security)
  - Шаг «Commit and push»: `${{ github.event.client_payload.url }}` интерполируется напрямую в shell-строку commit message → уязвимость command injection.
  - Перевести `url` и `project` в env-переменные шага, обращаться только через `"$VAR"`.
  - Статус: **выполнено** в этом спринте.

- [x] **T-28** Синхронизировать шаблон и живые AGENTS.md (Phase 0e)
  - Добавить блок «Обязательное чтение _wiki» в `projects/metrica/AGENTS.md` и `projects/reefiki/AGENTS.md`.
  - Добавить `_dashboard.md` в scope команд `/new` и `/sync-template`.
  - Статус: **выполнено** в этом спринте.

- [x] **T-29** Починить `.agents/skills/source-command-*/SKILL.md` (Phase 0e)
  - `source-command-new`: исправить дубль `AGENTS.md` → `CLAUDE.md`.
  - `source-command-sync-template`: исправить `.Codex/` → `.claude/`, `AGENTS.md` → `CLAUDE.md`.
  - Статус: **выполнено** в этом спринте.

- [x] **T-30** Добавить `## Skills` в `_template/wiki/index.md` и `status.md` (Phase 0e)
  - `_template/wiki/index.md`: добавить секцию `## Skills` после `## Decisions`.
  - `_template/.claude/commands/status.md`: добавить skills в пример вывода.
  - Статус: **выполнено** в этом спринте.

- [x] **T-31** Добавить acceptance check для synthesis в `/harvest` (Phase 0f)
  - Перед предложением synthesis-страницы: «чем эта страница будет полезна через 3 месяца? если только как снимок сессии — предложить `seen/` или `deep-research/`».
  - Обновить `_template/.claude/commands/harvest.md` и синхронизировать в проекты.
  - Триггер: metrica 55 synthesis, большинство `use_count: 0`.

- [x] **T-32** Исправить Dataview-запрос в `_dashboard.md` (Phase 0e)
  - Добавить скобки в WHERE-условие stale candidates: `WHERE ((use_count = 0) OR (!use_count)) AND date(date_added) < date(today) - dur(60 days)`
  - Обновить `_template/wiki/_dashboard.md` и синхронизировать в проекты.

- [x] **T-33** Обновить `push-public.ps1`: force-with-lease + prompt + whitelist (Security)
  - Заменить `--force` на `--force-with-lease`.
  - Добавить `Read-Host "Push to public? (y/N)"` перед push.
  - Читать список приватных проектов из конфига вместо хардкода `reefiki`/`metrica`.

- [x] **T-34** Обновить `pre-commit-hooks` до актуальной версии (Phase 0a)
  - `.pre-commit-config.yaml`: `rev: v4.6.0` → `v6.0.0` (актуальная на момент выполнения).
  - Расширить `trailing-whitespace` и `end-of-file-fixer` на root-документы (`*.md` в корне).

## Sprint 6 — Memory/Search/Planning Layer (Phase 0g)

Источник: разбор `claude-mem`, `planning-with-files`, `agentmemory` — май 2026.

- [x] **T-35** Добавить локальный REEFIKI CLI
  - `scripts/reefiki.py`
  - Команды: `index`, `search`, `privacy`, `status`, `timeline`, `plan create`, `plan check`.
  - Без внешних зависимостей; Python stdlib + SQLite FTS5.

- [x] **T-36** Внедрить progressive `/query` + provenance
  - `_template/.claude/commands/query.md`
  - `projects/reefiki/.claude/commands/query.md`
  - Поиск через `.reefiki/index.sqlite`, fallback на `wiki/index.md`.

- [x] **T-37** Усилить privacy guard
  - `_template/.claude/commands/save.md`
  - `_template/.claude/commands/process.md`
  - `projects/reefiki/.claude/commands/save.md`
  - `projects/reefiki/.claude/commands/process.md`
  - Запрещённые имена, директории, бинарники, размер >5 MB.

- [x] **T-38** Добавить plan/recovery/timeline primitives
  - `plans/<task>.md` создаётся через `python scripts/reefiki.py --project projects/<name> plan create "<task>"`.
  - Plan checksum проверяется через `plan check`.
  - Timeline берётся из `wiki/log.md`.

- [x] **T-39** Обновить `/status` и `/harvest`
  - `/status` показывает индекс поиска и активные планы.
  - `/harvest` читает plan/timeline перед сохранением выводов.

- [ ] **T-40** Минимальный MCP/REST API
  - Отложено до стабильного локального `/query` и provenance.
  - 2026-06-14 status: do not start a daemon/server by default. The safe successor is a local adapter smoke over the existing CLI/JSON surface, preserving markdown source-of-truth and existing provenance.

- [ ] **T-41** Vector/graph search layer
  - Отложено до реальных промахов FTS5 или сильной синонимии.
  - 2026-06-14 status: runtime adoption remains blocked, but benchmark work is allowed. qmd preflight/benchmark must compare against current FTS5/golden before any vector/rerank/model-download decision.

## Sprint 7 — Agent Skills Governance (Phase 0h)

Источник: audit-first adoption plan по внешним agent skills, май 2026.

- [x] **T-42** Добавить skill-adoption schema в REEFIKI
  - `projects/reefiki/wiki/_schema.md`: поля `source_url`, `license`, `status`, `scope`, `validation`, `risks` для external/adopted skills.
  - `scripts/validate_frontmatter.py`: проверка skill-only governance fields и allowlist статусов.
  - `projects/reefiki/wiki/decisions/adopt-skill-adoption-governance.md`: ADR по audit-first policy.
  - `projects/reefiki/wiki/index.md` и `wiki/log.md`: обновлены после добавления ADR.

- [x] **T-43** Создать первые adopted-skill entries
  - Кандидаты: `keep-codex-fast`, `agent-skills` workflow patterns, `open-design` prototype workflow.
  - Для каждого: `source_url`, `license`, `status: candidate|sandboxed|accepted`, `scope`, `validation`, `risks`.
  - Не переводить в `accepted` без report-only/sandbox proof.

- [x] **T-44** Перевести `keep-codex-fast` из `candidate` в `sandboxed`
  - Inspect source/scripts locally.
  - Run report-only only.
  - Save proof and risks in `wiki/skills/keep-codex-fast-candidate.md`.
  - Do not run apply/archive/move/prune/repair.

- [x] **T-45** Решить, принимать ли `keep-codex-fast` в `accepted`
  - Перед apply создать handoff для активных важных тредов.
  - Apply только когда Codex закрыт или через явный wait-for-exit.
  - Repair title/preview metadata только отдельным решением, не в normal apply.
  - Решение: accepted только как runbook/gate, не как unattended apply.

- [x] **T-46** Sandbox-evaluate `agent-skills` workflow patterns
  - Выбрать 3-5 patterns для локальной адаптации.
  - Не vendor-import целиком.
  - Обновить candidate skill после review.

- [x] **T-47** Sandbox-evaluate `open-design` на одном UI prototype
  - Только scratch workspace/branch.
  - Сохранить screenshot/proof и dependency notes.
  - Не интегрировать runtime dependencies в Metrica product repo.
  - Read-only sandbox audit завершён.
  - Static proof завершён; full live runtime no-run из-за Node/pnpm mismatch и не нужен без отдельного решения.

- [x] **T-48** Создать REEFIKI-native skill из `agent-skills` patterns
  - Взять lifecycle routing, prove-it bugfix, vertical slice build, source-driven verification, go/no-go ship gate.
  - Не импортировать hooks и vendor command formats.

- [x] **T-49** Подготовить Metrica open-design evaluation prompt
  - Scratch cwd, no production env, no Metrica repo cwd.
  - OD_DATA_DIR в temp.
  - Output: screenshot/proof + dependency notes + go/no-go.

- [x] **T-50** Добавить project-local Metrica task entry для open-design evaluation
  - Не копировать весь REEFIKI план.
  - Добавить короткий task/backlog пункт в подходящий Metrica docs файл.
  - Сослаться на REEFIKI prompt/runbook или вставить короткий operational prompt.

- [x] **T-51** Применить Project X lifecycle contract
  - Добавить manual-first isolated-run path: intake -> planned -> isolated_run -> proof_attached -> reviewing -> handoff_ready -> completed.
  - Обновить docs/DECISIONS.md, docs/TASK_LIFECYCLE.md, docs/EXECUTOR_CONTRACT.md.
  - Добавить contract tests и прогнать full suite.

- [x] **T-52** Выполнить Metrica open-design static proof
  - Full runtime no-run из-за Node/pnpm mismatch.
  - Создать scratch static artifact вне Metrica.
  - Проверить через localhost и screenshot desktop/mobile.

- [x] **T-53** Установить `keep-codex-fast` как sandboxed Codex skill
  - Скопировать в `C:\Users\kissl\.codex\skills\keep-codex-fast`.
  - Добавить `ADOPTION.md`.
  - Проверить smoke tests из установленного пути.
  - Не запускать apply/backup-only/repair.

- [x] **T-54** Синхронизировать Metrica audit-first note
  - Добавить в `docs/ACTIVE_CONTEXT.md` короткую строку про external skills/design tools.
  - Явно зафиксировать: open-design static proof only, no product redesign accepted.

- [x] **T-55** Добавить project activation prompts
  - Metrica: sandbox-only open-design follow-up prompt.
  - Project X: fresh-thread lifecycle continuation prompt.

- [x] **T-56** Добавить общий Metrica activation prompt
  - `docs/ACTIVATION_PROMPT.md` для fresh-thread entry.
  - `marketing/open-design-activation-prompt.md` оставить узким sandbox prompt.

- [x] **T-57** Индексировать activation prompts
  - Metrica: добавить `docs/ACTIVATION_PROMPT.md` в `docs/PROJECT_MAP.md`.
  - Project X: добавить `docs/ACTIVATION_PROMPT.md` в root/docs README.

- [x] **T-58** Закрыть stale docs/index links после adoption pass
  - Metrica: README/ACTIVE_CONTEXT/PROJECT_MAP ссылки на activation/open-design sandbox docs.
  - REEFIKI: ROADMAP Phase 0h больше не говорит, что first entries ещё предстоит создать.

- [x] **T-73** Зафиксировать external-tool governance registry entries
  - `codegraph`: sandboxed candidate для project-local code navigation; smoke evidence recorded.
  - `codebase-memory-mcp`: watch/deferred; Windows smoke blocked.
  - `SkillOpt`: R&D reference для future skill evaluation gates.
  - `taste-skill`: reference-only для skill-writing inspiration.
  - Ограничение: no vendor code, no replacement for graphify/memoir/REEFIKI layers.

- [x] **T-74** Добавить `codegraph` evaluation runbook
  - Цель: один безопасный project-local smoke перед любым повышением статуса.
  - Gate: `.codegraph/` ignored, `status/query/callers/impact` работают, найденные связи подтверждены чтением кода.
  - Output: обновить governance candidate evidence, не коммитить generated database.

- [x] **T-75** Протестировать `codegraph` runbook на REEFIKI или одном подключённом codebase
  - Scope: один codebase, один реальный symbol/impact вопрос.
  - Stop rule: если install/init/debug занимает больше 10-15 минут, остановить и записать blocker.
  - Не переводить `codegraph` в global accepted по одному smoke.
  - Результат 2026-05-30: REEFIKI smoke прошёл; 10 files, 285 nodes, 721 edges; `status/query/callers/impact` OK; `build_index` callers/impact подтверждены чтением `scripts/reefiki.py`.

- [x] **T-76** Повторно проверить `codebase-memory-mcp` только после простого Windows smoke path
  - Не менять REEFIKI runtime.
  - Не тратить implementation time, пока install route не даёт полезный локальный output.
  - Закрыто 2026-06-10: release `v0.7.0` Windows zip скачан вручную в temp, SHA-256 сверена с `checksums.txt`, binary `--version/--help` работает.
  - Smoke выполнен без installer/runtime changes: `CBM_CACHE_DIR` был изолирован в temp, temp Python git repo проиндексирован, `search_graph`, `get_architecture`, `index_status` вернули полезный JSON output.
  - Статус повышен только до `sandboxed`: `install.ps1` не запускался, user PATH/agent config/MCP hooks не менялись, adoption остаётся запрещён без отдельного proof gate.

- [x] **T-77** Спроектировать минимальные skill quality gates по мотивам SkillOpt/taste-skill
  - Локальный gate: useful_when, steps, validation, risks, exit criteria.
  - Сначала manual review 2-3 skills, затем решать нужен ли validator/helper.
  - Не подключать внешний optimizer без доказанной проблемы качества.
  - Закрыто 2026-05-30: добавлен accepted skill `skill-quality-gate`; ручной gate применён к 3 skills, validator/helper отложен.

- [x] **T-78** Добавить staged-path guard для cross-project harvest
  - Команда: `python scripts/reefiki.py guard-staged --target-project <name>`.
  - Gate: staged paths должны быть только `projects/<name>/wiki/**`.
  - Блокирует случайный stage/commit чужих project files или root docs при wiki-harvest.
  - Покрыто тестами pass/block.

- [x] **T-79** Зафиксировать Understand Anything как sandbox/watch candidate
  - Scope: visual knowledge graph для codebase/docs/wiki.
  - Статус: candidate/watch; local install/smoke не выполнялся.
  - Ограничение: не заменяет graphify/codegraph/REEFIKI, не запускать auto-update hooks без отдельного решения.

- [x] **T-80** Добавить автоматический trigger gate для Understand Anything
  - Команда: `python scripts/reefiki.py tool-trigger Understand-Anything --signal "<observed signal>"`.
  - `watch` для обычной работы; `sandbox-recommended` для visual graph / unknown large codebase / wiki graph / onboarding signals.
  - Gate read-only: не устанавливает tool, не запускает hooks, не меняет workspace.

- [x] **T-81** Зафиксировать ECC как reference-only patterns source
  - Scope: trigger gates, readiness/status snapshots, security checklist, selective install ideas.
  - Статус: reference-only; не устанавливать ECC, не подключать hooks/MCP/skills wholesale.
  - Авто-gate: `tool-trigger ECC` возвращает `reference-only`.

- [x] **T-82** Зафиксировать security/composable/restricted-browser external watch entries
  - `Anthropic-Cybersecurity-Skills`: defensive reference для будущего security checklist, без установки pack.
  - `mattpocock/skills`: small/composable skill patterns для `skill-quality-gate`, без wholesale install.
  - `CloakBrowser`: restricted watch только для легитимного public QA/repro с явным разрешением.
  - `agentmemory`: runtime не внедрять; только benchmark/status ideas.

## Sprint 8 — Memory Governance Layer (Phase 0i)

Источник: `H:\Downloads\reefiki_github_research.md`, май 2026.

- [x] **T-59** Зафиксировать routing contract между memoir / graphify / REEFIKI
  - Добавить ADR `reefiki-routing-and-promotion-contract`.
  - Зафиксировать роли слоёв, anti-duplication rule и review queues.

- [x] **T-60** Зафиксировать typed promotion gate `memoir -> REEFIKI`
  - Добавить concept `memoir-to-reefiki-promotion-gate`.
  - Описать target types, promotion criteria и anti-dump rule.

- [x] **T-61** Зафиксировать review queue contract
  - Добавить concept `reefiki-review-queue-contract`.
  - Описать semantics и triggers для `needs_verification`, `stale_review`, `orphan_review`, `duplicate_candidate`, `conflict_review`.

- [x] **T-62** Добавить implementation plan для первых automation steps
  - Добавить synthesis `reefiki-memory-governance-first-automation-steps`.
  - Зафиксировать приоритет: promotion dry-run -> review-queue scanner.

- [x] **T-63** Реализовать `promote-dry-run` в `scripts/reefiki.py`
  - Verdict: `ignore` / `memoir-only` / `promote`
  - Suggested target type
  - Confidence / review_state / duplicate refs

- [x] **T-64** Реализовать `review-queues` в `scripts/reefiki.py`
  - Read-only scan по durable pages.
  - Первый охват: needs_verification / stale / orphan / duplicate / basic conflict.

- [x] **T-65** Добавить artifact mode для governance команд
  - `review-queues --write-report`
  - `promote-dry-run --write-draft`

- [x] **T-66** Добавить confirm-only apply layer
  - `promote-dry-run --apply-draft <path> --yes`
  - Без silent mutation; запись страницы + log + reindex.

- [x] **T-67** Снизить шум первого governance pass
  - Убрать false positive `conflict_review` по prose `[[wikilinks]]`.
  - Сделать `duplicate_candidate` консервативнее через type-compatibility rules.

- [x] **T-68** Почистить `needs_verification` backlog в `projects/reefiki`
  - Добавить `sources`/evidence metadata для новых governance/concept/decision pages.
  - Цель: убрать auto-generated self-noise после Phase 0i.
  - Закрыто 2026-05-30: `dual-remote-public-snapshot`, `remove-wrapper-pilots`.

- [x] **T-69** Почистить `orphan_review` backlog в `projects/reefiki`
  - Добавить осмысленные inbound links / `## Related` для standalone durable pages.
  - Не удалять страницы автоматически; только связать или явно оставить standalone.
  - Закрыто 2026-05-30: durable pages связаны через Related; review queue пустая.

- [x] **T-70** Улучшить `duplicate_candidate` heuristics ещё на один проход
  - Свести report к high-confidence candidates.
  - Избегать source-derived overlap, который является нормальной архитектурой, а не duplicate.
  - Закрыто 2026-05-30: shared-source duplicate теперь требует более сильного title match; broad governance overlap не попадает в очередь.

- [x] **T-71** Расширить `conflict_review` beyond missing related pages
  - Следующий слой: detect incompatible durable claims по явным markers/sources/title clusters.
  - Без LLM и без auto-merge.
  - Закрыто 2026-05-31: scanner обрабатывает явные секции `## Conflicting claims` / `## Conflict` с wikilinks и ставит `conflict_review`.

- [x] **T-72** Добавить write-report / write-draft ссылки в project command docs более явно
  - `status/help/query/harvest` surfaces, где governance output должен предлагаться агентом сам.
  - Закрыто 2026-05-30: triggers добавлены в `review-queues`, `promote-dry-run`, `status`, `harvest`, `COMMANDS.md`.

## Sprint 9 — Phase 0j foundation follow-up

- [x] **T-83** Закрыть cross-platform repository baseline follow-up
  - Добавить `.gitattributes`, чтобы Markdown/YAML/Python/TOML/JSON сохранялись с LF и frontmatter parsing не зависел от Windows `autocrlf`.
  - Закрепить Python 3 для local pre-commit hooks через `language_version: python3`; минимальная версия проверяется runtime guard и `pyproject.toml`.
  - Добавить ранний CLI guard: Python <3.11 получает понятную ошибку до импорта внутренних модулей.
  - Расширить `pyproject.toml`: dev extras (`pytest`, `pre-commit`) и `pytest` testpaths.
  - Обновить README publish limitations после закрытия inventory guard/content scan в Python path.
  - Покрыть regression-тестами packaging/legal/cross-platform baseline.

- [x] **T-84** Закрыть `escape_fts()` crash cases
  - Quote FTS5 tokens so user text like `python AND NOT` is searched as text, not parsed as FTS operators.
  - Punctuation-only queries return no results instead of passing raw syntax to SQLite FTS5.
  - Добавлены regression tests для keyword-token query и punctuation-only query.

## Sprint 10 — Governance UX (Phase 0j P1)

- [x] **T-85** Добавить schema_version и `id == filename` validator gate
  - `_domain.md` получил project-level `schema_version: "1.0"` для `_template` и всех живых проектов.
  - `validate_frontmatter.py` проверяет поддерживаемую schema_version проекта при validation wiki-файлов.
  - `validate_frontmatter.py` блокирует wiki-страницы, где frontmatter `id` не совпадает с именем файла без `.md`.
  - `_schema.md`, `/lint` docs и `COMMANDS.md` обновлены под новые mechanical checks.
  - Добавлены regression-тесты для schema_version и id/filename mismatch.

- [x] **T-86** Добавить L0 `abstract` и `_overview.md` слой для `/query`
  - `abstract` описан в `_schema.md` как optional L0 summary field.
  - `scripts/reefiki.py index/search` хранит и ищет `abstract`; текстовый search output показывает `abstract` до `useful_when`.
  - `_overview.md` добавлен как служебная карта раздела для `_template` и `projects/reefiki`; validator/index не считают его wiki-страницей.
  - `/query` docs обновлены: abstract-first, затем `_overview.md` при конкурирующих страницах раздела, затем полные страницы только по необходимости.
  - Добавлены regression-тесты на abstract search и skip `_overview.md`.
  - 2026-06-10 follow-up: `reefiki.py search --format json` сохранил full output по умолчанию, но получил `--output compact` без полного body и `--output files` для agent-native точечного чтения.

- [x] **T-87** Реализовать practical `health` metrics без decorative score-only слоя
  - `reefiki.py health` отделён от `doctor`: `doctor` остаётся integrity gate, `health` считает practical wiki metrics.
  - JSON/text output включает size, usage, quality, structure, doctor sub-payload, warnings и recommendations.
  - Метрики: distillation ratio, avg/zero use_count, median last_used, useful_when quality, conflicts, orphan ratio, broken links, avg outgoing links.
  - `COMMANDS.md` и `/status` docs обновлены: health использовать перед cleanup/phase switch и при вопросах о рисках базы.
  - Добавлен regression-тест на practical health payload и recommendations.

## Sprint 11 — Core docs (Phase 0j P1)

- [x] **T-88** Создать user-facing core docs
  - Добавлен `QUICKSTART.md` для первого запуска без знания CLI.
  - Добавлен `docs/obsidian-setup.md` с safe Obsidian setup и предупреждением про `obsidian-git`.
  - Добавлен `docs/mobile-capture.md` с минимальным security contract для Telegram/Shortcut capture.
  - Добавлен `docs/RECOVERY.md` с recovery runbook для index/wiki/frontmatter/repo/public leak сценариев.
  - README и COMMANDS получили ссылки на runbooks.

## Sprint 12 — Publish Safety Closure (Phase 0j P0)

- [x] **T-89** Сканировать итоговый filtered public snapshot перед push
  - `publish-task --apply --public-snapshot` больше не short-circuit'ится при empty diff; resume flow реально строит public snapshot.
  - После удаления private projects из orphan snapshot Python path берёт `git ls-files` и запускает content scan по итоговым public files.
  - При secret-like content возвращается structured JSON block до `commit`/`push`; public remote не получает `main`.
  - Первый live apply заблокировал демонстрационные fake keys в `docs/Audit_07.06.26/REEFIKI_SECURITY_AUDIT.md`; audit examples sanitized до placeholder form.
  - README, COMMANDS и ROADMAP обновлены: full public snapshot content scan больше не считается открытым P0 gap.

## Sprint 13 — Path Containment (Phase 0j P0)

- [x] **T-90** Добавить общий repo-relative scope helper
  - Добавлен `repo_path_in_scope(path, scope)` поверх `normalize_repo_path()` для segment-boundary checks.
  - `guard-staged`, `harvest-commit`, publish diff classification, public snapshot exclusions и private path leak check переведены с ad-hoc `startswith()` на helper.
  - Regression test покрывает project names with spaces, normalized `..` внутри scope и prefix sibling bypass (`wiki2` не считается `wiki`).

## Sprint 14 — Publish Dry-run Safety (Phase 0j P0)

- [x] **T-91** Добавить final public snapshot scan в `publish-task --dry-run`
  - Dry-run теперь строит тот же filtered orphan snapshot, удаляет private projects и сканирует итоговые staged public files без `commit`/`push`.
  - Secret-like content в final public snapshot возвращает structured JSON block уже на dry-run, до private push.
  - Apply path переиспользует тот же snapshot inspection helper и повторяет scan перед public push.

## Sprint 15 — Phase 0j Closeout (Roadmap Sync)

- [x] **T-92** Синхронизировать roadmap с фактически закрытым Phase 0j P0/P1 baseline
  - ROADMAP Phase 0j теперь явно отмечает закрытые safety, CI, packaging/legal, concurrency/integrity, markdown query L0, governance UX и core docs slices.
  - Дальше P2/backlog не стартует автоматически: нужен новый finding, failing gate или реальный query/publish miss.
  - Closeout проверяется свежими local gates: tests, memory golden, health и publish dry-run.

## Sprint 16 — Read-only Governance UX (Phase 0j P2)

- [x] **T-93** Добавить компактный summary для `review-queues`
  - Trigger: после Phase 0j closeout `health` рекомендовал `review-queues`, но полный вывод давал 117 `missing_backlink` items в `projects/reefiki` и 254 в `projects/metrica`, что плохо подходит как dashboard/next-step gate.
  - Добавлен `review-queues --summary` с counts, top pages, уникальными sample pages и suggested action по типам очередей.
  - Добавлен `--limit N` для управления числом примеров.
  - `health` теперь рекомендует начинать с `review-queues --summary`, а не с полного triage dump.
  - `COMMANDS.md` и `projects/reefiki/.claude/commands/review-queues.md` обновлены.
  - Добавлены regression-тесты на summary payload и CLI JSON/text output.

- [x] **T-94** Исправить `memory route/explain` для roadmap governance задач
  - Trigger: `memory explain "continue REEFIKI roadmap development"` рекомендовал `memoir`, хотя задача явно требует durable REEFIKI project-governance context.
  - `memory_route()` теперь отправляет roadmap/backlog/phase/review-queue/health-gate intents в REEFIKI как primary layer.
  - `memoir` остаётся secondary layer для рабочего контекста, без durable-write risk flag.
  - `memory explain` теперь показывает REEFIKI selected source и next action `memory lookup --project reefiki --layer reefiki`.
  - `memory pack --strict` для roadmap development сохраняет strict pass, `why_included`, open queues и golden summary.
  - Добавлены regression-тесты на route и explain.

- [x] **T-95** Добавить explicit marker для intentional one-way backlinks
  - Trigger: `review-queues --summary` выявил 117 `missing_backlink` items; suggested action уже предлагал “mark one-way relation as intentional”, но scanner не поддерживал такой marker.
  - Добавлена секция `## Intentional one-way inbound links` на target page: plain/backtick source ids исключают конкретный inbound source из `missing_backlink`.
  - Scanner не требует искусственную reciprocal `[[wikilink]]`, если relation действительно one-way.
  - `COMMANDS.md` и `projects/reefiki/.claude/commands/review-queues.md` обновлены.
  - Добавлен regression-тест для intentional one-way inbound link.

- [x] **T-96** Выполнить первый bounded triage top `missing_backlink` pages
  - Scope: только две самые плотные target pages из `review-queues --summary`: `adopt-skill-adoption-governance` и `reefiki-routing-and-promotion-contract`.
  - Добавлены осмысленные reciprocal `Related` links для governance/control-plane pages, где связь действительно двусторонняя.
  - Остальные source pages помечены через `## Intentional one-way inbound links`, чтобы не превращать центральные ADR в каталоги всех candidate/tool pages.
  - Цель: доказать новый marker на живой wiki и снизить шум `missing_backlink` без массовых механических правок.

- [x] **T-97** Ограничить detail output `review-queues --type`
  - Trigger: после `--summary` следующий detail шаг `review-queues --type missing_backlink --limit 10` снова печатал весь список, поэтому gate оставался шумным.
  - Text detail output теперь уважает `--limit N` и явно пишет, сколько items скрыто.
  - Полный triage artifact остаётся через `--write-report`; JSON output не режется для automation.
  - Добавлен regression-тест на CLI text output limit.

- [x] **T-98** Добавить next action в `memory status --summary`
  - Trigger: `memory status --summary` показывал `open: yes` и counts, но не говорил следующий операторский шаг.
  - Summary JSON/text теперь включает `next_action` при open review queues или active promotion drafts.
  - Для open review queues next action ведёт к `review-queues --summary`, а не к новому tooling layer.
  - Добавлен regression-тест на summary JSON/text output.

- [x] **T-99** Сделать `memory pack --strict` устойчивым к lookup/index storage error
  - Trigger: `python -B scripts/reefiki.py memory pack ... --strict` падал raw SQLite traceback (`unable to open database file`) вместо structured pack result.
  - `memory_pack()` теперь сохраняет critical context из wiki rows даже при lookup storage error.
  - Strict output возвращает `lookup:error`/`golden:error`, а text/JSON output остаются читаемыми.
  - Добавлен regression-тест на lookup/golden storage error без traceback.

- [x] **T-100** Выполнить второй bounded triage top `missing_backlink` pages
  - Scope: только две самые плотные target pages из `review-queues --summary`: `global-memory-orchestration-cli` и `knowledge-capture-decision-tree`.
  - Добавлены reciprocal `Related` links для реально двусторонних governance/control-plane связей.
  - Tool/source/candidate mentions, где обратная связь была бы catalog noise, закрыты через `## Intentional one-way inbound links`.
  - Цель: продолжить снижение `missing_backlink` шума без массовых механических правок.

- [x] **T-101** Добавить read-only operator dashboard
  - Trigger: после `health`, `review-queues --summary` и `memory status --summary` оператору всё ещё приходилось вручную склеивать health warnings, queue counts и следующий шаг.
  - Добавлен `reefiki.py dashboard` с text/JSON output: practical health, review queue summary и `next_action`.
  - `dashboard` переиспользует существующие `health` и `review_queue_scan`; queue semantics/data model не менялись.
  - `COMMANDS.md`, `README.md` и `/status` docs обновлены.
  - Добавлены regression-тесты на JSON и text output.

## Sprint 17 — Memory Reflection Candidate (docs-only)

- [x] **T-102** Зафиксировать безопасную версию идеи "dreaming"
  - Trigger: review June 2026 dreaming idea batch показал полезный паттерн консолидации памяти, но исходная версия предлагала слишком широкий runtime: transcript capture, `raw/sessions/`, daemon/API/cron, schema-wide fields и auto-apply.
  - Добавлен `docs/MEMORY_REFLECTION.md` как boundary doc: REEFIKI принимает только read-only reflection/report поверх существующих gates.
  - README и ROADMAP ссылаются на документ как future candidate, не как реализованную фичу.
  - Non-goals: auto-apply, auto-delete, `raw/` writes, full session capture, cron/nightly job, IDE API, vector DB, schema-wide `status`/`expires`.

- [x] **T-103** Реализовать `memory reflect` только при подтверждённом триггере
  - Trigger: оператор повторно вручную склеивает 3+ отчёта (`memory diff`, `health`, `review-queues --summary`, `memory status --summary`, `memory pack --strict`, `promotion-inbox`) или governance gates дают шумный next-step.
  - Scope: read-only CLI command, optional `--write-report` только в `plans/reflection-YYYY-MM-DD.md`.
  - Tests: synthetic project + synthetic git history; JSON payload проверяет included/excluded sources, candidate_actions и blocked_actions.
  - Explicitly out of scope: writes to `wiki/`, `raw/`, `seen/`, `_user/`, git state, config or source code; no daemon, no cron, no external dependency.
  - Закрыто 2026-06-10: добавлена `memory reflect`, text/json output, optional `--write-report` только в `plans/reflection-YYYY-MM-DD.md`; live smoke подтвердил read-only report и strict pack pass после явного rebuild index.

## Sprint 18 — Skill Products Adapter Follow-up (Phase 0h)

- [x] **T-104** Реализовать portable base skills и тонкий adapter layer отдельным proof-gated slice
  - Trigger: после публикации docs-slice `docs/skill-products/*` и явного решения перейти от документации к реализации.
  - Scope: создать canonical markdown-first skills в `skills/base/*/SKILL.md` и runtime-specific adapters в `adapters/*` только как тонкое подключение к существующему workflow.
  - Reference docs: `docs/skill-products/BASE_SKILLS.md`, `docs/skill-products/AGENT_ADAPTERS.md`, `docs/skill-products/SKILL_PRODUCTS.md`, `docs/skill-products/SKILL_MONETIZATION.md`.
  - Candidate layout: `skills/base/safe-task-worktree-bootstrap/SKILL.md`, `skills/base/source-of-truth-diagnostics/SKILL.md`, `skills/base/staged-scope-and-publish-guard/SKILL.md`, `skills/base/reefiki-experience-monitor/SKILL.md`, `skills/base/durable-harvest-closeout/SKILL.md`, plus `adapters/codex`, `adapters/claude-code`, `adapters/cursor`, `adapters/generic-agents`, `adapters/hermes`.
  - Runtime boundary: adapters in this slice are read-only install docs/fragments/proofs, not live runtime wiring; no global Codex/Claude/Cursor config changes, no marketplace/package install, no new memory runtime, no product packaging before demo/proof gate.
  - Adapter rules: canonical skill stays markdown-first; adapter must not change skill meaning; adapter only connects the workflow to a concrete agent runtime.
  - Validation: markdown links pass, adapter install docs are read-only by default, and any live adapter hook/config requires separate explicit approval.
  - 2026-06-10 progress: published portable base skills, read-only adapter install guides and layout/link tests.
  - 2026-06-10 progress: added adapter proof gates, Codex no-live-wiring proof, repo-safety checklist and demo proof tests.
  - 2026-06-10 closeout: portable base skills and thin read-only adapter layer accepted as proof-gated artifacts; live runtime wiring (`hooks.json`, Claude commands, Cursor rules, Hermes runtime prompt) remains a future task requiring separate explicit approval.

- [x] **T-105** Реализовать Agent Readiness / Skill Recommendation MVP как read-only repo advisor
  - Trigger: после публикации `docs/skill-products/AGENT_READINESS_SPEC.md`, когда ближайший roadmap scope реально про agent workflow, skill products, repo audit, onboarding или adapter layer, и нет более приоритетного publish/preflight/P0/P1 блока.
  - Scope: добавить deterministic scan для внешнего git repo и выдать Agent Readiness Plan: `Skills`, `Rules`, `Adapters`, `Hooks`; каждая рекомендация имеет `reason`, `evidence`, `severity` и `confidence`.
  - Candidate CLI: `python scripts\reefiki.py agent-readiness --repo <path>`; alias `python scripts\reefiki.py skills recommend --repo <path>` может вести в тот же движок.
  - Outputs: markdown report и JSON; LLM не обязателен для ядра MVP.
  - Reference docs: `docs/skill-products/AGENT_READINESS_SPEC.md`, `docs/skill-products/AGENT_READINESS_README_BLOCK.md`, `docs/skill-products/BASE_SKILLS.md`, `docs/skill-products/AGENT_ADAPTERS.md`, `docs/skill-products/SKILL_PRODUCTS.md`.
  - Relationship to T-104: T-104 создаёт portable skills/adapters; T-105 рекомендует, какие skills/rules/adapters/hooks нужны конкретному repo.
  - Non-goals: no auto-install, no marketplace/external registry, no paid gating, no global Codex/Claude/Cursor config changes, no mutation target repo after scan, no package script execution, no secret reading.
  - Validation: fixture repos for risk mapping, no writes without explicit output path, no package scripts executed, secret-like files skipped, markdown links pass, JSON schema is stable enough for downstream automation.
  - 2026-06-10 progress: first read-only MVP skeleton implemented: `agent-readiness --repo`, `skills recommend --repo`, text/json output, optional report outside target repo, deterministic git/path inventory and first mapping across Skills/Rules/Adapters/Hooks.
  - 2026-06-10 progress: expanded fixture coverage to the spec's 10 synthetic repo shapes; added staged-path, symlink no-follow and low-confidence `review_needed` assertions.
  - 2026-06-10 progress: added deterministic `package_scopes` for monorepos, package-scoped repo types, and scoped rule/adapter recommendations without reading package scripts or mutating target repos.
  - 2026-06-10 progress: tuned noisy heuristics: package manifests alone no longer count as completion evidence, and docs-only `packages/*` folders no longer count as package scopes.
  - 2026-06-10 progress: bounded real-repo scan on Metrica found generated `.vercel/output` package-scope noise; scanner now ignores `.vercel` while keeping root `vercel.json` deploy detection.
  - 2026-06-10 progress: bounded real-repo scan on Coral Compress found source-file secret false positive (`token_count.rs`) and missed nested Rust integration tests; scanner now keeps known source-code extensions with secret-like words and treats `*/tests/*` files as completion evidence.
  - 2026-06-10 progress: follow-up read-only scan on clean Coral Compress (`refactor/v2`) passed without target mutation or heuristic changes; scanner skipped `.env` / `.env.example` by path and produced the expected Skills/Rules/Adapters recommendation for missing `AGENTS.md`.
  - 2026-06-10 progress: README onboarding block added after the clean real-repo proof; runtime adapters, hooks and auto-install remain out of scope.
  - 2026-06-10 closeout: MVP accepted as user-facing read-only advisor; future Windows junction coverage requires a concrete failing scan or path-containment finding.

## Sprint 19 — Worktree lifecycle hardening (Phase 0j follow-up)

- [x] **T-106** Добавить guarded semantic cleanup path для superseded worktrees
  - Trigger: live cleanup triage found branches whose intent was superseded, but `cleanup-worktree` could only prove ancestry and blocked `unmerged_worktree_head`.
  - Scope: add explicit `--semantic-superseded "<evidence>"` opt-in for clean worktrees where useful intent was ported/reimplemented elsewhere.
  - Safety: default unmerged cleanup still blocks; short/empty evidence blocks; dirty/current/missing-base worktrees still block.
  - Docs: `COMMANDS.md` and `docs/WORKTREE_LIFECYCLE.md`.

- [x] **T-107** Make cleanup branch deletion respect the requested base instead of launcher HEAD
  - Trigger: live cleanup from a shared checkout that was behind `origin/main` removed the clean worktree but left its local branch, because `git branch -d` checks merge against the launcher checkout `HEAD`.
  - Scope: after `cleanup-worktree` proves target `HEAD` is reachable from `--base`, apply uses checked force-delete for that local task branch and fails closed if deletion fails.
  - Safety: dirty/current/missing-base/unmerged worktrees still block; force-delete is only after ancestry proof or explicit semantic supersession evidence.
  - Validation: regression test covers cleanup launched from a deliberately behind checkout.

## Sprint 20 — Product readiness backlog from 2026-06-11 product analysis

- [x] **T-108** Add cross-platform CI matrix for Windows and macOS
  - Trigger: product analysis found the public CI still runs only on `ubuntu-latest`, while the primary operator environment is Windows.
  - Scope: extend `.github/workflows/ci.yml` to run the existing validation, tests and memory golden gates on `ubuntu-latest`, `windows-latest` and `macos-latest`, with platform-specific command syntax handled explicitly.
  - Validation: CI workflow remains read-only, finishes within current timeout or a documented adjusted timeout, and catches newline/path issues without changing project runtime behavior.
  - 2026-06-11 closeout: CI now runs the existing validator, pytest and memory golden gates across Ubuntu, Windows and macOS via a non-fail-fast OS matrix. The wiki validation step uses explicit `pwsh` path collection instead of GNU `xargs`, preserving the current 10-minute job timeout and read-only workflow behavior.

- [x] **T-109** Build agent-flow E2E and conformance harness
  - Trigger: core behavior is specified in markdown command contracts, but current tests mostly cover Python helpers rather than full agent-facing flows.
  - Scope: create fixture projects/inbox inputs and deterministic checks for `/save`, `/process`, `/query`, `/harvest`, `/status`, `guard-staged` and publish/preflight behavior; add a conformance checklist for supported agents.
  - Non-goals: no live LLM judge as required gate in CI, no mutation of real project wiki, no external service dependency.
  - Validation: synthetic fixture runs prove expected files, logs, indexes and refusal cases without touching `raw/` outside fixture scope.
  - 2026-06-11 closeout: added `tests/test_agent_flow_e2e.py` with synthetic fixture coverage for save→status, staged-scope guard, publish dirty-worktree preflight and command-contract conformance for `/save`, `/process`, `/query`, `/harvest` and `/status`. Added `docs/AGENT_FLOW_CONFORMANCE.md` as the supported-agent checklist and deterministic no-LLM-judge harness reference.

- [x] **T-110** Define and implement one-command local install path
  - Trigger: product analysis identified installability as the next product boundary after local CLI maturity.
  - Scope: make `pyproject.toml` expose a stable CLI entrypoint suitable for `pipx` or equivalent local install while preserving `python scripts/reefiki.py ...` compatibility.
  - Non-goals: no new runtime dependencies, no cloud account requirement, no marketplace packaging before local smoke.
  - Validation: clean temp environment can install, run `reefiki --help`, run a read-only command against a fixture project, then uninstall cleanly.
  - 2026-06-11 closeout: fixed the `reefiki` console entrypoint by allowing `main()` to default to `sys.argv[1:]`, routed project-level commands before repo-level commands so installed CLI works against a standalone fixture project, documented `pipx install git+...` and checkout install paths, and added a clean venv install/help/status/uninstall smoke test.

- [x] **T-111** Split `scripts/reefiki.py` into a package without breaking the CLI
  - Trigger: `scripts/reefiki.py` is now the memory/search/publish/control-plane monolith; review and blast radius will keep growing if every change touches one 5k+ line file.
  - Scope: incremental package extraction under `reefiki/` or equivalent: `cli`, `index_search`, `memory`, `publish_guards`, `projects`, `agent_readiness`; keep the existing script as a thin compatibility entrypoint.
  - Order: first extract pure helpers with tests, then command handlers, then shared data structures; no behavior change in the first slice.
  - Validation: full pytest, memory golden, representative CLI smoke and publish dry-run still pass after each extraction slice.
  - 2026-06-11 progress: first extraction slice moved pure file/string helpers (`slugify`, numbered paths and exclusive/unique file writers) into `scripts/reefiki_core/file_utils.py` with focused regression tests, while keeping `scripts/reefiki.py` as the compatibility CLI entrypoint.
  - 2026-06-11 progress: second extraction slice moved repo-relative path normalization, target-project validation and scope checks into `scripts/reefiki_core/repo_paths.py` with focused tests, preserving guard-staged, harvest and publish behavior.
  - 2026-06-11 progress: third extraction slice moved project/repo root discovery, project listing, wiki page iteration, DB path and project-relative path helpers into `scripts/reefiki_core/project_paths.py` with focused tests, preserving installed CLI and project status behavior.
  - 2026-06-11 progress: fourth extraction slice moved markdown/frontmatter helpers (`parse_frontmatter`, `as_text`, wikilink extraction and heading chunk extraction) into `scripts/reefiki_core/markdown.py` with focused regression tests, preserving search index, wikilink queue and CLI search behavior.
  - 2026-06-11 progress: fifth extraction slice moved SQLite connection and project-local index lock helpers into `scripts/reefiki_core/storage.py` with focused commit/rollback and lock-file tests, preserving existing search/index and memory golden behavior.
  - 2026-06-11 progress: sixth extraction slice moved subprocess timeout/git-root helper into `scripts/reefiki_core/process_utils.py` and contained-path resolution into `scripts/reefiki_core/repo_paths.py`, preserving project command dispatch and status behavior.
  - 2026-06-11 progress: seventh extraction slice moved index/search helpers and the search printer into `scripts/reefiki_core/index_search.py`, keeping `scripts/reefiki.py` as the compatibility CLI entrypoint and preserving health, dashboard, review queues, memory golden and CLI search behavior.
  - 2026-06-11 progress: eighth extraction slice moved privacy, URL canonicalization, inbox listing and dedup helpers into `scripts/reefiki_core/privacy.py`, preserving `/privacy`, `/dedup`, `/save`, status/health inbox counts and install behavior.
  - 2026-06-11 progress: ninth extraction slice moved doctor payload/output helpers into `scripts/reefiki_core/doctor.py`, preserving doctor, health and dashboard behavior through backward-compatible imports.
  - 2026-06-11 progress: tenth extraction slice moved project status output into `scripts/reefiki_core/status.py`, preserving `/status`, agent-flow and installed CLI behavior through backward-compatible imports.
  - 2026-06-11 progress: eleventh extraction slice moved save/inbox path helpers into `scripts/reefiki_core/save_paths.py`, preserving `/save`, dedup and agent-flow behavior through backward-compatible imports.
  - 2026-06-11 progress: twelfth extraction slice moved plan create/check and timeline helpers into `scripts/reefiki_core/plans.py`, preserving plan checksum and outside-path guard behavior through backward-compatible imports.
  - 2026-06-11 progress: thirteenth extraction slice moved duplicate/source similarity helpers into `scripts/reefiki_core/duplicates.py`, preserving dedup and review-queue behavior through backward-compatible imports.
  - 2026-06-11 progress: fourteenth extraction slice moved wiki row read-model construction into `scripts/reefiki_core/wiki_rows.py`, preserving health, dashboard and review-queue consumers through backward-compatible imports.
  - 2026-06-11 progress: fifteenth extraction slice moved project code-path and graphify report discovery helpers into `scripts/reefiki_core/code_context.py`, preserving memory/status graph context behavior through backward-compatible imports.
  - 2026-06-11 progress: sixteenth extraction slice moved memoir command construction, noisy JSON parsing and subprocess runner helpers into `scripts/reefiki_core/memoir_io.py`, preserving memory lookup behavior through backward-compatible imports.
  - 2026-06-11 progress: seventeenth extraction slice moved generic git subprocess/status/ref helpers into `scripts/reefiki_core/git_utils.py`, preserving publish, cleanup, harvest and worktree behavior through backward-compatible imports.
  - 2026-06-11 progress: eighteenth extraction slice moved private-project inventory and publish diff classification helpers into `scripts/reefiki_core/publish_classification.py`, preserving publish dry-run inventory and public snapshot decisions through backward-compatible imports.
  - 2026-06-11 progress: nineteenth extraction slice moved repository content secret-scan payload construction into `scripts/reefiki_core/secret_scan.py`, preserving harvest, publish and public snapshot secret guard behavior through backward-compatible imports.
  - 2026-06-11 progress: twentieth extraction slice moved worktree status parsing, ahead/behind calculation, recommendation and output helpers into `scripts/reefiki_core/worktree_status.py`, preserving `worktree-status` behavior through backward-compatible imports.
  - 2026-06-11 progress: twenty-first extraction slice moved public snapshot inspect/push helpers into `scripts/reefiki_core/public_snapshot.py`, preserving dry-run leak/secret checks and resume public snapshot behavior through backward-compatible imports.
  - 2026-06-11 progress: twenty-second extraction slice moved cleanup-worktree payload and output helpers into `scripts/reefiki_core/cleanup_worktree.py`, preserving cleanup safety checks and semantic supersession behavior through backward-compatible imports.
  - 2026-06-11 progress: twenty-third extraction slice moved publish-task payload and output helpers into `scripts/reefiki_core/publish_task.py`, preserving private/public publish orchestration through backward-compatible imports.
  - 2026-06-11 progress: twenty-fourth extraction slice moved tool-trigger payload and output helpers into `scripts/reefiki_core/tool_trigger.py`, preserving Understand-Anything/ECC trigger behavior through backward-compatible imports.
  - 2026-06-11 progress: twenty-fifth extraction slice moved memory route decision helpers into `scripts/reefiki_core/memory_route.py`, preserving route/explain/pack behavior through backward-compatible imports.
  - 2026-06-11 progress: twenty-sixth extraction slice moved memory route output helper into `scripts/reefiki_core/memory_route.py`, preserving JSON/text route output through backward-compatible imports.
  - 2026-06-11 progress: twenty-seventh extraction slice moved memory status open/summary helpers into `scripts/reefiki_core/memory_status.py`, preserving memory status gating and summary output through backward-compatible imports.
  - 2026-06-11 progress: twenty-eighth extraction slice moved memory preflight helpers into `scripts/reefiki_core/memory_preflight.py`, preserving policy gate behavior for status, lookup, explain and pack through backward-compatible imports.
  - 2026-06-11 progress: twenty-ninth extraction slice moved memoir store path resolution into `scripts/reefiki_core/memoir_io.py`, preserving environment override and platform default behavior through backward-compatible imports.
  - 2026-06-11 progress: thirtieth extraction slice moved save command helpers into `scripts/reefiki_core/save.py`, preserving URL/file inbox capture and append-only save logging through backward-compatible imports.
  - 2026-06-11 progress: thirty-first extraction slice moved secret-scan output helper into `scripts/reefiki_core/secret_scan.py`, preserving text/json scan output and exit codes through backward-compatible imports.
  - 2026-06-11 progress: thirty-second extraction slice moved guard-staged payload and output helpers into `scripts/reefiki_core/guard_staged.py`, preserving target-project staged path guard behavior through backward-compatible imports.
  - 2026-06-11 progress: thirty-third extraction slice moved review-queue and backlink scan/output helpers into `scripts/reefiki_core/review_queues.py`, preserving review queue, dashboard/health and backlink behavior through backward-compatible imports.
  - 2026-06-11 progress: thirty-fourth extraction slice moved health and dashboard payload/output helpers into `scripts/reefiki_core/health.py`, preserving project health, dashboard and memory reflection behavior through backward-compatible imports.
  - 2026-06-11 progress: thirty-fifth extraction slice moved harvest-commit payload/output helpers into `scripts/reefiki_core/harvest_commit.py`, preserving isolated-index cross-project harvest safety through backward-compatible imports.
  - 2026-06-11 progress: thirty-sixth extraction slice moved golden-query config parsing into `scripts/reefiki_core/memory_golden.py`, preserving memory golden output through backward-compatible imports and focused parser coverage.
  - 2026-06-11 progress: thirty-seventh extraction slice moved project-local memory lookup shaping into `scripts/reefiki_core/index_search.py`, preserving global lookup and memory golden result shape through backward-compatible imports.
  - 2026-06-11 progress: thirty-eighth extraction slice moved memory diff payload/output helpers into `scripts/reefiki_core/memory_diff.py`, preserving since-date baseline resolution and memory reflection consumers through backward-compatible imports.
  - 2026-06-11 progress: thirty-ninth extraction slice moved memory explain payload/output helpers into `scripts/reefiki_core/memory_explain.py`, preserving route/policy/source-decision output through backward-compatible imports.
  - 2026-06-11 progress: fortieth extraction slice moved memory reflection candidate-action selection into `scripts/reefiki_core/memory_reflect.py`, preserving reflection report recommendations through backward-compatible imports.
  - 2026-06-11 progress: forty-first extraction slice moved promotion draft/inbox helpers into `scripts/reefiki_core/promotion.py`, preserving promote dry-run, memory promotion-inbox and backward-compatible imports from `scripts/reefiki.py`.
  - 2026-06-11 progress: forty-second extraction slice moved memory status payload/output helpers into `scripts/reefiki_core/memory_status.py`, preserving memory status summary, fail-on-open and compatibility imports from `scripts/reefiki.py`.
  - 2026-06-11 progress: forty-third extraction slice moved global memory lookup payload/output helpers into `scripts/reefiki_core/memory_lookup.py`, preserving memoir/REEFIKI/graph lookup routing and compatibility imports from `scripts/reefiki.py`.
  - 2026-06-11 progress: forty-fourth extraction slice moved global promote output into `scripts/reefiki_core/promotion.py`, preserving memory promote trace output and compatibility imports from `scripts/reefiki.py`.
  - 2026-06-11 progress: forty-fifth extraction slice moved memory preflight output into `scripts/reefiki_core/memory_preflight.py`, preserving text/json preflight behavior and compatibility imports from `scripts/reefiki.py`.
  - 2026-06-11 progress: forty-sixth extraction slice moved memory reflection report rendering/writing into `scripts/reefiki_core/memory_reflect.py`, preserving report-only reflection behavior and compatibility imports from `scripts/reefiki.py`.
  - 2026-06-11 progress: forty-seventh extraction slice moved memory pack strict/output helpers into `scripts/reefiki_core/memory_pack.py`, preserving CLI memory pack behavior and compatibility imports from `scripts/reefiki.py`.
  - 2026-06-11 progress: forty-eighth extraction slice moved memory golden output formatting into `scripts/reefiki_core/memory_golden.py`, preserving CLI golden behavior and compatibility imports from `scripts/reefiki.py`.
  - 2026-06-11 progress: forty-ninth extraction slice moved memory reflect text/json output formatting into `scripts/reefiki_core/memory_reflect.py`, preserving report-write behavior and compatibility imports from `scripts/reefiki.py`.
  - 2026-06-11 progress: fiftieth extraction slice moved reflection read-only pack quality summarization into `scripts/reefiki_core/memory_reflect.py`, preserving `memory_pack` dependency injection and compatibility wrapper behavior in `scripts/reefiki.py`.
  - 2026-06-11 progress: fifty-first extraction slice moved memory reflect payload assembly into `scripts/reefiki_core/memory_reflect.py`, preserving the `scripts/reefiki.py` compatibility wrapper and injected `memory_pack` dependency.
  - 2026-06-11 progress: fifty-second extraction slice moved memory pack payload assembly into `scripts/reefiki_core/memory_pack.py`, preserving injected lookup/golden dependencies and the `scripts/reefiki.py` compatibility wrapper.
  - 2026-06-12 progress: fifty-third extraction slice moved memory golden payload assembly into `scripts/reefiki_core/memory_golden.py`, preserving injected lookup/promote/pack dependencies and the `scripts/reefiki.py` compatibility wrapper.
  - 2026-06-12 progress: fifty-fourth extraction slice moved memory golden/pack CLI wrapper helpers into `scripts/reefiki_core/memory_cli.py`, preserving injected payload dependencies and the `scripts/reefiki.py` compatibility wrappers.
  - 2026-06-12 progress: fifty-fifth extraction slice moved memory reflect CLI wrapper helpers into `scripts/reefiki_core/memory_cli.py`, preserving report-write behavior and the injected `memory_reflect` dependency.
  - 2026-06-12 progress: fifty-sixth extraction slice moved reflection pack-quality wrapper glue into `scripts/reefiki_core/memory_cli.py`, preserving the injected `memory_pack` dependency used by `memory reflect`.
  - 2026-06-12 progress: fifty-seventh extraction slice moved project command dispatch into `scripts/reefiki_core/project_commands.py`, preserving `scripts/reefiki.py` as a compatibility wrapper with injected command dependencies.
  - 2026-06-12 closeout: `scripts/reefiki.py` is reduced to compatibility wrappers, argparse wiring and runtime dispatch glue; package logic now lives under `scripts/reefiki_core/*` with focused tests for extracted helpers, memory CLI wrappers and project command dispatch. Final gates passed: full pytest, memory golden, memory pack strict, project status smoke and publish dry-run.

- [x] **T-112** Add onboarding wizard for the 5-minute first run
  - Trigger: README/COMMANDS/AGENTS are comprehensive but too large for a first-time zero-coder path.
  - Scope: guided local flow for create/connect project, save a source, process inbox, query wiki, harvest a session result and show status; reuse existing CLI commands and docs.
  - Non-goals: no GUI, no daemon, no Obsidian plugin requirement.
  - Validation: wizard can run in dry-run/fixture mode and produces the same durable artifacts as the documented manual flow.
  - 2026-06-12 closeout: added `reefiki onboarding` with default dry-run plan and `--fixture-root` deterministic demo project generation. The fixture covers create/save/process/query/harvest/status, leaves inbox empty after simulated process, writes raw/wiki/index/log artifacts, is documented in README/COMMANDS, and has core plus CLI E2E coverage.

- [x] **T-113** Add minimal MCP/REST entrypoints only after install and conformance gates
  - Trigger: product analysis confirms MCP is the next compatibility lever, but only after CLI installability and conformance are stable.
  - Scope: expose `query`, `save` and `status` over a minimal adapter that delegates to existing CLI/core functions and preserves project isolation.
  - Non-goals: no vector DB, no new memory runtime, no public network service by default, no write operation without the same guards as CLI.
  - Validation: local adapter smoke against fixture project, no secrets read, no writes outside selected project, and documented rollback.
  - 2026-06-12 closeout: added local JSON `adapter-call` surface for `reefiki_query`, `reefiki_status` and gated `reefiki_save`; query/status are read-only, save requires `--allow-write` and delegates to existing save guards. Usage and rollback are documented in COMMANDS/README, with core tests and live adapter smoke coverage.

- [x] **T-114** Add read-only cross-project query and synthesis with provenance
  - Trigger: product analysis identifies cross-project synthesis as a differentiator, but root contract still requires project isolation for writes.
  - Scope: root-level read-only lookup across `projects/*/wiki/index.md` and selected pages, with explicit source project/page provenance and no durable write unless target project is chosen.
  - Non-goals: no merged database, no auto-promotion across projects, no writes to multiple project wikis in one command.
  - Validation: fixture with two projects proves routing, provenance, duplicate project names/paths safety and no mutation.
  - 2026-06-12 closeout: added read-only `cross-query`, which scans project wiki indexes and referenced markdown pages without creating a merged DB, `.reefiki` SQLite index or durable write. Results include deterministic synthesis plus project/page/sources/sha256 provenance, support explicit `--project-name` routing, block duplicate project filters and warn on unsafe index paths.

- [x] **T-115** Product positioning harvest from 2026-06-11 analysis
  - Trigger: `docs/product-analysis-2026-06-11.md` contains useful positioning and competitive framing, but several implementation-risk claims are already closed or stale.
  - Scope: distill only still-useful product positioning into durable wiki/README material: distillation gate, agent-agnostic portability, golden retrieval baseline, memory pack handoff and local-first markdown control.
  - Non-goals: do not copy stale P0 findings as new blockers; do not publish the whole analysis as canonical truth without errata.
  - Validation: resulting docs link to current ROADMAP/TASKS state and distinguish completed baseline from future work.
  - 2026-06-12 closeout: added a README product-positioning block and `projects/reefiki/wiki/synthesis/product-positioning-2026-06-11.md`, distilling only still-current positioning from the local analysis draft. The page links the completed Sprint 20 baseline back to `TASKS.md`/`ROADMAP.md` and keeps MCP server, vector/hybrid search, marketplace/GTM and managed sync as future work rather than current blockers.

- [x] **T-116** Add local Codex Workspace Ops Board
  - Trigger: operator needs one local read-only screen for all current Codex workspace git projects under `S:\Coding\01_PROJECTS`, with REEFIKI used as enrichment when a project is connected.
  - Scope: add `ops-dashboard` JSON snapshot and localhost UI server; discover one-level git repos only; inspect target projects by safe metadata and git status only; enrich from `projects/<name>` / `.reefiki` mapping; keep MVP read-only.
  - Non-goals: no cloud service, no MCP/vector/runtime dependency, no package-script execution in target projects, no git fetch/pull/push in target projects, no publish/apply/cleanup buttons.
  - Validation: focused ops-dashboard tests, JSON snapshot smoke against `S:\Coding\01_PROJECTS`, localhost server smoke, browser smoke, memory golden, pytest and publish preflight.
  - 2026-06-11 follow-up: web UI now supports persisted language switching (`ru` / `en`), theme switching (`dark` / `light`), a top `Current Work` operator lane for active branches/dirty projects/warnings, and an Activity filter that includes every discovered project without changing dashboard read-only boundaries.
  - 2026-06-11 follow-up: desktop `16:9` layout now keeps the right rail compact by splitting it into a top Activity panel and a lower `Project Detail` + `REEFIKI Control` pair, with internal scroll instead of one tall vertical stack.
  - 2026-06-11 follow-up: desktop `16:9` top viewport is now compressed so summary, `Current Work`, project inventory and the right rail all remain visible together without scrolling past a tall current-work block.

## Sprint 21 — Workflow fail-closed hardening from 2026-06-12 audit

- [x] **T-117** Normalize workflow audit findings into accepted / downgraded / rejected backlog
  - Trigger: `docs/AUDIT_WORKFLOW_2026-06-12.md` identified real workflow risks, but several findings are stale or severity-inflated against current `origin/main`.
  - Scope: write a concise normalization note in `TASKS.md`/`ROADMAP.md` terms: accepted findings, downgraded findings, rejected stale claims, and implementation order.
  - Accepted baseline: operation-aware staged guards, broad-staging contract fixes, append-only log guard, raw immutable guard, publish/cleanup evidence polish.
  - Downgraded baseline: `scripts/reefiki.py` monolith claim is stale after T-111, `privacy` command exists, `--public-snapshot` private-only behavior is API clarity unless guards fail, Claude hook wiring is adapter-layer hardening rather than the portable first fix.
  - Validation: no code change; docs diff only; ROADMAP/TASKS/log stay internally consistent.
  - 2026-06-12 closeout: normalization is captured in `ROADMAP.md` Phase 0k and this Sprint 21 backlog: accepted findings became T-118..T-121, stale/inflated findings were downgraded, and coordination-owner registry stayed design-only in T-122.

- [x] **T-118** Fix unsafe command contracts and broad staging instructions
  - Trigger: audit plus live process work showed command docs still mix "stage only touched files" with broad examples such as `git add -A`, `git add wiki/`, `git add raw/ seen/ inbox/`.
  - Scope: update root/project command docs and root `AGENTS.md` stale git workflow wording so they require explicit paths or a profile-specific helper.
  - Non-goals: no CLI behavior change in this task; no hook installation.
  - Validation: `rg -n "git add -A|git add wiki/|git add raw/|git add seen/|git add inbox/" AGENTS.md .claude projects/reefiki/.claude` returns only intentional historical references or none.
  - 2026-06-12 closeout: removed active broad staging contracts from root/project/template `AGENTS.md`, root `/new` and `/sync-template`, and template/project `/process`, `/lint`, `/resolve`, `/reindex`, `/harvest`; docs now require explicit touched paths or future operation-profile wording. No code, hooks or `guard-staged --mode` behavior changed.

- [x] **T-119** Add operation-aware staged guard modes
  - Trigger: current `guard-staged --target-project <name>` is wiki-only and correctly blocks `seen/`; `/process` needs a distinct safe profile.
  - Scope: extend guard-staged with `--mode harvest|process|docs|code` while preserving existing default behavior for wiki-only harvest.
  - Process mode allowlist: `projects/<name>/inbox/**`, `projects/<name>/seen/**`, `projects/<name>/wiki/log.md`, `projects/<name>/wiki/index.md`, created `projects/<name>/wiki/<type>/*.md`, and raw create-only paths when process explicitly accepts a source.
  - Harvest mode allowlist: `projects/<name>/wiki/**` plus semantic checks for append-only log/index updates.
  - Docs/code modes: root docs and code paths only when declared; never silently include `projects/*/raw/**`.
  - Validation: focused tests for each mode, including a regression where process paths pass and cross-project paths fail.
  - 2026-06-12 closeout: `guard-staged` now supports `--mode harvest|process|docs|code`; default `harvest` preserves wiki-only behavior, `process` allows inbox/seen/wiki/index/log/wiki pages and raw create-only paths, and docs/code profiles block raw paths. Focused guard tests cover pass/block cases.

- [x] **T-120** Add machine guards for append-only log and raw immutability
  - Trigger: `wiki/log.md` append-only and `raw/` immutable are core contracts but currently rely mostly on agent discipline.
  - Scope: add staged/diff checks that reject non-append edits to `projects/<name>/wiki/log.md`; reject modify/delete under `projects/<name>/raw/**`; allow raw create-only only in explicit process mode.
  - Non-goals: do not rewrite existing raw files; do not add a new storage layer.
  - Validation: tests for append, rewrite, deletion and create-only cases; existing process/harvest/publish tests still pass.
  - 2026-06-12 closeout: staged guard now rejects non-append edits to `projects/<name>/wiki/log.md`, rejects raw modify/delete, and allows raw create-only only in explicit process mode. No existing raw files were rewritten.

- [x] **T-121** Improve publish/cleanup evidence surfaces without changing publish semantics
  - Trigger: audit findings around `--public-snapshot`, cleanup branch deletion and JSON reason strings are mostly API/evidence clarity issues, not immediate P0 leaks.
  - Scope: add structured `error_code` to block JSON, add `snapshot_origin` / explicit public snapshot intent fields, add cleanup checks for `codex/` branch prefix and actual task-branch reachability evidence before local branch deletion.
  - Non-goals: no public/private semantic rewrite; no remote branch deletion by default.
  - Validation: focused publish/cleanup tests plus existing `publish-task --dry-run --cleanup --format json` smoke.
  - 2026-06-12 closeout: block JSON now includes `error_code`; publish payloads include `public_snapshot_intent` and `snapshot_origin`; cleanup payloads include branch reachability evidence and block non-`codex/` task branch cleanup. Publish semantics and remote branch deletion behavior were not changed.

- [x] **T-122** Design but defer coordination-owner registry
  - Trigger: coordination files (`ROADMAP.md`, `TASKS.md`, `AGENTS.md`, `wiki/log.md`, `wiki/index.md`) still depend on human integration-owner discipline.
  - Scope: document a minimal future `coordination-claim` design and where it would plug into staged guards.
  - Non-goals: do not implement a lease/lock system until T-118..T-121 are complete and a real parallel-conflict need remains.
  - Validation: design note only or backlog refinement; no runtime behavior change.
  - 2026-06-12 closeout: added `docs/COORDINATION_OWNER_REGISTRY.md` as a deferred design. No lease, lock, hook, daemon or runtime registry was implemented.

## Sprint 22 — Odysseus dogfood follow-up after PR #4093

- [ ] **T-123** Track Odysseus cross-platform regression PR through CI/review
  - Trigger: Odysseus dogfood produced one scoped upstream PR: `pewdiepie-archdaemon/odysseus#4093`.
  - Current proof: WSL full pytest passed with `2189 passed, 1 skipped, 7 warnings`; Windows focused/related tests passed; changed files are limited to `static/js/cookbookRunning.js` and `tests/test_tool_index_keyword_boundaries.py`.
  - Scope: monitor CI/review, answer review comments, and update REEFIKI dogfood notes only if the outcome changes the reusable workflow.
  - Non-goals: no new Odysseus feature work, no REEFIKI MCP/vector/static export, no Hermes work, no Windows portability cleanup in this task.
  - Validation: PR status is recorded with final outcome; if extra code changes are requested, keep them in the same Odysseus PR scope and rerun focused plus relevant full tests.

- [ ] **T-124** Decide whether Odysseus Windows portability/env cleanup is worth a separate task
  - Trigger: only start after PR #4093 CI/review, or if the user explicitly wants Windows support for Odysseus tests.
  - Known bucket: hardcoded `/tmp`, bash vs Windows `S:\...` paths, Node ESM raw drive path / `s:` protocol handling, HOME/local-bin expectations, JS helper path failures, `tool_path_confinement`, and `rag_remove_directory_scope`.
  - Scope: triage and plan Windows support separately from real cross-platform regressions; first output can be a no-code compatibility matrix or a bounded bugfix list.
  - Non-goals: do not mix with PR #4093, do not change REEFIKI/Hermes, do not treat Windows support as required unless a maintainer/user decision says so.
  - Validation: focused Windows repro commands, classification into unsupported/env/test-portability/real bug, and explicit go/no-go before edits.

## Sprint 23 — Product surface and distribution

- [x] **T-125** Build a public demo/static docs surface
  - Trigger: product-readiness baseline is closed and REEFIKI needs a public way to show value without a local checkout.
  - Scope: publish a static, non-sensitive product/demo surface that explains the local-first wiki/control-plane flow, shows current CLI/dashboard/install capabilities and links to safe public docs.
  - Non-goals: no private project content, no managed cloud sync, no account system, no vector/search runtime, no automatic export of private `projects/*`.
  - Validation: generated/served demo contains no private project paths/content, links resolve, and the public/private boundary is documented.
  - 2026-06-13 closeout: added `docs/PUBLIC_DEMO.md` and a README entrypoint as a static public-safe demo surface. It shows the local-first wiki flow, onboarding fixture commands, public-safe capabilities and private boundary rules without implementing a static-site generator, cloud sync, MCP server, vector search, hosted dashboard or marketplace submission.

- [x] **T-126** Create install landing around the one-command path
  - Trigger: T-110 already implemented and smoke-tested the installable `reefiki` CLI entrypoint.
  - Scope: make a concise install landing or docs page for `pipx install git+...`, checkout install, `reefiki --help`, first `status/dashboard/onboarding` commands and uninstall/rollback notes.
  - Non-goals: no marketplace package submission, no auto-update installer, no curl-to-shell installer until the current install path has public proof.
  - Validation: commands are tested from a clean temp environment or linked to the existing install smoke; page distinguishes user install from developer checkout.
  - 2026-06-13 closeout: added `docs/INSTALL.md` and README entrypoint for pipx install, checkout install, first safe commands, developer install, uninstall and smoke verification. It documents current boundaries explicitly: no marketplace package, auto-update installer, curl-to-shell installer, MCP server, vector/hybrid runtime or managed sync backend.

- [x] **T-127** Turn the local dashboard into a product-facing demo
  - Trigger: T-101 and T-116 provide working dashboard JSON plus localhost ops UI.
  - Scope: create a demo path for `reefiki dashboard` / `ops-dashboard serve` that is understandable outside the operator context: screenshots or static demo data, core states, current-work lane and safety boundaries.
  - Non-goals: no cloud dashboard, no remote project mutation, no publish/apply buttons, no live package-script execution in target repos.
  - Validation: localhost smoke or static screenshot proof; demo must show real dashboard value without exposing private project details.
  - 2026-06-13 closeout: added `docs/DASHBOARD_DEMO.md` and README entrypoint for a synthetic-workspace Ops Board demo. It documents expected visible panels, JSON/browser smoke, local-only boundaries and excluded cloud/remote/publish actions without adding a hosted dashboard or mutating target repos.

- [x] **T-128** Write a managed sync product decision without implementation
  - Trigger: product development needs a sync direction before any cloud/runtime work starts.
  - Scope: produce an ADR/spec comparing local-first git sync, filtered public snapshot, encrypted private sync, and managed service options; include threat model, private project boundary and rollback.
  - Non-goals: no backend, no account system, no hosted database, no background daemon, no automatic sync.
  - Validation: decision states go/no-go criteria and the first safe implementation slice, if any, without committing to runtime work.
  - 2026-06-13 closeout: added `docs/MANAGED_SYNC_DECISION.md` and updated the existing `dual-remote-public-snapshot` decision. Current decision: keep local-first git plus filtered public snapshot as default; defer encrypted/private sync until demand and proof gates; managed service backend remains no-go without a separate future slice.

- [x] **T-129** Prepare marketplace/GTM readiness pack without submission
  - Trigger: install path, product positioning and demo surface are available enough to package the story.
  - Scope: collect product narrative, screenshots/demo links, install instructions, supported use cases, security/local-first claims, limitations and target user profile into a reviewable GTM pack.
  - Non-goals: no marketplace submission, no paid gating, no external analytics, no global runtime config changes.
  - Validation: pack is internally consistent with current CLI/dashboard behavior and does not claim cloud/vector/managed sync features that are not implemented.
  - 2026-06-13 closeout: added `docs/GTM_READINESS_PACK.md` and README entrypoint. The pack collects narrative, target users, supported use cases, demo links, install instructions, security/local-first claims, limitations and review checklist; it explicitly excludes marketplace submission, paid gating, analytics, hosted services and cloud sync backend.

## Sprint 24 — Website landing and promo surface

- [x] **T-130** Research GitHub project landing patterns for REEFIKI
  - Trigger: REEFIKI has public docs/install/demo surfaces, but no polished product website.
  - Scope: review current open-source landing patterns: strong hero, product proof, install CTA, GitHub trust signals, comparison, README continuity, mascot identity and interactive explanation.
  - Non-goals: no broad competitive research doc, no new cloud/runtime strategy.
  - Validation: summarize chosen and rejected ideas before implementation.
  - 2026-06-14 closeout: research summarized in `site/README.md`. Chosen pattern: README-continuous open-source product landing with install/docs/GitHub CTAs, product proof, mascot-led interactive explanation and local-first trust signals. Rejected: generic AI gradients, cloud-memory claims and stock SaaS dashboard framing.

- [x] **T-131** Define website IA/copy and README continuity
  - Scope: turn existing README positioning into a concise page structure: Hero, Problem, How it works, Token Economy, Memory Types, Agent-agnostic, Local-first Safety and Final CTA.
  - Validation: CTAs link to Quick Start, docs/install and public GitHub without claiming unimplemented features.
  - 2026-06-14 closeout: `site/index.html` implements the required section order and keeps CTAs pointed at Quick Start, install docs and the public GitHub repository.

- [x] **T-132** Define visual system and mascot usage
  - Scope: refined minimalism with warm technical craft, Rifiki as product guide, palette derived from mascot, no purple/blue AI gradient.
  - Validation: visual direction fits existing assets and remains readable on desktop/mobile.
  - 2026-06-14 closeout: `site/styles.css` defines a warm parchment, reef green, muted teal, moss, coral, amber and graphite system with Rifiki as the central guide in the hero and final CTA.

- [x] **T-133** Plan asset pipeline and missing mascot prompts
  - Scope: use existing mascot/token/architecture assets, list missing Rifiki scenes and ready-to-generate prompts.
  - Non-goals: do not stretch one image across the whole page; do not generate new images in this task unless explicitly requested.
  - 2026-06-14 closeout: existing assets are referenced from `assets/`; missing image prompts are documented in `site/README.md`.

- [x] **T-134** Implement responsive static landing page
  - Scope: create a working `site/` frontend with animation: hero reveal, token dots, cards into distillation gate, subtle graph pulses, hover states and mascot-led transitions.
  - Non-goals: no Next/Vite/Astro build chain unless the repo already has one; no private wiki/project content.
  - Validation: serve locally and verify desktop/mobile.
  - 2026-06-14 closeout: added static `site/index.html`, `site/styles.css` and `site/script.js` with animated distillation hero, flow rail, token economy, memory cards, graph proof, safety terminal and final CTA. No new build chain or private wiki content was added.

- [x] **T-135** Verify browser rendering and link safety
  - Scope: check image loading, text fit, responsive layout, console/page errors and key links.
  - Validation: Playwright/browser smoke on desktop and mobile screenshots.
  - 2026-06-14 closeout: local Chrome/Playwright smoke passed on `1440x900` and `390x844`: HTTP 200, no console/page errors, all images loaded, no horizontal overflow, no detected text overflow, and next section heading visible in the first viewport.

- [x] **T-136** Publish-readiness docs and deploy path decision
  - Scope: document where the site lives, how to open it, which assets are used and what remains optional before public deploy.
  - Non-goals: no push, no deployment and no public snapshot without separate approval.
  - 2026-06-14 closeout: `site/README.md` documents local open instructions, asset usage, missing prompts and publish boundary. No deploy or push was performed.

## Sprint 25 — Active backlog after landing unlock

- [x] **T-137** Add qmd retrieval preflight gate
  - Trigger: qmd candidate existed as wiki synthesis but was not actionable in `TASKS.md`.
  - Scope: add `retrieval-preflight qmd` so agents can distinguish sandbox/eval work from blocked runtime adoption.
  - Non-goals: no qmd install, no MCP daemon, no embeddings, no rerank, no model downloads, no `/query` path switch.
  - Validation: focused tests cover missing project, experiment-ready, runtime-eval-ready and text output; full suite must still pass before publish.
  - 2026-06-14 closeout: implemented `scripts/reefiki_core/retrieval_preflight.py`, wired `scripts/reefiki.py retrieval-preflight qmd`, and added focused regression tests.

- [x] **T-138** Benchmark qmd candidate against current FTS5/golden
  - Trigger: T-137 preflight exists and qmd has a durable synthesis page.
  - Scope: build a fixed small corpus and compare current `search` / `memory golden` behavior with qmd BM25/lex output.
  - Non-goals: no runtime adoption, no MCP daemon, no vector/rerank/model downloads, no global install.
  - Validation: report includes query set, expected pages, FTS5 result, qmd result, misses/improvements, generated path cleanup and go/no-go.
  - 2026-06-14 closeout: added `retrieval-benchmark qmd`, generated `docs/retrieval/qmd-benchmark-2026-06-14.md`, and compared 9 golden lookup cases. FTS5 hit 9/9; qmd BM25 hit 9/9; improved 0, regressed 0. Decision: no adoption benefit, keep qmd disabled by default.

- [x] **T-139** Smoke a local adapter surface without daemon commitment
  - Trigger: T-113 local JSON adapter already exists, while T-40 MCP/REST remains too broad.
  - Scope: verify a minimal local adapter call for `query`, `status` and one read-only project lookup using existing CLI/JSON surfaces.
  - Non-goals: no server, no network listener, no MCP config write, no public API guarantee.
  - Validation: focused tests plus one command-line smoke with structured JSON output.
  - Done: added `adapter-smoke` local CLI/JSON surface; real smoke returned `outcome=pass`, `daemon_started=false`, `network_listener=false`, `mcp_config_written=false`, and write guard blocked `reefiki_save` without `--allow-write`.

- [x] **T-140** Generate link-confidence report before schema changes
  - Trigger: T-21 is useful only if current wikilinks show repeated ambiguity.
  - Scope: read-only report over current `review-queues`, backlinks and wikilinks: extracted-looking, inferred-looking, ambiguous-looking links.
  - Non-goals: no `_schema.md` change, no auto-rewrite of links, no LLM semantic conflict detection.
  - Validation: report states whether confidence tagging is still needed, and if yes gives the smallest schema/doc slice.
  - Done: `link-confidence --project-name reefiki --write-report` generated `docs/link-confidence/link-confidence-reefiki-2026-06-14.md`; live counts were 434 wikilinks, 408 extracted-looking, 18 inferred-looking, 8 ambiguous-looking, so optional confidence tagging is still useful as a smallest future schema/doc slice.

- [x] **T-141** Decide landing publish path after private/public dry-run
  - Trigger: Sprint 24 landing is implemented and `publish-task --dry-run --cleanup` reported public-safe in the landing branch.
  - Scope: repeat dry-run from the integration branch, confirm diff class and choose no-push / private-only / public snapshot path.
  - Non-goals: no push, deploy or cleanup without explicit approval.
  - Validation: dry-run JSON evidence is captured before any apply.
  - Done: `publish-task --dry-run --cleanup --format json` passed from `codex/publish-path-dry-run` with `diff_class=public-safe`; evidence saved under `docs/publish/`. Chosen eligible path is guarded public snapshot flow, but execution state remains no-push/no-apply until explicit approval.

- [x] **T-21a** Add optional confidence marker schema/report support
  - Trigger: T-140 reported 434 wikilinks with 8 ambiguous-looking links, enough for a schema-support slice.
  - Scope: document optional `## Related` confidence markers, teach `link-confidence` to parse/report `[EXTRACTED]`, `[INFERRED]` and `[AMBIGUOUS]`, and make the `code/docs` staged guard profile cover this schema+code slice.
  - Non-goals: no auto-rewrite of existing wiki pages, no qmd runtime, no MCP/server/vector/rerank/model downloads, no README/site/assets changes.
  - Validation: focused marker tests, full pytest, `memory golden`, `link-confidence` smoke, `diff --check`, secret scan and staged guard.

## Принципы ведения задач

1. **Одна задача = один коммит.** Возможен `git revert`.
2. **Триггер обязателен для runtime/cloud/vector/marketplace задач.** Для маленьких local-first growth slices допустим явный bounded scope с тестами, rollback и без смены source of truth.
3. **Тесты до кода.** Для T-01 (validate_frontmatter) — сначала создать тестовый файл с битым frontmatter, потом скрипт.
4. **Логировать в wiki/log.md** после каждого завершённого спринта.
