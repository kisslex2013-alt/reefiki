# REEFIKI — Аудит: Dashboard

> Дата: 4 июня 2026. Дополнительная тема по результатам анализа UX и onboarding.

---

## 12.1 Философия дашборда

Дашборд — это **не замена CLI**, а визуальный слой поверх него. Три принципа:

- **Local-first:** работает без интернета, данные не покидают машину
- **CLI-прозрачность:** каждое действие в UI — это видимая CLI-команда под капот
- **Progressive disclosure:** базовый вид простой, расширенные метрики скрыты до запроса

Стек: **Python + FastAPI** + **HTMX** + **минимальный CSS**. Никакого React, никакого Node.js — только то, что уже есть в Python-окружении.

```bash
# Запуск
reefiki dashboard

# Или с параметрами
reefiki dashboard --port 7777 --project research --open
```

---

## 12.2 Визуальный язык

**Цветовая схема — две темы:**

```css
/* Dark (по умолчанию) — Catppuccin Mocha */
--bg:        #1e1e2e;
--surface:   #313244;
--overlay:   #45475a;
--text:      #cdd6f4;
--subtext:   #a6adc8;
--accent:    #89b4fa;
--green:     #a6e3a1;
--yellow:    #f9e2af;
--red:       #f38ba8;
--purple:    #cba6f7;

/* Light — переключается кнопкой */
--bg:        #eff1f5;
--surface:   #ffffff;
--text:      #4c4f69;
--accent:    #1e66f5;
```

**Типографика:**
```css
font-family: "Inter", system-ui, sans-serif;
/* Моноширинный для CLI-вывода */
font-family: "JetBrains Mono", "Fira Code", monospace;
```

**Принципы компоновки:**
- Сетка 12 колонок, gap 16px
- Карточки с `border-radius: 12px`, тонкая граница `1px solid var(--overlay)`
- Иконки: Lucide (SVG, встроены инлайн — без внешних зависимостей)
- Анимации: только `transition: 0.15s ease`

---

## 12.3 Структура — три уровня

```
┌─────────────────────────────────────────────────────────┐
│  SIDEBAR          │  MAIN CONTENT                   │
│  (постоянный)     │  (меняется по разделу)          │
│                   │                                 │
│  🌊 REEFIKI       │  [ активный раздел ]            │
│                   │                                 │
│  ▸ Главная        │                                 │
│  ▸ Поиск          │                                 │
│  ▸ Проекты        │                                 │
│  ▸ Копилка        │                                 │
│  ▸ Вики           │                                 │
│  ▸ Здоровье       │                                 │
│                   │                                 │
│  ───────────────    │                                 │
│  [+ Сохранить]    │                                 │
│                   │                                 │
│  ⚙ Настройки      │                                 │
└───────────────────┴─────────────────────────────────┘
```

Sidebar фиксированный, 220px. На мобильном — скрывается, появляется по гамбургеру.

---

## 12.4 Core — Главная страница

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Добрый день 👋                          research  ▾   🌙  ⚙   │
│  Вики в хорошем состоянии                                       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔍  Найти в вики...                              ⌘K           │
│                                                                 │
├─────────────────┬───────────────┬───────────────┬──────────────┤
│                 │               │               │              │
│  📥 Копилка     │  📄 Страниц   │  ✅ Здоровье  │  🔥 Серия   │
│                 │               │               │              │
│      3          │     127       │    Good       │   12 дней   │
│                 │               │               │              │
│  разобрать →    │  смотреть →   │  детали →     │              │
│                 │               │               │              │
├─────────────────┴───────────────┴───────────────┴──────────────┤
│                                                                 │
│  Последняя активность                                           │
│                                                                 │
│  ● Сохранено: "SQLite FTS5 performance tips"          2ч назад │
│  ● Добавлена страница: python-async-patterns           вчера   │
│  ● Разобрана копилка (3 → 0)                          3д назад │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Быстрые действия                                               │
│                                                                 │
│  [+ Сохранить ссылку]  [📋 Разобрать копилку]  [🔍 Поиск]     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Приветствие** меняется по времени суток и состоянию:

```python
def get_greeting(health_score: str, lang: str) -> str:
    hour = datetime.now().hour
    time_part = {
        "ru": "Доброе утро" if hour < 12
              else "Добрый день" if hour < 18
              else "Добрый вечер",
        "en": "Good morning" if hour < 12
              else "Good afternoon" if hour < 18
              else "Good evening",
    }[lang]

    status_part = {
        "excellent": "Вики в отличной форме 🌟",
        "good":      "Вики в хорошем состоянии",
        "fair":      "Есть что улучшить в вики",
        "poor":      "Вики требует внимания ⚠️",
    }[health_score]

    return f"{time_part} 👋\n{status_part}"
```

**Серия** — количество дней подряд с активностью (геймификация). Считается по `wiki/log.md`.

---

## 12.5 Core — Поиск

Главная функция — быстрый доступ через `⌘K` / `Ctrl+K` из любого места:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  🔍  python async                                    ✕  ⌘K     │
│                                                                 │
│  ────────────────────────────────────────────────────────────────    │
│                                                                 │
│  Страницы вики (4)                                              │
│                                                                 │
│  📄  python-async-patterns                          skill      │
│      "Используй asyncio.gather() для параллельных..."          │
│      #python  #async  #performance          use: 7  →          │
│                                                                 │
│  📄  fastapi-background-tasks                       skill      │
│      "Фоновые задачи через BackgroundTasks или..."             │
│      #python  #fastapi  #async              use: 3  →          │
│                                                                 │
│  📄  sqlite-async-access                            concept    │
│      "SQLite не поддерживает настоящий async..."               │
│      #sqlite  #python                       use: 1  →          │
│                                                                 │
│  ────────────────────────────────────────────────────────────────    │
│  Показать все результаты (4)                reefiki search  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Поиск работает через HTMX с debounce 200ms:

```html
<input
  type="text"
  hx-get="/api/search"
  hx-trigger="keyup changed delay:200ms"
  hx-target="#search-results"
  hx-include="[name='project']"
  placeholder="Найти в вики..."
/>
```

```python
@app.get("/api/search")
async def search(q: str, project: str, limit: int = 7):
    results = search_existing(
        project=get_project_path(project),
        query=q, limit=limit
    )
    return {
        "results": results,
        "cli_cmd": f'reefiki search "{q}"'
    }
```

---

## 12.6 Core — Копилка (Inbox)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  📥 Копилка                                    [Разобрать всё] │
│  3 элемента ждут обработки                                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  🔗 https://sqlite.org/fts5.html                        │   │
│  │  Сохранено 2 часа назад                                 │   │
│  │                                                         │   │
│  │  [▶ Обработать]  [👁 Открыть]  [🗑 Удалить]            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  📄 notes-from-meeting.md                               │   │
│  │  Сохранено вчера                                        │   │
│  │  [▶ Обработать]  [👁 Открыть]  [🗑 Удалить]            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  + Добавить в копилку                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  URL или путь к файлу...                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  [Сохранить]                    CLI: reefiki save <url>      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12.7 Core — Вики (список страниц)

```
┌─────────────────────────────────────────────────────────────────┐
│  📚 Вики                                                        │
│  127 страниц                                                    │
│                                                                 │
│  Фильтры:  [Все ▾]  [Тег ▾]  [Сортировка ▾]  🔍 Поиск...  │
│                                                                 │
│  skills (34)                                              ─ ▾  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  python-async-patterns       #python #async    ★★★★★  │  │
│  │  fastapi-background-tasks    #fastapi           ★★★☆☆  │  │
│  │  git-interactive-rebase      #git               ★★☆☆☆  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  decisions (18)  concepts (41)  sources (22)  synthesis (8)    │
│  [показать]      [показать]      [показать]    [показать]       │
└─────────────────────────────────────────────────────────────────┘
```

Звёздочки = `use_count` визуально (0–2: ★☆☆☆☆, 3–5: ★★★☆☆, 6–10: ★★★★☆, 11+: ★★★★★).

Клик на страницу открывает split view с превью содержимого.

---

## 12.8 Core — CLI-прозрачность

Каждое действие в UI показывает эквивалентную CLI-команду:

```
┌─────────────────────────────────────────────────────────────────┐
│  [Разобрать копилку]                                            │
│                                                                 │
│  $ reefiki process                            📋 копировать │
└─────────────────────────────────────────────────────────────────┘
```

**CLI-лог** — опциональная панель внизу (как DevTools), открывается кнопкой `>_`:

```
┌─────────────────────────────────────────────────────────────────┐
│  CLI лог                                              ─  ✕     │
│  ────────────────────────────────────────────────────────────────  │
│  $ reefiki search "python async"                                │
│  Found 4 results in 18ms                                        │
│                                                                 │
│  $ reefiki save https://sqlite.org/fts5.html                   │
│  Saved: inbox/sqlite-org-fts5.md                               │
│  Inbox entries: 3                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12.9 Опционально — Здоровье вики

```
┌─────────────────────────────────────────────────────────────────┐
│  💚 Здоровье вики                              Обновить  ↻     │
│  Последняя проверка: 5 минут назад                              │
│                                                                 │
├────────────┬──────────────┬──────────────┬──────────────────┤
│              │              │              │                  │
│  Дистилляция │  Активность  │  Качество    │  Структура         │
│              │              │              │                  │
│    75%  ✅   │   4.2 avg    │   87%  ✅    │  18% orphans ⚠️  │
│              │  use_count   │  useful_when │                  │
│              │              │              │                  │
├────────────┴──────────────┴──────────────┴──────────────────┤
│                                                                 │
│  Общий score: GOOD                                              │
│  ████████████████████░░░░░░░░░░  68/100                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Рекомендации                                                   │
│                                                                 │
│  ⚠️  23 страницы никогда не использовались                     │
│     [Показать список]  →  reefiki review-queues --type stale   │
│                                                                 │
│  ℹ️  3 неразрешённых конфликта                                  │
│     [Разрешить]  →  reefiki resolve                             │
│                                                                 │
│  ✅ Broken links: 0                                             │
│  ✅ Последний harvest: сегодня                                    │
│                                                                 │
│  Тренд (30 дней)                                                  │
│  Страниц:  ▁▂▃▄▅▆▇█  +12                                           │
│  Здоровье: ▃▄▄▅▅▆▆▇  fair → good                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12.10 Опционально — Граф связей

Визуализация `[[wikilinks]]` через `d3-force` (~80KB, lazy-load):

```
┌─────────────────────────────────────────────────────────────────┐
│  🕸 Граф знаний                    [Фильтр ▾]  [Полный экран]  │
│                                                                 │
│                    ●python-async                                │
│                   /    \                                        │
│         ●fastapi-bg    ●sqlite-async                            │
│              |              |                                   │
│         ●aiohttp-vs    ●fts5-perf                               │
│                                                                 │
│  ● skills  ● decisions  ● concepts  ● sources                  │
│                                                                 │
│  Узлов: 127  |  Связей: 284  |  Orphans: 23                    │
└─────────────────────────────────────────────────────────────────┘
```

Цвета узлов = типы страниц. Размер узла = `use_count`. Клик на узел — открывает страницу.

```python
@app.get("/api/graph")
async def get_graph(project: str):
    backlinks = build_backlink_index(get_project_path(project))
    nodes = [{"id": p, "type": fm["type"], "use_count": fm.get("use_count", 0)}
             for p, fm in backlinks["pages"].items()]
    edges = [{"source": s, "target": t}
             for s, targets in backlinks["outgoing"].items()
             for t in targets]
    return {"nodes": nodes, "edges": edges}
```

---

## 12.11 Технический стек — детально

```
Backend:
  FastAPI          — HTTP сервер, API endpoints
  Jinja2           — шаблоны HTML
  watchfiles       — hot-reload при изменении wiki-файлов
  reefiki.py       — прямой импорт функций (не subprocess)

Frontend:
  HTMX 1.9         — интерактивность без JS-фреймворка (~14KB)
  Alpine.js 3      — минимальный реактивный стейт (~15KB)
  d3-force         — только для графа (~80KB, lazy-load)
  Lucide icons     — SVG иконки инлайн
  CSS custom props — без Tailwind, hand-crafted ~300 строк

Итого JS: ~30KB (без графа) / ~110KB (с графом)
Внешних зависимостей: 0 (всё CDN или инлайн)
```

**Архитектура:**

```python
# scripts/reefiki_dashboard.py

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import uvicorn

# Прямой импорт из reefiki.py — не subprocess
from reefiki import (
    search_existing, build_index, status,
    build_backlink_index, knowledge_health,
    save_source, iter_pages
)

app = FastAPI(title="REEFIKI Dashboard")
templates = Jinja2Templates(directory="scripts/dashboard/templates")

@app.get("/")
async def home(request: Request, project: str = None):
    config = load_config()
    project_path = get_project_path(project or config["last_project"])
    health = knowledge_health(project_path)
    recent = get_recent_activity(project_path, limit=5)
    inbox_count = len(list((project_path / "inbox").glob("*.md")))
    return templates.TemplateResponse("home.html", {
        "request": request,
        "health": health,
        "recent": recent,
        "inbox_count": inbox_count,
        "greeting": get_greeting(health["health_score"], config["lang"]),
    })

@app.post("/api/save")
async def save(url: str, project: str):
    result = save_source(get_project_path(project), url)
    return {
        "ok": result == 0,
        "cli_cmd": f'reefiki save "{url}"'
    }

def launch(port: int = 7777, open_browser: bool = True):
    if open_browser:
        import webbrowser
        webbrowser.open(f"http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
```

---

## 12.12 Что в core, что опционально

| Раздел | Core | Опционально | Почему |
|---|---|---|---|
| Главная с метриками | ✅ | | Нужна всегда |
| Поиск (⌘K) | ✅ | | Главная функция |
| Копилка (inbox) | ✅ | | Ежедневное использование |
| Список страниц вики | ✅ | | Навигация |
| CLI-прозрачность | ✅ | | Философия проекта |
| Здоровье вики | | ✅ | Нужно периодически |
| Граф связей | | ✅ | Тяжёлый, нужен редко |
| Timeline | | ✅ | Приятно, не критично |
| Мульти-проектный вид | | ✅ | Только при 2+ проектах |
| Тренды (30 дней) | | ✅ | Нужны данные за период |

Опциональные разделы загружаются **lazy** — только при переходе в них.

---

## 12.13 Action plan

| ID | Действие | Сложность | Приоритет |
|---|---|---|---|
| DASH-01 | Создать `scripts/reefiki_dashboard.py` с FastAPI | M | P1 |
| DASH-02 | Реализовать главную страницу (метрики, активность) | M | P1 |
| DASH-03 | Реализовать поиск с HTMX и ⌘K | M | P1 |
| DASH-04 | Реализовать раздел Копилка (inbox) | M | P1 |
| DASH-05 | Реализовать список страниц вики с фильтрами | M | P1 |
| DASH-06 | Добавить CLI-прозрачность (показ команд) | S | P1 |
| DASH-07 | Добавить CLI-лог панель (опциональная) | S | P2 |
| DASH-08 | Реализовать раздел Здоровье вики | M | P2 |
| DASH-09 | Реализовать граф связей (d3-force) | L | P3 |
| DASH-10 | Реализовать Timeline | S | P2 |
| DASH-11 | Реализовать мульти-проектный вид | M | P2 |
| DASH-12 | Добавить dark/light тему | S | P2 |
| DASH-13 | Добавить локализацию EN/RU/ZH в UI | M | P2 |
| DASH-14 | Добавить `reefiki dashboard` как глобальную команду | S | P1 |
| DASH-15 | Добавить hot-reload при изменении wiki-файлов | S | P3 |
