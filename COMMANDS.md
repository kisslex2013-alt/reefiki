# COMMANDS — справочник команд

Агент работает **автономно** — не ждёт slash-команд. Просто скажи по-человечески, что хочешь, и он сделает. Этот файл — справочник на случай, если хочется вспомнить, что какая команда делает.

Плюс агент сам предлагает действия: разобрать копилку, записать выводы, сохранить навык, проверить здоровье вики — когда видит, что пора.

Полные инструкции для агента — в `.claude/commands/<имя>.md` (в корне для `/new`, в проекте для остальных).

Заметные изменения проекта ведутся в `CHANGELOG.md`.

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

### `/review-queues` (или `reefiki.py review-queues`) / read-only governance scan

**Что делает.** Показывает candidates для governance-очередей durable knowledge: stale, orphan, duplicate, needs verification, conflict.
**Когда нужна.** После крупных `/harvest`, batch `/process`, перед cleanup или когда база растёт.
**Как сказать по-человечески.** «Покажи проблемные страницы durable-слоя», «что у нас stale/orphan/duplicate?».
**Что произойдёт.** Агент выполнит read-only scan и покажет queue type, причину, связанные страницы и suggested action. Ничего автоматически не меняет.
**Дополнительно.** Режим `--type <queue>` фильтрует одну очередь, например `placeholder_link` или `missing_backlink`. Режим `--write-report` пишет markdown-отчёт в `plans/review-queues-YYYY-MM-DD.md` для ручного triage. Агент должен использовать его, когда очередь не пустая и cleanup не закрывается сразу, нужен handoff или пользователь просит план/артефакт.
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
**Что произойдёт.** Агент выполнит read-only поиск. Фильтры: `--type`, `--tag`, `--link-to`, `--linked-by`, `--orphan`. Режим `--chunks` ищет по heading-aware chunks и возвращает matched heading.

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
**Как сказать по-человечески.** «Объясни, почему это пойдёт в такой слой памяти», «почему graphify не используется?».
**Что произойдёт.** Агент покажет route decision, policy preflight, source decisions, excluded sources и next action. Ничего не записывает.
**JSON-режим.** `--format json` возвращает стабильный explain payload для handoff/audit.

### `reefiki.py memory status` / registry, health summary и open-queue gate

**Что делает.** Показывает provider registry и короткий health summary для выбранного REEFIKI project.
**Когда нужна.** Перед реализацией/отладкой unified memory flow: понять, какие слои доступны, какие capabilities они объявляют и есть ли открытые очереди.
**Как сказать по-человечески.** «Покажи registry слоёв памяти», «что умеют memoir/graphify/wiki?», «проверь memory status Metrica», «покажи status всех проектов».
**Что произойдёт.** Агент покажет providers `reefiki`, `memoir`, `graphify`, graphify status, review queue counts и promotion inbox counts для `--project <name>`. С `--all-projects` покажет totals и per-project summary; `--only-open` оставит только проекты с open review queues или active promotion drafts. `--summary` уберёт provider details для компактной проверки. `--fail-on-open` завершит команду ошибкой, если есть open review queues или active promotion drafts. `--format jsonl` отдаёт один project status на строку для automation. Ничего не меняет.

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

### `reefiki.py memory pack` / task handoff bundle

**Что делает.** Собирает компактный context pack для задачи из durable wiki, quality/strict verdict, golden summary, diff summary и open queues.
**Когда нужна.** Перед новым тредом, handoff другому агенту или сборкой следующего этапа REEFIKI 2.
**Как сказать по-человечески.** «Собери пакет контекста по задаче X».
**Что произойдёт.** Агент выполнит policy preflight, подберёт релевантные wiki pages с `why_included`, покажет quality/strict status, open queues, exclusions и не будет писать файлы. `task_route` показывает классификацию текста задачи, а `assembly_trace.pack_scope` отдельно показывает реальный scope сборки pack. При упоминании REEFIKI 2 агент запускает `memory pack --strict` сам.

### `reefiki.py guard-staged` / staged-path guard перед cross-project harvest commit

**Что делает.** Проверяет, что staged-файлы относятся только к `projects/<name>/wiki/**` выбранного проекта.
**Когда нужна.** Перед commit/push после `/harvest` из другого кодового проекта, особенно когда в REEFIKI repo есть чужие dirty-файлы.
**Как сказать по-человечески.** «Проверь, что в коммит попадёт только wiki проекта Metrica».
**Что произойдёт.** Агент сравнит staged paths с разрешённым префиксом. Если есть файлы вне `projects/<name>/wiki/**`, команда завершится ошибкой и покажет blocking paths. Dirty, но не staged файлы не блокируют commit, но должны быть перечислены в финале как excluded.

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
**Что произойдёт.** Dry-run проверит clean worktree, diff относительно base, приватные project paths и нужные действия. Apply push-ит task branch/private main, а при public-safe/mixed делает filtered public snapshot. Dirty worktree, non-fast-forward base и прямой риск public leak блокируются.

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

### `reefiki.py cleanup-worktree` / safe task worktree cleanup

**Что делает.** Проверяет, можно ли удалить отдельный task worktree после publish/merge.
**Когда нужна.** Когда после публикации остался каталог вроде `REEFIKI__harvest_isolated` на ветке `codex/*`.
**Что произойдёт.** Dry-run блокирует dirty worktree, missing base и commit, который ещё не reachable from base. Apply удаляет worktree и пытается удалить local branch только после safety checks.

```bash
python scripts/reefiki.py cleanup-worktree --worktree S:/Coding/01_PROJECTS/REEFIKI__harvest_isolated --dry-run --format json
```

## Команды проекта — обслуживание

Нужны редко.

### `/lint`

**Что делает.** Проверяет здоровье вики по 6 механическим категориям (битый frontmatter, дубли, осиротевшие ссылки, истёкшие карантины, устаревшие страницы, пропавшие связи).
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
