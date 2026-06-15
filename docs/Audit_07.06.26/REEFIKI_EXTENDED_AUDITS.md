# REEFIKI — Расширенные аудиты

> Дата: 2 июня 2026. Срез main-ветки `kisslex2013-alt/reefiki`.
> Четыре аудита по темам, не покрытым предыдущими проверками.

---

## Содержание

- [Аудит 1 — AI-agent contract](#аудит-1--ai-agent-contract)
- [Аудит 2 — Параллелизм и целостность данных](#аудит-2--параллелизм-и-целостность-данных)
- [Аудит 3 — Производительность и масштабируемость](#аудит-3--производительность-и-масштабируемость)
- [Аудит 4 — Тестовое покрытие](#аудит-4--тестовое-покрытие)
- [Итоговая таблица findings](#итоговая-таблица-findings)

---

## Аудит 1 — AI-agent contract

### Что проверялось

Насколько предсказуемо и безопасно использование REEFIKI AI-агентами: JSON-схема ответов, консистентность exit codes, идемпотентность команд, поведение при частичных сбоях, deadlock-состояния.

---

### 1.1 Инвентаризация команд и их вывода

| Команда | Функция | Тип вывода | `--format json`? | `outcome` поле? |
|---|---|---|---|---|
| `index` | `build_index()` | `int` (count) + print | ❌ | ❌ |
| `search` | `search_existing()` | list → `print_search()` | ✅ | ❌ |
| `status` | `status()` | print | ❌ | ❌ |
| `save` | `save_source()` | `int` + print | ❌ | ❌ |
| `dedup` | `dedup_check()` | `int` + print | ❌ | ❌ |
| `privacy` | `privacy_scan()` | `int` + print | ❌ | ❌ |
| `plan create` | `plan_create()` | `int` + print | ❌ | ❌ |
| `plan check` | `plan_check()` | `int` + print | ❌ | ❌ |
| `timeline` | `timeline()` | print | ❌ | ❌ |
| `guard-staged` | `guard_staged_payload()` | `dict` → `print_guard_staged()` | ✅ | ✅ `"pass"/"block"` |
| `harvest-commit` | `harvest_commit_payload()` | `(int, dict)` → `print_harvest_commit()` | ✅ | ✅ `"pass"/"block"` |
| `publish-task` | `publish_task_payload()` | `(int, dict)` → `print_publish_task()` | ✅ | ✅ `"pass"/"block"` |
| `cleanup-worktree` | `cleanup_worktree_payload()` | `(int, dict)` → `print_cleanup_worktree()` | ✅ | ✅ `"pass"/"block"` |
| `tool-trigger` | `tool_trigger_payload()` | dict → `print_tool_trigger()` | ✅ | ✅ но **другие значения** |
| `memory route` | `memory_route()` | dict → `print_memory_route()` | ✅ | ❌ нет `outcome` |
| `memory status` | `memory_status()` | dict → `print_memory_status()` | ✅ | ❌ нет `outcome` |
| `memory preflight` | `memory_preflight()` | dict → `print_memory_preflight()` | ✅ | ✅ но **`"pass"/"fail"`** |
| `memory lookup` | `global_lookup()` | dict → `print_global_lookup()` | ✅ | ✅ `"pass"/"fail"` |
| `memory pack` | `memory_pack()` | dict → `print_memory_pack()` | ✅ | ✅ `"pass"/"fail"` |
| `memory promote` | `promotion_dry_run()` | dict → `print_promotion_dry_run()` | ✅ | ❌ нет `outcome`, есть `verdict` |
| `review-queues` | `review_queue_scan()` | list | ✅ | ❌ нет `outcome` |
| `backlinks` | `build_backlink_index()` | dict | ✅ | ❌ нет `outcome` |

---

### A1-001 — `outcome` field: три несовместимых значения
> **Severity: MEDIUM**

**Описание:**

Агент строит решения на основе `outcome` поля в JSON. Но в разных командах оно принимает несовместимые значения:

```python
# Группа А: git/publish команды (L1133, L1251, L1389, L1501)
"outcome": "pass" | "block"

# Группа Б: memory layer (L2171, L2416, L2481)
"outcome": "pass" | "fail"        # ← другое значение!

# Группа В: tool_trigger_payload (L1548, L1560, L1569, L1576)
"outcome": "reference-only" | "unsupported" | "sandbox-recommended" | "watch"
                                  # ← полностью другой словарь!

# Команды без outcome:
# memory route, memory status, review-queues, backlinks, promote (используют "verdict")
```

Агент, обрабатывающий `if result["outcome"] != "pass"` — поймает `"fail"` как успех в Группе Б:

```python
# Ошибочная логика агента:
if payload.get("outcome") == "block":
    stop()
# memory_pack с outcome="fail" → пройдёт незамеченным!
```

**Exploit scenario:**

```bash
# Агент запускает memory pack:
python scripts/reefiki.py --project myproject memory pack --task "Deploy" --format json
# → {"outcome": "fail", "reason": "required_ids_missing", ...}
# Агент проверяет: outcome != "block" → продолжает без context → деградированное поведение
```

**Решение — унифицировать семантику:**

```python
# Конвенция: outcome = "pass" | "block" | "warn"
# "fail" → переименовать в "block" во всех командах
# tool_trigger → добавить верхнеуровневый "outcome": "pass"/"block" + "action" поле

# reefiki_memory/__init__.py:
# "outcome": "fail" → "outcome": "block"

# Документировать в AGENTS.md:
# outcome семантика:
#   "pass"  — операция выполнена, агент может продолжать
#   "block" — операция заблокирована, причина в "reason"
#   "warn"  — операция выполнена с замечаниями, рекомендуется проверить
```

**Сложность: M** (переименование + обновление тестов)

---

### A1-002 — Отсутствие `schema_version` в большинстве ответов
> **Severity: LOW**

**Описание:**

Только `build_backlink_index()` возвращает `"schema_version": 1`. Остальные 20+ команд не имеют версии схемы. Агент не может обнаружить изменение контракта между версиями REEFIKI.

Пример: если `harvest_commit_payload` добавит новое обязательное поле — агент узнает об этом только из сломавшегося кода.

**Решение:**

```python
# Добавить в все payload-команды:
SCHEMA_VERSION = 1  # глобальная константа

def guard_staged_payload(...) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "outcome": ...,
        # ...
    }
```

Или минимально — в AGENTS.md добавить `reefiki_contract_version: "1.0"`.

**Сложность: S**

---

### 1.2 Идемпотентность команд

| Команда | Идемпотентна? | Примечание |
|---|---|---|
| `index` | ✅ | DROP + rebuild, всегда одинаковый результат |
| `search` | ✅ | Read-only |
| `status` | ✅ | Read-only |
| `save` | ✅ | dedup_check блокирует повтор |
| `dedup` | ✅ | Read-only |
| `privacy` | ✅ | Read-only |
| `guard-staged` | ✅ | Read-only |
| `harvest-commit` | ❌ | Создаёт новый коммит каждый раз |
| `publish-task` | ⚠️ | Повторный push с --force-with-lease безопасен, если нет новых коммитов |
| `cleanup-worktree` | ⚠️ | Повтор при уже удалённом worktree → `"block": "worktree_missing"` |
| `memory promote` | ⚠️ | Создаёт файл draft; повтор создаёт другой файл |
| `plan create` | ⚠️ | Повтор при существующем плане → `raise SystemExit` |

---

### A1-003 — `harvest-commit` без идемпотентного ключа: двойной коммит при retry
> **Severity: MEDIUM**

**Описание:**

Если агент отправил `harvest-commit` и не получил ответ (timeout, сеть), он не знает — коммит произошёл или нет. Повторный вызов с теми же путями и сообщением создаст **второй коммит**, потому что `diff_check.returncode == 0` (нет изменений относительно нового HEAD) → блокируется с `"reason": "no_changes_to_commit"`. 

Это корректное поведение, но только если агент корректно разбирает эту причину. Агент может не обработать `"reason": "no_changes_to_commit"` как "успех-дубль" и упасть в retry loop.

```python
# harvest_commit_payload, строка 1235:
if diff_check.returncode == 0:      # нет изменений → уже закоммичено
    return 1, {
        **base_payload,
        "outcome": "block",
        "reason": "no_changes_to_commit",  # ← агент должен трактовать это как "уже выполнено"
    }
```

**Решение — документировать в AGENTS.md:**

```markdown
## Обработка частичных сбоев harvest-commit

Если harvest-commit вернул timeout или ошибку сети:
1. Проверить `git log --oneline -3` — был ли создан коммит
2. Если коммит есть — harvest успешен, не повторять
3. Если outcome="block", reason="no_changes_to_commit" — коммит уже выполнен
4. Только если outcome="block" с другими reasons — безопасно повторить
```

**Сложность: S** (документация)

---

### 1.3 Анализ deadlock-состояний

**Сценарии, из которых агент не может выйти самостоятельно:**

| Состояние | Причина | Доступная команда | Есть в AGENTS.md? |
|---|---|---|---|
| Dirty worktree блокирует `publish-task` | Незакоммиченные изменения | `git stash` (вне REEFIKI CLI) | ⚠️ частично |
| `publish-task` требует `create_pr_required` | base не является предком HEAD | Нет REEFIKI-команды для rebase | ❌ |
| `cleanup-worktree` блокируется `unmerged_worktree_head` | Worktree HEAD не влит в base | Нет команды force-merge | ❌ |
| Staged files вне target wiki | Случайный `git add` | `git reset HEAD` (вне CLI) | ⚠️ |

---

### A1-004 — Deadlock при `create_pr_required` без команды выхода
> **Severity: MEDIUM**

**Описание:**

`publish_task_payload` возвращает `"reason": "create_pr_required"` когда base не является предком HEAD (diverged history). Агент получает инструкцию создать PR, но в REEFIKI CLI нет команды для этого.

Состояние:
1. `publish-task` → block: `create_pr_required`
2. Агент не может создать PR через CLI
3. `cleanup-worktree` → block: `unmerged_worktree_head` (HEAD не влит)
4. Дедлок: нельзя ни опубликовать, ни очистить

**Решение:**

```markdown
# AGENTS.md: добавить раздел "Разрешение create_pr_required"

При outcome=block, reason=create_pr_required:
1. python scripts/reefiki.py publish-task --dry-run true  # проверить статус
2. git log --oneline <base>..HEAD  # увидеть что не влито
3. Вариант А: gh pr create --base main --head <branch>  # если есть gh CLI
4. Вариант Б: git rebase <base> (осторожно — изменяет историю)
5. Вариант В: git merge --ff-only <branch>  # если remote позволяет
```

**Сложность: S** (документация)

---

### 1.4 Анализ `--format` покрытия

Команды `status`, `save`, `dedup`, `privacy`, `plan create/check`, `timeline`, `index` не имеют `--format json`. Агент получает только plain-text вывод и должен парсить его регулярными выражениями.

Например, результат `plan check`:
```
plans/deploy.md: checksum OK      # ← только текст
```

Агент должен grep строку, чтобы понять успех/неудачу. Exit code доступен, но причина — нет.

---

### A1-005 — CLI-команды без машиночитаемого JSON-вывода
> **Severity: LOW**

**Affected:** `status`, `save`, `dedup`, `privacy`, `plan create`, `plan check`, `timeline`, `index`

**Решение — добавить `--format json` к критичным для агента командам:**

```python
# Пример для plan_check():
if fmt == "json":
    print(json.dumps({
        "path": str(relative(project, path)),
        "outcome": "pass" if actual == expected else "block",
        "reason": None if actual == expected else "checksum_mismatch",
    }, ensure_ascii=False, indent=2))
else:
    print(f"{relative(project, path)}: checksum OK")
```

**Приоритет:** `plan check`, `save`, `status` — чаще всего вызываются агентами.

**Сложность: S** (per command)

---

### 1.5 Что хорошо работает в agent contract ✅

- **AGENTS.md** — исключительно подробный, 16 КБ, охватывает: запреты, режимы работы, cross-project harvest rules, dual-remote publish rule, memory routing. Vendor-агностичен, ссылаются все vendor-специфичные файлы.
- **`guard_staged_payload`** — чёткая прекондиция перед любым коммитом. Идиоматично используется в AGENTS.md.
- **`payload` + `print_*` разделение** — логика и вывод разделены, что упрощает тестирование.
- **`outcome`/`reason` паттерн** (там где применяется) — агент может строить решения на `reason`, не парся текст.

---

## Аудит 2 — Параллелизм и целостность данных

### Что проверялось

Безопасность при одновременном запуске нескольких процессов REEFIKI (два агента, агент + пользователь), SQLite-блокировки, race conditions, целостность планов.

---

### 2.1 Карта конкурентного доступа

| Ресурс | Записывает | Читает | Механизм защиты |
|---|---|---|---|
| `.reefiki/index.sqlite` | `build_index()` | `search_existing()`, `_wiki_rows()`-based commands | WAL mode ✅ |
| `inbox/*.md` | `save_source()` via `unique_inbox_path()` | `status()`, `dedup_check()` | ❌ нет lock |
| `wiki/*.md` | `write_promotion_draft()`, `apply_promotion_draft()` | `iter_pages()` | ❌ нет lock |
| `plans/*.md` | `plan_create()` | `plan_check()` | ❌ нет lock |
| `wiki/log.md` | `append_save_log()`, `apply_promotion_draft()` | `status()`, `timeline()` | append mode ⚠️ |
| `GIT_INDEX_FILE` (temp) | `harvest_commit_payload()` | изолирован в tempdir | ✅ per-process |
| git worktree | `push_public_snapshot()` | `cleanup_worktree_payload()` | ✅ worktree isolation |

### 2.2 SQLite: WAL и соединения

```python
# WAL mode только в build_index():
conn.execute("PRAGMA journal_mode=WAL")   # L260

# Единственный conn.commit() — в конце build_index() (L388)
# search_existing() закрывает conn в finally ✅ (L555)
# build_index() закрывает conn в конце (L389)
```

WAL mode, установленный однажды, сохраняется в файле БД для всех последующих соединений. Concurrent readers в WAL не блокируются reader-ами.

---

### C1-001 — TOCTOU race condition в `unique_inbox_path()`
> **Severity: MEDIUM**

**Описание:**

```python
# reefiki.py, строки 826–836:
def unique_inbox_path(project: Path, source: str) -> Path:
    inbox = project / "inbox"
    inbox.mkdir(exist_ok=True)
    stem = source_slug(source)
    path = inbox / f"{stem}{suffix}"
    counter = 2
    while path.exists():              # ← CHECK
        path = inbox / f"{stem}-{counter}{suffix}"
        counter += 1
    return path                       # ← USE: ещё не создан, окно для race
```

Между `path.exists()` → `False` и реальной записью `destination.write_text()` другой процесс успевает создать тот же файл → **молчаливая перезапись**.

**Exploit scenario:**

```bash
# Два параллельных агента сохраняют разные статьи с похожим URL:
# Процесс A: save_source(project, "https://example.com/article")
# Процесс B: save_source(project, "https://example.com/article-v2")
# Оба вычисляют stem="example-com-article" (разные, но одинаковая длина slug)
# Оба проверяют inbox/example-com-article.md → не существует
# A пишет свой контент, B перезаписывает его своим
# В итоге в inbox только контент B, A потерян молча
```

**Решение — атомарная запись через `O_EXCL`:**

```python
import os

def save_source_atomic(project: Path, source: str) -> Path:
    inbox = project / "inbox"
    inbox.mkdir(exist_ok=True)
    suffix = ".md" if is_url(source) else Path(source).suffix
    stem = source_slug(source)
    counter = 1
    while True:
        name = f"{stem}.{suffix}" if counter == 1 else f"{stem}-{counter}{suffix}"
        path = inbox / name
        try:
            # O_CREAT | O_EXCL — атомарно создаёт файл; если уже существует → FileExistsError
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(fd)
            return path
        except FileExistsError:
            counter += 1
```

**Сложность: S**

---

### C1-002 — `build_index()` DROP TABLE без exclusive lock: concurrent search → рекурсивный rebuild
> **Severity: MEDIUM**

**Описание:**

```python
# build_index(), строки 261–317:
conn.executescript("""
    DROP TABLE IF EXISTS pages;
    DROP TABLE IF EXISTS pages_fts;
    ...
    CREATE TABLE pages (...);
    CREATE VIRTUAL TABLE pages_fts USING fts5(...);
""")
# ← В этот момент таблицы отсутствуют
# ← Другой процесс выполняет search()

# search_existing(), строки 552–557:
except sqlite3.OperationalError as exc:
    if "no such table" not in str(exc):
        raise
# ← Поймал "no such table" → вызывает build_index() снова!
build_index(project)
return search_existing(...)   # ← рекурсивный вызов
```

Два параллельных `index` команды → оба делают DROP TABLE → оба делают CREATE → race на вставке.

**Exploit scenario:**

```bash
# Терминал 1:
python reefiki.py --project myproject index &
# Терминал 2 (одновременно):
python reefiki.py --project myproject search "python"
# → search находит "no such table" → вызывает build_index() снова
# → два build_index() параллельно: INSERT конфликт на PRIMARY KEY → OperationalError
```

**Решение — advisory lock через SQLite:**

```python
def build_index(project: Path) -> int:
    database = db_path(project)
    # Используем lock-файл для взаимного исключения
    lock_path = database.with_suffix(".lock")
    import fcntl
    with open(lock_path, "w") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # Другой процесс уже строит индекс — подождать
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            return 0  # Индекс уже построен параллельным процессом
        # ... rebuild index ...
```

Или проще — SQLite BEGIN IMMEDIATE:

```python
conn = sqlite3.connect(database, timeout=30)  # timeout для ожидания lock
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("BEGIN IMMEDIATE")   # эксклюзивный write lock сразу
# ... DROP + CREATE + INSERT ...
conn.commit()
```

**Сложность: M** (нужно тестировать на разных ОС, особенно Windows где fcntl недоступен)

---

### C1-003 — `_wiki_rows()` не использует кеш SQLite: тройное чтение диска в одной операции
> **Severity: LOW (Performance impact: MEDIUM)**

**Описание:**

`_wiki_rows()` читает все `.md` файлы с диска через `iter_pages()` + `parse_frontmatter()` при каждом вызове. Вызывается из:

- `review_queue_scan()` — явно
- `build_backlink_index()` — явно
- `promotion_dry_run()` — явно
- `promotion_inbox_summary()` — явно

Команды типа `memory pack` или `memory status` могут запускать несколько из них в одном вызове — тройное-четверное чтение всех wiki-файлов.

**Решение:**

```python
# Кеш уровня вызова:
def _wiki_rows(project: Path, _cache: dict[Path, list] = {}) -> list[dict[str, object]]:
    key = project / "wiki"
    mtime = max((p.stat().st_mtime for p in iter_pages(project)), default=0)
    if key in _cache and _cache[key]["mtime"] == mtime:
        return _cache[key]["rows"]
    rows = _load_wiki_rows(project)
    _cache[key] = {"rows": rows, "mtime": mtime}
    return rows
```

Или передавать `rows` как аргумент в функции, которые их используют.

**Сложность: M**

---

### 2.3 Целостность `plan` SHA256

```python
# plan_create(): строки 899–900
checksum = hashlib.sha256(body.encode("utf-8")).hexdigest()
path.write_text(body + f"\n<!-- reefiki-plan-sha256:{checksum} -->\n", ...)

# plan_check(): строки 910–916
match = re.search(r"\n<!-- reefiki-plan-sha256:([a-f0-9]{64}) -->\s*$", text)
body = text[:match.start()]
actual = hashlib.sha256(body.encode("utf-8")).hexdigest()
```

**Схема целостности правильная** — хеш от всего содержимого до метки, метка в конце.

Ограничение: агент, модифицирующий файл, может пересчитать и обновить хеш. Это не защита от намеренного агента, но защищает от случайных изменений ✅.

---

### 2.4 `log.md` при параллельной записи

```python
# append_save_log(), строки 842–843:
with log.open("a", encoding="utf-8", newline="\n") as handle:
    handle.write(f"\n## [{date.today().isoformat()}] /save | {source}\n")
```

Режим `"a"` (append) + `with` — на POSIX это атомарно для коротких записей (< PIPE_BUF ~4096 байт). Записи из двух процессов не перемешаются побайтно, но могут чередоваться построчно на Windows или при длинных строках.

**Практический риск: LOW** — log.md форматирован как markdown, чередование строк не ломает структуру.

---

## Аудит 3 — Производительность и масштабируемость

### Что проверялось

Алгоритмическая сложность ключевых операций, SQLite-оптимизация, поведение на больших наборах данных (1K, 10K страниц), узкие места.

---

### 3.1 Инвентаризация алгоритмической сложности

| Операция | Функция | Сложность | Размер при N страницах |
|---|---|---|---|
| `index` | `build_index()` | O(N × C) где C — чанков на страницу | N=10K → ~300K INSERT |
| `search` | `search_existing()` + FTS5 | O(log N) — FTS5 BM25 | Быстро |
| `status` | `status()` | O(N) filesystem reads + frontmatter parse | N=10K → 10K reads |
| `dedup` (URL) | `dedup_check()` | O(N × U) где U — URL в файле | N=10K → медленно |
| `save` | `save_source()` → dedup | O(N) | Каждый save = O(N) |
| `review-queues` | `review_queue_scan()` | **O(N²)** — backlink check | N=1K → 1M итераций |
| `backlinks` | `build_backlink_index()` | O(N × L) где L — ссылок | N=10K → приемлемо |
| `memory pack` | `memory_pack()` | O(N) + FTS5 | Приемлемо |
| `promote-dry-run` | `promotion_dry_run()` | O(N) — сканирует тела страниц | O(N) |

---

### P1-001 — O(N²) алгоритм в `review_queue_scan()`: missing backlink detection
> **Severity: MEDIUM**

**Описание:**

В `review_queue_scan()` есть вложенный цикл (строки 3072–3086):

```python
# Внешний цикл: O(N)
for row in rows:
    row_id = as_text(row["id"])
    all_links = outgoing_by_id[row_id]    # предвычислен

    # Внутренний цикл: O(N) для каждой row
    for source_row in rows:               # ← O(N²) ЗДЕСЬ
        source_id = as_text(source_row["id"])
        if source_id == row_id:
            continue
        source_links = outgoing_by_id[source_id]
        if row_id in source_links and source_id not in all_links:
            items.append({
                "queue_type": "missing_backlink", ...
            })
```

Это детектор «страница B ссылается на A, но A не ссылается на B» — потенциальный missing reciprocal link.

**Производительность:**

| N (страниц) | Итерации | Примерное время |
|---|---|---|
| 100 | 10K | < 0.1 сек |
| 500 | 250K | ~0.3 сек |
| 1000 | 1M | ~1–3 сек |
| 5000 | 25M | ~30–100 сек |
| 10000 | 100M | несколько минут |

**Решение — O(N) через предвычисленный обратный индекс:**

```python
# Вместо вложенного цикла — перестроить логику:

# Построить: для каждой страницы — кто на неё ссылается (incoming_by_id)
incoming_by_id: dict[str, set[str]] = {as_text(row["id"]): set() for row in rows}
for row in rows:
    source_id = as_text(row["id"])
    for target_id in outgoing_by_id[source_id]:
        if target_id in incoming_by_id:
            incoming_by_id[target_id].add(source_id)

# Затем для каждой страницы: O(1) поиск
for row in rows:
    row_id = as_text(row["id"])
    all_links = outgoing_by_id[row_id]
    for source_id in incoming_by_id[row_id]:    # кто ссылается на меня
        if source_id not in all_links:          # а я не ссылаюсь на них
            items.append({"queue_type": "missing_backlink", ...})
```

Итог: O(N + E) где E — количество ссылок в системе.

**Сложность: S**

---

### P1-002 — `dedup_check()` O(N): полное сканирование при каждом `save`
> **Severity: MEDIUM**

**Описание:**

```python
# dedup_check(), строки 713–746:
def dedup_check(project: Path, source: str) -> int:
    if is_url(source):
        source_url = canonical_url(source)
        for path in iter_project_text_files(project):     # ← все файлы проекта
            text = path.read_text(encoding="utf-8", errors="replace")  # ← каждый читается
            if any(canonical_url(url) == source_url for url in extract_urls(text)):
                matches.append(...)
```

`iter_project_text_files()` возвращает: `wiki/**/*.md` + `inbox/*.md` + `seen/*.md`.

При N=1000 страниц + 500 inbox + 200 seen = 1700 файловых чтений на каждый `save` URL.

**Почему не использует SQLite?** Индекс FTS5 содержит `sources` поле, но `dedup_check` читает файлы напрямую — возможно, для свежих данных (индекс может быть устаревшим).

**Решение — использовать SQLite `sources` поле для URL-дедупликации:**

```python
def dedup_check_fast(project: Path, source: str) -> int:
    if is_url(source):
        source_url = canonical_url(source)
        database = db_path(project)
        if database.exists():
            conn = sqlite3.connect(database)
            try:
                # Проверить sources поле (содержит URL)
                rows = conn.execute(
                    "SELECT id, sources FROM pages WHERE sources LIKE ?",
                    (f"%{source_url[:50]}%",)   # prefix-match для скорости
                ).fetchall()
                for row_id, sources_text in rows:
                    if source_url in sources_text:
                        return 1  # duplicate found
            finally:
                conn.close()
        # Fallback: filesystem scan для inbox (не проиндексирован)
        # ...
```

**Компромисс:** индекс может быть устаревшим. Принять это как допустимое (index stale → редкий false negative, не false positive).

**Сложность: M**

---

### P1-003 — `status()` не использует SQLite: O(N) parse_frontmatter при каждом вызове
> **Severity: LOW**

**Описание:**

```python
# status(), строки 784–793:
for page in iter_pages(project):
    fm, _ = parse_frontmatter(page.read_text(encoding="utf-8"))
    counts[as_text(fm.get("type")) or "unknown"] += 1
    # ...
```

`status` читает и парсит frontmatter ВСЕХ страниц, хотя эти данные (type, date_added, use_count) уже хранятся в SQLite индексе.

**Решение:**

```python
def status(project: Path) -> int:
    database = db_path(project)
    if database.exists():
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute("SELECT type, date_added, use_count FROM pages").fetchall()
        finally:
            conn.close()
    else:
        # fallback: filesystem scan
        rows = [...]
    counts = Counter(row["type"] or "unknown" for row in rows)
    stale = sum(1 for row in rows
                if int(row["use_count"] or 0) == 0
                and _is_stale(row["date_added"]))
    # ...
```

**Сложность: S**

---

### 3.2 SQLite индексирование и FTS5

**Что проиндексировано:**

```sql
-- FTS5 (pages_fts): id, title, tags, useful_when, body
-- FTS5 (chunks_fts): page_id, heading_path, content
-- B-Tree: idx_links_source (source_id), idx_links_target (target_id), idx_chunks_page (page_id)
```

**Что НЕ проиндексировано в B-Tree:**
- `pages.type` — `status()` с `type=X` фильтром → full table scan (если бы использовался SQL)
- `pages.date_added` — temporal queries медленны
- `pages.use_count` — нет индекса

**Практически:** FTS5 покрывает основной use-case (полнотекстовый поиск). B-Tree индексы есть на ссылках — правильно. `review_queue_scan` и `status` используют `_wiki_rows()` (filesystem), не SQL, поэтому отсутствие этих индексов не проблема сейчас — но станет при переходе на SQL-based commands.

---

### 3.3 `iter_pages()` — ограничение глубины

```python
# iter_pages(), строки 238–244:
def iter_pages(project: Path) -> list[Path]:
    wiki = project / "wiki"
    return sorted(
        p
        for p in wiki.glob("*/*.md")    # ← только 2 уровня!
        if p.name not in SKIP_WIKI_FILES and p.parent.name not in SKIP_WIKI_DIRS
    )
```

`wiki.glob("*/*.md")` = `wiki/<type>/<file>.md`. Файлы на 3+ уровнях (`wiki/concepts/python/asyncio.md`) **не индексируются**.

---

### P1-004 — `iter_pages()` не рекурсивна: страницы в поддиректориях теряются
> **Severity: LOW** (архитектурное ограничение)

**Описание:**

Wiki-организация предполагает `wiki/<type>/<page>.md`. Но агент может создать `wiki/concepts/python/asyncio.md` — этот файл будет проигнорирован `iter_pages()`, `build_index()`, `search()`, `review_queue_scan()` и всеми командами, использующими `_wiki_rows()`.

**Решение:**

```python
def iter_pages(project: Path) -> list[Path]:
    wiki = project / "wiki"
    return sorted(
        p
        for p in wiki.rglob("*.md")    # ← рекурсивно
        if p.name not in SKIP_WIKI_FILES
        and not any(part in SKIP_WIKI_DIRS for part in p.relative_to(wiki).parts[:-1])
        and p.parent != wiki            # пропустить корневые .md (log.md, index.md уже в SKIP)
    )
```

**Сложность: S**

---

### 3.4 `build_index()` — транзакционная модель

**Одна большая транзакция** — всё или ничего:

```python
conn = sqlite3.connect(database)
conn.executescript("DROP TABLE ... CREATE TABLE ...")  # autocommit
# ... INSERT loop (нет промежуточных commit) ...
conn.commit()   # единственный commit в конце
conn.close()
```

`executescript()` в Python SQLite неявно commit-ит перед выполнением. Затем `INSERT` операции находятся в неявной транзакции до явного `conn.commit()`. Это эффективно — SQLite вставляет тысячи записей намного быстрее в одной транзакции.

**Но:** `executescript(DROP + CREATE)` и последующие INSERT — **две отдельные транзакции**. Если процесс упадёт ПОСЛЕ DROP TABLE но ДО финального commit — таблицы пусты. Поиск найдёт `"no such table"` или пустой индекс.

**Улучшение — atomic rebuild через rename:**

```python
# Построить во временной БД, затем переименовать атомарно:
import tempfile
tmp_db = database.with_suffix(".tmp")
conn = sqlite3.connect(tmp_db)
# ... полный rebuild в tmp_db ...
conn.commit()
conn.close()
tmp_db.replace(database)   # атомарная замена на большинстве FS
```

**Сложность: S**

---

### P1-005 — Отсутствие кеширования `_wiki_rows()`: многократное чтение одних файлов
> **Severity: LOW**

Функции `review_queue_scan`, `build_backlink_index`, `promotion_dry_run`, `promotion_inbox_summary` — все вызывают `_wiki_rows()` независимо. В `memory pack` или `memory status` может происходить 2–4 полных прохода по wiki.

На 1K страниц при среднем файле 5KB: 5MB IO × 4 = 20MB IO на одну команду.

**Решение:** передавать предзагруженные `rows` как параметр или использовать SQLite индекс (если актуален).

---

## Аудит 4 — Тестовое покрытие

### Что проверялось

Какие функции покрыты тестами, что критически не покрыто, качество тестов.

---

### 4.1 Статистика покрытия

| Файл | Тестов | Что покрывает |
|---|---|---|
| `test_reefiki_memory_contracts.py` | 57 | Memory layer (полностью), guard/harvest/publish/cleanup через main(), tool-trigger, memory pack |
| `test_reefiki_memory_governance.py` | 19 | review_queue_scan, backlinks, promotion workflow, global_lookup |
| `test_reefiki_dedup.py` | 8 | dedup_check, save_source |
| `test_public_snapshot_guard.py` | 1 | Проверяет что все реальные проекты в private list |
| `test_validate_frontmatter.py` | 2 | JSON output формат и location reporting |
| **Итого** | **87** | |

### 4.2 Карта покрытия (106 публичных функций в reefiki.py)

**Покрыто (прямо или через main()):**

`build_index`, `search`, `search_existing`, `dedup_check`, `status`, `save_source`, `push_public_snapshot`, `memory_route`, `memory_status`, `memory_status_all_projects`, `promotion_inbox_summary`, `memory_explain`, `memory_preflight`, `global_lookup`, `memory_diff`, `memory_pack`, `review_queue_scan`, `write_review_queue_report`, `build_backlink_index`, `promotion_dry_run`, `write_promotion_draft`, `promotion_inbox`, `reject_promotion_inbox_draft`, `prune_closed_promotion_drafts`, `apply_promotion_draft`, `find_project`, `repo_root`, `relative`, `guard_staged_payload`, `harvest_commit_payload`, `publish_task_payload`, `cleanup_worktree_payload`

**НЕ покрыто (важные):**

| Функция | Почему важно | Связанные риски |
|---|---|---|
| `escape_fts()` | SEC-003: fallback bug, FTS5 keyword crash | Crash на `---`, `AND`, `"*"` |
| `classify_path()` | SEC-005: path traversal | `../../etc/passwd` проходит |
| `privacy_scan()` | Ключевая команда проверки | Нет регрессии |
| `plan_create()` | SHA256-подписи планов | Нет проверки формата |
| `plan_check()` | Верификация целостности | Нет теста tampering |
| `timeline()` | Часто используется | Нет теста |
| `classify_publish_diff()` | SEC-009 potential | Нет теста edge cases |
| `private_project_names()` | SEC-011: missing file = all public | Нет теста |
| `normalize_repo_path()` | Безопасность путей | Нет теста `../` |

---

### T1-001 — Нет тестов для `escape_fts()`: критические edge cases без регрессии
> **Severity: HIGH**

**Описание:**

`escape_fts()` была обнаружена с двумя багами (SEC-003):
1. Fallback `return query` при пустых токенах → FTS5 crash
2. FTS5 keywords (`AND`, `OR`, `NOT`) проходят как токены → syntax error

Нет ни одного теста. Исправление без теста — следующий регресс гарантирован.

**Решение — добавить `tests/test_fts_search.py`:**

```python
import unittest, importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "reefiki", Path(__file__).parent.parent / "scripts" / "reefiki.py"
)
reefiki = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reefiki)

class TestEscapeFts(unittest.TestCase):
    def test_word_query_tokenized(self):
        self.assertEqual(reefiki.escape_fts("python async"), '"python" OR "async"')

    def test_punctuation_only_returns_empty_not_raw(self):
        # Не должен возвращать "---" → передаётся в FTS5 как raw
        result = reefiki.escape_fts("---")
        self.assertEqual(result, "")  # или безопасная строка

    def test_fts5_keyword_and_is_excluded(self):
        result = reefiki.escape_fts("python AND asyncio")
        self.assertNotIn("AND", result)  # AND не должен быть оператором

    def test_fts5_keyword_or_is_excluded(self):
        result = reefiki.escape_fts("a OR b")
        self.assertNotIn(" OR OR ", result)  # не "a OR OR OR b"

    def test_empty_query_returns_empty(self):
        self.assertEqual(reefiki.escape_fts(""), "")

    def test_unicode_tokens(self):
        result = reefiki.escape_fts("машинное обучение")
        self.assertIn("машинное", result)
        self.assertIn("обучение", result)

    def test_star_query_does_not_crash_fts5(self):
        # Проверить что escape_fts("*") не возвращает "*"
        result = reefiki.escape_fts("*")
        self.assertNotEqual(result, "*")
```

**Сложность: S**

---

### T1-002 — Нет тестов для `classify_path()`: path traversal не регрессируется
> **Severity: HIGH**

После исправления SEC-005 необходим тест, который гарантирует, что исправление не будет случайно удалено:

```python
class TestClassifyPath(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.project = Path(self.tmp)

    def test_url_is_accepted(self):
        ok, _ = reefiki.classify_path("https://example.com/article", self.project)
        self.assertTrue(ok)

    def test_binary_url_is_rejected(self):
        ok, reason = reefiki.classify_path("https://example.com/file.exe", self.project)
        self.assertFalse(ok)
        self.assertIn("binary", reason)

    def test_dotdot_path_is_rejected(self):  # ← РЕГРЕССИОННЫЙ ТЕСТ ДЛЯ SEC-005
        ok, reason = reefiki.classify_path("../../etc/passwd", self.project)
        self.assertFalse(ok)
        self.assertIn("outside", reason)

    def test_ssh_directory_is_rejected(self):
        ok, reason = reefiki.classify_path(
            str(Path.home() / ".ssh" / "id_rsa"), self.project
        )
        self.assertFalse(ok)

    def test_env_file_is_rejected(self):
        ok, reason = reefiki.classify_path(".env", self.project)
        self.assertFalse(ok)

    def test_data_env_is_rejected(self):    # ← РЕГРЕССИОННЫЙ ТЕСТ ДЛЯ SEC-009
        ok, reason = reefiki.classify_path("data.env", self.project)
        self.assertFalse(ok)  # Должен быть отклонён после исправления

    def test_large_file_is_rejected(self):
        large = self.project / "big.md"
        large.write_bytes(b"x" * (6 * 1024 * 1024))
        ok, reason = reefiki.classify_path(str(large), self.project)
        self.assertFalse(ok)
```

**Сложность: S**

---

### T1-003 — Нет тестов для `private_project_names()` и `classify_publish_diff()`
> **Severity: MEDIUM**

SEC-011 (missing file = all public) не покрыт тестом:

```python
class TestPublishSafety(unittest.TestCase):
    def test_missing_private_projects_file_raises_instead_of_returning_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            # Файл не существует
            with self.assertRaises(SystemExit) as cm:
                reefiki.private_project_names(repo)
            self.assertIn("Missing", str(cm.exception))

    def test_classify_publish_diff_mixed_case(self):
        paths = [
            "projects/private/wiki/page.md",
            "projects/public/wiki/page.md",
        ]
        result = reefiki.classify_publish_diff(paths, ["private"])
        self.assertEqual(result, "mixed")

    def test_classify_publish_diff_empty_private_list_all_public(self):
        paths = ["projects/personal/wiki/sensitive.md"]
        result = reefiki.classify_publish_diff(paths, [])
        # Это должно быть "public-safe" — и это потенциально опасно
        # Тест документирует поведение и служит триггером для ревью
        self.assertEqual(result, "public-safe")
```

**Сложность: S**

---

### 4.3 Качество существующих тестов

**Сильные стороны:**

- `test_reefiki_memory_contracts.py` (57 тестов) — исчерпывающий контрактный тест. Проверяет JSON-схему каждой команды, включая поля `outcome`, `reason`, `schema_version`. Это эталон качества для проекта.
- Тесты используют реальные git-операции с `tempfile.TemporaryDirectory` — не моки → реальная верификация.
- `test_public_snapshot_guard.py` — умный метатест: проверяет что все реальные проекты в `private-projects.txt`.

**Слабые стороны:**

- `test_validate_frontmatter.py` — только 2 теста. Не покрывает: UTF-8 BOM, CRLF, вложенные списки, inline-список `[a, b]`, большой frontmatter, битый YAML (нет `---`).
- Нет тестов для edge cases `escape_fts()`, `classify_path()`, `normalize_repo_path()`.
- Нет теста на idempotency `save_source` (уже есть один: `test_save_url_refuses_canonical_duplicate_before_writing` ✅).
- Нет performance-тестов (хотя это обычная практика не иметь их в unit-тестах).

---

### 4.4 Тестовая инфраструктура

```python
# Паттерн во всех тестах:
SPEC = importlib.util.spec_from_file_location("reefiki", REEFIKI_PATH)
reefiki = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reefiki)
```

Это **динамическая загрузка модуля** без pip install. Работает ✅, но:
- Типы, импортированные из модуля, не совместимы с типами из других импортов того же модуля
- Нельзя использовать `isinstance(result, reefiki.SomeClass)` из другого места

Альтернатива: добавить `pyproject.toml` + `pip install -e .` → `import reefiki` везде.

---

## Итоговая таблица findings

| ID | Severity | Аудит | Описание | Сложность |
|---|---|---|---|---|
| T1-001 | **HIGH** | Тесты | Нет тестов `escape_fts()` — критические edge cases без регрессии | S |
| T1-002 | **HIGH** | Тесты | Нет тестов `classify_path()` — path traversal без регрессионного теста | S |
| A1-001 | MEDIUM | Agent contract | `outcome` имеет три несовместимых словаря значений в разных командах | M |
| A1-003 | MEDIUM | Agent contract | `harvest-commit` без идемпотентного ключа — двойной коммит при retry | S |
| A1-004 | MEDIUM | Agent contract | Deadlock `create_pr_required` без команды выхода из состояния | S |
| C1-001 | MEDIUM | Параллелизм | TOCTOU race в `unique_inbox_path()` → silent overwrite при параллельных save | S |
| C1-002 | MEDIUM | Параллелизм | `build_index()` DROP TABLE без lock → concurrent search вызывает рекурсивный rebuild | M |
| P1-001 | MEDIUM | Производительность | O(N²) в `review_queue_scan()`: missing_backlink detection | S |
| P1-002 | MEDIUM | Производительность | `dedup_check()` O(N) filesystem scan на каждый `save` | M |
| T1-003 | MEDIUM | Тесты | Нет тестов `private_project_names()` и `classify_publish_diff()` edge cases | S |
| A1-002 | LOW | Agent contract | Нет `schema_version` в большинстве JSON-ответов | S |
| A1-005 | LOW | Agent contract | 8 команд без `--format json` — агент вынужден парсить plain text | S |
| C1-003 | LOW | Параллелизм | `_wiki_rows()` без кеша — многократное чтение диска в одной операции | M |
| P1-003 | LOW | Производительность | `status()` не использует SQLite индекс: O(N) parse_frontmatter | S |
| P1-004 | LOW | Производительность | `iter_pages()` не рекурсивна: файлы в поддиректориях теряются | S |
| P1-005 | LOW | Производительность | `_wiki_rows()` вызывается N раз в одной команде без кеша | M |

### Распределение по severity

```
CRITICAL:  0
HIGH:      2  (T1-001, T1-002)
MEDIUM:    8  (A1-001, A1-003, A1-004, C1-001, C1-002, P1-001, P1-002, T1-003)
LOW:       6  (A1-002, A1-005, C1-003, P1-003, P1-004, P1-005)
```

### Приоритизированный action plan

**Немедленно (HIGH):**

```
1. T1-001 — Написать тесты escape_fts() (S) — предотвращает регресс SEC-003
2. T1-002 — Написать тесты classify_path() (S) — предотвращает регресс SEC-005
```

**Ближайший релиз (MEDIUM):**

```
3. P1-001 — O(N) рефакторинг review_queue_scan missing_backlink (S)
4. A1-001 — Унификация outcome словаря (M) — улучшает надёжность агентов
5. C1-001 — Атомарный unique_inbox_path через O_EXCL (S)
6. T1-003 — Тесты publish safety guards (S)
7. A1-004 — Документировать create_pr_required в AGENTS.md (S)
8. A1-003 — Документировать retry semantics harvest-commit в AGENTS.md (S)
```

**Рекомендуемые улучшения (LOW):**

```
9.  C1-002 — SQLite BEGIN IMMEDIATE в build_index (M)
10. P1-002 — SQLite-based dedup_check (M)
11. A1-005 — --format json для plan check, status, save (S, per command)
12. P1-004 — Рекурсивный iter_pages (S — возможно breaking change)
13. P1-003 — status() использует SQLite индекс (S)
14. A1-002 — schema_version в payload командах (S)
```

### Общий статус по всем 5 аудитам

| Аудит | Findings | HIGH | MEDIUM | LOW |
|---|---|---|---|---|
| Безопасность данных (REEFIKI_SECURITY_AUDIT.md) | 20 | 5 | 8 | 6 |
| AI-agent contract | 5 | 0 | 3 | 2 |
| Параллелизм / целостность данных | 3 | 0 | 2 | 1 |
| Производительность / масштабируемость | 5 | 0 | 2 | 3 |
| Тестовое покрытие | 3 | 2 | 1 | 0 |
| **ИТОГО** | **36** | **7** | **16** | **12** |
