# REEFIKI — Адаптация концептов Headroom

> **Версия:** 1.0 | **Дата:** 2026-06-04
> **Источник:** [chopratejas/headroom](https://github.com/chopratejas/headroom)
> **Лицензия источника:** Apache 2.0 — свободно для использования, модификации,
> включения в свой проект. Attribution не обязателен, но рекомендуется в NOTICE.
> **Принцип адаптации:** все концепты реализуются как нативные механизмы REEFIKI
> без внешних зависимостей, работают с любым IDE/агентом (Claude Code, Codex,
> Cursor, Windsurf, Gemini CLI и др.).

---

## Содержание

1. [Лицензионный статус](#1-лицензионный-статус)
2. [Что берём и что не берём](#2-что-берём-и-что-не-берём)
3. [Концепт 1: CCR → raw/ как full version](#3-концепт-1-ccr--raw-как-full-version)
4. [Концепт 2: CacheAligner → Stable Prefix Rule](#4-концепт-2-cachealigner--stable-prefix-rule)
5. [Концепт 3: IntelligentContext → retrieval_weight](#5-концепт-3-intelligentcontext--retrieval_weight)
6. [Концепт 4: RollingWindow → Session Budget Rule](#6-концепт-4-rollingwindow--session-budget-rule)
7. [Концепт 5: SmartCrusher → context-pack команда](#7-концепт-5-smartcrusher--context-pack-команда)
8. [Совместная работа всех концептов](#8-совместная-работа-всех-концептов)
9. [План внедрения](#9-план-внедрения)
10. [Attribution](#10-attribution)

---

## 1. Лицензионный статус

| Аспект | Статус |
|---|---|
| Лицензия Headroom | **Apache 2.0** |
| Использование идей/концептов | ✅ Свободно (идеи не защищены авторским правом) |
| Копирование кода с модификацией | ✅ Разрешено с attribution |
| Включение в REEFIKI (Apache 2.0) | ✅ Полная совместимость лицензий |
| Коммерческое использование | ✅ Разрешено |
| Требования | Сохранить NOTICE при копировании кода |

**Вывод:** можно брать всё — идеи, алгоритмы, код — без ограничений.
При копировании кода добавить attribution в `NOTICE`.

---

## 2. Что берём и что не берём

### Берём (адаптируем нативно)

| Компонент Headroom | Адаптация в REEFIKI | Механизм |
|---|---|---|
| CCR (Compress-Cache-Retrieve) | `raw/` как full version + compressed wiki | Файловая система + frontmatter |
| CacheAligner | Stable Prefix Rule | Правило в AGENTS.md |
| IntelligentContext | `retrieval_weight` в frontmatter | Schema + query pipeline |
| RollingWindow | Session Budget Rule | AGENTS.md + `_user/profile.md` |
| SmartCrusher | `context-pack` команда | Python CLI + slash-команда |

### Не берём

| Компонент | Причина |
|---|---|
| Proxy-сервер | Нарушает local-first философию; не работает прозрачно с Codex/Gemini CLI |
| Kompress ML-модель | Внешняя зависимость; избыточно для markdown |
| SharedContext API | Не нужен — файловая система уже shared state между агентами |
| Image compression | REEFIKI не работает с изображениями в wiki |
| HeadroomClient wrapper | Привязка к конкретному провайдеру; REEFIKI агент-нейтрален |

---

## 3. Концепт 1: CCR → raw/ как full version

### Оригинальная идея Headroom

CCR (Compress-Cache-Retrieve): агент получает сжатую версию контента.
Если нужны детали — явно запрашивает оригинал через `retrieve_compressed`.
Обратимость гарантирована: оригинал всегда доступен.

### Адаптация для REEFIKI

REEFIKI уже имеет `raw/` как хранилище оригиналов и `wiki/` как дистилляцию.
Нужно только добавить явный CCR-указатель в frontmatter и правило для агента.

**Новое поле в `_schema.md` для `type: source`:**

```yaml
# Для source страниц в wiki/ — CCR поля
compressed: true                              # эта страница — сжатая версия
full_version: raw/codex-changelog-v2-full.md  # путь к оригиналу
compression_ratio: 0.15                       # 15% от оригинала (инфо)
```

**Пример source страницы с CCR:**

```yaml
---
type: source
title: Codex Changelog v2 — May 2026
slug: codex-changelog-v2
compressed: true
full_version: raw/codex-changelog-v2-full.md
compression_ratio: 0.12
url: https://github.com/openai/codex/releases/tag/v2.0-may2026
skills_affected: [iterative-code-review, context-handoff]
useful_when: >
  Когда нужно проверить изменилось ли поведение Codex
  при передаче контекста между сессиями.
---

## Ключевые факты (извлечение)

- §3: нет persistent context между сессиями — основа context-handoff skills
- §7: лимит 10 tool calls за ход — влияет на iterative-review workflow
- §12: новый batch mode — до 15 calls в batch context

## Сигналы для адаптации skills

Cursor Composer имеет аналогичное ограничение §3.
Claude Code решает через Memory layer (другой подход).
```

**Правило в AGENTS.md:**

```markdown
## CCR Rule — Compressed Sources

Wiki source страницы с `compressed: true` содержат только
ключевые факты для работы со skills.

При работе с source страницей:
- Для /query и /skill-port: используй сжатую версию (wiki/)
- Для /source-check и детального анализа: читай full_version (raw/)
- Агент сам решает когда нужна полная версия — не читай raw/ по умолчанию

Признак что нужна полная версия:
  - Пользователь просит детали оригинала
  - Сжатой версии недостаточно для разрешения конфликта источников
  - /source-check требует сравнения с новой версией документа
```

**Эффект:** source страница в wiki/ занимает ~200–300 токенов вместо 2000–5000.
Оригинал в `raw/` доступен по требованию. Работает в любом IDE.

---

## 4. Концепт 2: CacheAligner → Stable Prefix Rule

### Оригинальная идея Headroom

CacheAligner стабилизирует начало (префикс) API-запроса так чтобы
провайдерский KV-кэш срабатывал при повторных вызовах. Любой динамический
токен в начале контекста — разрушает весь кэш.

### Почему это критично для REEFIKI

AGENTS.md читается при каждой команде. Если файл содержит:
- Текущую дату
- Счётчик страниц
- Имя активного проекта
- Статус последнего lint

...то кэш не срабатывает ни разу. При Anthropic prompt caching это означает
оплату полной стоимости AGENTS.md (~5 500 токенов) при каждом вызове.
С рабочим кэшем — только при первом вызове в сессии.

### Адаптация: Stable Prefix Rule

**Структурное правило для AGENTS.md** (новая секция в начале файла):

```markdown
# AGENTS.md — Stable Prefix Rule

ВАЖНО ДЛЯ АВТОРОВ ЭТОГО ФАЙЛА:
Первые 3 000 токенов этого файла должны быть СТАБИЛЬНЫ между сессиями.
Стабильность = провайдерский кэш работает для всех IDE.

ЗАПРЕЩЕНО в начале файла (до раздела ## Dynamic State):
  ❌ Текущая дата или время
  ❌ Счётчики страниц, размер wiki
  ❌ Имена активных проектов
  ❌ Результаты последних операций
  ❌ Статусы (lint прошёл/не прошёл)
  ❌ Любые данные которые меняются между сессиями

РАЗРЕШЕНО в начале файла:
  ✅ Запреты (NEVER секции)
  ✅ Константные операционные правила
  ✅ Типы страниц и их описания
  ✅ Slash-команды и их поведение
  ✅ Governance правила

ДИНАМИЧЕСКИЕ данные → только в:
  .drift-cache.json     (источники, требующие проверки)
  index.min.json        (состояние wiki)
  _user/.compiled.json  (пользовательский контекст)
  status --bootstrap    (текущий статус проекта)
```

**Структура AGENTS.md с Stable Prefix:**

```
AGENTS.md
├── [0–3 000 токенов] STABLE PREFIX
│   ├── Запреты (NEVER)
│   ├── Операционные правила
│   ├── Типы страниц
│   └── Slash-команды
├── [3 000–5 000 токенов] SEMI-STABLE
│   ├── Governance правила
│   └── Agent contracts
└── [конец] DYNAMIC (НЕ ХРАНИТЬ ЗДЕСЬ)
    → вынесено во внешние кэши
```

**Эффект по IDE:**

| IDE / Провайдер | Механизм кэша | Экономия при стабильном префиксе |
|---|---|---|
| Claude Code | Anthropic prompt caching | до 90% стоимости AGENTS.md |
| Gemini CLI | Google context caching | до 75% |
| Codex (OpenAI) | OpenAI prompt caching | до 80% |
| Cursor / Windsurf | Зависит от модели под капотом | 50–80% |

Это **пассивная оптимизация** — не требует кода, только дисциплины при редактировании AGENTS.md.

---

## 5. Концепт 3: IntelligentContext → retrieval_weight

### Оригинальная идея Headroom

IntelligentContext выбирает что включить в контекст на основе
score-based оценки важности с learned importance weights.

### Адаптация для REEFIKI

Простая эвристическая версия без ML — через frontmatter.
Агент обновляет вес при каждом обращении к странице.

**Новые поля в `_schema.md` для всех типов страниц:**

```yaml
# Retrieval intelligence fields — обновляются агентом автоматически
retrieval_weight: 0.5        # 0.0–1.0, вычисляется из access_count + recency
access_count: 0              # сколько раз страница была прочитана агентом
last_accessed: YYYY-MM-DD    # дата последнего обращения
```

**Формула вычисления `retrieval_weight`:**

```python
from datetime import date

def compute_retrieval_weight(
    access_count: int,
    last_accessed: str,
    created: str,
    page_type: str
) -> float:
    """
    Вычисляет retrieval_weight для wiki-страницы.
    Обновляется агентом при каждом /query обращении.

    Факторы:
    - access_count: чем чаще — тем выше вес (логарифмически)
    - recency: свежие обращения важнее старых
    - page_type: synthesis и decision получают бонус (высокая ценность)
    """
    import math

    # Recency score: 1.0 если сегодня, убывает со временем
    days_since_access = (date.today() -
                         date.fromisoformat(last_accessed)).days
    recency = math.exp(-days_since_access / 30)  # полураспад 30 дней

    # Frequency score: логарифм от числа обращений
    frequency = min(1.0, math.log1p(access_count) / math.log1p(20))

    # Type bonus
    type_bonus = {
        "synthesis": 0.15,
        "decision": 0.10,
        "skill": 0.05,
        "concept": 0.0,
        "entity": 0.0,
        "source": -0.05,  # source менее приоритетны чем дистилляции
    }.get(page_type, 0.0)

    weight = (recency * 0.4) + (frequency * 0.6) + type_bonus
    return round(min(1.0, max(0.0, weight)), 3)
```

**Как агент обновляет вес — правило в AGENTS.md:**

```markdown
## retrieval_weight — автоматическое обновление

После каждого /query при котором страница была прочитана:
1. Увеличить access_count на 1
2. Обновить last_accessed на сегодня
3. Пересчитать retrieval_weight по формуле
4. Обновить frontmatter (только эти три поля)

Обновление — append-style: только frontmatter, не body.
Не делать git commit только ради обновления весов —
включать в следующий обычный коммит.
```

**Использование при /query:**

```python
def query_with_intelligence(project: Path, query: str,
                             budget: int = 4000) -> list[dict]:
    """
    /query с IntelligentContext сортировкой.
    FTS релевантность × retrieval_weight = итоговый приоритет.
    """
    fts_results = fts_search(project, query, limit=20)

    # Обогатить FTS score весами из frontmatter
    scored = []
    for r in fts_results:
        fm = load_frontmatter(project / "wiki" / r["id"])
        weight = fm.get("retrieval_weight", 0.5)
        # Комбинированный score: 70% FTS + 30% historical weight
        combined = (r["fts_score"] * 0.7) + (weight * 0.3)
        scored.append({**r, "combined_score": combined})

    # Сортировка по combined score
    scored.sort(key=lambda x: x["combined_score"], reverse=True)
    return scored
```

**Эффект:** страницы которые реально оказывались полезными всплывают выше.
Новые страницы начинают с weight=0.5 (нейтральный). Работает в любом IDE
потому что логика в Python, не в агенте.

---

## 6. Концепт 4: RollingWindow → Session Budget Rule

### Оригинальная идея Headroom

RollingWindow управляет контекстом в пределах лимита без обрыва tool calls —
автоматически вытесняет старые части при приближении к лимиту.

### Проблема для REEFIKI

Разные IDE имеют разные лимиты контекста. Агент без явного бюджета
может незаметно упереться в лимит посреди операции — особенно опасно
при /process batch или длинном /skill-port.

### Адаптация: Session Budget Rule

**Поля в `_user/profile.md`:**

```yaml
# Context budget по IDE — агент читает при старте сессии
context_limits:
  claude-code: 180000     # 200K лимит, оставляем 10% запас
  codex: 110000           # ~128K лимит
  gemini-cli: 900000      # 1M лимит, billing по токенам
  windsurf: 90000         # зависит от модели под капотом
  cursor: 90000           # аналогично
  aider: 90000            # консервативная оценка
  default: 100000         # для неизвестных IDE
```

**Правило в AGENTS.md:**

```markdown
## Session Budget Rule

При старте каждой сессии:
1. Определи текущий IDE из переменных окружения:
   CLAUDE_CODE → claude-code
   OPENAI_API_BASE содержит codex → codex
   GEMINI_API_KEY присутствует → gemini-cli
   Иначе → default
2. Прочитай context_limits[current_ide] из _user/profile.md
3. Отслеживай приблизительный расход токенов в сессии

Пороги и действия:
  При достижении 70% бюджета:
    → Кратко сообщить: "Использовано ~70% контекста сессии."
    → Предложить: "Если планируешь долгую работу — сделай /harvest сейчас."

  При достижении 85% бюджета:
    → Остановить чтение новых крупных файлов (wiki страниц, raw/ файлов)
    → Завершить текущую операцию
    → Обязательно предложить /harvest

  При достижении 95% бюджета:
    → Выполнить только /harvest и завершить сессию
    → Сообщить что нужно начать новую сессию

Оценка токенов (приближение для счётчика):
  1 токен ≈ 4 символа EN ≈ 2.5 символа RU
  Файл размером N байт ≈ N/3 токенов (для mixed RU/EN)
```

**Автоматическая команда `/session-status`:**

```python
def session_status(current_ide: str,
                   user_profile_path: Path) -> dict:
    """
    Возвращает текущий статус бюджета сессии.
    Агент вызывает при старте и при каждой тяжёлой операции.
    """
    limits = load_user_profile(user_profile_path).get(
        "context_limits", {}
    )
    budget = limits.get(current_ide, limits.get("default", 100000))

    return {
        "ide": current_ide,
        "budget_tokens": budget,
        "warning_threshold": int(budget * 0.70),
        "stop_reading_threshold": int(budget * 0.85),
        "emergency_threshold": int(budget * 0.95),
    }
```

**Эффект:** предотвращает обрывы посреди /process batch и /skill-port.
Особенно важно для Codex (меньший контекст) и при работе с large skills-core.

---

## 7. Концепт 5: SmartCrusher → context-pack команда

### Оригинальная идея Headroom

SmartCrusher статистически сжимает JSON tool outputs, сохраняя
ошибки, аномалии и релевантные элементы. Заявленная экономия: 70–90%.

### Адаптация для REEFIKI

SmartCrusher оптимизирован под JSON. Wiki-страницы REEFIKI — структурированный
markdown. Адаптация: budget-aware packing с приоритизацией по retrieval_weight.

**Новая команда `/context-pack` — slash-команда:**

```markdown
# .claude/commands/context-pack.md

# /context-pack <query> [--budget <токенов>] [--type <тип>]

Собирает максимально информативный контекст для агента
в рамках токен-бюджета. Используется агентом автоматически
перед /query при большом corpus (500+ страниц).

Параметры:
  query    — поисковый запрос (обязательно)
  budget   — лимит токенов (default: 3000)
  type     — фильтр по типу страницы (source/skill/concept/...)

Примеры:
  /context-pack "iterative code review"
  /context-pack "context handoff" --budget 5000 --type skill
```

**Реализация в `scripts/reefiki.py`:**

```python
def context_pack(
    project: Path,
    query: str,
    budget_tokens: int = 3000,
    page_type: str | None = None
) -> str:
    """
    Budget-aware context packing для /query.

    Алгоритм (адаптация SmartCrusher для markdown):
    1. FTS поиск → топ-N страниц по релевантности
    2. Сортировка по combined_score (FTS × retrieval_weight)
    3. Компактное представление каждой страницы:
       frontmatter (полностью) + первые 100 слов body
    4. Добавление страниц пока не исчерпан бюджет
    5. Последняя страница — обрезается точно по бюджету
    """
    results = query_with_intelligence(project, query, budget=99999)

    if page_type:
        results = [r for r in results
                   if load_frontmatter(
                       project / "wiki" / r["id"]
                   ).get("type") == page_type]

    packed_pages = []
    used_tokens = 0

    for result in results:
        page_path = project / "wiki" / result["id"]
        fm, body = parse_frontmatter(page_path.read_text(encoding="utf-8"))

        # Компактный формат: ключевые frontmatter поля + усечённое тело
        compact = _format_compact(fm, body, max_body_words=100)
        page_tokens = estimate_tokens(compact)

        if used_tokens + page_tokens > budget_tokens:
            # Последняя страница: обрезаем до остатка бюджета
            remaining_chars = (budget_tokens - used_tokens) * 3
            if remaining_chars > 200:  # минимальный полезный размер
                packed_pages.append(compact[:remaining_chars] + "\n[усечено]")
            break

        packed_pages.append(compact)
        used_tokens += page_tokens

        if used_tokens >= budget_tokens:
            break

    header = (
        f"<!-- context-pack: {len(packed_pages)} страниц, "
        f"~{used_tokens} токенов из {budget_tokens} бюджета -->\n\n"
    )
    return header + "\n---\n".join(packed_pages)


def _format_compact(fm: dict, body: str, max_body_words: int = 100) -> str:
    """Компактное представление wiki-страницы для context-pack."""
    lines = [
        f"## {fm.get('title', 'Без названия')} [{fm.get('type', '?')}]",
        f"useful_when: {fm.get('useful_when', '—')}",
        f"tags: {', '.join(fm.get('tags', []))}",
    ]

    # Дополнительные поля по типу
    if fm.get("type") == "skill":
        impl = fm.get("implementations", {})
        if impl:
            status = ", ".join(f"{k}:{v}" for k, v in impl.items())
            lines.append(f"implementations: {status}")

    if fm.get("type") == "source":
        lines.append(f"skills_affected: {fm.get('skills_affected', [])}")
        if fm.get("compressed"):
            lines.append(f"full_version: {fm.get('full_version', '')}")

    if fm.get("retrieval_weight"):
        lines.append(f"weight: {fm['retrieval_weight']}")

    # Усечённое тело
    words = body.split()[:max_body_words]
    body_excerpt = " ".join(words)
    if len(body.split()) > max_body_words:
        body_excerpt += "..."

    lines.append("")
    lines.append(body_excerpt)

    return "\n".join(lines)
```

**Эффект по размеру corpus:**

| Corpus | /query без pack | /query с pack (budget 3K) |
|---|---|---|
| 100 страниц | ~3 000 токенов | ~3 000 токенов (нет разницы) |
| 500 страниц | ~14 000 токенов | ~3 000 токенов (-79%) |
| 1000 страниц | ~26 000 токенов | ~3 000 токенов (-88%) |

---

## 8. Совместная работа всех концептов

### Как концепты взаимодействуют

```
Запрос пользователя: /query "как делать code review в Codex"

1. Session Budget Rule (Концепт 4)
   └─→ Проверяет бюджет: 45% использовано → OK, продолжаем

2. context-pack (Концепт 5)
   └─→ FTS поиск → 20 кандидатов
   └─→ Сортировка по combined_score (Концепт 3: retrieval_weight)
   └─→ Упаковка в 3000 токенов бюджет

3. Агент читает packed контекст
   └─→ Видит source с compressed: true → не читает raw/ (Концепт 1: CCR)
   └─→ AGENTS.md уже закэширован (Концепт 2: Stable Prefix)

4. Агент отвечает
   └─→ После ответа: обновляет retrieval_weight использованных страниц (Концепт 3)
```

### Суммарный эффект при 500 страницах

```
Операция         Без концептов   С концептами   Экономия
──────────────────────────────────────────────────────────
Bootstrap        40 800 токенов   9 320 токенов    -77%
/query           14 000 токенов   3 500 токенов    -75%
/skill-port      20 000 токенов   8 000 токенов    -60%
/source-check    10 000 токенов   4 000 токенов    -60%
Типичная сессия 100 000 токенов  35 000 токенов    -65%
──────────────────────────────────────────────────────────
```

### Агент-нейтральность

Все пять концептов реализованы так что работают с любым IDE:

| Концепт | Claude Code | Codex | Cursor | Windsurf | Gemini CLI |
|---|---|---|---|---|---|
| CCR (raw/ pointer) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Stable Prefix | ✅ | ✅ | ✅ | ✅ | ✅ |
| retrieval_weight | ✅ | ✅ | ✅ | ✅ | ✅ |
| Session Budget | ✅ | ✅ | ✅ | ✅ | ✅ |
| context-pack | ✅ | ✅ | ✅ | ✅ | ✅ |

Механизм работы: Python CLI + AGENTS.md правила + frontmatter.
Не зависит от конкретного провайдера или SDK.

---

## 9. План внедрения

### Фаза 1 — Немедленно (Phase 0i, ~100 страниц)

Бесплатные изменения без кода — максимальная отдача сейчас:

```
HR-01  Stable Prefix Rule — добавить секцию в AGENTS.md       [S, P0]
       Запрещает динамический контент в начале файла.
       Включает провайдерский кэш для всех IDE.

HR-02  CCR правило в AGENTS.md — когда читать raw/            [S, P1]
       Агент перестаёт читать raw/ по умолчанию.
```

### Фаза 2 — При 200+ страницах

Код который решает проблему роста:

```
HR-03  context-pack команда в scripts/reefiki.py              [M, P1]
       + .claude/commands/context-pack.md
       Главная оптимизация /query при большом corpus.

HR-04  retrieval_weight поле в _schema.md                     [S, P2]
       + compute_retrieval_weight() в reefiki.py
       + обновление в /query pipeline

HR-05  compressed/full_version поля в source _schema.md       [S, P1]
       Формализует CCR концепт в схеме.
```

### Фаза 3 — При 500+ страницах

```
HR-06  Session Budget Rule — context_limits в _user/profile.md [S, P1]
       + session_status() функция
       + правило в AGENTS.md с порогами

HR-07  Wizard: спросить про IDE для заполнения context_limits  [S, P2]
       Интеграция с существующим wizard flow.
```

### Зависимости

```
HR-01 (Stable Prefix)     ──── независимо, сразу
HR-02 (CCR rule)          ──── независимо, сразу

HR-03 (context-pack)      ←── требует FTS работающего /query
HR-04 (retrieval_weight)  ←── лучше после HR-03 (используется в нём)
HR-05 (CCR в schema)      ←── после HR-02 (правило уже есть)

HR-06 (Session Budget)    ←── после HR-03 (понимание реального расхода)
HR-07 (wizard)            ←── после UC-01 (wizard создаёт _user/)
```

### Сводная таблица

| ID | Действие | Файлы | Сложность | Приоритет | Фаза |
|---|---|---|---|---|---|
| HR-01 | Stable Prefix Rule | AGENTS.md | S | P0 | 1 |
| HR-02 | CCR правило | AGENTS.md | S | P1 | 1 |
| HR-03 | context-pack CLI + slash-команда | reefiki.py, commands/ | M | P1 | 2 |
| HR-04 | retrieval_weight в schema + query | _schema.md, reefiki.py | S | P2 | 2 |
| HR-05 | compressed/full_version в schema | _schema.md | S | P1 | 2 |
| HR-06 | Session Budget Rule | AGENTS.md, _user/profile.md | S | P1 | 3 |
| HR-07 | Wizard: context_limits вопрос | wizard.py | S | P2 | 3 |

---

## 10. Attribution

При включении кода или алгоритмов из Headroom добавить в `NOTICE`:

```
REEFIKI context optimization concepts adapted from:
  Headroom — The Context Optimization Layer for LLM Applications
  Copyright 2025 Headroom Contributors
  Licensed under the Apache License, Version 2.0
  https://github.com/chopratejas/headroom

Adapted concepts:
  - CCR (Compress-Cache-Retrieve) → raw/ as full version pattern
  - CacheAligner → Stable Prefix Rule for AGENTS.md
  - IntelligentContext → retrieval_weight frontmatter field
  - RollingWindow → Session Budget Rule
  - SmartCrusher → context-pack command
```

Если берётся только идея (без кода) — attribution в NOTICE не обязателен
по Apache 2.0, но рекомендуется как хорошая практика open-source.

---

*Все концепты адаптированы как нативные механизмы REEFIKI.
Внешняя зависимость от пакета `headroom-ai` не требуется.*
*Совместимость: Python 3.11+, любой IDE/агент.*
