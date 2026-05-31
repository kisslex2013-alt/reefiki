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

- [ ] **T-21** Confidence tagging для cross-reference edges в `_schema.md` (Phase 1)
  - Триггер: активация Phase 1 (qmd search)
  - Паттерн: `EXTRACTED` / `INFERRED` / `AMBIGUOUS` по образцу [graphify](https://github.com/safishamsi/graphify)
  - Применять к связям `[[wikilinks]]` между страницами когда их станет достаточно
  - Источник отложен в `seen/`, май 2026

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

- [ ] **T-41** Vector/graph search layer
  - Отложено до реальных промахов FTS5 или сильной синонимии.

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

- [ ] **T-76** Повторно проверить `codebase-memory-mcp` только после простого Windows smoke path
  - Не менять REEFIKI runtime.
  - Не тратить implementation time, пока install route не даёт полезный локальный output.

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

## Принципы ведения задач

1. **Одна задача = один коммит.** Возможен `git revert`.
2. **Триггер обязателен** для задач из backlog. Без триггера — не начинать.
3. **Тесты до кода.** Для T-01 (validate_frontmatter) — сначала создать тестовый файл с битым frontmatter, потом скрипт.
4. **Логировать в wiki/log.md** после каждого завершённого спринта.
