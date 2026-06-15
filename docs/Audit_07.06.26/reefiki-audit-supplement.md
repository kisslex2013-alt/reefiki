# REEFIKI — Дополнительный аудит: непокрытые и поверхностно затронутые темы

> **Версия:** 1.0 | **Дата:** 2026-06-04
> **Статус:** Дополнение к основному аудиту `reefiki-audit.md`
> **Охват:** Лицензирование, локализация/FTS5, производительность, disaster recovery,
> accessibility, mobile capture, Obsidian-конфликты, schema migrations,
> конкурентный анализ, метрики здоровья базы знаний.

---

## Содержание

1. [Лицензирование и юридика](#1-лицензирование-и-юридика)
2. [Локализация и мультиязычность в FTS5](#2-локализация-и-мультиязычность-в-fts5)
3. [Производительность на реальных данных](#3-производительность-на-реальных-данных)
4. [Disaster Recovery и бэкап-стратегия](#4-disaster-recovery-и-бэкап-стратегия)
5. [Accessibility и UX для нетехнических пользователей](#5-accessibility-и-ux-для-нетехнических-пользователей)
6. [Mobile и capture-flow](#6-mobile-и-capture-flow)
7. [Obsidian-интеграция: конфликты и риски](#7-obsidian-интеграция-конфликты-и-риски)
8. [Эволюция схемы: migrations](#8-эволюция-схемы-migrations)
9. [Конкурентный анализ](#9-конкурентный-анализ)
10. [Метрики здоровья базы знаний](#10-метрики-здоровья-базы-знаний)
11. [Сводная таблица предложений](#11-сводная-таблица-предложений)

---

## 1. Лицензирование и юридика

### Текущее состояние

В репозитории отсутствует файл `LICENSE`. Это не технический недочёт — это юридический
вакуум с конкретными последствиями.

По умолчанию в большинстве юрисдикций **код без лицензии защищён авторским правом
автора, все права сохранены**. Это означает:

- Форк репозитория технически возможен, но юридически является нарушением
- Контрибьюторы не могут законно использовать код в своих проектах
- Компании не могут использовать REEFIKI в коммерческих продуктах без явного разрешения
- GitHub звёзды и форки не дают никаких прав на использование

### Выбор лицензии: матрица решений

| Цель | Рекомендуемая лицензия | Что разрешает | Что запрещает |
|---|---|---|---|
| Максимальное adoption | MIT | Всё, включая коммерческое использование | Ничего |
| Защита от закрытых форков | AGPL-3.0 | Использование, модификацию, распространение | Использование в SaaS без открытия кода |
| Баланс: open + коммерция | Apache 2.0 | Всё + патентная защита | Использование товарных знаков |
| Knowledge Commons | CC BY 4.0 (для контента) + MIT (для кода) | Свободное распространение знаний | Нет атрибуции |

**Рекомендация для REEFIKI:**

Двойная лицензия отражает двойственную природу проекта:
- **Код** (`scripts/`, `tests/`, `.claude/commands/`): **MIT** — минимум friction для adoption
- **Контент-шаблоны** (`projects/_template/wiki/`, `AGENTS.md`, `COMMANDS.md`): **CC BY 4.0**

Это стандартная практика для knowledge tools (Obsidian, Logseq используют похожие схемы).

### Что добавить в репозиторий

```
LICENSE              ← MIT для кода
LICENSE-CONTENT      ← CC BY 4.0 для шаблонов и документации
NOTICE               ← список использованных зависимостей (Apache 2.0 требует)
```

В `README.md` добавить секцию:
```markdown
## License
Code: [MIT](LICENSE)
Templates & documentation: [CC BY 4.0](LICENSE-CONTENT)
```

### Дополнительные риски

**CLA (Contributor License Agreement).** Если проект планирует монетизацию или смену
лицензии в будущем — лучше добавить простой CLA сейчас, пока контрибьюторов мало.
GitHub App `cla-assistant` настраивается за 10 минут.

**Frontmatter с внешними источниками.** Пользователи сохраняют `raw/` копии
веб-страниц и статей. Это может нарушать copyright источников. Стоит добавить
`docs/legal-notice.md` с предупреждением: `raw/` — только для личного использования,
не публиковать в публичных репозиториях.

**LLM-generated content.** Страницы созданные агентом содержат AI-generated text.
В некоторых юрисдикциях это влияет на copyright. Рекомендация: добавить в AGENTS.md
явное указание что пользователь несёт ответственность за публикуемый контент.

### Приоритет и сложность

**Приоритет: P0** — блокирует любое серьёзное open-source adoption.
**Сложность: S** (< 1 дня) — добавить LICENSE, обновить README.

---

## 2. Локализация и мультиязычность в FTS5

### Текущее состояние

REEFIKI содержит документацию на трёх языках (RU/EN/ZH), пользователи пишут wiki-страницы
на русском и английском. SQLite FTS5 используется как поисковый движок. Это создаёт
нетривиальную техническую проблему.

### Как FTS5 токенизирует текст по умолчанию

По умолчанию FTS5 использует токенизатор `unicode61`. Он корректно:
- Разбивает текст по пробелам и пунктуации
- Нормализует Unicode (lowercase, NFD)
- Обрабатывает кириллические символы как буквы (не разбивает их)

Но он **не** делает:
- Морфологического анализа (stemming) — "искать", "ищет", "поиск" — разные токены
- Лемматизации — "страницы" и "страница" не совпадают при поиске
- Транслитерации — запрос "reefiki" не найдёт "рифики"

### Практические последствия для русского языка

**Проблема 1: Флексии глаголов и существительных**

```sql
-- Пользователь ищет:
SELECT * FROM fts WHERE fts MATCH 'анализировать';

-- Не найдёт страницы содержащие:
-- "анализировал", "анализируем", "анализируется", "анализ"
```

Для английского это менее критично (меньше словоформ). Для русского — серьёзная
проблема: у типичного русского глагола ~20 форм, у существительного ~12.

**Проблема 2: Поиск по `useful_when`**

`useful_when` — ключевое поле для retrieval. Пользователь пишет:
```yaml
useful_when: "когда нужно анализировать производительность"
```

Запрос "анализ производительности" это **не найдёт**. Поиск работает только при
точном совпадении формы слова.

**Проблема 3: Смешанные запросы RU+EN**

```
/query когда использовать async/await
```

FTS5 корректно обработает "async/await" (латиница) и "использовать" (кириллица)
как отдельные токены — но морфологии нет ни для одного из них в русской части.

### Диагностика: как проверить текущее состояние

```python
import sqlite3

conn = sqlite3.connect("projects/myproject/.reefiki/index.sqlite")

# Проверить какой токенизатор используется
cursor = conn.execute("SELECT * FROM fts_config WHERE k = 'tokenize'")
print(cursor.fetchone())
# Ожидаем: ('tokenize', 'unicode61') или ('tokenize', 'porter unicode61')

# Проверить как индексируются русские слова
cursor = conn.execute("""
    SELECT snippet(fts, 0, '[', ']', '...', 10)
    FROM fts
    WHERE fts MATCH 'анализировать'
    LIMIT 3
""")
print(cursor.fetchall())
```

### Решения по уровню сложности

**Решение A: PREFIX поиск (S, 1 день)**

Наименее инвазивное изменение. FTS5 поддерживает prefix queries:

```sql
-- Вместо точного совпадения:
SELECT * FROM fts WHERE fts MATCH 'анализировать';

-- Prefix search (найдёт анализировать, анализировал, анализирует):
SELECT * FROM fts WHERE fts MATCH 'анализирова*';
```

В `reefiki.py` при построении запроса добавлять `*` к каждому токену запроса
если он длиннее 4 символов. Простая эвристика которая значительно улучшает recall.

```python
def build_fts_query(user_query: str, prefix_threshold: int = 4) -> str:
    tokens = user_query.split()
    fts_tokens = []
    for token in tokens:
        if len(token) >= prefix_threshold:
            fts_tokens.append(f"{token}*")
        else:
            fts_tokens.append(token)
    return " ".join(fts_tokens)
```

**Решение B: Porter stemmer для английской части (S, 1 день)**

FTS5 поддерживает встроенный Porter stemmer для английского:

```sql
CREATE VIRTUAL TABLE fts USING fts5(
    content,
    tokenize = 'porter unicode61'  -- только для EN
);
```

Плюс: "analyze", "analyzing", "analysis" становятся одним токеном.
Минус: на русском Porter не работает корректно (алгоритм разработан для EN).

**Решение C: Внешний стеммер для русского (M, 3–5 дней)**

Наиболее полное решение. `snowballstemmer` — легковесная библиотека без зависимостей:

```python
import snowballstemmer

stemmer_ru = snowballstemmer.stemmer("russian")
stemmer_en = snowballstemmer.stemmer("english")

def stem_query(query: str) -> str:
    tokens = query.split()
    stemmed = []
    for token in tokens:
        # Определяем язык по Unicode диапазону
        if any('\u0400' <= c <= '\u04ff' for c in token):
            stemmed.append(stemmer_ru.stemWord(token.lower()))
        else:
            stemmed.append(stemmer_en.stemWord(token.lower()))
    return " ".join(stemmed)
```

При индексировании применять тот же stemmer к контенту страниц.
При поиске применять к запросу пользователя.

Результат: "анализировать", "анализировал", "анализ" → один стем "анализ".

**Решение D: Hybrid search (XL, 3+ недели)**

Добавить векторный поиск (embeddings) параллельно с FTS5.
Это решает семантическое несоответствие ("быстродействие" ≈ "производительность"),
но добавляет внешнюю зависимость (OpenAI/local embeddings model) и хранилище векторов.

Обозначено в ROADMAP как будущая фаза. Не рекомендуется до Phase 1 (500+ страниц).

### Рекомендуемая последовательность

1. **Сейчас:** добавить prefix search (Решение A) — немедленное улучшение, 1 день
2. **При 200+ страницах:** добавить snowball stemmer (Решение C)
3. **При Phase 1:** оценить hybrid search (Решение D)

### Документация

Добавить в `docs/fts-internals.md`:
- Как построен индекс, что индексируется (title, body, useful_when, tags)
- Текущие ограничения морфологии
- Как пользователю улучшить поиск (кавычки для фразы, `*` для prefix, `OR` для вариантов)
- Пример: `"code review" OR "проверка кода"*`

**Приоритет: P1** | **Сложность: S→M** (prefix сейчас, stemmer позже)

---

## 3. Производительность на реальных данных

### Почему это важно сейчас

Phase 0i: ~100 страниц — производительность не ощущается. Но ROADMAP описывает
переходы: Phase 0ii (200+), Phase 1 (500+), Phase 2 (1000+). Без бенчмарков
невозможно понять когда FTS5 станет узким местом и нужна ли замена.

### Операции которые нужно замерить

**1. `build_index` / `/reindex`**

Полная перестройка индекса — самая тяжёлая операция. Выполняется при:
- Первом запуске на репозитории
- После `/reindex` (аварийный сброс)
- После массового импорта страниц

```python
# Псевдокод бенчмарка
import time, sqlite3, pathlib

def benchmark_build_index(wiki_dir: str) -> dict:
    pages = list(pathlib.Path(wiki_dir).rglob("*.md"))
    
    start = time.perf_counter()
    # ... вызов build_index ...
    elapsed = time.perf_counter() - start
    
    return {
        "page_count": len(pages),
        "total_seconds": elapsed,
        "ms_per_page": (elapsed / len(pages)) * 1000,
        "db_size_mb": os.path.getsize("index.sqlite") / 1024 / 1024
    }
```

**Ожидаемые результаты (оценка):**

| Страниц | Время build_index | Размер БД | Приемлемо? |
|---|---|---|---|
| 100 | < 0.5s | ~1 MB | Да |
| 500 | 1–3s | ~5 MB | Да |
| 1000 | 3–8s | ~10 MB | Зависит от контекста |
| 5000 | 20–60s | ~50 MB | Нужна инкрементальная индексация |
| 10000 | 60–180s | ~100 MB | FTS5 достигает предела |

**2. `search` / `/query`**

Поиск — критичная операция для UX. Агент вызывает её часто.

```python
def benchmark_search(db_path: str, queries: list[str]) -> dict:
    conn = sqlite3.connect(db_path)
    results = []
    
    for query in queries:
        start = time.perf_counter()
        cursor = conn.execute(
            "SELECT rowid, rank FROM fts WHERE fts MATCH ? ORDER BY rank LIMIT 20",
            (query,)
        )
        rows = cursor.fetchall()
        elapsed = (time.perf_counter() - start) * 1000
        results.append({"query": query, "ms": elapsed, "hits": len(rows)})
    
    return results
```

**Ожидаемые результаты:**

| Страниц | Простой запрос | Сложный запрос (3+ слова) | BM25 ранжирование |
|---|---|---|---|
| 100 | < 1ms | < 5ms | < 5ms |
| 1000 | 1–5ms | 5–20ms | 10–30ms |
| 5000 | 5–20ms | 20–100ms | 50–200ms |
| 10000 | 20–100ms | 100–500ms | 200–1000ms |

При >100ms пользователь начинает ощущать задержку. Для агента в интерактивной сессии
критична граница ~50ms.

**3. Инкрементальное обновление (add/update single page)**

Самая частая операция — добавление одной страницы после `/process`.

```python
def benchmark_incremental_update(db_path: str, page_content: str) -> float:
    conn = sqlite3.connect(db_path)
    start = time.perf_counter()
    conn.execute("INSERT INTO fts(content) VALUES (?)", (page_content,))
    conn.commit()
    return (time.perf_counter() - start) * 1000  # ms
```

Должна быть < 10ms независимо от размера корпуса — это свойство FTS5.

### Узкие места помимо FTS5

**Frontmatter parsing при build_index.**
Если `validate_frontmatter.py` парсит YAML на Python для каждой страницы —
при 5000 страниц это может быть узким местом. Стоит профилировать:

```bash
python -m cProfile -o profile.out scripts/reefiki.py reindex --project myproject
python -m pstats profile.out  # топ-20 функций по времени
```

**Git операции.**
`guard-staged` вызывает `git status` и `git diff --staged`. При большом репозитории
(10000+ файлов) это может быть медленным. Рассмотреть `--porcelain` флаг и кэширование
результата в рамках сессии.

**index.md генерация.**
Если `index.md` генерируется как markdown-таблица из всех страниц — при 1000+ страниц
файл становится большим (>500KB) и медленным для агента. Рассмотреть пагинацию
или замену на `index.min.json` (описано в разделе оптимизации токенов).

### Рекомендации

**Добавить `scripts/benchmark.py`:**

```python
#!/usr/bin/env python3
"""REEFIKI performance benchmarks.
Usage: python scripts/benchmark.py --project myproject --sizes 100,500,1000
"""
import argparse, time, sqlite3, pathlib, json

# ... реализация всех трёх бенчмарков выше ...

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", default="benchmark-results.json")
    args = parser.parse_args()
    
    results = run_all_benchmarks(args.project)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {args.output}")
```

**Добавить в GitHub Actions:**

```yaml
# .github/workflows/benchmark.yml
# Запускается еженедельно или при изменении scripts/
on:
  schedule:
    - cron: '0 9 * * 1'  # каждый понедельник
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/benchmark.py --project _template --output benchmark.json
      - uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: benchmark.json
```

**Триггеры для смены архитектуры:**

| Метрика | Порог "обратить внимание" | Порог "нужна замена" |
|---|---|---|
| `build_index` время | > 10s | > 60s |
| `search` latency | > 50ms | > 200ms |
| Размер index.sqlite | > 50MB | > 200MB |
| Страниц в корпусе | > 2000 | > 5000 |

**Приоритет: P2** | **Сложность: M** (бенчмарк-скрипт + CI)

---

## 4. Disaster Recovery и бэкап-стратегия

### Текущее состояние: единственная защита

REEFIKI хранит знания в:
1. **Markdown файлы** — в git, защищены историей коммитов
2. **SQLite FTS5 индекс** — в `.reefiki/index.sqlite`, **не в git** (в `.gitignore`)
3. **Git история** — локальная + remote (dual-remote при настройке)

Единственная защита данных — `git push` на remote. Если remote не настроен
или push не делался давно — все изменения существуют только локально.

### Сценарии потери данных

**Сценарий 1: Повреждение SQLite базы**

SQLite базы могут повреждаться при:
- Внезапном отключении питания в момент записи
- Заполнении диска во время транзакции
- Аппаратных ошибках (bad sectors)
- Одновременном доступе нескольких процессов без WAL mode

```bash
# Проверить целостность базы
sqlite3 .reefiki/index.sqlite "PRAGMA integrity_check;"
# Ожидаемый ответ: "ok"
# При ошибке: "*** in database main ***" + описание проблемы
```

**Последствие:** потеря FTS5 индекса. Решение: `/reindex` восстанавливает из markdown.
**Вывод: SQLite в REEFIKI — не критичный компонент**, это кэш. Markdown — источник правды.

**Сценарий 2: Случайное удаление wiki страницы**

Пользователь или агент удалил страницу. В git — коммит без неё.

```bash
# Восстановление из git
git log --all --full-history -- "projects/myproject/wiki/concepts/my-concept.md"
git checkout <commit-hash>^ -- "projects/myproject/wiki/concepts/my-concept.md"
```

**Проблема:** нет документации этого процесса в REEFIKI. Пользователь в стрессе
не знает эту команду.

**Решение:** добавить `docs/recovery.md` с готовыми командами для типичных сценариев.

**Сценарий 3: Полная потеря локального репозитория**

Сгорел диск / украли ноутбук / случайный `rm -rf`.

При настроенном dual-remote: восстановление через `git clone`. Потеря = незапушенные
коммиты. Если последний push был неделю назад — потеря недели работы.

**Проблема:** нет механизма контроля "давно ли был последний push". Bootstrap checklist
это частично решает (D4 из основного аудита), но нет автоматического напоминания.

**Сценарий 4: Corruption в dual-remote**

Если `publish-task` имеет баг и публикует private данные — отозвать из публичного
git remote сложно (история сохраняется). Git не имеет "удалить навсегда" без
`git filter-branch` / `git filter-repo`.

**Это самый серьёзный из сценариев** — необратим по природе.

### Рекомендации

**R1: WAL mode для SQLite (S, < 1 дня)**

```python
# В начале каждого подключения к БД
conn = sqlite3.connect("index.sqlite")
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
```

WAL (Write-Ahead Logging) значительно снижает риск повреждения при сбоях питания.
Это стандартная практика для production SQLite.

**R2: Документ `docs/recovery.md` (S, 1 день)**

```markdown
# REEFIKI — Recovery Guide

## Повреждён или потерян FTS5 индекс
python scripts/reefiki.py reindex --project <name>
Индекс восстанавливается из markdown за ~30 секунд.

## Случайно удалена wiki страница
# Найти коммит до удаления:
git log --all --oneline -- "projects/<name>/wiki/<path>.md"
# Восстановить:
git checkout <hash>^ -- "projects/<name>/wiki/<path>.md"

## Случайно удалён целый проект
git log --all --oneline -- "projects/<name>/"
git checkout <hash>^ -- "projects/<name>/"

## Полная потеря репозитория (если есть remote)
git clone <remote-url> reefiki
cd reefiki && python scripts/reefiki.py reindex --all-projects

## Проверить целостность БД
sqlite3 projects/<name>/.reefiki/index.sqlite "PRAGMA integrity_check;"

## Проверить давность последнего push
git log --oneline -1 origin/main  # или master
git log --format="%ar" -1 origin/main  # "3 days ago"
```

**R3: Backup age как метрика в `/status` (S, включён в D4)**

```json
{
  "backup_age": {
    "last_push_days": 7,
    "last_push_remote": "origin",
    "warning": true,
    "message": "Последний push 7 дней назад. Рекомендуется git push."
  }
}
```

Порог предупреждения: > 3 дней для активного использования, > 7 дней для любого.

**R4: Pre-commit hook для проверки WAL mode (S)**

```bash
#!/bin/bash
# .git/hooks/pre-commit

for db in $(find projects/ -name "index.sqlite" 2>/dev/null); do
    mode=$(sqlite3 "$db" "PRAGMA journal_mode;" 2>/dev/null)
    if [ "$mode" != "wal" ]; then
        echo "WARNING: $db не в WAL mode. Запустите: python scripts/reefiki.py db-init"
    fi
done
```

**R5: Документация для dual-remote emergency recovery**

Если private данные попали в public remote:

```bash
# Немедленно: сделать репо приватным на GitHub
# Потом очистить историю:
git filter-repo --path projects/private-project/ --invert-paths
git push origin --force --all
git push origin --force --tags
# ПРЕДУПРЕЖДЕНИЕ: это переписывает историю, все форки сломаются
```

Добавить в `docs/recovery.md` секцию "Privacy Emergency" с этими командами
и явным предупреждением о последствиях.

**R6: Cron-скрипт для локального бэкапа (P3, опциональный)**

Для параноидальных пользователей:

```bash
# scripts/local-backup.sh
#!/bin/bash
BACKUP_DIR="$HOME/.reefiki-backups"
DATE=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/reefiki-$DATE.tar.gz" \
    --exclude=".git" \
    --exclude="*.sqlite-wal" \
    --exclude="*.sqlite-shm" \
    .
# Удалить бэкапы старше 30 дней
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
echo "Backup: $BACKUP_DIR/reefiki-$DATE.tar.gz"
```

Добавить в crontab: `0 2 * * * cd ~/reefiki && bash scripts/local-backup.sh`

**Приоритет: R1+R2=P1, R3–R5=P2, R6=P3** | **Сложность: S–M**

---

## 5. Accessibility и UX для нетехнических пользователей

### Текущие барьеры

REEFIKI неявно предполагает пользователя который:
- Знает git (clone, commit, push, branch)
- Понимает markdown
- Работает в IDE/code editor
- Комфортно читает техническую документацию
- Знает Python или не нуждается в установке

Реальные потенциальные пользователи которых это исключает:
- **Исследователи и академики** — работают с большими корпусами знаний, но не программисты
- **Менеджеры продуктов** — накапливают решения и контекст, но используют Notion/Confluence
- **Журналисты и writers** — управляют источниками и идеями, но в Obsidian или Bear
- **Юристы** — структурированное знание критично, но CLI недоступен

### Gap анализ по барьерам

**Барьер 1: Git как обязательное условие**

Git — инструмент разработки. Для нетехнического пользователя команды `git add`,
`git commit`, `git push` — непрозрачный ритуал без понятного смысла.

REEFIKI использует git для: версионирования, бэкапа, dual-remote publish.
Для нетехнического пользователя нужна абстракция:

```
"Сохранить" = git add + git commit (скрыто)
"Синхронизировать" = git push + git pull (скрыто)
"История" = git log (скрыто)
```

Агент уже частично это делает — но только в сессии. Вне IDE с агентом пользователь
видит "голый" git.

**Барьер 2: Markdown как формат ввода**

Пользователи Notion и Obsidian знают markdown. Пользователи Word и Google Docs — нет.
`## Заголовок`, `**жирный**`, `[[ссылка]]` — не очевидны.

REEFIKI не требует markdown от пользователя напрямую — агент пишет страницы сам.
Но пользователь видит markdown в файлах и это может пугать.

**Барьер 3: IDE как обязательная среда**

Claude Code, Cursor, Windsurf — инструменты для разработчиков. Нетехнический
пользователь не знает как их установить и настроить. Время установки: 20–40 минут.

Альтернатива: claude.ai (веб) или мобильное приложение Claude. Но они не имеют
доступа к локальной файловой системе.

**Барьер 4: Документация написана для разработчиков**

AGENTS.md начинается с "Control plane operations", "dual-remote publishing",
"FTS5 cache". Это нормально для contributor, но не для researcher который хочет
просто сохранять заметки об источниках.

### Рекомендации

**A1: User persona документация (S, 1–2 дня)**

Добавить в `docs/` руководства для конкретных персон:
- `docs/for-researchers.md` — как REEFIKI помогает управлять источниками и синтезом
- `docs/for-managers.md` — как хранить решения, контекст проекта, lessons learned
- `docs/for-writers.md` — как организовать research для статей и книг

Каждый документ: без технического жаргона, конкретные примеры use cases,
скриншоты результата (wiki страницы) а не команд.

**A2: "Easy mode" через claude.ai (M, 3–5 дней)**

Для пользователей без локальной IDE — REEFIKI через GitHub + claude.ai:

```markdown
# REEFIKI без установки

1. Форкни репозиторий на GitHub
2. Открой claude.ai → прикрепи ссылку на репозиторий
3. Скажи: "Помоги мне сохранить эту статью: [URL]"
4. Claude создаёт файл через GitHub API
5. Файл появляется в твоём форке

Ограничения: нет локального FTS5 поиска, только GitHub search.
Подходит для: начального использования, мобильного capture.
```

Это не требует изменений в коде — только документацию и настройку GitHub Actions
для auto-commit через API.

**A3: Obsidian как нетехнический интерфейс (S, 1 день)**

Obsidian — знакомый нетехническим пользователям инструмент.
Документировать REEFIKI через призму Obsidian-first:

```markdown
# Если ты знаешь Obsidian

1. Открой папку проекта в Obsidian как vault
2. Используй Obsidian для чтения и навигации по wiki
3. Для добавления новых знаний — переключись в Claude Code / claude.ai
4. Obsidian автоматически обновляется — это твой "reader view"
```

**A4: Glossary для нетехнических пользователей (S, 1 день)**

```markdown
# Словарь REEFIKI

**Проект** — папка со связанными знаниями (например, "Исследование рынка 2026")
**Wiki-страница** — структурированная заметка с обязательным полем "когда полезно"
**Источник** — сохранённая веб-страница или документ до обработки
**Обработать** (/process) — превратить сырой источник в структурированное знание
**Индекс** — поисковая база данных (строится автоматически, не трогать руками)
**Карантин** — временное хранилище для спорных или устаревших знаний
**Снапшот** — публичная версия вики (только страницы помеченные как публичные)
```

**A5: Progress indicator для долгих операций (S)**

Нетехнические пользователи тревожатся когда ничего не происходит видимо.
`/reindex` при 500 страниц занимает секунды — без прогресса выглядит как зависание.

```python
def reindex_with_progress(pages: list) -> None:
    total = len(pages)
    for i, page in enumerate(pages, 1):
        index_page(page)
        # Прогресс каждые 10% или каждые 50 страниц
        if i % max(1, total // 10) == 0:
            print(f"Индексирование: {i}/{total} страниц ({i*100//total}%)")
    print(f"✓ Индексирование завершено: {total} страниц")
```

**Приоритет: A1=P2, A2=P3, A3=P1, A4=P2, A5=P2** | **Сложность: S–M**

---

## 6. Mobile и Capture-Flow

### Текущее состояние

ROADMAP упоминает Telegram-бот + Pipedream как способ мобильного capture.
Это решает реальную задачу — "увидел интересное на телефоне, хочу в REEFIKI" —
но создаёт новые риски.

### Архитектура мобильного capture (как понимается из контекста)

```
Телефон
  └─→ Telegram бот (отправить URL / текст)
        └─→ Pipedream webhook (cloud function)
              └─→ GitHub API (создать файл в inbox/)
                    └─→ projects/<name>/inbox/<slug>.md
                          └─→ /process в следующей сессии
```

### Анализ рисков

**Риск 1: Безопасность токенов**

Pipedream workflow содержит:
- Telegram Bot Token
- GitHub Personal Access Token (PAT) с правами на запись в репозиторий

Оба токена — высокая ценность. Компрометация PAT даёт полный доступ к репозиторию
включая private projects и dual-remote настройки.

**Проблемы:**
- PAT в Pipedream environment variables — третья сторона имеет доступ к credentials
- Если используется PAT с широкими правами (`repo` scope) — избыточные права
- Нет ротации токенов: если Pipedream скомпрометирован — доступ к репо открыт бессрочно

**Рекомендации по безопасности токенов:**

```
GitHub Fine-grained PAT (предпочтительно):
  Repository: только reefiki-репозиторий
  Permissions: Contents → Read and Write
               (не нужно: Actions, Issues, PRs, Settings)
  Expiration: 90 дней с напоминанием о ротации
  
НЕ использовать:
  - Classic PAT с repo scope (избыточные права)
  - PAT без expiration
  - OAuth App токен (сложнее ротировать)
```

**Риск 2: Надёжность pipeline**

Pipedream → GitHub API — двухзвенный pipeline. Точки отказа:
- Telegram webhook timeout (Telegram ждёт ответ 60 секунд)
- Pipedream rate limits (free tier: 10,000 invocations/month)
- GitHub API rate limits (5000 requests/hour для authenticated)
- GitHub API unavailability (99.9% uptime ≠ 100%)

При падении любого звена: пользователь отправил в Telegram, файл не создан,
нет уведомления об ошибке, знание потеряно.

**Решение: Dead Letter Queue**

```python
# В Pipedream workflow добавить fallback:
try:
    github_api.create_file(...)
    telegram_bot.send_message("✓ Сохранено в inbox")
except Exception as e:
    # Fallback: сохранить в Pipedream data store
    pipedream.data_store.set(f"failed_{timestamp}", {
        "content": message_text,
        "error": str(e),
        "timestamp": timestamp
    })
    telegram_bot.send_message(
        "⚠️ Временная ошибка. Сохранено локально, "
        "попробую снова через 5 минут."
    )
    # Retry через Pipedream scheduled trigger
```

**Риск 3: Качество capture без обработки**

Telegram capture создаёт файлы в `inbox/` без frontmatter — просто raw текст или URL.
При большом потоке captures:
- `inbox/` переполняется необработанными файлами
- `/process` становится тяжёлой операцией с большим числом принятий решений
- Пользователь откладывает обработку → накапливается долг

**Решение: Minimal structured capture**

Telegram бот при capture задаёт 1 вопрос:
```
Бот: "Сохранено! К какому проекту относится?"
[myproject] [notes] [research] [Другой]
```

Это занимает 2 секунды и позволяет бесплатно добавить `project:` тег в frontmatter
stub, что упрощает `/process` — агент уже знает контекст.

### Альтернативы Telegram+Pipedream

| Метод | Плюсы | Минусы |
|---|---|---|
| Telegram + Pipedream | Уже есть, удобен | Cloud dependency, security risks |
| iOS Shortcut + Working Copy | Полностью локально | Только iOS, нужен Working Copy ($) |
| Obsidian Mobile | Знакомый UI | Нет AI обработки |
| Email → GitHub (Actions) | Нет отдельного сервиса | Медленнее, нет Rich capture |
| Telegram + self-hosted bot | Контроль безопасности | Нужен сервер |

**Рекомендация:** для privacy-first пользователей документировать iOS Shortcut вариант.
Для удобства — оставить Telegram+Pipedream с hardened security (fine-grained PAT, rotation).

### Документация capture-flow

Добавить `docs/mobile-capture.md`:
- Настройка Telegram бота (пошаговая инструкция)
- Настройка fine-grained PAT
- Ротация токенов (напоминание в `/status`)
- iOS Shortcut как альтернатива
- Dead Letter Queue setup

**Приоритет: P1** (security risks актуальны сейчас) | **Сложность: M**

---

## 7. Obsidian-интеграция: конфликты и риски

### Текущая интеграция

Obsidian используется как "reader view" — для навигации по wiki, просмотра графа связей,
поиска. Это разумное разделение: Obsidian читает, REEFIKI (через агента) пишет.

Проблема: это разделение нигде явно не задокументировано и не принудительно.

### Сценарии конфликтов

**Конфликт 1: Одновременное редактирование**

```
Timeline:
  10:00 — Агент начинает писать wiki/concepts/caching.md
  10:01 — Пользователь открывает тот же файл в Obsidian, редактирует
  10:02 — Агент завершает запись, перезаписывает файл
  10:02 — Obsidian видит изменение на диске, показывает diff или просто обновляется
  Результат: правки пользователя в Obsidian потеряны
```

Obsidian не имеет lock mechanism для файлов. Он просто перечитывает файл при изменении
на диске — без merge, без предупреждения о потере данных.

**Конфликт 2: Obsidian Sync и dual-remote**

Если пользователь использует Obsidian Sync (платная функция) параллельно с REEFIKI
dual-remote — два механизма синхронизации работают с одними файлами независимо.

```
Obsidian Sync: vault → Obsidian cloud → другое устройство
REEFIKI:       wiki/ → git origin → git public-remote
```

Это не создаёт конфликта данных (файловая система — источник правды), но создаёт
путаницу: какая версия "правильная"? Что произойдёт если Obsidian Sync обновит
файл который только что был записан агентом?

**Конфликт 3: Obsidian плагины изменяющие файлы**

Obsidian плагины могут модифицировать файлы:
- **Dataview** — read-only, безопасен
- **Templater** — вставляет шаблоны, может добавлять контент в существующие файлы
- **Auto Note Mover** — перемещает файлы по правилам → может сломать REEFIKI structure
- **Linter** — форматирует markdown → может изменить frontmatter, нарушив schema
- **Tag Wrangler** — переименовывает теги → меняет frontmatter во всех файлах

**Критически опасный плагин: Linter**

Obsidian Linter при неправильной настройке может:
- Переформатировать YAML frontmatter (добавить/убрать кавычки, изменить отступы)
- Это приведёт к падению `validate_frontmatter.py` для всех страниц
- pre-commit hook заблокирует коммит
- Пользователь не понимает почему

**Конфликт 4: `.obsidian/` настройки в git**

`.obsidian/` папка содержит: настройки плагинов, темы, раскладки workspace.
Если это в git — разные устройства и разные участники будут конфликтовать по
UI-настройкам. Если не в git — каждое устройство требует ручной настройки.

### Рекомендации

**O1: Явный "read-only mode" для Obsidian в документации (S)**

Добавить в `docs/obsidian-setup.md`:

```markdown
## Важно: Obsidian как reader, не editor

REEFIKI wiki управляется через AI-агента (Claude Code, Cursor и др.).
Obsidian используется для чтения и навигации.

НЕ редактируй wiki-страницы напрямую в Obsidian — 
изменения могут конфликтовать с агентом.

Исключение: можно добавлять заметки в inbox/ через Obsidian.
inbox/ специально не управляется агентом напрямую.
```

**O2: `.obsidian/` в `.gitignore` с объяснением (S)**

```gitignore
# .gitignore
.obsidian/workspace.json   # специфично для устройства
.obsidian/workspace-mobile.json

# НО оставить в git:
# .obsidian/app.json       — базовые настройки приложения
# .obsidian/graph.json     — настройки графа
# .obsidian/plugins/       — список плагинов (но не их data/)
```

Добавить `docs/obsidian-setup.md` секцию "Синхронизация настроек между устройствами".

**O3: Whitelist безопасных плагинов (S)**

```markdown
## Рекомендуемые плагины (безопасны с REEFIKI)

✓ Dataview — запросы к frontmatter, read-only
✓ Tag Wrangler — переименование тегов (использовать осторожно, после backup)
✓ Graph Analysis — анализ связей, read-only
✓ Kanban — для планирования, не трогает wiki/

## Плагины требующие осторожности

⚠️ Linter — отключи "Format frontmatter" для папки wiki/
   Настройка: Linter → Excluded folders → projects/*/wiki/

⚠️ Auto Note Mover — не создавай правила для папки wiki/

⚠️ Templater — не применяй шаблоны к существующим wiki страницам

## Несовместимые плагины

✗ Obsidian Git — конфликтует с REEFIKI git workflow
   (оба пытаются управлять git, результат непредсказуем)
```

**O4: Pre-commit проверка Obsidian Linter damage (S)**

```python
# В validate_frontmatter.py добавить проверку:
def check_for_linter_artifacts(frontmatter: str) -> list[str]:
    """Detect common Obsidian Linter modifications that break REEFIKI schema."""
    issues = []
    
    # Linter добавляет 'date created' и 'date modified'
    if 'date created:' in frontmatter or 'date modified:' in frontmatter:
        issues.append(
            "Обнаружены поля добавленные Obsidian Linter "
            "(date created/modified). "
            "Отключи 'YAML Timestamp' в настройках Linter."
        )
    
    # Linter может изменить формат tags: ['tag'] → tags:\n  - tag
    # Проверить соответствие ожидаемому формату
    
    return issues
```

**O5: Решение конфликта при одновременном редактировании (M)**

Добавить в агентский контракт (AGENTS.md):

```markdown
## Obsidian conflict prevention

Перед записью в wiki-страницу:
1. Проверить mtime файла — если изменён в последние 60 секунд не агентом
   (нет соответствующего entry в session log) → предупредить пользователя
2. Сообщить: "Файл был изменён недавно. Возможно через Obsidian.
   Показать diff перед перезаписью?"
```

**Приоритет: O1+O3=P1, O2+O4=P1, O5=P2** | **Сложность: S–M**

---

## 8. Эволюция схемы: Migrations

### Проблема

REEFIKI построен на frontmatter schema с обязательными полями. По мере развития
проекта schema будет меняться:
- Добавление новых обязательных полей (например, `portability` для skills)
- Переименование полей (`useful_when` → `use_case`?)
- Изменение типов (`tags: string` → `tags: list`)
- Удаление устаревших полей
- Добавление новых типов страниц

При этом существующие страницы не соответствуют новой schema. `validate_frontmatter.py`
начинает падать на всех старых страницах. `/lint` выдаёт сотни ошибок. Пользователь
парализован.

### Текущее состояние

Нет явного механизма миграций. Schema версионирована неявно (через изменения в
`_schema.md`), но нет:
- Версионирования самой schema
- Инструмента для массовой миграции существующих страниц
- Стратегии для backwards compatibility
- Changelog schema изменений

### Реальные сценарии миграции

**Сценарий A: Добавление нового обязательного поля**

Добавляем `portability` как обязательное для `type: skill`.

```yaml
# Старая страница (невалидна после изменения schema):
---
type: skill
title: Iterative Code Review
useful_when: "..."
---

# Новая schema требует:
---
type: skill
title: Iterative Code Review
portability: full | partial | ide-only  # ← новое обязательное
useful_when: "..."
---
```

200 существующих skill страниц разом становятся невалидными.

**Сценарий B: Переименование поля**

`check_interval` (строка "30d") → `check_interval_days` (число 30).

Все source страницы невалидны. Старые данные теряются если миграция некорректна.

**Сценарий C: Изменение типа поля**

`tags: "code-review, workflow"` → `tags: [code-review, workflow]`

FTS5 индекс построен на старом формате. После миграции нужен `/reindex`.

### Решения

**M1: Schema versioning (S, 1 день)**

Добавить версию схемы в `_schema.md` каждого проекта:

```yaml
# projects/skills-core/wiki/_schema.md
---
schema_version: "2.1.0"
last_updated: 2026-06-04
breaking_changes_from: "2.0.0"
---
```

И в frontmatter каждой страницы — опционально:
```yaml
schema_version: "2.0.0"  # версия при создании
```

Это позволяет `validate_frontmatter.py` знать какую schema применять к старой странице.

**M2: Migration CLI (M, 3–5 дней)**

```python
# scripts/reefiki.py migrate --project <name> --from 2.0.0 --to 2.1.0 --dry-run

def migrate_schema(project: str, from_version: str, to_version: str,
                   dry_run: bool = True) -> dict:
    """
    Применяет migration script для перехода между версиями schema.
    dry-run показывает что изменится без реальных изменений.
    """
    migration_path = f"scripts/migrations/{from_version}_to_{to_version}.py"
    
    pages = find_pages_with_schema_version(project, from_version)
    results = {"total": len(pages), "migrated": [], "skipped": [], "errors": []}
    
    for page in pages:
        try:
            new_frontmatter = apply_migration(page, migration_path)
            if dry_run:
                results["migrated"].append({
                    "path": page,
                    "diff": compute_diff(page.frontmatter, new_frontmatter)
                })
            else:
                write_frontmatter(page, new_frontmatter)
                results["migrated"].append(page)
        except Exception as e:
            results["errors"].append({"path": page, "error": str(e)})
    
    return results
```

Каждая миграция — отдельный Python файл:

```python
# scripts/migrations/2.0.0_to_2.1.0.py

def migrate_page(frontmatter: dict) -> dict:
    """Migration: add portability field to skill pages."""
    if frontmatter.get("type") != "skill":
        return frontmatter  # только skill страницы
    
    if "portability" not in frontmatter:
        # Дефолтное значение — "unknown" безопаснее чем угадывать
        frontmatter["portability"] = "unknown"
        frontmatter["_migration_note"] = "portability=unknown: требует ручной проверки"
    
    frontmatter["schema_version"] = "2.1.0"
    return frontmatter
```

**M3: Backwards compatibility mode (M)**

Добавить в `validate_frontmatter.py` режим совместимости:

```python
def validate_page(page_path: str, strict: bool = False) -> ValidationResult:
    """
    strict=False (default): предупреждения вместо ошибок для устаревших полей
    strict=True: ошибки для любого несоответствия schema
    """
    frontmatter = parse_frontmatter(page_path)
    page_schema_version = frontmatter.get("schema_version", "1.0.0")
    current_schema = load_schema()
    
    if page_schema_version < current_schema.version:
        if strict:
            return ValidationResult.error(
                f"Schema устарела: {page_schema_version} → {current_schema.version}. "
                f"Запусти: reefiki migrate --from {page_schema_version}"
            )
        else:
            return ValidationResult.warning(
                f"Страница создана под schema {page_schema_version}. "
                f"Рекомендуется миграция."
            )
    
    return validate_against_current_schema(frontmatter, current_schema)
```

**M4: CHANGELOG.schema.md (S)**

```markdown
# REEFIKI Schema Changelog

## 2.1.0 (2026-06-04)
**Breaking change для type: skill**
- Добавлено обязательное поле `portability: full | partial | ide-only | unknown`
- Добавлено поле `implementations` (map IDE → status)
Migration: `reefiki migrate --from 2.0.0 --to 2.1.0`
Затронуто страниц: ~50 skill страниц в skills-core и IDE-проектах

## 2.0.0 (2026-03-15)
**Breaking change для type: source**
- Добавлено поле `source_nature: static | living`
- `check_interval` теперь обязательный для living источников
Migration: `reefiki migrate --from 1.9.0 --to 2.0.0`
```

**M5: Pre-migration backup (автоматический, S)**

```python
def safe_migrate(project: str, from_v: str, to_v: str) -> None:
    """Всегда создаёт git commit перед миграцией."""
    
    # Проверить что нет unstaged изменений
    if has_unstaged_changes():
        raise MigrationError(
            "Есть несохранённые изменения. "
            "Сделай git commit или git stash перед миграцией."
        )
    
    # Создать backup commit
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m",
                    f"chore: pre-migration backup (schema {from_v})"])
    
    # Выполнить миграцию
    result = migrate_schema(project, from_v, to_v, dry_run=False)
    
    # Commit результата
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m",
                    f"chore: migrate schema {from_v} → {to_v} "
                    f"({result['total']} pages)"])
    
    print(f"✓ Миграция завершена. Откат: git revert HEAD")
```

**Приоритет: M1+M4=P1, M2+M3=P1, M5=P0 (безопасность данных)** | **Сложность: M–L**

---

## 9. Конкурентный анализ

### Позиционирование REEFIKI

REEFIKI — не SaaS memory service и не просто markdown vault.
Это **local-first knowledge control plane с AI-agent governance**.

Ближайшая аналогия из других областей: Terraform для infrastructure, но для personal knowledge.
"Infrastructure as Code" → "Knowledge as Code".

### Полный конкурентный ландшафт

#### Tier 1: Прямые конкуренты (PKM + AI)

**Notion AI**

| Параметр | Notion AI | REEFIKI |
|---|---|---|
| Хранение | Cloud (Notion servers) | Local-first (git) |
| Формат | Proprietary blocks | Open markdown |
| AI интеграция | Встроенная, один провайдер | Агент-нейтральный, любой LLM |
| Governance | Нет schema enforcement | Обязательный frontmatter + useful_when |
| Поиск | Full-text + AI semantic | FTS5 (+ будущий vector) |
| Цена | $10–20/месяц | Бесплатно (self-hosted) |
| Vendor lock | Высокий (экспорт ограничен) | Нулевой (plain markdown + git) |
| Privacy | Данные на серверах Notion | Полный контроль |

**REEFIKI выигрывает:** privacy, vendor independence, governance discipline, offline-first.
**Notion AI выигрывает:** UX для нетехнических пользователей, collaboration, no setup.

---

**Roam Research**

| Параметр | Roam | REEFIKI |
|---|---|---|
| Парадигма | Bidirectional links, outliner | Typed pages, control plane |
| AI | Minimal (community plugins) | Core feature (multi-agent) |
| Формат | Proprietary (EDN) | Open markdown |
| Governance | Нет | Обязательные поля, quarantine |
| Цена | $15/месяц | Бесплатно |
| Экспорт | Ограничен | Git → любой формат |

Roam — инструмент для мышления (non-linear notes). REEFIKI — инструмент для
дистилляции (structured knowledge extraction). Разные философии, не прямые конкуренты.

---

**Logseq**

| Параметр | Logseq | REEFIKI |
|---|---|---|
| Local-first | Да (опционально sync) | Да |
| Формат | Markdown + Org-mode | Markdown |
| AI | Logseq AI (plugin) | Native multi-agent |
| Governance | Нет | Core feature |
| Open source | Да (AGPL) | Нет лицензии пока |
| Мобильный | Да (iOS/Android app) | Через Telegram bot |

Logseq — ближайший аналог по философии (local-first, open format). Разница:
Logseq фокусируется на daily notes и outlining, REEFIKI на structured extraction и agent governance.

**Стратегический вопрос:** Logseq имеет активное open-source сообщество и мобильные приложения.
REEFIKI не должен конкурировать с Logseq на поле UX — нужно дифференцироваться
через governance и multi-agent integration.

---

**Capacities**

Менее известный, но релевантный конкурент. Typed objects (аналог typed pages в REEFIKI),
visual graph, AI features. Cloud-first, не open format.

REEFIKI `type: source / entity / concept / synthesis / decision / skill` — прямой аналог
Capacities "object types". Но REEFIKI делает это через plain markdown, не через
proprietary data model.

---

**Obsidian (без AI плагинов)**

Уже используется как viewer в REEFIKI. Как конкурент:

| Параметр | Obsidian | REEFIKI |
|---|---|---|
| Редактирование | Человек | AI-агент |
| Governance | Нет | Core feature |
| AI | Через плагины (Copilot, Smart Connections) | Native |
| Community | Огромное (1M+ пользователей) | Начальное |
| Плагины | 1000+ | CLI commands |

REEFIKI может позиционироваться как "governance layer для Obsidian vault" —
не конкурент, а расширение. Это снижает барьер входа для Obsidian-пользователей.

#### Tier 2: Смежные конкуренты (AI Memory Services)

| Сервис | Модель | Отличие от REEFIKI |
|---|---|---|
| Mem0 | Memory as a Service API | Cloud, no governance, для приложений не людей |
| Zep | Long-term memory для агентов | Для разработчиков, не для personal knowledge |
| LangChain Memory | Framework компонент | Техническая библиотека, не user tool |
| Honcho | User context для AI apps | Closest to REEFIKI in philosophy |

**Honcho** — наиболее близкий идеологически: "user model" для AI apps, local-first опции.
Стоит следить как reference implementation.

#### Tier 3: Workflow tools с knowledge features

**Linear** (для decision tracking), **Notion** (для team knowledge), **Confluence**
(для enterprise) — конкурируют только в части `type: decision` и `type: synthesis`.
Не прямая конкуренция.

### Позиционирование: что реально уникально

После анализа — три действительно уникальных комбинации в REEFIKI:

**1. Governance-first + open format**

Ни один конкурент не имеет обязательного `useful_when` с refusal enforcement.
Это не фича — это философия. "Distillation over archival" как core principle.
Ни Notion, ни Obsidian, ни Logseq не делают это.

**2. Multi-agent, vendor-neutral**

AGENTS.md как vendor-neutral contract — работает с Claude, Codex, Cursor, Windsurf
одновременно. Конкуренты завязаны на один AI provider.

**3. Dual-remote privacy model**

"Я хочу часть знаний публичной, часть — приватной, в одном vault" — это решает
только REEFIKI. Obsidian Publish — отдельный сервис без гранулярного контроля.

### Стратегические рекомендации

**Не конкурировать с Notion/Logseq на UX.** Это проигрышная стратегия — у них
годы разработки UI. REEFIKI выигрывает на governance и agent-native design.

**Позиционироваться как "Obsidian + AI governance".** Obsidian-пользователи —
готовая аудитория, tech-savvy, ценят local-first и open format. Мост: REEFIKI
как governance layer поверх существующего Obsidian vault.

**Создать сравнительную страницу на сайте/README.** "REEFIKI vs Notion",
"REEFIKI vs Obsidian+AI" — прямые сравнения помогают пользователям принять решение
и повышают SEO.

**Приоритет: P2** (стратегический) | **Сложность: S** (документация)

---

## 10. Метрики здоровья базы знаний

### Проблема: нет способа измерить "работает ли дистилляция"

REEFIKI создаёт структурированное знание. Но как понять что знание полезное?
Что дистилляция работает? Что база не деградирует?

Без метрик: пользователь добавляет страницы, не знает используются ли они,
не видит что `useful_when` стало шаблонным, не замечает что концепции не связаны.

### Предлагаемая система метрик

Все метрики вычисляются из существующих данных — не требуют новых полей.

#### Группа 1: Distillation Quality

**DQ1: Conversion rate inbox → wiki**

```
conversion_rate = wiki_pages_created / inbox_items_processed

Норма: > 0.3 (каждый третий источник становится wiki-страницей)
Предупреждение: < 0.1 (источники не конвертируются — возможно /process пропускается)
Предупреждение: = 1.0 (каждый источник → страница — возможно нет реальной дистилляции)
```

**DQ2: useful_when specificity score**

Простая эвристика на основе длины и наличия конкретных слов:

```python
GENERIC_PHRASES = [
    "может пригодиться", "useful", "general reference",
    "когда нужно", "для использования", "при работе"
]

def useful_when_score(text: str) -> float:
    """0.0 = очень generic, 1.0 = очень специфично"""
    if len(text) < 30:
        return 0.2  # слишком коротко
    
    generic_count = sum(1 for phrase in GENERIC_PHRASES
                       if phrase.lower() in text.lower())
    
    # Специфичные сигналы
    specific_signals = [
        len(text) > 80,           # достаточно длинный
        any(c.isdigit() for c in text),  # содержит числа/условия
        "когда" in text and "и" in text,  # составное условие
    ]
    
    score = (sum(specific_signals) / len(specific_signals))
    score -= (generic_count * 0.2)
    return max(0.0, min(1.0, score))
```

**DQ3: Synthesis rate**

```
synthesis_rate = synthesis_pages / (source_pages + entity_pages + concept_pages)

Норма: > 0.1 (есть реальный синтез поверх источников)
Тревога: = 0 (знания накапливаются но не синтезируются — нет insights)
```

#### Группа 2: Knowledge Graph Health

**KG1: Connectivity (средняя связность)**

```python
def connectivity_score(wiki_dir: str) -> dict:
    pages = load_all_pages(wiki_dir)
    backlinks = build_backlink_graph(pages)
    
    isolated = [p for p in pages if len(backlinks[p]) == 0]
    connected = [p for p in pages if len(backlinks[p]) >= 2]
    
    return {
        "isolated_pages": len(isolated),  # норма: < 10% от всех
        "isolated_pct": len(isolated) / len(pages),
        "well_connected": len(connected),
        "avg_backlinks": sum(len(v) for v in backlinks.values()) / len(pages)
    }
```

**KG2: Type distribution**

```
Норма для зрелой базы:
  source:    30–40% (источники)
  concept:   20–30% (понятия)
  entity:    15–25% (сущности)
  skill:     10–20% (навыки)
  synthesis: 10–15% (синтез — самый ценный тип)
  decision:   5–10% (решения)

Красные флаги:
  synthesis < 5%  → база — архив, не knowledge base
  source > 60%    → нет обработки, только сохранение
  skill = 0%      → нет извлечения actionable knowledge
```

**KG3: Staleness index**

```python
def staleness_score(page: Page) -> float:
    """Насколько страница устарела — 0.0 свежая, 1.0 мёртвая"""
    age_days = (today - page.created_date).days
    
    # Разные типы стареют по-разному
    decay_rates = {
        "source": 180,    # источники устаревают быстро
        "concept": 730,   # концепции живут дольше
        "skill": 365,     # навыки — средне
        "synthesis": 730, # синтез — медленно
        "decision": 365,  # решения — нужна ревизия раз в год
    }
    
    decay_rate = decay_rates.get(page.type, 365)
    return min(1.0, age_days / decay_rate)
```

#### Группа 3: Usage & Retrieval

**UR1: Query success rate**

```
Добавить логирование в /query:
  - запрос
  - количество результатов
  - выбрал ли пользователь результат (implicit feedback)

success_rate = queries_with_selection / total_queries
Норма: > 0.6
Тревога: < 0.3 (поиск не находит нужное — проблема с FTS или useful_when)
```

**UR2: Zero-result rate**

```
zero_result_rate = queries_with_0_results / total_queries
Норма: < 0.1
Тревога: > 0.3 (база не покрывает реальные запросы)
```

**UR3: Promotion velocity**

```
Сколько memoir записей поднимается до wiki (promote --write-draft)?

promotion_velocity = promoted_this_month / memoir_entries_this_month
Норма: > 0.2
Тревога: = 0 (memoir накапливается, promote не происходит)
```

#### Группа 4: Maintenance

**M1: Lint age**

```
lint_age_days = today - last_lint_run
Норма: < 14 дней
Предупреждение: > 30 дней
Тревога: > 60 дней
```

**M2: Unresolved conflicts**

```
Норма: 0
Предупреждение: > 3
Тревога: > 10 (активное накопление конфликтов)
```

**M3: Inbox pressure**

```
inbox_pressure = inbox_items / avg_processing_rate_per_week
(в неделях)

Норма: < 1 (меньше недели накопленного)
Предупреждение: > 2 (два+ недели необработанного)
Тревога: > 4 (месяц необработанного — вероятно бросили обработку)
```

### Dashboard: `/health` команда

```python
# /health — агрегированный отчёт здоровья проекта

def health_report(project: str) -> dict:
    return {
        "overall_score": compute_overall_score(...),  # 0–100
        "distillation": {
            "conversion_rate": ...,
            "avg_useful_when_score": ...,
            "synthesis_rate": ...,
        },
        "graph": {
            "isolated_pages_pct": ...,
            "type_distribution": {...},
            "avg_backlinks": ...,
        },
        "retrieval": {
            "query_success_rate": ...,
            "zero_result_rate": ...,
        },
        "maintenance": {
            "lint_age_days": ...,
            "unresolved_conflicts": ...,
            "inbox_pressure_weeks": ...,
        },
        "recommendations": [
            "3 страницы с generic useful_when — рассмотри уточнение",
            "synthesis_rate = 3% — попробуй /harvest для создания synthesis страниц",
            "42 изолированных страницы — добавь перекрёстные ссылки"
        ]
    }
```

Вывод в терминале:

```
reefiki health --project myproject

══════════════════════════════════════════
 REEFIKI Health Report: myproject
 Общий счёт: 74/100 ▓▓▓▓▓▓▓▓░░
══════════════════════════════════════════

Дистилляция          68/100  ⚠️
  Conversion rate:    0.34   ✓
  useful_when score:  0.52   ⚠️  (14 страниц требуют уточнения)
  Synthesis rate:     0.03   ✗  (слишком мало synthesis страниц)

Граф знаний          82/100  ✓
  Изолированных:      8%     ✓
  Тип distribution:   OK     ✓
  Avg backlinks:      2.3    ✓

Retrieval            71/100  ⚠️
  Query success:      0.58   ⚠️
  Zero-result rate:   0.18   ⚠️  (поиск не находит ~18% запросов)

Обслуживание         91/100  ✓
  Lint age:           8 дней ✓
  Конфликтов:         1      ✓
  Inbox pressure:     0.5w   ✓

Рекомендации:
  1. /harvest для создания synthesis страниц (сейчас только 2)
  2. /lint --check useful_when для 14 страниц с generic описанием
  3. Проверить FTS tokenizer — высокий zero-result rate
══════════════════════════════════════════
```

### Как хранить метрики исторически

```
projects/<name>/plans/health/
  2026-06-04.json   ← снапшот
  2026-05-28.json
  2026-05-21.json
  trend.json        ← агрегированный тренд (last 12 weeks)
```

Тренды позволяют видеть: растёт ли synthesis rate? Улучшается ли query success?
Не деградирует ли useful_when specificity?

**Приоритет: P1 для /health команды** | **Сложность: M** (метрики) + **M** (dashboard)

---

## 11. Сводная таблица предложений

| ID | Предложение | Приоритет | Сложность | Категория |
|---|---|---|---|---|
| L1 | Добавить LICENSE (MIT + CC BY 4.0) | P0 | S | Юридика |
| L2 | NOTICE файл для зависимостей | P1 | S | Юридика |
| L3 | docs/legal-notice.md (raw/ copyright) | P2 | S | Юридика |
| F1 | Prefix search для FTS5 (add `*` к токенам) | P1 | S | FTS/Локализация |
| F2 | Porter stemmer для EN части | P1 | S | FTS/Локализация |
| F3 | Snowball stemmer для RU (snowballstemmer) | P1 | M | FTS/Локализация |
| F4 | docs/fts-internals.md с query tips | P2 | S | FTS/Локализация |
| P1 | scripts/benchmark.py | P2 | M | Производительность |
| P2 | GitHub Actions benchmark workflow | P2 | M | Производительность |
| P3 | WAL mode для SQLite (PRAGMA journal_mode=WAL) | P1 | S | Производительность |
| DR1 | docs/recovery.md (ready-to-run commands) | P1 | S | Disaster Recovery |
| DR2 | Backup age в /status --bootstrap | P1 | S | Disaster Recovery |
| DR3 | WAL mode pre-commit check | P2 | S | Disaster Recovery |
| DR4 | scripts/local-backup.sh + cron | P3 | S | Disaster Recovery |
| A1 | docs/for-researchers.md | P2 | S | Accessibility |
| A2 | docs/for-managers.md | P2 | S | Accessibility |
| A3 | docs/for-writers.md | P2 | S | Accessibility |
| A4 | Obsidian как нетехнический интерфейс | P1 | S | Accessibility |
| A5 | Progress indicators для долгих операций | P2 | S | Accessibility |
| A6 | Glossary для нетехнических пользователей | P2 | S | Accessibility |
| MB1 | Fine-grained PAT + rotation docs | P1 | S | Mobile Capture |
| MB2 | Dead Letter Queue для Telegram pipeline | P1 | M | Mobile Capture |
| MB3 | Minimal structured capture (1 вопрос бота) | P2 | M | Mobile Capture |
| MB4 | docs/mobile-capture.md + iOS Shortcut | P2 | M | Mobile Capture |
| O1 | Явный read-only mode в docs/obsidian-setup.md | P1 | S | Obsidian |
| O2 | .obsidian/ в .gitignore (правильно) | P1 | S | Obsidian |
| O3 | Whitelist безопасных плагинов | P1 | S | Obsidian |
| O4 | validate_frontmatter: check Linter damage | P1 | S | Obsidian |
| O5 | mtime check перед записью агента | P2 | M | Obsidian |
| M1 | Schema versioning в _schema.md | P1 | S | Migrations |
| M2 | scripts/reefiki.py migrate CLI | P1 | M | Migrations |
| M3 | Backwards compatibility mode в validate | P1 | M | Migrations |
| M4 | CHANGELOG.schema.md | P1 | S | Migrations |
| M5 | Pre-migration git backup (автоматический) | P0 | S | Migrations |
| C1 | Конкурентная страница в README | P2 | S | Конкуренты |
| C2 | Позиционирование как "governance для Obsidian" | P2 | S | Конкуренты |
| H1 | /health команда с overall score | P1 | M | Метрики |
| H2 | DQ метрики (conversion, useful_when, synthesis) | P1 | M | Метрики |
| H3 | KG метрики (connectivity, type distribution) | P2 | M | Метрики |
| H4 | UR метрики (query success, zero-result) | P1 | M | Метрики |
| H5 | Health history в plans/health/ | P2 | S | Метрики |
| H6 | useful_when specificity linting | P1 | S | Метрики |

---

*Дополнение к основному аудиту `reefiki-audit.md`. Вместе эти документы покрывают
все аспекты проекта REEFIKI на Phase 0i и описывают путь к Phase 1.*
