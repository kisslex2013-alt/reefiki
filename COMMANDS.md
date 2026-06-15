# COMMANDS — справочник команд

Languages: [Русский](#русский) · [English](#english) · [中文](#中文)

## Русский

Агент работает **автономно** — не ждёт slash-команд. Просто скажи по-человечески, что хочешь, и он сделает. Этот файл — справочник на случай, если хочется вспомнить, что какая команда делает.

## English

The agent works **autonomously** and does not require slash commands. Tell it what you want in plain language, and it maps the request to the correct REEFIKI operation.

Most-used intents:

| Intent | Say this |
|---|---|
| Create a wiki project | "Create a new project `<name>` about `<topic>`" |
| Connect a code project | "Connect `<path>` to the wiki" |
| Save a link/file for later | "Put this in the inbox" |
| Process saved material | "Process the inbox" |
| Ask accumulated knowledge | "What did we decide about `<topic>`?" |
| Capture conclusions | "Capture the session conclusions" |
| Check health | "Show project status" / "Run a health check" |

The detailed canonical command reference continues below in Russian.

## 中文

代理会**自主工作**，不需要你记住 slash commands。你可以用自然语言说明目标，代理会映射到正确的 REEFIKI 操作。

常用意图：

| 意图 | 可以这样说 |
|---|---|
| 创建 wiki 项目 | “创建一个名为 `<name>` 的新项目，主题是 `<topic>`” |
| 连接代码项目 | “把 `<path>` 连接到 wiki” |
| 保存链接/文件以后处理 | “把这个放进收件箱” |
| 处理已保存材料 | “处理收件箱” |
| 查询已有知识 | “我们对 `<topic>` 做过什么决定？” |
| 记录会话结论 | “记录本次会话结论” |
| 检查健康状态 | “显示项目状态” / “运行健康检查” |

下面继续保留俄语的详细 canonical command reference。

Плюс агент сам предлагает действия: разобрать копилку, записать выводы, сохранить навык, проверить здоровье вики — когда видит, что пора.

Полные инструкции для агента — в `.claude/commands/<имя>.md` (в корне для `/new`, в проекте для остальных).

Заметные изменения проекта ведутся в `CHANGELOG.md`.

Для первого запуска и восстановления смотри:
`QUICKSTART.md`, `docs/obsidian-setup.md`, `docs/mobile-capture.md`, `docs/RECOVERY.md`.

После локальной установки можно вызывать CLI как `reefiki`:

```powershell
pipx install git+https://github.com/kisslex2013-alt/reefiki-personal.git
reefiki --help
reefiki --project projects/reefiki status
```

Из checkout без установки остаётся рабочим прежний путь:
`python scripts/reefiki.py --project projects/reefiki status`.

## Корневые команды

Запускаются из корня `REEFIKI/` (там, где этот файл).

### `/new <имя>`

**Что делает.** Создаёт новый проект из шаблона `projects/_template/`.
**Когда нужна.** Хочешь начать новую базу знаний по отдельной теме.
**Как сказать по-человечески.** «Создай новый проект `<имя>` про `<тему>`».
**Что произойдёт.** Скопируется шаблон в `projects/<имя>/`, агент задаст 3 вопроса про домен, заполнит `_domain.md`, сделает git-коммит. После — открой папку проекта в любом IDE.

### `/connect <путь> [имя]`

**Что делает.** Подключает кодовый проект к вики. Создаёт junction `_wiki/` в кодовом проекте, маркер `.reefiki`, обновляет AGENTS.md кодового проекта и фиксирует git-bridge contract: `_wiki/` и `.reefiki` не должны жить в git-истории кодового проекта. Если вики-проект не существует — создаёт через `/new`.
**Когда нужна.** Хочешь вести вики для существующего кодового проекта.
**Как сказать по-человечески.** «Подключи проект `<путь>` к вики».

### `/sync-template`

**Что делает.** Синхронизирует обновления из `_template` во все проекты (команды, schema, правила).
**Когда нужна.** После обновления шаблона — новые команды, изменения формата, новые типы страниц.
**Как сказать по-человечески.** «Обнови все проекты из шаблона».

## Команды проекта — ежедневные

Запускаются изнутри `projects/<имя>/`.

### `/save <ссылка или путь>`

**Что делает.** Кладёт URL или файл в `inbox/` (копилку) **без анализа**. Дешёвая операция, нулевое трение.
**Когда нужна.** Увидел что-то стоящее, не хочешь сейчас разбирать — просто чтобы не потерялось.
**Как сказать по-человечески.** «Сохрани `<ссылка или путь>`», «положи это в копилку».
**Что произойдёт.** Файл скопируется в `inbox/` (или создастся стаб с URL). Перед записью агент проверит дубликаты: тот же URL, то же имя в `inbox/`, exact content hash для файла. **Не сохраняет**: секреты, бинарники, файлы >5 MB.

### `/process`

**Что делает.** Разбирает всё, что лежит в `inbox/`. Каждый источник либо превращается в страницу в `wiki/`, либо отправляется в `seen/` с причиной отказа (карантин 30 дней).
**Когда нужна.** Когда копилка набралась (агент сам напомнит при ≥1 файле в начале сессии).
**Как сказать по-человечески.** «Разбери копилку», «обработай что я насохранял».
**Что произойдёт.** Агент прочитает каждый файл, применит внутренние 4 вопроса (дельта / сценарий / тип / решение) + acceptance check, покажет тебе план («X сохраню как страницу про Y, Z отложу как повтор»), спросит подтверждение, потом запишет всё. URL без локального текста — попросит сохранить через Web Clipper.

### `/query <вопрос>`

**Что делает.** Отвечает на вопрос **только** на основе того, что уже есть в `wiki/` твоего проекта. Не из общих знаний.
**Когда нужна.** Хочешь поднять накопленное по теме.
**Как сказать по-человечески.** «Вики, что у нас по `<тема>`?», «спроси у вики `<вопрос>`».
**Что произойдёт.** Агент пройдёт по `wiki/index.md`, найдёт релевантные страницы, прочитает их и составит ответ со ссылками на источники. Обновит счётчики использования (`use_count`).

### `/harvest`

**Что делает.** Извлекает выводы из текущей сессии: решения («выбрал X»), синтез («оказалось что…»), повторяющиеся приёмы.
**Когда нужна.** К концу содержательной сессии — особенно если было «решил…», «выяснили что…», или повторил приём 2+ раза.
**Как сказать по-человечески.** «Запиши выводы из сессии», «зафиксируй что мы поняли».
**Что произойдёт.** Агент пересмотрит ход разговора, предложит сохранить ключевые моменты как страницы (`decisions/`, `synthesis/`, `concepts/`). Ты подтверждаешь — он пишет.

### `/status`

**Что делает.** Показывает состояние проекта одним экраном. Read-only — ничего не меняет.
**Когда нужна.** «Что у нас тут происходит?»
**Как сказать по-человечески.** «Покажи статус», «что у нас».
**Что произойдёт.** Агент посчитает: сколько в копилке, сколько страниц по типам, сколько давно не открывалось, есть ли просроченные карантины, давно ли был `/lint`.

### `reefiki.py doctor` / integrity check

**Что делает.** Проверяет базовую целостность проекта и SQLite-индекса. Read-only — ничего не меняет.
**Когда нужна.** Перед publish/release, после сбоя, или если поиск/индекс ведёт себя странно.
**Как сказать по-человечески.** «Проверь индекс проекта», «проверь целостность».
**Что произойдёт.** Агент проверит обязательные папки и файлы, выполнит SQLite `integrity_check`, сравнит число wiki-страниц с индексом и вернёт `pass` или список проблем.

### `reefiki.py health` / practical knowledge health metrics

**Что делает.** Показывает read-only практические метрики здоровья durable wiki: размер, distillation ratio, использование, orphan/broken links, conflicts, warnings и recommendations.
**Когда нужна.** После batch `/process`/`/harvest`, перед cleanup, перед roadmap phase switch или когда база начинает расти.
**Как сказать по-человечески.** «Проверь здоровье базы знаний», «какие есть тревожные сигналы по wiki?».
**Что произойдёт.** Агент выполнит `doctor` как под-блок, посчитает practical metrics и вернёт `pass`/`warn`/`fail`. `warn` не блокирует работу, но даёт следующий ручной triage step.

### `reefiki.py dashboard` / read-only operator dashboard

**Что делает.** Показывает один короткий read-only экран: practical health, ключевые warning-сигналы, review queue summary и следующий операторский шаг.
**Когда нужна.** Перед ручным triage, после `health`, при вопросе «что дальше по wiki?» или когда полный `review-queues` слишком шумный.
**Как сказать по-человечески.** «Покажи dashboard», «что сейчас делать по базе?», «дай короткий gate status».
**Что произойдёт.** Агент переиспользует `health` и `review-queues --summary`, ничего не пишет и не меняет. `--limit N` ограничивает примеры очередей; JSON-режим отдаёт тот же payload для automation.

### `reefiki.py ops-dashboard` / Codex Workspace Ops Board

**Что делает.** Показывает локальный read-only обзор всех git-проектов Codex workspace на одном экране, а REEFIKI использует как enrichment layer для подключённых проектов.
**Когда нужна.** Когда нужно быстро увидеть состояние всех локальных проектов под `S:\Coding\01_PROJECTS`: clean/dirty, branch, ahead/behind, stack, AGENTS/CI/tests indicators, REEFIKI mapping и последние wiki log entries.
**Как сказать по-человечески.** «Покажи Codex Workspace Ops Board», «открой локальную доску проектов», «дай JSON snapshot workspace».
**Что произойдёт.** Команда discover-ит только git repos на 1 уровень глубины внутри явного `--workspace-root`, выполняет только read-only git/status/metadata checks, не запускает package scripts, не делает fetch/pull/push в target projects и не читает `.env*`, `raw/`, `.git/objects`, `node_modules`, `dist`, `build`, `.next`, `target`.
**JSON snapshot.** `python scripts\reefiki.py ops-dashboard --workspace-root S:\Coding\01_PROJECTS --format json`
**Локальная web-доска.** `python scripts\reefiki.py ops-dashboard serve --workspace-root S:\Coding\01_PROJECTS --port 7310`
**UI.** Web-доска поддерживает переключение языка `ru/en` и темы `dark/light`; выбор хранится локально в браузере. Верхний блок `Current Work` показывает активные агентские ветки, dirty projects, worktree/warning signals и безопасный следующий шаг; `Activity` даёт фильтр по всем найденным проектам, включая plain git projects без REEFIKI log.
**Ограничение MVP.** Web server bind-ится только на `127.0.0.1`; UI не содержит publish/apply/cleanup buttons. Будущие действия показываются только как read-only status или recommended command.

### `reefiki.py onboarding` / first-run wizard

**Что делает.** Показывает короткий первый маршрут: создать проект, сохранить источник, разобрать копилку, спросить wiki, зафиксировать вывод и проверить status.
**Когда нужна.** Первый запуск или проверка установки без чтения больших README/AGENTS.
**Как сказать по-человечески.** «Покажи первый запуск REEFIKI», «создай demo onboarding flow».
**Что произойдёт.** Без `--fixture-root` команда только показывает план и ничего не пишет. С `--fixture-root <папка>` создаёт deterministic demo project в этой папке: raw source, wiki concept, harvest synthesis, index и log; inbox остаётся пустым после simulated process.
**Проверка.**

```powershell
python scripts\reefiki.py onboarding --format json
python scripts\reefiki.py onboarding --fixture-root C:\Temp\reefiki-demo --format json
python scripts\reefiki.py --project C:\Temp\reefiki-demo\projects\reefiki-onboarding-demo status
```

### `reefiki.py adapter-call` / local MCP/REST-ready adapter

**Что делает.** Даёт минимальный локальный JSON entrypoint для будущих MCP/REST wrappers: `reefiki_query`, `reefiki_status`, `reefiki_save`.
**Когда нужна.** Когда агенту или интеграции нужен stable tool-like вызов без парсинга human CLI output.
**Как сказать по-человечески.** «Вызови REEFIKI как adapter tool», «проверь query/status/save через JSON adapter».
**Что произойдёт.** Команда выбирает только явный REEFIKI project из `projects/<name>`. `reefiki_query` и `reefiki_status` read-only. `reefiki_save` пишет только через существующий `/save` path и блокируется без `--allow-write`.

```powershell
python scripts\reefiki.py adapter-call reefiki_status --project reefiki
python scripts\reefiki.py adapter-call reefiki_query --project reefiki --payload "{\"query\":\"memory pack\",\"limit\":3}"
python scripts\reefiki.py adapter-call reefiki_save --project reefiki --payload "{\"source\":\"https://example.com\"}" --allow-write
```

**Rollback.** Это не daemon, не network server и не runtime config. Чтобы откатить adapter surface, достаточно убрать `adapter-call` wiring и `scripts/reefiki_core/adapters.py`; durable wiki/raw/config не создаются, кроме явного `reefiki_save --allow-write` в выбранном проекте.

### `reefiki.py cross-query` / read-only cross-project lookup

**Что делает.** Ищет по `projects/*/wiki/index.md` и указанным там wiki-страницам без создания общей базы, SQLite index или durable write.
**Когда нужна.** Когда нужно найти совпадения и собрать короткую deterministic synthesis по нескольким REEFIKI projects, сохраняя project isolation.
**Как сказать по-человечески.** «Поищи по всем проектам REEFIKI», «собери read-only cross-project evidence».
**Что произойдёт.** Команда читает только wiki index/page markdown, возвращает source project/page/sources/sha256 provenance и предупреждает о небезопасных index paths. Запись в wiki не делается.

```powershell
python scripts\reefiki.py cross-query "adapter provenance" --limit 5
python scripts\reefiki.py cross-query "adapter provenance" --project-name reefiki --format json
python scripts\reefiki.py cross-query "Odysseus dogfood external project onboarding roadmap trigger" --project-name reefiki --format json
```

Для dogfood/onboarding внешнего проекта формулируй запрос узко: называй внешний test-case, сценарий и gate, например `Odysseus dogfood external project onboarding roadmap trigger`. Не используй общий `control plane` wording, если нужна именно dogfood-проверка: он намеренно тянет более широкие control-plane страницы.

**Rollback.** Это read-only CLI surface. Чтобы откатить, достаточно убрать `cross-query` wiring и `scripts/reefiki_core/cross_project.py`; wiki/raw/config не меняются.

### `reefiki.py agent-readiness` / read-only repo skill advisor

**Что делает.** Анализирует внешний git-репозиторий или обычную папку и выдаёт Agent Readiness Plan: какие `Skills`, `Rules`, `Adapters` и `Hooks` нужны агентам для безопасной работы.
**Когда нужна.** Перед подключением нового кодового проекта, перед выдачей задачи AI-агенту, при грязном worktree, нескольких remotes, frontend/auth/deploy/migration surface или непонятных agent rules.
**Как сказать по-человечески.** «Проверь, какие навыки и правила нужны этому репозиторию», «сделай Agent Readiness Plan для `<путь>`».
**Что произойдёт.** Команда read-only: не запускает package scripts, не устанавливает skills/hooks/adapters, не меняет target repo и не читает secret-like файлы глубже path/name checks. JSON/text output содержит `reason`, `evidence`, `severity` и `confidence` для каждой рекомендации. Alias: `reefiki.py skills recommend --repo <path>`.

### `/review-queues` (или `reefiki.py review-queues`) / read-only governance scan

**Что делает.** Показывает candidates для governance-очередей durable knowledge: stale, orphan, duplicate, needs verification, conflict.
**Когда нужна.** После крупных `/harvest`, batch `/process`, перед cleanup или когда база растёт.
**Как сказать по-человечески.** «Покажи проблемные страницы durable-слоя», «что у нас stale/orphan/duplicate?».
**Что произойдёт.** Агент выполнит read-only scan и покажет queue type, причину, связанные страницы и suggested action. Ничего автоматически не меняет.
**Дополнительно.** Режим `--summary` даёт компактные counts, sample pages, top pages и next action по типам очередей. Режим `--type <queue>` фильтрует одну очередь, например `placeholder_link` или `missing_backlink`; text output показывает короткий список и уважает `--limit N`. Для осознанных one-way inbound links target page может содержать секцию `## Intentional one-way inbound links` с plain source ids. Режим `--write-report` пишет полный markdown-отчёт в `plans/review-queues-YYYY-MM-DD.md` для ручного triage. Агент должен использовать его, когда очередь не пустая и cleanup не закрывается сразу, нужен handoff или пользователь просит план/артефакт.
**Stale-процедура.** Устаревшие страницы разбираются только вручную: `use_count=0` без входящих ссылок → кандидат в `seen/` с `reason: stale`; `use_count=0` с входящими ссылками → освежить `useful_when`/связи; `use_count>0` и давно не проверялась → verification источника или процедуры.

### `reefiki.py backlinks` / generated backlink index

**Что делает.** Строит read-only граф связей поверх текущих wiki-страниц: incoming/outgoing links, orphans, broken links.
**Когда нужна.** Перед cleanup, review очередей, поиском осиротевших страниц или проверкой связности durable wiki.
**Как сказать по-человечески.** «Покажи граф ссылок», «найди битые wiki-ссылки», «кто на кого ссылается?».
**Что произойдёт.** Агент выполнит команду без изменения markdown-страниц. Режим `--write` пишет generated artifact `wiki/_backlinks.json`, который можно пересобрать из wiki.

### `reefiki.py search` / frontmatter + link + heading query

**Что делает.** Ищет по wiki через SQLite FTS5 и rebuildable index поверх markdown.
**Когда нужна.** Когда нужен быстрый технический lookup: по типу, тегу, ссылкам, orphan-состоянию или конкретной секции страницы.
**Как сказать по-человечески.** «Найди skill про память», «покажи страницы, которые ссылаются на X», «найди orphan skills».
**Что произойдёт.** Агент выполнит read-only поиск. Фильтры: `--type`, `--tag`, `--link-to`, `--linked-by`, `--orphan`. Режим `--chunks` ищет по heading-aware chunks и возвращает matched heading. Для progressive disclosure в JSON используй `--output compact` без полного body или `--output files` как список `docid`/`path` для точечного чтения.

### `reefiki.py tool-trigger` / read-only gate для внешних tool candidates

**Что делает.** Проверяет, есть ли уже достаточный сигнал для sandbox smoke внешнего инструмента, не устанавливая его.
**Когда нужна.** Когда в сессии звучит “большой незнакомый codebase”, “нужна визуальная карта”, “wiki graph”, “interactive onboarding” или похожий сигнал.
**Как сказать по-человечески.** «Проверь, пора ли тестировать Understand-Anything», «нужна визуальная карта проекта».
**Что произойдёт.** Агент выполнит `tool-trigger Understand-Anything --signal "<сигнал>"` и получит `watch` или `sandbox-recommended`.
**Ограничение.** Даже при `sandbox-recommended` это не установка в основной workspace: только isolated sandbox, без global install, без auto-update hooks, с сравнением против graphify/codegraph/REEFIKI.

### `/promote-dry-run` (или `reefiki.py promote-dry-run`) / dry-run promotion из memoir

**Что делает.** Делает сухой прогон `memoir -> REEFIKI`: стоит ли поднимать knowledge в durable wiki и в какой target type.
**Когда нужна.** Когда есть memory item/вывод и нужно понять: оставить в memoir, игнорировать или оформить как `decision/concept/skill/synthesis`.
**Как сказать по-человечески.** «Проверь, стоит ли это поднимать из memoir в REEFIKI», «сделай promotion dry-run».
**Что произойдёт.** Агент покажет verdict (`ignore` / `memoir-only` / `promote`), suggested type, confidence, review_state и duplicate candidates. Без записи в wiki.
**Дополнительно.** Режим `--write-draft` пишет markdown draft в `plans/` для ручного review перед durable write. Агент должен использовать его, если материал выглядит durable, но нужен typed review, есть риск дубля или источник пришёл из memoir/другого слоя.
**Ещё шаг.** Режим `--apply-draft <путь> --yes` создаёт реальную wiki-страницу из promotion draft. Это mutating шаг, выполнять только по явному подтверждению.

### `reefiki.py memory route` / глобальный router

**Что делает.** Выбирает, в какой контур памяти должен идти новый факт: `memoir`, `REEFIKI` или `graphify`.
**Когда нужна.** Когда неочевидно, это временное правило, durable решение или structural/navigation запрос.
**Как сказать по-человечески.** «Куда это класть: в память агента, в вики или в граф?».
**Что произойдёт.** Агент покажет выбранный слой и короткую причину. Ничего не записывает.
**JSON-режим.** `--format json` возвращает стабильный `RouteDecision`: `recommended_layer`, `secondary_layers`, `reason`, `target_project`, `risk_flags`, `needs_user_confirmation`.

### `reefiki.py memory explain` / объяснение routing и источников

**Что делает.** Объясняет, почему для запроса выбран конкретный слой памяти и какие источники исключены.
**Когда нужна.** Когда нужно понять не только ответ, но и маршрут: REEFIKI wiki, memoir или graphify.
**Routing note.** Roadmap/backlog/phase/review-queue/health-gate запросы считаются REEFIKI governance context; memoir может быть secondary для рабочего контекста.
**Как сказать по-человечески.** «Объясни, почему это пойдёт в такой слой памяти», «почему graphify не используется?».
**Что произойдёт.** Агент покажет route decision, policy preflight, source decisions, excluded sources и next action. Ничего не записывает.
**JSON-режим.** `--format json` возвращает стабильный explain payload для handoff/audit.

### `reefiki.py memory status` / registry, health summary и open-queue gate

**Что делает.** Показывает provider registry и короткий health summary для выбранного REEFIKI project.
**Когда нужна.** Перед реализацией/отладкой unified memory flow: понять, какие слои доступны, какие capabilities они объявляют и есть ли открытые очереди.
**Как сказать по-человечески.** «Покажи registry слоёв памяти», «что умеют memoir/graphify/wiki?», «проверь memory status Metrica», «покажи status всех проектов».
**Что произойдёт.** Агент покажет providers `reefiki`, `memoir`, `graphify`, graphify status, review queue counts и promotion inbox counts для `--project <name>`. С `--all-projects` покажет totals и per-project summary; `--only-open` оставит только проекты с open review queues или active promotion drafts. `--summary` уберёт provider details для компактной проверки и покажет `next_action`, если есть open gate. `--fail-on-open` завершит команду ошибкой, если есть open review queues или active promotion drafts. `--format jsonl` отдаёт один project status на строку для automation. Ничего не меняет.

### `reefiki.py memory preflight` / policy safety check

**Что делает.** Проверяет boundary перед lookup/promote/export/pack: project scope, forbidden paths, public visibility и секретоподобный текст.
**Когда нужна.** Перед public/export/handoff или если есть риск смешать проекты.
**Как сказать по-человечески.** «Проверь, безопасно ли это отдавать/паковать/публиковать».
**Что произойдёт.** Агент вернёт `pass` или `block` с причинами. Ничего не меняет.

### `reefiki.py memory lookup` / единый lookup по слоям

**Что делает.** Ищет по `memoir`, `REEFIKI` и `graphify` через одну точку входа.
**Когда нужна.** Когда нужно быстро понять: «что у нас вообще уже есть по этой теме».
**Как сказать по-человечески.** «Посмотри во всех слоях памяти по X».
**Что произойдёт.** Агент сначала выполнит policy preflight, затем вернёт hits по working memory, durable wiki и graph-report, если он есть у подключённого проекта. Запросы в forbidden project scope блокируются до чтения providers.

### `reefiki.py memory promote` / глобальный promotion flow

**Что делает.** Делает dry-run promotion из глобального working-memory контекста в выбранный REEFIKI project.
**Когда нужна.** Когда вывод уже выглядит durable, но ещё нужно понять: стоит ли поднимать его в wiki и в каком типе страницы.
**Как сказать по-человечески.** «Подготовь это к подъёму в durable knowledge проекта X».
**Что произойдёт.** Агент выполнит policy preflight и такой же gate, как `promote-dry-run`, но через глобальную корневую точку входа. С `--write-draft` запишет review draft в `plans/`; durable wiki page без явного apply не создаёт.

### `reefiki.py memory promotion-inbox` / review drafts

**Что делает.** Показывает promotion drafts из `plans/`, раскрывает draft для review, применяет или отклоняет его явным действием.
**Когда нужна.** Когда `memory promote --write-draft` уже создал drafts, и нужно закрыть review без ручного поиска файлов.
**Как сказать по-человечески.** «Покажи promotion inbox», «прими этот promotion draft», «отклони этот promotion draft».
**Что произойдёт.** Агент выполнит policy preflight и вернёт список активных drafts или один draft через `--show <path>`. `--apply <path> --yes` создаёт durable wiki page и помечает draft applied. `--reject <path> --reason ... --yes` помечает draft rejected и пишет причину в draft/log. `--prune-closed --yes` переносит закрытые drafts в `plans/closed/`; `--all` показывает active + closed archive.

### `reefiki.py memory golden` / baseline memory checks

**Что делает.** Прогоняет `projects/<name>/golden-queries.yml` как контрольный набор lookup/promote cases.
**Когда нужна.** Перед qmd/vector/graph upgrades, `memory diff` и `memory pack`, чтобы измерять качество на стабильных вопросах.
**Как сказать по-человечески.** «Прогони золотые вопросы REEFIKI».
**Что произойдёт.** Агент вернёт pass/fail по cases и не будет писать wiki/draft-файлы. При работе с REEFIKI 2 агент запускает это сам перед изменениями memory-логики.

### `reefiki.py memory diff` / durable wiki diff

**Что делает.** Показывает git-based diff только по `projects/<name>/wiki/**`.
**Когда нужна.** Перед handoff, pack или review: понять, какие durable pages реально изменились.
**Как сказать по-человечески.** «Покажи, что изменилось в памяти проекта», «что изменилось с 2026-05-21?».
**Что произойдёт.** Агент выполнит policy preflight и вернёт changed files/counts между `--from` и worktree/`--to`, либо с baseline по `--since-date YYYY-MM-DD`.

### `reefiki.py memory reflect` / read-only memory reflection report

**Что делает.** Собирает один review report из существующих gates: `memory diff`, `health`, `review-queues --summary`, `memory status --summary`, `memory pack --strict` и `promotion-inbox`.
**Когда нужна.** Когда оператор вручную склеивает 3+ отчёта, queues/diff/promotion дают шумный next-step или нужен компактный weekly/handoff review без durable write.
**Как сказать по-человечески.** «Собери reflection report», «сведи memory diff, health и очереди в один отчёт».
**Что произойдёт.** Агент выполнит read-only сборку и покажет `candidate_actions`, `blocked_actions`, included/excluded sources. `--write-report` пишет только `plans/reflection-YYYY-MM-DD.md`; wiki/raw/seen/config/git не меняются.

### `reefiki.py memory pack` / task handoff bundle

**Что делает.** Собирает компактный context pack для задачи из durable wiki, quality/strict verdict, golden summary, diff summary и open queues.
**Когда нужна.** Перед новым тредом, handoff другому агенту или сборкой следующего этапа REEFIKI 2.
**Как сказать по-человечески.** «Собери пакет контекста по задаче X».
**Что произойдёт.** Агент выполнит policy preflight, подберёт релевантные wiki pages с `why_included`, покажет quality/strict status, open queues, exclusions и не будет писать файлы. `task_route` показывает классификацию текста задачи, а `assembly_trace.pack_scope` отдельно показывает реальный scope сборки pack. При упоминании REEFIKI 2 агент запускает `memory pack --strict` сам. Storage/index ошибки lookup/golden возвращаются как structured strict fail, а не raw traceback.

### `reefiki.py guard-staged` / staged-path guard перед commit

**Что делает.** Проверяет staged-файлы по operation profile: `harvest` (по умолчанию), `process`, `docs` или `code`.
**Когда нужна.** Перед commit/push после `/harvest`, `/process`, docs/code slice или cross-project durable write, особенно когда в REEFIKI repo есть чужие dirty-файлы.
**Как сказать по-человечески.** «Проверь, что в коммит попадёт только wiki проекта Metrica».
**Что произойдёт.** Агент сравнит staged paths с выбранным profile. `harvest` разрешает только `projects/<name>/wiki/**`; `process` дополнительно разрешает `inbox/`, `seen/`, `wiki/index.md`, append-only `wiki/log.md`, created wiki pages и raw create-only paths; `docs`/`code` не разрешают `projects/*/raw/**`. Non-append edits к `wiki/log.md` и raw modify/delete блокируются. Dirty, но не staged файлы не блокируют commit, но должны быть перечислены в финале как excluded.

Пример:

```bash
python scripts/reefiki.py guard-staged --target-project reefiki --mode process --format json
```

### `reefiki.py harvest-commit` / isolated cross-project harvest commit

**Что делает.** Создаёт commit только из явно перечисленных `projects/<name>/wiki/**` файлов выбранного проекта через временный git index.
**Когда нужна.** Когда `/harvest` выполняется из другого проекта или когда в REEFIKI repo есть параллельные dirty/staged изменения от других агентов.
**Как сказать по-человечески.** «Закоммить только harvest Metrica, не трогая Hermes/REEFIKI dirty state».
**Что произойдёт.** Агент передаст target project, список touched wiki-файлов и commit message. Команда заблокирует path вне `projects/<name>/wiki/**`, проваленную wiki-валидацию или target-файл, который уже был staged до запуска. Чужие dirty/staged paths вне target остаются на месте, не попадают в commit и возвращаются в отчёте как excluded/preexisting.

Пример для агента:

```bash
python scripts/reefiki.py harvest-commit --target-project metrica \
  --path projects/metrica/wiki/skills/mobile-adaptation-route-scroll-reset-and-compact-layouts.md \
  --path projects/metrica/wiki/log.md \
  --message "Harvest Metrica mobile layout fixes"
```

### `reefiki.py publish-task` / safe dual-remote publication

**Что делает.** Автоматически классифицирует task branch/worktree перед публикацией: `private-only`, `public-safe`, `mixed` или `block`.
**Когда нужна.** При любой просьбе «push», «пуш», «отправь на git», «merge», «PR», особенно когда работа сделана в отдельном `git worktree`/`codex/*` branch.
**Как сказать по-человечески.** «Опубликуй безопасно с учётом private/public repo».
**Что произойдёт.** Dry-run проверит clean worktree, diff относительно base, fail-closed private project inventory, content scan изменённых файлов, приватные project paths и нужные действия; если нужен public snapshot, dry-run также построит filtered snapshot и просканирует итоговые staged public files без push. Apply push-ит task branch/private main, а при public-safe/mixed делает filtered public snapshot и перед public push повторяет scan итоговых staged public files. Dirty worktree и non-fast-forward base блокируются.

Стартовый dry-run:

```bash
python scripts/reefiki.py publish-task --dry-run --cleanup --format json
```

Применение после pass:

```bash
python scripts/reefiki.py publish-task --apply --cleanup --format json
```

Если private push уже прошёл, а public snapshot упал по сети:

```bash
python scripts/reefiki.py publish-task --apply --public-snapshot --format json
```

Текущие ограничения:

- `scripts/public-snapshot.private-projects.txt` должен оставаться полным и актуальным; Python path блокирует missing/empty/incomplete inventory, но сам список всё равно является critical safety surface.
- Content scan rule-based: он блокирует известные secret-like patterns, но не заменяет human review для спорного public text.
- `push-public.ps1` остаётся manual fallback для PowerShell/Windows-сценариев.

### `reefiki.py cleanup-worktree` / safe task worktree cleanup

**Что делает.** Проверяет, можно ли удалить отдельный task worktree после publish/merge.
**Когда нужна.** Когда после публикации остался каталог вроде `REEFIKI__harvest_isolated` на ветке `codex/*`.
**Что произойдёт.** Dry-run блокирует dirty worktree, missing base и commit, который ещё не reachable from base. Apply удаляет worktree и удаляет local branch только после safety checks; branch cleanup проверяется fail-closed. Если intent уже перенесён или заменён без ancestry-merge, нужен явный semantic evidence:
`--semantic-superseded "<что именно заменило этот branch>"`. Короткая/пустая evidence строка блокируется.

```bash
python scripts/reefiki.py cleanup-worktree --worktree S:/Coding/01_PROJECTS/REEFIKI__harvest_isolated --dry-run --format json
```

### `reefiki.py worktree-status` / parallel worktree lifecycle status

**Что делает.** Read-only показывает состояние всех git worktrees: path, branch, head, dirty paths, dirty groups by scope, ahead/behind vs base, ancestry и рекомендацию `keep`/`delete`/`review`/`block`.
**Когда нужна.** Перед closeout, publish, cleanup или разбором старых task worktrees.
**Что произойдёт.** Команда ничего не удаляет, не stage-ит и не меняет git state. С `--scope <path>` отдельно показывает `excluded_dirty_paths`, `scope_conflicts` и рекомендацию для dirty shared checkout. С `--ledger <path>` добавляет owner/milestone/lease status из LeadOps ledger. Правила lifecycle описаны в `docs/WORKTREE_LIFECYCLE.md`.

```bash
python scripts/reefiki.py worktree-status --format json
python scripts/reefiki.py worktree-status --scope projects/reefiki --format json
python scripts/reefiki.py worktree-status --ledger plans/leadops/worktree-ledger.json --format json
```

### `reefiki.py orchestration-check` / LeadOps control-plane preflight

**Что делает.** Read-only объединяет live worktree inventory, LeadOps ledger, coordination-file owner checks, remote `codex/*` branch cleanup candidates, optional global Codex rule scan and local CI visibility.
**Когда нужна.** Перед publish/cleanup длинного batch, при параллельных worktrees, при проверке разрозненности или перед передачей работы другому агенту.
**Что произойдёт.** Команда не создаёт и не удаляет worktree, не stage-ит, не commit-ит и не push-ит. `block` означает: текущий task worktree грязный, нет owner/milestone/lease discipline, есть конфликт coordination files или global rule scan нашёл опасный паттерн. GitHub branch protection возвращается как manual check, потому локальный git не доказывает настройки GitHub.

```bash
python scripts/reefiki.py orchestration-check --ledger plans/leadops/worktree-ledger.json --format json
python scripts/reefiki.py orchestration-check --ledger plans/leadops/worktree-ledger.json --include-global-config --format json
```

## Команды проекта — обслуживание

Нужны редко.

### `/lint`

**Что делает.** Проверяет здоровье вики по механическим категориям: битый frontmatter, `id` vs filename, schema_version проекта, дубли, осиротевшие ссылки, истёкшие карантины, устаревшие страницы, пропавшие связи.
**Когда нужна.** Раз в месяц или после большого батча `/process`. Агент сам напомнит после 10 операций `/process`.
**Как сказать по-человечески.** «Проверь здоровье вики», «прогон линта».
**Что произойдёт.** Агент пройдёт по wiki, покажет список проблем по категориям, для каждой предложит fix. Ничего не меняет без подтверждения.
**JSON-режим.** Для CI/агентов можно запускать `scripts/validate_frontmatter.py --format json ...`; ошибки содержат `path`, `code`, `message`, `line`, `column`, `expected`, `actual`.

### `/resolve`

**Что делает.** Закрывает старые конфликты в страницах (блоки `## Conflicting claims` старше 30 дней).
**Когда нужна.** Если `/status` сообщает про невыключенные конфликты, или сам помнишь, что давно был спорный момент.
**Как сказать по-человечески.** «Закрой старые споры», «разреши конфликты в вики».
**Что произойдёт.** Для каждого конфликта старше 30 дней агент покажет старое и новое утверждение, спросит: оставить старое / новое / оба / нужно копнуть. По выбору правит страницу и логирует решение.

### `/reindex`

**Что делает.** Пересобирает `wiki/index.md` из frontmatter всех страниц. **Аварийная команда** — для восстановления.
**Когда нужна.** Индекс рассинхронился с реальными файлами или испорчен.
**Как сказать по-человечески.** «Пересобери индекс», «восстанови оглавление вики».
**Что произойдёт.** Текущий `index.md` сохранится как `index.md.bak`, новый соберётся заново из всех страниц. Битые страницы (без обязательных полей) попадут в отчёт — их нужно чинить вручную или через `/lint`.

## Discovery

### `/help`

**Что делает.** Показывает список команд на простом языке (специально для случая «забыл, что умеешь»).
**Когда нужна.** Запутался; объясняешь кому-то третьему как этим пользоваться.
**Как сказать по-человечески.** «Что ты умеешь?», «помоги», «как этим пользоваться».
**Что произойдёт.** Агент выдаст короткий plain-text список с ежедневными командами и пометкой про обслуживающие. Без модификаций.

## Шпаргалка одним экраном

| Хочу…                          | Команда                 |
| ------------------------------ | ----------------------- |
| Создать новый проект           | `/new <имя>` (из корня) |
| Сохранить ссылку/файл          | `/save <что-то>`        |
| Разобрать копилку              | `/process`              |
| Спросить у вики                | `/query <вопрос>`       |
| Зафиксировать выводы из сессии | `/harvest`              |
| Посмотреть состояние           | `/status`               |
| Проверить здоровье             | `/lint`                 |
| Закрыть старые споры           | `/resolve`              |
| Восстановить индекс            | `/reindex`              |
| Объяснение команд              | `/help`                 |

В 90% случаев хватает `/save` и `/query` — остальное Claude напомнит сам в нужный момент.
