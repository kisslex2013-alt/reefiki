# REEFIKI — Аудит: Метрики здоровья базы знаний

> Дата: 4 июня 2026. Часть комплексного аудита незатронутых тем.

## 10.1 Проблема

Философия REEFIKI — "дистилляция, не архивация". Но как понять, что вики действительно дистиллирует, а не превращается в свалку? Сейчас нет ни одной метрики для этого.

## 10.2 Предлагаемые метрики

**Группа 1 — Метрики использования:**

| Метрика | Что измеряет | Как получить |
|---|---|---|
| `use_count` среднее | Насколько активно используется вики | `AVG(use_count)` по всем страницам |
| Доля страниц с `use_count = 0` | "Мёртвые" страницы | `COUNT WHERE use_count = 0 / total` |
| Медиана дней с последнего использования | Актуальность вики | `MEDIAN(today - last_used)` |
| Топ-10 самых используемых страниц | Ядро знаний | `ORDER BY use_count DESC LIMIT 10` |

**Группа 2 — Метрики дистилляции:**

| Метрика | Что измеряет | Норма |
|---|---|---|
| Коэффициент дистилляции | `wiki_pages / (wiki_pages + seen_pages)` | > 0.3 |
| Средний возраст страницы при первом использовании | Насколько быстро применяются знания | < 30 дней |
| Доля страниц с `useful_when` > 20 слов | Качество формулировок | > 80% |
| Количество `## Conflicting claims` | Противоречия в базе | < 5% страниц |

**Группа 3 — Метрики структуры:**

| Метрика | Что измеряет | Норма |
|---|---|---|
| Доля orphan-страниц | Изолированные знания | < 20% |
| Средняя степень связности | Насколько связана вики | > 2 ссылки/страницу |
| Распределение по типам | Баланс типов страниц | Нет одного доминирующего типа |
| Доля страниц с тегами | Навигируемость | > 90% |

**Группа 4 — Метрики деградации:**

| Метрика | Что измеряет | Тревожный сигнал |
|---|---|---|
| Скорость роста seen/ vs wiki/ | Ужесточается ли фильтр | seen растёт быстрее wiki в 5+ раз |
| Количество stale-страниц (> 90 дней без использования) | Устаревание | > 30% страниц |
| Количество broken links | Целостность | > 0 |
| Дни с последнего `/harvest` | Регулярность обслуживания | > 14 дней |

## 10.3 Реализация — команда `health`

```python
def knowledge_health(project: Path) -> dict:
    pages = list(iter_pages(project))
    seen = list((project / "seen").glob("*.md"))
    inbox = list((project / "inbox").glob("*.md"))

    total_pages = len(pages)
    if total_pages == 0:
        return {"status": "empty"}

    use_counts = []
    last_used_days = []
    useful_when_lengths = []
    conflicting = 0

    for page in pages:
        fm, body = parse_frontmatter(page.read_text(encoding="utf-8"))
        use_counts.append(int(fm.get("use_count", 0)))

        last_used = fm.get("last_used")
        if last_used:
            try:
                delta = (date.today() - date.fromisoformat(str(last_used))).days
                last_used_days.append(delta)
            except ValueError:
                pass

        uw = str(fm.get("useful_when", ""))
        useful_when_lengths.append(len(uw.split()))

        if "## Conflicting claims" in body:
            conflicting += 1

    distillation_ratio = total_pages / max(total_pages + len(seen), 1)
    dead_pages = sum(1 for c in use_counts if c == 0)
    dead_ratio = dead_pages / total_pages
    good_useful_when = sum(1 for l in useful_when_lengths if l >= 5)
    useful_when_quality = good_useful_when / total_pages

    return {
        "total_pages": total_pages,
        "seen_count": len(seen),
        "inbox_count": len(inbox),
        "distillation_ratio": round(distillation_ratio, 2),
        "dead_pages_ratio": round(dead_ratio, 2),
        "avg_use_count": round(sum(use_counts) / total_pages, 1),
        "useful_when_quality": round(useful_when_quality, 2),
        "conflicting_claims_count": conflicting,
        "median_last_used_days": sorted(last_used_days)[len(last_used_days)//2]
            if last_used_days else None,
        "health_score": _compute_health_score(
            distillation_ratio, dead_ratio, useful_when_quality
        ),
    }

def _compute_health_score(distillation: float, dead: float, quality: float) -> str:
    score = (distillation * 0.3) + ((1 - dead) * 0.4) + (quality * 0.3)
    if score > 0.8: return "excellent"
    if score > 0.6: return "good"
    if score > 0.4: return "fair"
    return "poor"
```

## 10.4 Пример вывода

```
$ python scripts/reefiki.py --project myproject health

📊 Здоровье базы знаний: myproject
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Общее состояние: GOOD ✅

Размер:
  Страниц в вики:     127
  Отложено (seen):     43
  В копилке (inbox):    3
  Коэффициент дистилляции: 0.75

Использование:
  Среднее use_count:   4.2
  Мёртвых страниц:    18% ⚠️
  Медиана последнего использования: 12 дней

Качество:
  useful_when качество: 87% ✅
  Конфликтующих утверждений: 3
  Broken links: 0 ✅

Рекомендации:
  ⚠️  18% страниц ни разу не использовались. Запусти /lint.
  ℹ️  3 неразрешённых конфликта. Запусти /resolve.
```

## 10.5 Трендовый трекинг

```python
def append_health_snapshot(project: Path) -> None:
    health = knowledge_health(project)
    health["date"] = date.today().isoformat()
    log = project / "wiki" / "health-log.jsonl"
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(health, ensure_ascii=False) + "\n")
```

## Action plan

| ID | Действие | Сложность | Приоритет |
|---|---|---|---|
| MET-01 | Реализовать `knowledge_health()` функцию | M | P1 |
| MET-02 | Добавить команду `health` в CLI | M | P1 |
| MET-03 | Интегрировать health score в `/status` | S | P2 |
| MET-04 | Добавить health warnings в `/lint` | S | P2 |
| MET-05 | Реализовать `health-log.jsonl` для трендов | M | P3 |
| MET-06 | Добавить health в `memory golden` baseline | M | P3 |
