# Ops Dashboard — UX/UI/Frontend Audit & Implementation Brief

**Target:** `scripts/reefiki_core/ops_dashboard.py` (2188 строк: Python backend + монолитный HTML/CSS/JS в raw-строке 844–2132)
**Repo:** REEFIKI (worktree `REEFIKI-ops-dashboard-run`)
**URL:** http://127.0.0.1:7310/ · запуск: `run-ops-dashboard.cmd`
**Дата:** 2026-06-12
**Аудитор:** read-only review, код не менялся.

> Для агента Codex: это бриф на доработку. Каждый пункт = где / почему / как / критерий. Соблюдай constraints из раздела «Hard constraints» — нарушение любого = откат.

---

## Hard constraints (не нарушать)

- Local-first, **localhost-only** (bind строго `127.0.0.1`, строка 2172 — оставить как есть).
- **Read-only**: никаких записей в обнаруженные проекты, в `raw/`, в REEFIKI wiki.
- **Без новых зависимостей**: no cloud, no MCP, no vector, no runtime deps, no npm, no chart-libs, no frameworks.
- **Не запускать** package-скрипты обнаруженных проектов (тесты/build/lint).
- **Не делать** `git fetch/pull/push` внутри target-проектов из dashboard logic. Разрешён только локальный read git (`log`, `status`, `rev-parse` и т.п.).
- Desktop/workstation фокус. Mobile — не приоритет.

---

## Snapshot модели данных (как сейчас)

Backend `ops_dashboard_snapshot()` отдаёт:
```
{ workspace{root, discovered_project_count, refresh_timestamp, warnings[]},
  projects[ {name, path, branch, head, dirty, dirty_paths_count, dirty_paths_sample,
             ahead, behind, worktree_count, remotes[], detected_stack[],
             has_agents_md, has_ci, has_tests, has_package_manifest, detected_files{},
             readiness_summary, reefiki_mapping{}, reefiki_status{}, latest_log_entries[], warnings[]} ],
  reefiki{ roadmap, current_sprint, task_counts, active_tasks[], next_tasks[],
           sprint_20_status, t111_package_split_status, latest_log_entries[],
           health_summary, review_queue_summary, ... },
  summary{ total/clean/dirty/connected/warnings, top_blockers[], next_actions[] } }
```
Frontend-состояние: `snapshot`, `selected`, `detailTab`. Зоны: Summary → top-grid (Current Work + REEFIKI Control) → workspace-layout (Projects + Detail | Activity rail).

---

## Проблемы по severity

### P0 — ломают главную задачу «понять, чем занят агент»

#### P0-1. Нигде нет времени — доска не отвечает на «что прямо сейчас»
- **Где:** `inspect_workspace_project` (583–612); `renderCurrentWork` (1836); Activity `renderLogs` (2032).
- **Почему:** на проект нет ни одной временной метки (last commit, mtime, когда обновлялась ветка). Оператор видит `dirty`, но не знает — трогали 2 минуты или 2 недели назад. Для ops-доски это центральный провал. Порядок Current Work задаёт скрытая эвристика `workWeight` (1761: dirty=40, codex=30, …) — непрозрачно для пользователя.
- **Как чинить:** в backend добавить на проект `last_commit_iso` = `_git_output(repo, ["log","-1","--format=%cI"])` и `last_commit_subject` = `…--format=%s`. Дёшево, локально, read-only. На фронте — относительное время «N мин назад» и сортировка Current Work по нему.
- **Критерий:** верхняя карточка вида `REEFIKI-ops-dashboard-run · codex/… · dirty 3 · обновлено 4 мин назад`.

#### P0-2. Выбор проекта уничтожает глобальную REEFIKI-панель без пути назад
- **Где:** `renderReefiki` (1785) — ветка `if (selected) {…} else {…}`. Снятия выбора нет; `selected` переживает refresh (`syncSelected`, 1730).
- **Почему:** клик по любому проекту полностью заменяет глобальный control-plane (roadmap, sprint, active/next task, health, review queue, T-111) на mini-карточки проекта. Глобальный статус REEFIKI **исчезает**, вернуть — только перезагрузкой страницы.
- **Как чинить:** убрать ветку `if (selected)` — REEFIKI Control всегда показывает глобальное. Проектную связь перенести в Project Detail (там она уже почти вся есть). Доп.: кнопка/повторный клик «Сбросить выбор».
- **Критерий:** глобальный roadmap/sprint/health не пропадает никогда; детали проекта — только в Detail.

### P1 — серьёзно бьют по IA и восприятию

#### P1-1. На широком 16:9 верх раздут, таблица Projects уходит под фолд
- **Где:** медиазапрос строки 1280–1284: `.top-grid { grid-template-columns: 1fr }`.
- **Почему:** Current Work и REEFIKI Control стоят двумя полноширинными баннерами друг под другом (каждый с `max-height` ~150–160px и внутренним скроллом). На 1080p Summary + эти два блока = почти весь первый экран, главная таблица Projects начинается ниже сгиба. Горизонталь широкого монитора простаивает.
- **Как чинить:** в `@media (min-width:981px)` поставить `.top-grid { grid-template-columns: 2fr 1fr }` (Current Work — герой, REEFIKI уже). Альтернатива — REEFIKI-global в правый rail к Activity.
- **Критерий:** на первом экране 1080p сразу видно Current Work + таблицу Projects.

#### P1-2. Данные выбранного проекта дублируются в трёх местах
- **Где:** Project Detail (`renderDetail` 1900, вкладки) + REEFIKI Control в project-scope (1793–1802) + подсветка строки таблицы. mapping/readiness/safe-action/latest-log показываются дважды.
- **Почему:** визуальный шум и перегруз, лишние карточки.
- **Как чинить:** следствие P0-2 — убрать project-scope из REEFIKI-панели, детали оставить только в Detail.

#### P1-3. Activity — не хронология, а группировка по порядку проектов
- **Где:** `renderLogs` (2032–2090). Записи копятся в порядке итерации `data.projects`; синтетические события без timestamp; финал `entries.slice(-16).reverse()`.
- **Почему:** «Активность» выглядит лентой, но упорядочена по алфавиту проектов, а не по времени — для ops-фида бесполезно понять последовательность.
- **Как чинить:** прикрепить timestamp каждому событию (из P0-1 + даты log-заголовков), сортировать по времени desc; где времени нет — «—».
- **Доп. баг:** строка 2073 `if (selectedFilter !== "all" && !entries.length)` проверяет **глобальную** длину `entries` внутри per-project цикла → fallback «нет активности» срабатывает некорректно при фильтре. Вынести проверку за цикл по конкретному проекту.

#### P1-4. Главная таблица Projects недоступна с клавиатуры
- **Где:** `renderProjects` (1893–1897) — только `click`. При этом `lane` (1865) и `log-entry` (2085) имеют `tabindex` + `bindKeyboardActivation`.
- **Почему:** ключевая поверхность не управляется с клавиатуры, второстепенные — да. Несогласованно, WCAG AA провал.
- **Как чинить:** строкам `tabindex="0"`, `role="button"`, `aria-selected`, привязать `bindKeyboardActivation`.

### P2 — полировка

- **P2-1. Состояние выбора непоследовательно.** `.selected` (1114–1118) только у строки таблицы. Клик по lane в Current Work подсвечивает строку, но не сам lane. Ввести общий `data-selected` на lane/row/log-entry выбранного проекта.
- **P2-2. Нет loading/skeleton; ошибка прячет только Summary.** `refresh()` при ошибке (2108) пишет error лишь в `#summary`; остальные панели висят со старыми данными без пометки «устарело». До первого ответа — пусто. Добавить skeleton + stale-бейдж во всех панелях.
- **P2-3. Время в Summary — сырой ISO UTC.** `refresh_timestamp.replace("T"," ")` (1780) → `…+00:00`. Форматировать в локальное `HH:MM:SS` + относительное.
- **P2-4. `setInterval(renderLogs, 5000)` (2127) крутится всегда,** даже при «Auto: Off», и полностью перестраивает DOM ленты (теряются фокус/скролл). Полный `renderProjects` тоже сбрасывает скролл таблицы. Привязать к auto-refresh и/или делать частичный re-render.
- **P2-5. Summary мешает KPI и мету.** Из 6 карточек «Last refresh» и «Refresh mode» — служебные. Вынести в header, освободив место под KPI (dirty / codex-ветки / без тестов).
- **P2-6. i18n/мелочи:** `gates` mini выводит литерал `health=pass` (1816, префикс не переведён); подсказки `activityHint`/`detailHint` дублируют очевидное. Light-тема: `tr.selected` (accent 10%) почти не виден — поднять контраст.
- **P2-7. Технический риск (техдолг):** весь UI — одна raw-строка ~1280 строк внутри `.py`, без линтинга JS. Экранирование `esc()` применяется сквозно → XSS-риск низкий (это плюс). Монолит оставить как есть в рамках MVP, но зафиксировать как долг.

---

## Предлагаемая desktop-раскладка

```
┌─ Header: title · Language · Theme · Refresh · Auto ───────────────────┐
├─ KPI row: total · clean/dirty · codex-ветки · connected · warnings ───┤
├───────────────────────────────────────────┬───────────────────────────┤
│  CURRENT WORK (hero, 2fr)                   │  REEFIKI (global, 1fr)    │
│  ─ сортировка по «обновлено»                │  roadmap · sprint         │
│  ─ проект · ветка · dirty · «4 мин назад»   │  active/next task         │
│  ─ active task T-XXX                        │  health · review · T-111  │
│                                             │  (НЕ меняется при выборе) │
├─────────────────────────────────┬──────────┴───────────────────────────┤
│  PROJECTS (таблица, keyboard)    │  ACTIVITY (sticky rail)              │
│  выбор → подсветка везде         │  хронология по времени desc          │
│  ───────────────────────────────│  фильтр проекта                       │
│  PROJECT DETAIL (вкладки)        │  события с timestamp                 │
│  overview/readiness/files/logs   │                                      │
│  ← вся проектная REEFIKI-связь   │                                      │
└──────────────────────────────────┴──────────────────────────────────────┘
```

Ключевое: REEFIKI-global всегда виден и не переключается; вся проектная информация консолидирована в Project Detail; Current Work — герой с временем.

---

## Implementation plan (по шагам, для Codex)

1. **Backend (read-only):** в `inspect_workspace_project` добавить `last_commit_iso` (`git log -1 --format=%cI`) и `last_commit_subject` (`--format=%s`) через существующий `_git_output`. Без сети.
2. **Current Work:** сортировка по `last_commit_iso` desc (fallback `workWeight`), относительное время, active-task из mapping если есть.
3. **REEFIKI-панель:** убрать ветку `if (selected)`; всегда глобальный control-plane. Проектную связь — в Detail.
4. **Layout:** в `@media (min-width:981px)` → `.top-grid { grid-template-columns: 2fr 1fr }`.
5. **Activity:** timestamp всем событиям, сортировка по времени desc; починить fallback-баг (2073).
6. **A11y:** строкам таблицы `tabindex`/`role`/keyboard; кнопка/клик для снятия выбора.
7. **Selection feedback:** общий `data-selected` на lane/row/log-entry.
8. **Polish:** loading + stale-бейдж во всех панелях, локальное форматирование времени, привязать 5s-таймер к auto-refresh, вынести мету из Summary в header, контраст light `tr.selected`.

**Критерий успеха каждого шага:** `run-ops-dashboard.cmd` → открыть `http://127.0.0.1:7310/`, проверить вживую (golden path + dark/light + ru/en), импорт без ошибок: `python -c "import scripts.reefiki_core.ops_dashboard"`.

---

## Что НЕ делать (чтобы не раздуть MVP)

- Никаких websocket/SSE/live-стриминга — поллинга достаточно.
- Никаких chart-библиотек, фреймворков, npm-зависимостей.
- Не запускать package-скрипты обнаруженных проектов ради метрик.
- Не делать `git fetch/pull/push` для свежести ahead/behind — только локальный `git log`.
- Не трогать `raw/`; состояние выбора/фильтров не писать на диск (localStorage хватает).
- Не переделывать под mobile.
- Не добавлять per-file git-blame/diff — замедлит refresh при многих проектах.

---

## Сильные стороны — сохранить, не ослаблять

- **Безопасность backend:** `FORBIDDEN_DIR_NAMES`, пропуск secret-like путей, `followlinks=False`, reparse-point проверка, лимиты `MAX_METADATA_FILES/DEPTH`, `GIT_OPTIONAL_LOCKS=0`, bind только `127.0.0.1`, отказ вызывать memory-golden/publish (724, 729). Образцовый read-only контур.
- **`_safe_payload` (695):** частичные падения не роняют доску.
- **Сквозное `esc()`** → низкий XSS-риск.
- **CSS-переменные тема** dark/light + `prefers-color-scheme` + localStorage.
- **Полный ru/en i18n** (1447–1672).
- **Progressive disclosure уже есть:** вкладки Detail + `<details>` — правильное направление, расширять.
- **`syncSelected` по `path`** сохраняет выбор между refresh.
- **Sticky header + sticky right-rail.**

**Итог:** backend и safety-модель сильные — трогать не нужно. Основная работа на фронте: время (P0-1), развести глобальный/проектный REEFIKI (P0-2), перекомпоновать верх под широкий монитор (P1-1).
