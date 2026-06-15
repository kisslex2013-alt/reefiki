# REEFIKI — Финальный анализ оптимизации токенов

> **Версия:** 3.0 (финальная) | **Дата:** 2026-06-04
> **Включает:** baseline → аудиты → оптимизации → Headroom концепты
> **Целевой агент:** Claude Code (основной) + Codex, Cursor, Windsurf, Gemini CLI
> **Целевой размер wiki:** 500–1000 страниц (горизонт 6–12 месяцев)

---

## Содержание

1. [Итоговые числа: все сценарии включая Headroom](#1-итоговые-числа-все-сценарии)
2. [Что добавляет Headroom и где конфликты](#2-что-добавляет-headroom-и-где-конфликты)
3. [Полная согласованная карта оптимизаций](#3-полная-согласованная-карта-оптимизаций)
4. [Незатронутые резервы: есть ли ещё](#4-незатронутые-резервы)
5. [Немедленное внедрение всего сразу](#5-немедленное-внедрение-всего-сразу)
6. [Полный чеклист одним релизом](#6-полный-чеклист-одним-релизом)

---

## 1. Итоговые числа: все сценарии

### Bootstrap (токенов на старт сессии)

```
Сценарий                              100 стр.   500 стр.  1000 стр.
──────────────────────────────────────────────────────────────────────
A. Сейчас (baseline)                   10 850     10 850     10 850
B. После аудитов, без оптимизаций      16 600     40 800     68 000
C. Аудиты + все описанные оптимизации   9 320      9 320      9 500
D. C + Headroom концепты (финал)        4 800      5 000      5 200
──────────────────────────────────────────────────────────────────────
Финал (D) vs baseline (A):             -56%       -54%       -52%
Финал (D) vs аудиты без оптим. (B):    -71%       -88%       -92%
──────────────────────────────────────────────────────────────────────
```

### Типичная сессия (токенов)

```
Сценарий                              100 стр.   500 стр.  1000 стр.
──────────────────────────────────────────────────────────────────────
A. Сейчас (baseline)                   50 000     50 000     50 000
B. После аудитов, без оптимизаций      60 000    100 000    155 000
C. Аудиты + все описанные оптимизации  28 000     38 000     45 000
D. C + Headroom концепты (финал)       18 000     24 000     30 000
──────────────────────────────────────────────────────────────────────
Финал (D) vs baseline (A):             -64%       -52%       -40%
Финал (D) vs аудиты без оптим. (B):    -70%       -76%       -81%
──────────────────────────────────────────────────────────────────────
```

### Месячный расход (20 сессий/месяц, млн токенов)

```
Сценарий                              100 стр.   500 стр.  1000 стр.
──────────────────────────────────────────────────────────────────────
A. Сейчас (baseline)                     1.0        1.0        1.0
B. После аудитов, без оптимизаций        1.2        2.0        3.1
C. Аудиты + все описанные оптимизации    0.56       0.76       0.90
D. C + Headroom концепты (финал)         0.36       0.48       0.60
──────────────────────────────────────────────────────────────────────
Финал (D) vs baseline (A):              -64%       -52%       -40%
Финал (D) vs аудиты без оптим. (B):     -70%       -76%       -81%
──────────────────────────────────────────────────────────────────────
```

### Вклад Headroom поверх сценария C

```
Headroom концепт         Экономия/сессию    Механизм
──────────────────────────────────────────────────────────────
Stable Prefix Rule       3 000–8 000        Провайдерский кэш AGENTS.md
CCR (raw/ as full)       2 000–4 000        Source страницы в 10× меньше
retrieval_weight         1 500–3 000        Меньше нерелевантных страниц
Session Budget Rule      0 (страховка)      Предотвращает переполнение
context-pack             4 000–8 000        Budget-aware /query packing
──────────────────────────────────────────────────────────────
ИТОГО Headroom добавка   10 000–23 000
──────────────────────────────────────────────────────────────
```

**Главный вывод:** рост wiki с 100 до 1000 страниц при финальной конфигурации
стоит +67% токенов (0.36 → 0.60 млн/месяц) вместо +210% без оптимизаций.

---

## 2. Что добавляет Headroom и где конфликты

### Stable Prefix Rule — самый крупный незатронутый резерв

Предыдущие оптимизации сокращали **что читается**.
Stable Prefix сокращает **стоимость повторного чтения** того же контента.

```
Без Stable Prefix:
  AGENTS.md = полная стоимость при каждом вызове (~5 500 токенов)

С Stable Prefix + провайдерский кэш:
  Первый вызов:    5 500 токенов
  Повторные:       550–1 100 токенов (80–90% скидка)
  При 10 командах/сессию: экономия ~40 500 токенов
```

Работает для всех IDE: Anthropic, OpenAI, Google — у всех есть prompt caching.

### Конфликт 1: OPT-08 vs HR-03 (дублирование) → RESOLVED

```
OPT-08  FTS pre-filter   ← ОТМЕНЯЕТСЯ
HR-03   context-pack     ← РЕАЛИЗУЕТСЯ (покрывает OPT-08 полностью + лучше)

context-pack добавляет: точный токен-бюджет + retrieval_weight сортировку.
FTS pre-filter не реализовывать — context-pack строго лучше.
```

### Конфликт 2: OPT-05 (AGENTS split) vs HR-01 (Stable Prefix) → СИНЕРГИЯ

```
OPT-05: Разбивает AGENTS.md на несколько файлов
HR-01:  Требует стабильного префикса

Решение: каждый файл имеет свой стабильный префикс.
  AGENTS-core.md     (1 500 токенов) — читается каждую сессию, кэшируется
  AGENTS-ops.md      (1 000 токенов) — lazy load при /save, /process
  AGENTS-governance.md (1 000 токенов) — lazy load при /lint, /resolve
  AGENTS-publish.md   (800 токенов) — lazy load при publish-task

Кэш работает для каждого файла отдельно. Синергия, не конфликт.
```

### Конфликт 3: OPT-06 (Session memory) vs HR-06 (Session Budget) → ДОПОЛНЯЮТ

```
OPT-06: Агент не перечитывает файлы в рамках сессии (экономия)
HR-06:  Агент останавливается при 85% бюджета (потолок)

Реализовать как единое правило в AGENTS.md. Нет противоречия.
```

### Конфликт 4: OPT-02 vs HR-04 → НЕТ КОНФЛИКТА

```
OPT-02  .drift-cache.json  — для source страниц (check_interval)
HR-04   retrieval_weight   — для всех wiki страниц (access frequency)

Разные данные, разные файлы. Оба нужны.
```

---

## 3. Полная согласованная карта оптимизаций

Итоговый список без дублей и конфликтов:

### Группа А — Кэши (заменяют чтение файлов на компактный JSON)

```
OPT-01  index.min.json           wiki индекс (14K → 2.5K токенов)
OPT-02  .drift-cache.json        source drift состояние
OPT-03  _user/.compiled.json     user context (950 → 120 токенов)
HR-05   compressed поля в schema source страницы в wiki/ (2K → 200 токенов)
```

### Группа Б — Структурные правила (0 строк кода)

```
HR-01   Stable Prefix Rule       кэш AGENTS.md у провайдера
OPT-04  Lazy loading COMMANDS.md не читать при старте (экономия 8К)
OPT-06  Session memory           не перечитывать файлы в сессии
HR-06   Session Budget Rule      потолок 85%/95% по IDE
HR-02   CCR правило              когда читать raw/, когда compressed
RES-1   log.md не читать         явный запрет в AGENTS.md
RES-3   plans/ lazy load         только при явном запросе
RES-4   Task-Aware Bootstrap     читать только нужное для первой команды
```

### Группа В — Алгоритмы (Python код)

```
HR-03   context-pack             budget-aware /query (заменяет OPT-08)
HR-04   retrieval_weight         умная сортировка FTS результатов
OPT-07  Batch /process           пакетная обработка inbox
OPT-09  AGENTS.md рефакторинг   убрать объяснения (5.5K → 3K токенов)
OPT-05  AGENTS.md split         иерархия файлов (синергия с HR-01)
```

### Группа Г — UX/Schema

```
OPT-10  Patterns pruning        cap 15 записей в _user/patterns.md
HR-07   context_limits в wizard бюджет по IDE из wizard
MIG     Migration скрипт        добавить новые поля в существующие страницы
```

---

## 4. Незатронутые резервы

### Резерв 1: log.md читается — не должен (S, P0)

```markdown
# В AGENTS.md добавить:
log.md файлы (wiki/log.md, _user/log.md) — НИКОГДА не читать при bootstrap.
Они только для записи. История → status --bootstrap или index.min.json.
```

Стоимость: одна строка. Экономия: 0 если уже не читается, большая если читается.

### Резерв 2: .gitignore и служебные файлы (S, P1)

```markdown
# В AGENTS.md:
Не читай при bootstrap: .gitignore, requirements.txt, pyproject.toml,
setup.py, *.cfg, *.ini — структура описана в _domain.md.
```

### Резерв 3: plans/ только по требованию (S, P1)

```markdown
# В AGENTS.md:
plans/ — читать только при /resolve, /skill-port --apply, явном запросе.
НЕ читать при bootstrap или /query.
```

### Резерв 4: Task-Aware Bootstrap (S, P1)

Разные задачи требуют разного контекста при старте:

```markdown
# В AGENTS.md — Task-Aware Bootstrap:

Всегда читать: AGENTS-core.md
Дополнительно только при:
  /query, /save, /process → index.min.json + .compiled.json
  /lint, /resolve         → AGENTS-governance.md
  /skill-port, /skill-sync → skills-core/index.min.json
  /source-check           → .drift-cache.json
  /health                 → все кэши
  /harvest                → memoir файлы
```

```
Экономия:
  /query сессия:  4 800 → 3 200 токенов на bootstrap (-33%)
  /lint сессия:   4 800 → 4 000 токенов (-17%)
  /skill-port:    4 800 → 3 500 токенов (-27%)
```

### Резерв 5: Deduplicated context для multi-project сессий (M, P3)

При работе с двумя проектами одновременно дублирующиеся секции
из разных project AGENTS.md читаются дважды. Deduplication по хэшу блоков.
**Рекомендация: пропустить.** Сложность выше отдачи при текущем размере.

### Нужны ли дополнительные оптимизации?

**Ответ: Резервы 1–4 нужны (бесплатны). Резерв 5 — нет.**

При финальной конфигурации с резервами 1–4:
- Bootstrap: ~3 200 токенов (vs 10 850 сейчас, -70%)
- Сессия: ~20 000 токенов (vs 50 000 сейчас, -60%)

Дальнейшая оптимизация — зона убывающей отдачи. Следующий шаг
при 2000+ страниц — vector search как замена FTS5, но это
смена архитектуры, не оптимизация токенов.

### Что нельзя оптимизировать без деградации качества

```
НЕ сжимать:
  - Governance правила в AGENTS.md (потеря нюансов)
  - useful_when поля при /process (нельзя принять решение о дистилляции)
  - Body страниц при /process или /harvest
  - Контекст /skill-port (нужен полный для адаптации)
  - Frontmatter при /lint (именно его и проверяем)
```

---

## 5. Немедленное внедрение всего сразу

### Почему поэтапность не обязательна

Поэтапность предлагалась как "решай проблему когда она возникает".
Но правильнее заложить архитектуру сразу — по трём причинам:

**1. Обратная совместимость.** Все оптимизации совместимы с малым corpus.
`index.min.json` при 10 страницах просто маленький. `retrieval_weight: 0.5`
на новой странице — нейтральный дефолт. Ничего не ломается.

**2. Стоимость retrofit.** Добавить поля в 50 страниц — 10 минут.
В 500 страниц — час. В 1000 страниц — несколько часов.
Retrofit всегда дороже чем upfront.

**3. Привычки агента.** Агент сразу учится использовать `context-pack`
и `index.min.json`. Переучивать сложнее и ненадёжнее.

### Что безопасно при любом размере corpus

```
Группа Б (правила в AGENTS.md):     безопасны при 0 страниц
Группа А (кэши):                    безопасны при 0 страниц (пустые JSON)
Группа В (алгоритмы):               безопасны при 10 страниц
Migration скрипт:                   безопасен, только добавляет поля с дефолтами
```

### Wizard: новые проекты создаются оптимизированными сразу

```python
def setup_project_with_optimizations(project_path: Path) -> None:
    """Новый проект создаётся с кэшами с первого дня."""

    # Пустой index.min.json
    (project_path / "wiki" / "index.min.json").write_text(
        '{"generated":"' + date.today().isoformat() + '","pages":[]}',
        encoding="utf-8", newline="\n"
    )

    # Пустой drift cache для skills-core
    if project_path.name == "skills-core":
        (project_path / ".drift-cache.json").write_text(
            '{"generated":"' + date.today().isoformat() +
            '","overdue":[],"ok_count":0}',
            encoding="utf-8", newline="\n"
        )

    # _domain.md с optimization flags
    write_domain_md(project_path, {
        "context_optimization": {
            "index_format": "min-json",
            "ccr_enabled": True,
            "retrieval_weight_enabled": True,
        }
    })
```

---

## 6. Полный чеклист одним релизом

Общее время: **1–2 дня**.

### День 1 — Правила (без кода, без рисков)

```
AGENTS.md рефакторинг:
□ HR-01  Добавить Stable Prefix Rule (запрет дат/счётчиков в первых 3К токенов)
□ HR-02  Добавить CCR правило (когда читать raw/, когда compressed достаточно)
□ OPT-04 Добавить Lazy loading (COMMANDS.md — только при явном запросе)
□ OPT-06 Добавить Session Memory (bootstrap файлы читать 1× за сессию)
□ HR-06  Добавить Session Budget Rule (70%/85%/95% пороги)
□ RES-1  Добавить: log.md никогда не читать при bootstrap
□ RES-3  Добавить: plans/ только при явном запросе
□ RES-4  Добавить Task-Aware Bootstrap (разные файлы для разных команд)

Schema обновление:
□ HR-05  Добавить compressed/full_version поля в _schema.md (type: source)
□ HR-04  Добавить retrieval_weight/access_count в _schema.md (все типы)

_user/profile.md:
□ HR-07  Добавить context_limits по IDE
         claude-code: 180000, codex: 110000, gemini-cli: 900000,
         windsurf: 90000, cursor: 90000, default: 100000

OPT-05  Разбить AGENTS.md на иерархию:
□        AGENTS-core.md     — запреты + bootstrap + _user/ правила
□        AGENTS-ops.md      — /save, /process, /harvest, /query workflow
□        AGENTS-governance.md — frontmatter schema, quarantine, conflicts
□        AGENTS-publish.md  — dual-remote, publish-task правила
```

### День 2 — Код + миграция

```
Python реализация:
□ OPT-01 build-index-min в reefiki.py + автозапуск после /process и /harvest
□ OPT-02 drift-cache в reefiki.py + git post-commit hook
□ OPT-03 user compile в reefiki.py + инвалидация при изменении _user/
□ HR-03  context-pack в reefiki.py + .claude/commands/context-pack.md
         (НЕ реализовывать OPT-08 FTS pre-filter — HR-03 его заменяет)
□ HR-04  compute_retrieval_weight() + обновление в /query pipeline
□ OPT-07 process --batch --limit 10
□ OPT-09 AGENTS.md рефакторинг контента: убрать объяснения (цель: 5.5K→3K)

Migration:
□ MIG    python scripts/migrations/add_optimization_fields.py projects/*
         Добавляет retrieval_weight, access_count, compressed в существующие страницы
         Безопасен: только добавляет поля с дефолтами, контент не трогает

Wizard обновление:
□ WIZ    Новые проекты создаются с index.min.json и .drift-cache.json сразу
□ WIZ    context_limits добавляется в _user/profile.md при wizard setup

CI добавление:
□ CI     Проверка что index.min.json актуален (не старше последнего /process)
□ CI     Lint Stable Prefix: нет дат в первых 3К токенов AGENTS-core.md
□ CI     Проверка .drift-cache.json не старше 7 дней
```

### Проверка результата

```bash
# Оценка bootstrap после внедрения
python scripts/reefiki.py status --bootstrap --format json

# Проверка Stable Prefix
python scripts/reefiki.py lint-agents --check stable-prefix
# Ожидаем: "✅ No dynamic content in first 3000 tokens of AGENTS-core.md"

# Проверка index.min.json
python scripts/reefiki.py index --verify --format min-json
# Ожидаем: "✅ index.min.json up to date (N pages)"

# Тест context-pack
python scripts/reefiki.py context-pack "code review" --budget 3000
# Ожидаем: "<!-- context-pack: N страниц, ~XXXX токенов из 3000 бюджета -->"
```

---

## Итоговое резюме

| Вопрос | Ответ |
|---|---|
| Насколько Headroom снижает vs baseline? | -52% при 500 стр., -40% при 1000 стр. |
| Насколько vs аудиты без оптимизаций? | -76% при 500 стр., -81% при 1000 стр. |
| Конфликты между оптимизациями? | OPT-08 дублирует HR-03 → отменён. OPT-05+HR-01 → синергия. |
| Незатронутые резервы? | 4 резерва (правила в AGENTS.md, бесплатно, +20–33%) |
| Нужна ли оптимизация дальше? | Нет. Следующий уровень — vector search при 2000+ стр. |
| Можно ли внедрить всё сразу? | Да. День 1: правила. День 2: код + миграция. |
| Сломает ли маленький corpus? | Нет. Все оптимизации корректны при любом размере. |

```
Финал при полном внедрении (500 страниц, 20 сессий/месяц):

Baseline сейчас:          50 000 токенов/сессию    1.0 млн/месяц
После всех оптимизаций:   20 000 токенов/сессию    0.40 млн/месяц
                          ─────────────────────────────────────────
Экономия:                 -60%                      -60%
```
