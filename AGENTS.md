# AGENTS.md — REEFIKI (root contract)

## ⛔ Запреты (читай первым)

- **В корне нельзя:** `/save`, `/process`, `/query`, `/harvest` — только внутри `projects/<name>/`.
- Не создавай страницы в `projects/<name>/wiki/` из корневого режима.
- Не объединяй базы разных проектов без явной просьбы.
- Не модифицируй `raw/` ни в одном проекте — immutable архив.
- Не редактируй старые записи в `wiki/log.md` — только append.
- Не выходи за пределы папки проекта в рабочем режиме.

## 🗺 Режимы работы (читай вторым)

**cwd = корень REEFIKI/** → **диспетчерский режим.**
В начале сессии: найди папки в `projects/` (кроме `_template`), скажи:
> «У тебя есть проекты: [список]. Создать новый (`/new <имя>`) или перейти в существующий?»

Из корня доступны только:
1. `/new <имя>` — создать проект (`.claude/commands/new.md`).
2. `/connect <путь>` — подключить кодовый проект (`.claude/commands/connect.md`).
3. `/sync-template` — синхронизировать шаблон (`.claude/commands/sync-template.md`).
4. Cross-project search по `projects/*/wiki/index.md` — только чтение.
5. Аудит структуры: проверить наличие `raw/`, `wiki/index.md`, `wiki/log.md`, `AGENTS.md`, `_domain.md`.
6. Глобальный memory orchestration через `scripts/reefiki.py memory ...`:
   - `memory route` — выбрать слой (`memoir` / `REEFIKI` / `graphify`)
   - `memory lookup` — единый lookup по слоям
   - `memory promote` — dry-run promotion в конкретный REEFIKI project

**cwd = `projects/<name>/`** → **рабочий режим.**
Читай `projects/<name>/AGENTS.md` — там полный контракт. Этот файл больше не нужен.

---

Это **agent-agnostic контракт** для всего репозитория REEFIKI. Любой LLM-агент (Claude Code, Cascade/Windsurf, Cursor, Codex CLI, Aider, Cline, GPT в web, …) — читай этот файл как источник истины.

Vendor-specific entrypoints (`CLAUDE.md`, `.cursorrules`, `.windsurf/rules/main.md`, `.codex/instructions.md` и т.п.) — это короткие стабы, ссылающиеся сюда. Они нужны, чтобы соответствовать конвенциям конкретного агента, но **правила живут здесь и в `projects/<project>/AGENTS.md`**.

## Что это за репозиторий

REEFIKI — это **мульти-проектная персональная distillation-вики**. Пользователь складывает в неё источники (URL, файлы, репозитории, заметки) по разным темам, по одному проекту на тему. Агент (ты) читает источники, применяет фильтр из 4 внутренних вопросов и либо записывает wiki-страницу, либо отказывает с причиной (карантин 30 дней).

Цель — **не** пересказ тренировочных данных. Цель — зафиксировать то, что пользователь уже прочитал/решил, чтобы в следующей сессии можно было это поднять.

Дизайн опирается на:

- Karpathy, [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
- REEF protocol (capture / distillation / telemetry).
- Vannevar Bush, Memex (1945).

## Структура репо

```text
REEFIKI/
├── AGENTS.md            # этот файл — корневой контракт
├── README.md            # для людей: первое знакомство
├── COMMANDS.md          # для людей: справочник команд
├── ROADMAP.md           # для людей: что подключать дальше
├── CLAUDE.md            # стаб → AGENTS.md (для Claude Code)
├── .cursorrules         # стаб → AGENTS.md (для Cursor)
├── .clinerules          # стаб → AGENTS.md (для Cline / Roo Cline)
├── .codex/instructions.md   # стаб → AGENTS.md (для Codex CLI)
├── .windsurf/rules/main.md  # стаб → AGENTS.md (для Cascade/Windsurf)
├── .serena/project.yml      # конфиг Serena (initial_prompt → AGENTS.md)
├── .claude/commands/
│   ├── new.md           # /new — создать новый проект
│   ├── connect.md       # /connect — подключить кодовый проект
│   └── sync-template.md # /sync-template — обновить проекты из шаблона
└── projects/
    ├── _template/       # эталон, не работаем здесь напрямую
    └── <name>/          # конкретный проект — основное место работы
```

## Операции на уровне проекта (краткий перечень)

Когда ты внутри проекта, ты поддерживаешь эти операции. Пользователь может вызывать их:

- как slash-команды (Claude CLI): `/save`, `/process`, `/query`, `/harvest`, `/status`, `/lint`, `/resolve`, `/reindex`, `/help`
- на естественном языке: «сохрани X», «разбери копилку», «спроси у вики Y», «зафиксируй выводы», «проверь здоровье вики», ...

Распознай интент и выполни операцию. **Каждая операция полностью специфицирована в `projects/<name>/.claude/commands/<op>.md`** — это обычные markdown-файлы, читаемые любым агентом. Имя папки `.claude/` сохранено для совместимости с Claude CLI; содержимое vendor-neutral.

| Операция | Что делает |
|---|---|
| `save` | Кладёт URL/файл в `inbox/`. Без анализа. |
| `process` | Разбирает `inbox/` → `wiki/` или `seen/`. |
| `query` | Отвечает на вопрос только из накопленного в `wiki/`. |
| `harvest` | Извлекает выводы из текущей сессии. |
| `status` | Read-only обзор состояния проекта. |
| `lint` | Проверяет здоровье вики (6 механических категорий). |
| `resolve` | Закрывает старые `## Conflicting claims` (≥30 дней). |
| `reindex` | Пересобирает `wiki/index.md` из frontmatter. Аварийная команда. |
| `help` | Plain-text справочник для пользователя. |

Подробности: `projects/<name>/.claude/commands/<op>.md` или `COMMANDS.md` в корне.

## Принципы (распространяются на все проекты)

1. **Дистилляция, не архивация.** Сохраняется не «что это», а «что я могу из этого взять».
2. **`useful_when` обязателен.** Конкретный сценарий применения, не «может пригодиться». Без него — отказ в `seen/`.
3. **Capture отдельно от analysis.** `/save` дешёвый, `/process` батчем.
4. **Явный отказ.** Не подходит — запись в `seen/` с `quarantine_until`, не overwrite.
5. **Конфликты не перезаписываются.** Секция `## Conflicting claims` в существующей странице.
6. **Логируется всё.** `wiki/log.md` append-only. Append идёт **до** `git commit`, чтобы лог попал в коммит.
7. **Изоляция проекта.** Не выходить за пределы папки проекта во время рабочего режима.
8. **Чистое удаление старого.** Если решение признано неудачным — убирать целиком, не оставлять хвосты, переходники, заглушки.
9. **Процедура > факт.** Сохраняй метод, который позволяет проверить и воспроизвести результат, а не одноразовый факт.

## Автономность агента

Агент не ждёт slash-команд. Он распознаёт интент пользователя из контекста и выполняет соответствующую операцию. Подробности в project-level `AGENTS.md`.

## Cross-project skill sharing

Skills (навыки) изолированы в проектах, но могут быть полезны везде. Из корневого режима (диспетчер) агент может:

- **Поиск skills по всем проектам:** пользователь спрашивает «есть ли навык про X?» → агент ищет в `projects/*/wiki/skills/` и `projects/*/wiki/index.md` (секция Skills).
- **Копирование skill в другой проект:** по явному запросу — скопировать файл, обновить index/log в целевом проекте.

Это единственное исключение из принципа изоляции: агент **читает** skills из других проектов, но не модифицирует их.

## Global Memory Layer

В корне REEFIKI действует единая внешняя оболочка над тремя контурами памяти:

- `memoir` — short working memory и preferences;
- `graphify` — structure map подключённого кодового repo;
- `REEFIKI` — durable knowledge, decisions, procedures, synthesis.

Правило: объединять **routing/lookup/promotion**, но не сливать сами хранилища в одну базу.

- `route` решает, куда должен попасть новый факт;
- `lookup` может читать сразу из нескольких слоёв;
- `promote` поднимает ценное из `memoir` в REEFIKI как typed durable artifact.

Ограничение: durable write в REEFIKI всегда идёт в **явно выбранный project**. Глобальный orchestration не отменяет project isolation.

### Cross-project harvest / push rule

Если агент работает из другого кодового проекта и пользователь явно просит `/harvest`, «зафиксируй», «сохрани выводы» или похожий durable write, push в REEFIKI допустим только для wiki-артефактов выбранного проекта: `projects/<name>/wiki/**`.

Обязательные условия:

- target project должен быть явно определён до записи;
- staged/committed paths должны быть ограничены этим `projects/<name>/wiki/**`;
- для cross-project harvest commit использовать `python scripts/reefiki.py harvest-commit --target-project <name> --path <file> ... --message "<msg>"`, чтобы коммит собирался через изолированный git index;
- если агент всё же stage-ит вручную, перед commit/push выполнить `python scripts/reefiki.py guard-staged --target-project <name>` и остановиться, если outcome не `pass`;
- unrelated dirty files, особенно в других `projects/*`, нельзя stage/commit/push;
- в финале агент обязан перечислить touched paths и отдельно excluded dirty files;
- если touched paths выходят за выбранный project-scope, остановиться и не пушить без явного подтверждения пользователя.

Dirty worktree вне выбранного `projects/<name>/wiki/**` сам по себе не блокирует `/harvest`; это excluded context. Блокер — только committed paths вне scope или конфликт в тех же target-файлах. Не использовать `git add -A` и общий git index для cross-project harvest, потому что чужие staged-файлы из параллельных тредов могут попасть в commit.

### Dual-remote publish rule

Если пользователь просит «push», «пуш», «отправь на git», «запушь», «merge», «PR», «объедини ветку» или похожую публикацию REEFIKI-изменений, агент обязан использовать skill `reefiki-dual-remote-publish` и начать с:

```powershell
python scripts\reefiki.py publish-task --dry-run --cleanup --format json
```

Без этого нельзя делать ручной `git push`. REEFIKI имеет два remote:

- `origin` — private источник истины;
- `public` — только filtered orphan snapshot без приватных `projects/<name>/`.

Если dry-run показывает `private-only`, пушить только `origin`. Если `public-safe` или `mixed`, сначала обновить private `origin`, затем делать filtered public snapshot. Никогда не пушить private branch напрямую в `public`. После успешного publish удалить task worktree/branch только если worktree clean и commit уже reachable from `origin/main`; иначе оставить и явно объяснить почему.

### REEFIKI 2 startup contract

Если пользователь упоминает `REEFIKI 2`, `memory control plane`, `memory pack`, `handoff` или просит «продолжай REEFIKI 2», агент **сам** запускает из корня:

1. `memory pack <task> --project reefiki --strict`
2. `memory golden --project reefiki`

Пользователь не должен помнить эти команды. Если `pack --strict` или `golden` падает — сначала показать короткий блокер и чинить доказанную проблему, а не расширять архитектуру.

Исключение для быстрых durable writes: если пользователь говорит «запомни», «зафиксируй», «сохрани важное», `/harvest` или похожую фразу, даже с упоминанием `REEFIKI 2`, это **не** startup/handoff. Сначала выполни project-level `/harvest` в явно выбранный или текущий project. Не запускай `memory pack --strict`/`golden`, пока пользователь не просит продолжить разработку REEFIKI 2, собрать handoff/context pack или менять memory-логику.

Перед любыми правками memory-логики (`scripts/reefiki.py`, `scripts/reefiki_memory/`, `tests/test_reefiki_memory_*`) `memory golden --project reefiki` обязателен как regression baseline.

Не подключать qmd/vector/rerank/новые providers, пока `memory golden` или `memory pack --strict` не покажут измеримые misses текущего lookup/pack.

## Code navigation tools

Для задач по коду в корне REEFIKI используй инструменты слоями:

1. `graphify-out/GRAPH_REPORT.md`, если он есть, — как карту большого codebase.
2. `ast-index` — только для кода: символы, usages, outline по `scripts/`, `tests/` и другим исходникам.
3. `rg`, `git status`, `git diff` и тесты — как источник истины перед выводами и правками.

Ограничение: REEFIKI в основном markdown/wiki repo, поэтому `ast-index` не заменяет поиск по `projects/*/wiki/`, `wiki/index.md`, `wiki/log.md` и другим knowledge-файлам. Для wiki-знаний используй обычный текстовый поиск и REEFIKI-команды.

## Schema (формат страниц)

Полный формат frontmatter и тела страниц — в `projects/<name>/wiki/_schema.md`. Lazy-load: читай только когда создаёшь или правишь страницу.

## Safety — что не сохранять

`/save` и `/process` отказывают молча или с понятным сообщением, если источник содержит:

- **Секреты.** `.env*`, `id_rsa*`, `*.pem`, `*.key`, `*.pfx`, `.aws/credentials`, `.ssh/`, файлы с подозрительными именами (`secret`, `password`, `token` без расширения).
- **Запрещённые директории.** `.git/`, `node_modules/`, `vendor/`, `__pycache__/`, `dist/`, `build/`, `target/`, `.next/`, `.cache/`.
- **Бинарники.** По расширению (`.exe`, `.dll`, `.so`, `.dylib`, `.bin`, `.iso`, `.zip`, `.tar`, `.7z`, изображения и видео без явного контекста). PDF/docx — спросить у пользователя.
- **Размер.** Файлы >5 MB — отказ или подтверждение.

Сообщение об отказе формулируется по-человечески: «Не сохраняю `<имя>` — похоже на секрет/бинарник/слишком большой. Если уверен — переложи руками или скажи явно».

## Стиль общения с пользователем

По умолчанию пользователь — **не программист**. Не знает терминов из этого файла, не пишет markdown, не запускает команды оболочки. Говори бытовым языком.

- **Не используй технические термины без необходимости.** Если без них никак — переводи в той же фразе. Бытовые соответствия: «копилка» = `inbox/`, «отказ» = `seen/`, «архив» = `raw/`, «вики» = `wiki/`, «зачем нужно» = `useful_when`, «страница» = wiki-страница, «сохранил» = записал в wiki, «отложил» = в `seen/`.
- Технические артефакты (`frontmatter`, `slug`, `kebab-case`, `quarantine_until`, `[[Related]]`, `ADR`, `commit`, `git`, `source_id`) — твой внутренний словарь, не транслируй.
- Команды оболочки (PowerShell / bash / cmd) и сниппеты — не показывай. Нужна команда — выполняй сам, отдай только результат.
- Внутренние reasoning-структуры («4 вопроса», «acceptance check») — не транслируй. Покажи только итог: «X сохраню как страницу про Y, Z отложу как повтор».
- Если пользователь сам пишет техническими терминами — отзеркаль его словарь, не упрощай искусственно.
- Не будь нянькой. Если действие легально и пользователь явно его просит — выполняй спокойно, без перестраховок.

## Git workflow

Команды, изменяющие `wiki/`/`raw/`, коммитят сами в порядке: **изменения файлов → append `wiki/log.md` → обновить `wiki/index.md` → `git add -A` → `git commit`**.

Лог-запись идёт **до** коммита — чтобы запись попала в тот же коммит. Это критично, нарушать нельзя.

Телеметрия (`use_count` / `last_used`) не коммитится в `/query` — батчится в ближайший `/process` / `/lint` / `/harvest`.

## Запреты (общие)

- Не модифицируй `raw/` ни в одном проекте — immutable архив.
- Не редактируй старые записи в `wiki/log.md` — только append.
- Не выходи за пределы папки проекта в рабочем режиме.
- Не объединяй базы разных проектов без явной просьбы пользователя.
- Не создавай страницы в `projects/<name>/wiki/`, находясь в корне.

## Для конкретных агентов

Этот файл — vendor-neutral. Vendor-specific конвенции:

- **Claude Code (CLI / VSCode extension)** — читает `CLAUDE.md` (стаб → сюда) и `.claude/commands/*.md` (детальные спеки операций).
- **Cascade (Windsurf)** — читает `.windsurf/rules/main.md` (стаб → сюда). Workflows из `.windsurf/workflows/` опциональны.
- **Cursor** — читает `.cursorrules` (стаб → сюда). Альтернатива: `.cursor/rules/*.mdc`.
- **Codex CLI / Aider** — читают `AGENTS.md` напрямую (этот файл).
- **Cline / Roo Cline** — читают `.clinerules` (стаб). Если стаба нет — `AGENTS.md`.
- **Web Claude / ChatGPT Projects** — пользователь загружает `AGENTS.md` (и при работе в проекте — также `projects/<name>/AGENTS.md`) как project knowledge / system context.
- **Любой другой агент** — читай `AGENTS.md` (этот файл) и при работе в проекте — `projects/<name>/AGENTS.md`. Этого достаточно.

Если агент не знает, что делать — он должен **сообщить пользователю**, что прочитал `AGENTS.md` и попросить уточнить операцию или цель сессии. Не выдумывать.

## Куда смотреть дальше

- `projects/<name>/AGENTS.md` — контракт конкретного проекта.
- `projects/<name>/_domain.md` — тема проекта (что это вообще про что).
- `projects/<name>/wiki/_schema.md` — форматы страниц.
- `projects/<name>/.claude/commands/<op>.md` — детальные спецификации операций.
- `COMMANDS.md` — человеческий справочник команд.
- `README.md` — первое знакомство для людей.
