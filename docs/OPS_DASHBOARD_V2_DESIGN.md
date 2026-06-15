# Ops Dashboard v2 — Целевая архитектура

**Замена:** v1 = `scripts/reefiki_core/ops_dashboard.py` (2188 строк, монолитный HTML в raw-строке)
**v2:** полная перепрошивка с нуля
**Дата:** 2026-06-12
**Автор дизайна:** Claude (zero-coder audit, не codex)
**Назначение:** local-first, localhost-only, read-only обзор workspace и состояния REEFIKI для desktop-оператора.

---

## 0. Чего не делаем (constraints, дубль для самоконтроля)

- Local-first. Только bind `127.0.0.1`. Никаких external requests.
- Read-only. Никаких записей в обнаруженные проекты, `raw/`, `.reefiki/`, wiki/log.
- Zero new deps. Никаких framework, no chart-lib, no bundler, no npm. Только Python stdlib.
- Не запускать package-скрипты (`npm test`, `pytest`, `pnpm build` и т.п.) в обнаруженных проектах.
- Не делать `git fetch/pull/push` из dashboard. Только локальный `git log/status/rev-parse/branch`.
- Desktop-фокус 16:9. Mobile — не приоритет.
- Не дублировать v1. v2 — это новая точка входа, старую удаляем вместе с её `run-ops-dashboard.cmd`.

---

## 1. Корень проблем v1 (диагноз, а не правки)

| # | Проблема | Следствие |
|---|----------|-----------|
| 1 | **Нет времени нигде** | Непонятно, что прямо сейчас: трогали проект минуту назад или месяц назад |
| 2 | **Текущая работа = скрытый score** (`workWeight` 1761) | Оператор не знает, почему карточки в таком порядке |
| 3 | **Глобальное и проектное REEFIKI склеены** | Клик по проекту стирает control-plane |
| 4 | **Activity — группировка по проекту, а не хронология** | Ложное ощущение порядка |
| 5 | **Структура страницы — вертикальный стек** | На 16:9 ширина простаивает, главная таблица уходит под фолд |
| 6 | **Весь UI = одна raw-строка в Python** | Невозможно поддерживать, невозможно покрыть тестами |
| 7 | **Дублирование данных в трёх местах** (Detail + REEFIKI-панель + таблица) | Шум, перегруз, потеря фокуса |
| 8 | **Сильная связка backend↔frontend** (HTML/CSS/JS внутри `.py`) | Любая правка = правка Python-файла, никакого hot-reload, никакой раздельной эволюции |
| 9 | **A11y провалы** (Projects table без `tabindex`, `tr.selected` невидим в light) | WCAG AA не выполнен |
| 10 | **Polling на 5s сбрасывает фокус/скролл** (полный re-render) | Раздражает при длинной работе |

Корень всех корней: **v1 пытался быть «доской» и «дашбордом» одновременно**, плюс UI-инженерия была побочной задачей в Python-файле. v2 разделяет это явно.

---

## 2. Принципы v2

### P1. Три отдельных мира, склеенных через общий snapshot
- **Control Plane** — глобальное состояние REEFIKI. Никогда не реагирует на выбор проекта.
- **Work Surface** — что сейчас трогает агент/человек. Только время и активность.
- **Project Inspector** — детальный взгляд на один проект. Только после явного выбора.

Эти три мира **никогда не смешиваются в одном блоке**. Они живут рядом, как три окна, и стыкуются через единый snapshot и общий `selected: projectName | null`.

### P2. Время — главный глагол
Не «что плохого», а «что происходит прямо сейчас». Все карточки, lane'ы, события имеют timestamp. Сортировка по времени desc везде, где есть выбор из N>1.

### P3. Progressive disclosure по умолчанию
- Overview (без выбора) — минимум.
- Лёгкий выбор (клик по lane) — Project Inspector с вкладками.
- Глубокий выбор (конкретная вкладка) — раскрывающиеся секции.
- Никаких всплывающих окон, модальных окон, новых страниц.

### P4. Snapshot — single source of truth, рендер — diff-friendly
Backend отдаёт один `GET /api/snapshot` с полным графом. Клиент держит `currentSnapshot` и `pendingSnapshot`. Polling сравнивает и патчит DOM только там, где изменилось. Никаких `innerHTML = "..."` для всего блока.

### P5. UI из шаблонов, не из конкатенации строк
В v2 — `<template>` в HTML, `cloneNode` + `textContent` в JS. Никаких `innerHTML` с интерполяцией пользовательских данных → нет XSS-класса ошибок, нет проблем с экранированием в JS-логике.

### P6. Тестируемость = требование дизайна
- Каждый чистый селектор/сортировка/правило — функция, не inline-выражение. Экспортируется, тестируется.
- Backend snapshot'а разбит на чистые функции. Уже сейчас частично, но v2 усиливает контракт: `def compute_project_view(repo, ctx) -> ProjectView`.
- HTML — отдельный файл. Можно открыть в браузере с фиктивным snapshot и проверить статически.

### P7. Нулевая магия, явные действия
Никаких таймеров, которые сбрасывают фокус. Polling настраивается. Выбор проекта снимается повторным кликом или `Esc`. Любое «странное» поведение — это либо настройка, либо баг.

---

## 3. Структура файлов

```
scripts/reefiki_core/ops_dashboard/
    __init__.py            # публичный API: snapshot(server_url) и serve(host, port)
    snapshot.py            # build_snapshot(workspace, reefiki) -> Snapshot
    views.py               # чистые функции: derive_project_view(), derive_reefiki_view(), ...
    selectors.py           # current_work(), activity_feed(), kpi_row() — pure, тестируемы
    server.py              # build_handler(snapshot_fn) + serve(host, port)
    static/
        index.html         # одна страница, ~250 строк, без inline-стилей
        app.js             # модуль без сборки, ES2020 (const/let, optional chaining), < 400 строк
        theme.css          # CSS-переменные, dark/light, ~200 строк
        i18n.json          # en/ru
```

**Никаких** `.py` с embedded HTML. Frontend = 4 файла, читаются в браузере по `/static/...` (или подключаются inline в `index.html` для простоты первого шага — см. §11 поэтапный план).

**Удалить** старый `scripts/reefiki_core/ops_dashboard.py` после cutover. Иначе два разных `ops_dashboard` сольются.

---

## 4. Snapshot: модель данных v2

```python
@dataclass(frozen=True)
class CommitRef:
    iso: str              # "2026-06-12T13:47:00+00:00"
    short_sha: str        # "e50b93d"
    subject: str          # "Bump version to 1.5.0: refactor header"

@dataclass(frozen=True)
class ProjectView:
    name: str
    path: str
    branch: str | None
    head: CommitRef | None
    dirty: bool
    dirty_paths_count: int
    dirty_paths_sample: tuple[str, ...]
    ahead: int | None
    behind: int | None
    worktree_count: int
    remotes: tuple[tuple[str, str], ...]      # (name, url)
    detected_stack: tuple[str, ...]
    gates: dict[str, bool]                    # agents_md, ci, tests, package_manifest
    detected_files: dict[str, tuple[str, ...]]
    readiness: str                            # краткая сводка ("dirty; REEFIKI connected")
    warnings: tuple[Warning, ...]
    reefiki: ReefikiLink                     # None | connected/ambiguous/missing
    last_activity: CommitRef | None           # last commit timestamp
    activity_kind: str                        # "codex_branch" | "dirty" | "active" | "quiet"

@dataclass(frozen=True)
class ReefikiControl:
    roadmap_phase: str | None
    current_sprint: str | None
    active_tasks: tuple[Task, ...]
    next_tasks: tuple[Task, ...]
    health_outcome: str                       # "pass" | "warn" | "fail" | "unknown"
    review_queue_top: tuple[ReviewItem, ...]
    t111_status: str | None
    memory_golden_outcome: str                # "skipped" | "pass" | "fail"
    last_log_heading: str | None
    last_log_iso: str | None

@dataclass(frozen=True)
class Kpi:
    total: int
    clean: int
    dirty: int
    codex_branches: int                       # NEW: явный счётчик агентских веток
    connected: int
    warnings: int
    no_tests: int                             # NEW: часто нужный сигнал
    no_agents_md: int                         # NEW

@dataclass(frozen=True)
class Snapshot:
    schema_version: str                      # "ops-dashboard.v2"
    generated_at: str                        # ISO UTC
    workspace_root: str
    reefiki_root: str
    projects: tuple[ProjectView, ...]
    reefiki: ReefikiControl
    kpi: Kpi
```

**Ключевые отличия от v1:**
- `last_activity: CommitRef` на проект (P0-1).
- `activity_kind` (явный, не вычисленный клиентом).
- `kpi` сведён в один объект (v1 размазан по нескольких плейнах).
- `reefiki` — это control plane, не меняется при выборе.
- Всё `frozen=True` и `tuple` вместо `list` — diff-friendly на клиенте.
- `warnings` типизированы.

---

## 5. Frontend: информационная архитектура

### 5.1. Три зоны, фиксированный layout

```
┌─ HEADER (sticky, 64px) ──────────────────────────────────────────────┐
│  ◉ REEFIKI Workspace · Local read-only  · 1m 04s ago  ·  ⚙ ●        │
│  Sub: 14 projects · 2 dirty · 1 codex-branch                          │
└───────────────────────────────────────────────────────────────────────┘
┌─ CONTROL PLANE (top, 2fr:1fr) ───────────────────────────────────────┐
│  REEFIKI GLOBAL (2fr)             │  CURRENT WORK (1fr)              │
│  • Phase, Sprint, Active T-111    │  Top 5 by last activity          │
│  • Health, Review queue           │  project · branch · 4m ago       │
│  • Last log entry                 │  project · dirty 3 · 2h ago      │
│                                   │  project · codex · 1d ago        │
└───────────────────────────────────┴───────────────────────────────────┘
┌─ WORK SURFACE (left, 2fr) ──────────────┬─ INSPECTOR (right, 1fr) ──┐
│  ACTIVITY FEED (timeline)               │  SELECTED PROJECT          │
│  all events sorted by time desc         │  (only if selected)        │
│  • 13:47  project/foo  codex-branch     │                            │
│  • 13:32  project/bar  dirty 5          │  Tabs: Overview · Files ·  │
│  • 12:10  REEFIKI       log "T-111…"    │         Readiness · Logs   │
│                                         │  + sticky to viewport      │
│  PROJECTS (compact table)               │                            │
│  all projects, sortable headers         │                            │
└─────────────────────────────────────────┴────────────────────────────┘
```

### 5.2. Поведение по выбору

| Состояние | Что меняется | Что НЕ меняется |
|-----------|--------------|------------------|
| Ничего не выбрано | Inspector скрыт, Projects table показывает ВСЕ строки | Control Plane, KPI, Activity Feed |
| Выбран проект | Inspector появляется, Projects table **сворачивается в одну строку-превью** выбранного проекта (или скрывается, заменяясь Inspector-превью) | Control Plane, KPI, Activity Feed фильтруется по выбранному |
| Выбран + раскрыта вкладка | Inspector показывает вкладку, Recent Activity (sub-list) внутри Inspector | то же |
| Esc / повторный клик | Снятие выбора | то же |

### 5.3. Приоритеты внутри Activity Feed

Все события несут `timestamp: ISO` и `kind`. Сортировка строго по времени desc. Где времени нет — пометка "—", такие в самый низ.

Типы событий (расширяемо):
- `commit` — push в локальную ветку (по `last_commit_iso`).
- `dirty` — worktree стал dirty с N путями.
- `codex_branch` — проект на ветке `codex/*`.
- `reefiki_log` — заголовок из `wiki/log.md` с датой из заголовка.
- `warning` — новое предупреждение (по коду).

### 5.4. Текущая работа (Current Work)

Только время. Без скрытых score'ов. Сортировка: `last_activity.iso desc`, fallback `name asc`. Limit 5 (не 8 как в v1, лимит виден — «Показать все» в Activity).

### 5.5. Project Inspector (вкладки)

- **Overview:** branch, head (sha + subject + relative time), dirty state, ahead/behind, worktrees, remotes, mapping, readiness, last log heading.
- **Files:** счётчики manifests/CI/tests/agents + `<details>` со списком путей.
- **Readiness:** gates grid (A, CI, T, Manifest — да/нет), safe-next-action, warnings codes.
- **Logs:** 5 последних log-entries из REEFIKI (если connected) + 5 git-entries (subject + relative time).

Активная вкладка — в URL hash (`#overview`, `#files`...). Back/forward работает.

---

## 6. Frontend: рендер без innerHTML

```js
// Один раз, на старте
const tpl = {
    projectRow: document.getElementById('tpl-project-row'),
    kpiCell: document.getElementById('tpl-kpi-cell'),
    activityItem: document.getElementById('tpl-activity-item'),
    warningItem: document.getElementById('tpl-warning-item'),
    detailCard: document.getElementById('tpl-detail-card'),
    // ...
};

// Утилита
function fill(node, mapping) {
    for (const [selector, value] of Object.entries(mapping)) {
        const target = node.matches(selector) ? node : node.querySelector(selector);
        if (target) target.textContent = value == null ? '—' : String(value);
    }
    return node;
}

// Рендер списка — клонирование + заполнение
function renderProjectsTable(projects) {
    const tbody = document.getElementById('projects-tbody');
    const prev = new Map([...tbody.children].map(tr => [tr.dataset.name, tr]));
    const frag = document.createDocumentFragment();
    for (const p of projects) {
        let tr = prev.get(p.name);
        if (!tr) {
            tr = tpl.projectRow.content.firstElementChild.cloneNode(true);
            tr.dataset.name = p.name;
        }
        fill(tr, {
            '.col-name': p.name,
            '.col-branch': p.branch ?? '—',
            '.col-state': p.dirty ? `dirty ${p.dirty_paths_count}` : 'clean',
            '.col-ahead-behind': `${p.ahead ?? '—'}/${p.behind ?? '—'}`,
            '.col-stack': p.detected_stack.join(', ') || '—',
            '.col-last': relativeTime(p.last_activity?.iso),
            // ...
        });
        tr.classList.toggle('selected', p.name === state.selected);
        frag.appendChild(tr);
    }
    tbody.replaceChildren(frag);  // один раз, не innerHTML
}
```

`relativeTime()` — единственная функция форматирования времени; вся i18n времени — в ней.

### Преимущества подхода
- Фокус на `<tr>` сохраняется при polling.
- Скролл tbody не сбрасывается.
- Сравнение `Map(name → tr)` = нативный diff.
- Нет экранирования в JS (textContent не парсит HTML).
- Шаблоны читаются глазами в `index.html`.

---

## 7. Тема и i18n

### 7.1. Тема
CSS-переменные (как v1) + две темы. **Контраст**:
- `tr.selected` — `background: color-mix(in srgb, var(--accent) 22%, transparent); border-left: 3px solid var(--accent);` (видно и в light).
- APCA-уровень WCAG AA на ключевых текстах (muted на bg ≥ 60).
- Light theme: `color-scheme: light`; `prefers-color-scheme` fallback.
- `prefers-reduced-motion: reduce` → отключаем transition на hover/selected.

### 7.2. i18n
- `static/i18n.json` — внешний файл, грузится `fetch('/static/i18n.json')` при init и при смене языка.
- Два языка: `en`, `ru`. Ключи плоские, по доменам: `header.subtitle`, `control.phase`, `work.card.ago`, ...
- Plural-формы для чисел (1 проект / 2 проекта / 5 проектов) — через `Intl.PluralRules`.
- Время — `Intl.RelativeTimeFormat`.

### 7.3. Шрифт
Segoe UI / Aptos / system-ui (как v1). Моноширинный для `branch` и `head` — `ui-monospace, "Cascadia Code", "Consolas", monospace`.

---

## 8. Polling и состояние

### 8.1. Состояние клиента
```js
const state = {
    snapshot: null,            // последний применённый
    pending: null,             // пришёл новый, ждём применения
    selected: null,            // project name | null
    filter: { kind: 'all' },   // фильтр Activity (пока только kind)
    intervalMs: 0,             // 0 = off
    language: 'en',
    theme: 'dark',
};
```

### 8.2. Polling
- По умолчанию **off**. Явная опция в header.
- Tick: `fetch(/api/snapshot)` → сравнить `generated_at` с `state.snapshot.generated_at`.
  - Если равны → ничего не делать.
  - Если новый → применить диффом (через `Map(name → tr)` как в §6).
- Tick 5s polling, но tick активности (relative time, current time в header) — раз в 1s **только для текста**, без ре-fetch.
- `visibilitychange` → пауза, когда вкладка невидима.

### 8.3. Ошибки
- Fetch упал → `lastRefreshEl.classList.add('stale')` + tooltip "Updated Ns ago, refresh failed at HH:MM:SS".
- Snapshot пустой → показать "Empty workspace" в Work Surface, KPI = 0.

---

## 9. Backend v2

### 9.1. Точка входа
```python
# scripts/reefiki_core/ops_dashboard/__init__.py
from .snapshot import build_snapshot
from .server import serve, make_handler

__all__ = ["build_snapshot", "serve", "make_handler"]
```

### 9.2. Snapshot
- `build_snapshot(workspace_root: Path, reefiki_root: Path) -> Snapshot`.
- Чистые функции для derive:
  - `derive_project_view(repo, ctx) -> ProjectView`
  - `derive_reefiki_control(reefiki_root) -> ReefikiControl`
  - `derive_kpi(projects) -> Kpi`
- Каждая функция — top-level (не замыкание), экспортируется для теста.

### 9.3. Команда CLI
- `python scripts/reefiki.py ops-dashboard serve --port 7310`.
- `python scripts/reefiki.py ops-dashboard snapshot --format json` (как v1, для отладки).

### 9.4. Server
- `ThreadingHTTPServer((host, port), handler)`.
- `host = 127.0.0.1` (или `::1` если запросят). Любой другой → `SystemExit`.
- Роуты:
  - `GET /` → `index.html`.
  - `GET /static/<file>` → файлы из `static/` с правильным `Content-Type` и `Cache-Control: no-store`.
  - `GET /api/snapshot` → `build_snapshot(...)` сериализованный в JSON.
  - `GET /api/health` → `{ok: true, generated_at, schema_version}` для keep-alive без тяжёлой работы.
- Логи: `log_message = lambda *a, **k: None` (как v1).

### 9.5. Производительность
- `inspect_workspace_project` — самый дорогой вызов. v2:
  - Использует кеш `mtime`-based на уровне repo. Ключ `(repo_path, snapshot_ts_truncated_to_5s)`. TTL 5s.
  - Это убирает задержку на повторных snapshot'ах при polling.
  - Кеш в памяти процесса, не на диске (read-only, никаких записей).
- Параллелизм: `ThreadingHTTPServer` + `concurrent.futures.ThreadPoolExecutor` для параллельного `inspect_workspace_project` всех repo. Потолок — `min(8, cpu_count)`.

---

## 10. Тестирование

### 10.1. Backend
- `tests/test_ops_dashboard_selectors.py` — деривации, чистые функции, без I/O.
- `tests/test_ops_dashboard_snapshot.py` — с фикстурой временного git repo (через `tempfile` + `subprocess git init`).
- `tests/test_ops_dashboard_server.py` — handler unit (через mock socket или встроенный `http.client`).
- `tests/test_ops_dashboard_safety.py` — что server не биндится на `0.0.0.0`, что `FORBIDDEN_DIR_NAMES` работает.

### 10.2. Frontend
- `tests/test_ops_dashboard_templates.py` — статический парсинг `index.html`: проверить, что все `<template id="tpl-...">` существуют, что на каждый селектор в JS есть узел в шаблоне.
- Manual smoke: открыть в браузере, скриншоты, проверить keyboard nav.

### 10.3. Conformance
- Все `Gates` v1 audit должны быть решены или иметь тикет на «won't fix v2».

---

## 11. Поэтапный cutover

> Цель: не разломать существующее использование. Сначала добавить v2 параллельно, потом удалить v1.

### Шаг 1. Параллельная поставка
- Создать пакет `scripts/reefiki_core/ops_dashboard/`.
- Реализовать `snapshot.py` (бэкенд-часть) на чистых функциях.
- Существующий `ops_dashboard.py` (v1) **продолжает работать** (для тех, кто использует).

### Шаг 2. Frontend без HTTP
- Положить `static/index.html` + `static/app.js` + `static/theme.css` + `static/i18n.json` в `scripts/reefiki_core/ops_dashboard/static/`.
- Реализовать `server.py` (роуты `/`, `/static/...`, `/api/snapshot`).
- Запуск: `python scripts/reefiki.py ops-dashboard serve --port 7310`.
- v1 продолжает работать на отдельном порту (или отключаем явно флагом `--legacy`).

### Шаг 3. Тесты + ручной прогон
- Прогон по acceptance-списку (ниже).
- Скриншоты: dashboard с selected / без selected / с фильтром / dark+light+ru+en.

### Шаг 4. Cutover
- Удалить `scripts/reefiki_core/ops_dashboard.py`.
- Удалить `run-ops-dashboard.cmd`, заменить на запуск через reefiki.py CLI.
- Обновить `docs/` — `OPS_DASHBOARD_UX_AUDIT.md` оставить как историю (но пометить "superseded by V2 design").

### Шаг 5. Observability
- (Опционально, в v2.1) — `/_internal/who` показывает «polling: 5s · last refresh 14:03:00 · generated_at 14:02:58».

---

## 12. Acceptance criteria (Definition of Done v2)

Каждый пункт проверяем вживую перед merge.

### Функциональные
- [ ] При первом открытии видны Control Plane + Current Work + Activity + Projects.
- [ ] Клик по проекту в Current Work → Inspector появляется, проект подсвечен везде.
- [ ] Esc / повторный клик → сброс выбора.
- [ ] Polling 5s не сбрасывает фокус и скролл.
- [ ] Фильтр Activity по kind работает, счётчик событий обновляется.
- [ ] URL hash: `#files` открывает Files, `#logs` — Logs; back/forward переключает.
- [ ] Light theme: `tr.selected` видно (контраст ≥ 3:1 vs соседних строк).
- [ ] ru/en переключение без перезагрузки, плюрализация работает («1 проект / 2 проекта / 5 проектов»).

### Не-функциональные
- [ ] Cold start: server отдаёт `/api/snapshot` за < 2s при 14 проектах.
- [ ] Warm poll: < 200ms (cache hit).
- [ ] Zero new deps: `pip check` не показывает нового; `python -c "import requests"` не импортируется ни в одном файле v2.
- [ ] Bind только на `127.0.0.1` (тест с попыткой `--host 0.0.0.0` → exit 1).
- [ ] Не делает `git fetch` (тест: фиктивный remote с `://0.0.0.0:1` URL — должен работать без сети).
- [ ] Frontend a11y: Tab/Shift-Tab проходит по всем интерактивным; Enter активирует.
- [ ] HTML/CSS/JS отделены от Python: нигде в `ops_dashboard/` нет triple-quoted HTML.

### Миграционные
- [ ] Старый `ops_dashboard.py` удалён.
- [ ] `run-ops-dashboard.cmd` заменён на CLI reefiki.py.

---

## 13. Маленькие решения (фиксирую явно, чтобы Codex не «улучшал»)

1. **`selected: projectName | null`, а не объект.** Имя стабильнее индекса. Diff-friendly.
2. **Никаких глобальных объектов** в JS кроме `state`. Без `window.snapshot`, без `window.dashboard`.
3. **Без сторонних HTTP helpers.** `fetch` нативный. `EventTarget` для событий шины, без library.
4. **Без CSS-in-JS.** Один `theme.css`. Два набора переменных (dark/light) через `:root[data-theme]`.
5. **Без localStorage для состояния выбора** (в v1 был). Selection не переживает reload — это feature, не bug: иначе пользователь возвращается и не понимает, почему всё ещё «selected».
6. **Без web-storage для i18n/theme.** Восстанавливается по `navigator.language` и `prefers-color-scheme`.
7. **Polling off по умолчанию.** Свежесть данных — не самоцель. Если нужен live-режим, явная кнопка «Auto-refresh».
8. **Никаких уведомлений** (Notification API). Оператор смотрит в окно, не отвлекается.
9. **HTML один файл, без JSX, без template literals для разметки.** `<template>` + `cloneNode` + `textContent`.
10. **CSS Grid + Flexbox** для layout. Никаких `position: absolute` кроме `position: sticky` для header и Inspector.

---

## 14. Что НЕ делаем в v2 (расширения на v2.1+)

- Server-Sent Events / WebSocket. Polling хватает для 14 проектов.
- Diff для snapshot'а в JSON (json-patch). Diff на уровне DOM достаточно.
- Multi-workspace tabs. Один workspace за раз.
- Auth. Localhost-only = доверие к среде.
- Persistence. Каждый запуск — свежий.
- Charts. Цифры, не графики (пока не появится use-case).
- File-tree view в Inspector. Только счётчики + список по `<details>`.

---

## 15. Финальная мысль

v1 — это «Python-файл с сайтом внутри». v2 — это «маленький backend + 4 frontend-файла + 4 теста + acceptance-список». Разница не в количестве фич, а в **разделении ответственности и testability**. Backend можно покрыть тестами без браузера. Frontend можно открыть как `file://` с фиктивным snapshot. Полировка UI не требует перезапуска Python. Полировка snapshot'а не требует трогать HTML.

Это и есть «сделать лучше»: не добавить кнопок, а убрать шипение между слоями.
