# REEFIKI: Аудит мультиагентной конкурентности

> Дата: 2026-06-02
> Область: `scripts/reefiki.py` (3949 строк), `scripts/reefiki_memory/__init__.py`
> Фокус: race conditions, SQLite locks, git conflicts, file system races при параллельной работе нескольких AI-агентов (Claude, Codex, Hermes) в одном проекте

---

## Резюме

REEFIKI **не имеет ни одного механизма синхронизации** — ни file locks, ни mutexes, ни atomic writes, ни SQLite busy_timeout, ни git coordination. При параллельной работе 2+ агентов ожидаются: потеря данных, corrupted SQLite, git push conflicts, interleaved log entries. Обнаружено **12 конкретных проблем** — от критических до низких.

---

## FINDING 1: build_index() — деструктивная перезапись без блокировок

**Описание:** `build_index()` делает `DROP TABLE IF EXISTS` для всех таблиц, затем пересоздаёт и заполняет их. Два параллельных вызова `build_index()` (например, два агента одновременно вызвали `search()` на пустой БД) приводят к гонке: один агент может DROP'нуть таблицы пока другой INSERT'ит.

**Место:** `reefiki.py:257-389`
```python
def build_index(project: Path) -> int:
    conn = sqlite3.connect(database)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        DROP TABLE IF EXISTS pages;
        DROP TABLE IF EXISTS pages_fts;
        ...
    """)
    # ... long INSERT loop ...
    conn.commit()
    conn.close()
```

**Серьёзность:** 🔴 CRITICAL

**Сценарий эксплуатации:**
- Агент A вызывает `search("deploy")` → БД не существует → вызывает `build_index()`
- Агент B одновременно вызывает `search("config")` → БД не существует → вызывает `build_index()`
- Агент A делает DROP TABLE, начинает INSERT
- Агент B делает DROP TABLE → уничтожает данные Агента A mid-flight
- Результат: corrupted FTS5 index или SQLITE_BUSY (нет `busy_timeout`)

**Исправление:** Обернуть в advisory lock файл (`.reefiki/build.lock`) + `sqlite3.connect(database, timeout=30)` + сделать rebuild идемпотентным через `CREATE TABLE IF NOT EXISTS` + `DELETE FROM` вместо `DROP TABLE`.

**Сложность:** Средняя (1-2 дня)

---

## FINDING 2: SQLite — нет busy_timeout

**Описание:** Ни одна SQLite-коннекция не устанавливает `PRAGMA busy_timeout`. По умолчанию Python sqlite3 ждёт 5 секунд, но WAL mode без busy_timeout означает, что параллельные writers будут получать `SQLITE_BUSY` и падать с необработанным исключением.

**Место:** `reefiki.py:259, 486, 616`
```python
conn = sqlite3.connect(database)  # Нет timeout параметра
conn.execute("PRAGMA journal_mode=WAL")  # Только в build_index
```

**Серьёзность:** 🟠 HIGH

**Сценарий эксплуатации:**
- Агент A вызывает `search()` → открывает read connection
- Агент B вызывает `index` → открывает write connection → `conn.commit()`
- Агент A делает SELECT в момент commit'а → `SQLITE_BUSY` → необработанное исключение

**Исправление:** Добавить `PRAGMA busy_timeout=10000` после каждого `sqlite3.connect()`. Установить `journal_mode=WAL` во всех подключениях, не только в `build_index`.

**Сложность:** Низкая (30 минут)

---

## FINDING 3: unique_inbox_path() — TOCTOU race condition

**Описание:** Функция проверяет существование файла и генерирует уникальное имя через цикл `while path.exists()`, но между проверкой и записью другой агент может создать файл с тем же именем.

**Место:** `reefiki.py:826-836`
```python
def unique_inbox_path(project: Path, source: str) -> Path:
    path = inbox / f"{stem}{suffix}"
    counter = 2
    while path.exists():
        path = inbox / f"{stem}-{counter}{suffix}"
        counter += 1
    return path
# ...
destination.write_text(...)  # Несколько строк спустя, не атомарно
```

**Серьёзность:** 🟠 HIGH

**Сценарий эксплуатации:**
- Агент A: `save_source("https://example.com/article")` → получает `inbox/article.md`
- Агент B: `save_source("https://example.com/article")` → получает `inbox/article.md` (ещё не создан)
- Оба пишут в `inbox/article.md` → второй перезаписывает первый, теряя данные

**Исправление:** Использовать `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)` для атомарного создания или `tempfile.mkstemp` + `os.rename`.

**Сложность:** Низкая (1 час)

---

## FINDING 4: plan_create() — check-then-act race

**Описание:** `plan_create()` проверяет существование плана и создаёт его — два дискретных шага без атомарности.

**Место:** `reefiki.py:869-900`
```python
def plan_create(project: Path, title: str) -> int:
    path = plans / f"{slug}.md"
    if path.exists():
        raise SystemExit(f"Plan already exists: ...")
    # ... другой агент может создать файл здесь ...
    path.write_text(body + f"\n<!-- reefiki-plan-sha256:{checksum} -->\n", ...)
```

**Серьёзность:** 🟡 MEDIUM

**Сценарий эксплуатации:**
- Два агента одновременно создают план с одним title
- Оба проходят проверку `if path.exists()` → оба пишут → второй перезаписывает первый без checksum первого

**Исправление:** Атомарное создание через `O_CREAT | O_EXCL`.

**Сложность:** Низкая (30 минут)

---

## FINDING 5: apply_promotion_draft() — race при создании wiki-страниц

**Описание:** Цикл `while page_path.exists()` для генерации уникального имени страницы + последующий `write_text()` — классическая TOCTOU.

**Место:** `reefiki.py:3589-3613`
```python
page_path = project / "wiki" / subdir / f"{page_id}.md"
counter = 2
while page_path.exists():
    page_path = project / "wiki" / subdir / f"{page_id}-{counter}.md"
    counter += 1
# ... 
page_path.write_text(page_text, encoding="utf-8")
```

**Серьёзность:** 🟡 MEDIUM

**Сценарий эксплуатации:**
- Агент A применяет promotion draft "deploy-guide" → page_path = `wiki/concepts/deploy-guide.md`
- Агент B применяет другой draft с тем же slug → page_path = `wiki/concepts/deploy-guide.md`
- Оба пишут → потеря одного из promotion drafts

**Исправление:** Атомарное создание + retry.

**Сложность:** Низкая (1 час)

---

## FINDING 6: log.md — interleaved append от нескольких агентов

**Описание:** Четыре места делают `log.open("a")` → `handle.write(multi-line)`. POSIX гарантирует атомарность `write()` для небольших буферов, но multi-line writes через `handle.write(f"...\n...\n")` могут интерливиться.

**Место:** `reefiki.py:842, 3478, 3514, 3616`
```python
# Все 4 места одинаковый паттерн:
with log.open("a", encoding="utf-8", newline="\n") as handle:
    handle.write(f"\n## [{date.today().isoformat()}] ...\n\n- ...\n")
```

**Серьёзность:** 🟡 MEDIUM

**Сценарий эксплуатации:**
- Агент A пишет `\n## [2026-06-02] ...\n\n- draft: ...`
- Агент B одновременно пишет `\n## [2026-06-02] ...\n\n- page: ...`
- Результат: строки двух записей перемешаны → `log.md` becomes garbled
- `timeline()` потом не сможет распарсить записи

**Исправление:** Писать одной `write()` call с полной записью (как сейчас — OK для POSIX), но добавить advisory lock для multi-line writes. Или: собрать всю запись в одну строку-буфер и писать атомарно.

**Сложность:** Низкая (1 час)

---

## FINDING 7: harvest_commit_payload() — git race между read-tree и commit

**Описание:** `harvest_commit_payload()` выполняет последовательность git-операций с временным индексом: `read-tree HEAD` → `add -- paths` → `diff --cached` → `commit`. Между этими шагами другой агент может сделать свой commit, изменив HEAD.

**Место:** `reefiki.py:1219-1248`
```python
with tempfile.TemporaryDirectory(...) as tempdir:
    env["GIT_INDEX_FILE"] = str(Path(tempdir) / "index")
    run_git(repo, ["read-tree", "HEAD"], env=env)  # Шаг 1
    run_git(repo, ["add", "--", *normalized_paths], env=env)  # Шаг 2
    # ← Другой агент может сделать commit здесь
    run_git(repo, ["commit", "-m", message], env=env)  # Шаг 3: parent = old HEAD
# После with-блока:
run_git(repo, ["reset", "-q", "HEAD", "--", *normalized_paths])  # Шаг 4
```

**Серьёзность:** 🟠 HIGH

**Сценарий эксплуатации:**
- Агент A: `harvest-commit --path wiki/concepts/deploy.md`
  - read-tree HEAD (= commit X)
  - add deploy.md
  - commit → creates commit Y (parent=X)
- Агент B (параллельно): `harvest-commit --path wiki/decisions/auth.md`
  - read-tree HEAD (= commit X)  
  - add auth.md
  - commit → creates commit Z (parent=X)
- Git: Y и Z оба parent=X → один будет detached или push reject
- `git reset HEAD -- paths` Агента A может unstaged paths Агента B

**Исправление:** `git fetch origin && git rebase origin/main` перед commit. Или использоваgit lockfiles (`.git/index.lock` detection). Retry with rebase on conflict.

**Сложность:** Средняя (1-2 дня)

---

## FINDING 8: publish_task_payload() — concurrent push conflicts

**Описание:** `publish_task_payload()` делает `git push private_remote HEAD:main` без `--force-with-lease`. Два агента, одновременно пушащие в main, получат rejected push.

**Место:** `reefiki.py:1409-1411`
```python
run_git(repo, ["push", private_remote, f"HEAD:{branch}"])  # task branch
run_git(repo, ["push", private_remote, "HEAD:main"])  # main — NO --force-with-lease!
```

**Серьёзность:** 🟠 HIGH

**Сценарий эксплуатации:**
- Агент A: publish-task → push HEAD:main (commit Y)
- Агент B: publish-task → push HEAD:main (commit Z, parent X ≠ Y)
- B's push rejected → `require_git_success` → `SystemExit` → незавершённая операция, task branch запушен но main не обновлён

**Исправление:** Использовать `--force-with-lease` для main push. Добавить retry с fetch+rebase.

**Сложность:** Средняя (1 день)

---

## FINDING 9: push_public_snapshot() — worktree collision

**Описание:** `push_public_snapshot()` создаёт worktree и orphan branch с timestamp-именем. Два параллельных вызова создадут два worktree из одного repo → git worktree может конфликтовать.

**Место:** `reefiki.py:1418-1447`
```python
def push_public_snapshot(repo, public_remote, private_projects):
    with tempfile.TemporaryDirectory(...) as tempdir:
        snapshot = Path(tempdir) / "snapshot"
        run_git(repo, ["worktree", "add", "--detach", str(snapshot), "HEAD"])
        branch = f"public-snapshot-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        # ... orphan branch, add -A, commit, push --force-with-lease
```

**Серьёзность:** 🟡 MEDIUM

**Сценарий эксплуатации:**
- Два агента одновременно вызывают publish-task с public-snapshot
- Timestamp с секундным разрешением может совпасть
- `worktree add` может fail если git lock file существует
- `push --force-with-lease` к одной ветке → второй перезаписывает первый

**Исправление:** Использовать `tempfile.mkdtemp` (всегда уникально). Добавить PID/UUID к имени ветки.

**Сложность:** Низкая (30 минут)

---

## FINDING 10: search() — бесконечная рекурсия при failed build_index

**Описание:** `search_existing()` ловит `sqlite3.OperationalError("no such table")`, вызывает `build_index()` и рекурсивно вызывает себя. Если `build_index()` сам упадёт (другой агент DROP'нул таблицы), рекурсия не ограничена.

**Место:** `reefiki.py:552-568`
```python
except sqlite3.OperationalError as exc:
    if "no such table" not in str(exc):
        raise
finally:
    conn.close()
build_index(project)  # Если это упадёт — исключение, НО если таблицу снова удалат — infinite loop
return search_existing(...)  # Recursive call, no depth limit
```

**Серьёзность:** 🟡 MEDIUM

**Сценарий эксплуатации:**
- Агент A: `search("x")` → no such table → `build_index()` → начинает DROP+INSERT
- Агент B: `search("y")` → no such table (A ещё не закончил) → `build_index()` → DROP'ает таблицы A
- Агент A: рекурсивный `search_existing()` → no such table → `build_index()` → ...
- Stack overflow или infinite loop

**Исправление:** Добавить `max_retries=1` параметр. Или проверять существование таблиц перед рекурсивным вызовом.

**Сложность:** Низкая (30 минут)

---

## FINDING 11: conn.close() не всегда в finally block

**Описание:** В `build_index()` и `search_existing()` нет гарантии закрытия connection при исключении. `build_index()` вообще не имеет try/finally для conn.

**Место:** `reefiki.py:257-389` (build_index), `reefiki.py:528-556` (search_existing)
```python
def build_index(project):
    conn = sqlite3.connect(database)
    # ... 130 строк кода без try/finally ...
    conn.commit()
    conn.close()  # Если исключение между connect и close — connection leaked
```

**Серьёзность:** 🟡 MEDIUM

**Сценарий эксплуатации:**
- `build_index()` падает на line 350 (INSERT error) → conn не закрыт
- SQLite file locked → все последующие `sqlite3.connect()` блокируются
- Особенно критично при мультиагентной работе — один leaked connection блокирует всех

**Исправление:** Использовать `with sqlite3.connect(database) as conn:` (context manager) или явный try/finally.

**Сложность:** Низкая (1 час)

---

## FINDING 12: Нет coordination protocol между агентами

**Описание:** REEFIKI поддерживает работу Claude, Codex и Hermes в одном проекте, но не имеет никакого протокола координации: ни lock files, ни lease mechanism, ни agent registration, ни "я работаю с этим проектом" signal.

**Место:** Архитектурный пробел, весь `reefiki.py`

**Серьёзность:** 🟠 HIGH (design gap)

**Сценарий эксплуатации:**
- Claude редактирует `wiki/concepts/deploy.md`
- Codex одновременно редактирует ту же страницу
- Оба делают `harvest-commit` → git conflict
- Оба делают `build_index` → SQLite race
- Оба пишут в `log.md` → interleaved entries

**Исправление:** Ввести coordination mechanism:
1. `.reefiki/agent.lock` — advisory lock с PID + agent_id + timestamp
2. `reefiki.py lock --agent claude --timeout 300` → acquire
3. `reefiki.py unlock --agent claude` → release
4. Auto-expire stale locks (по PID + timestamp)

**Сложность:** Высокая (3-5 дней)

---

## Сводная таблица

| # | Название | Серьёзность | Сложность |
|---|----------|-------------|-----------|
| 1 | build_index DROP race | 🔴 CRITICAL | Средняя |
| 2 | SQLite no busy_timeout | 🟠 HIGH | Низкая |
| 3 | unique_inbox_path TOCTOU | 🟠 HIGH | Низкая |
| 4 | plan_create check-then-act | 🟡 MEDIUM | Низкая |
| 5 | apply_promotion TOCTOU | 🟡 MEDIUM | Низкая |
| 6 | log.md interleaved appends | 🟡 MEDIUM | Низкая |
| 7 | harvest-commit git race | 🟠 HIGH | Средняя |
| 8 | publish-task push conflict | 🟠 HIGH | Средняя |
| 9 | public-snapshot worktree collision | 🟡 MEDIUM | Низкая |
| 10 | search() infinite recursion | 🟡 MEDIUM | Низкая |
| 11 | conn.close() leak | 🟡 MEDIUM | Низкая |
| 12 | Нет agent coordination | 🟠 HIGH | Высокая |

---

## Приоритет исправления

**Phase 1 (Quick wins, 1-2 дня):**
- Finding 2: busy_timeout на все SQLite connections
- Finding 3: atomic inbox file creation (O_EXCL)
- Finding 4: atomic plan creation
- Finding 5: atomic page creation
- Finding 10: recursion depth limit
- Finding 11: context manager для SQLite

**Phase 2 (Git safety, 2-3 дня):**
- Finding 1: advisory lock для build_index
- Finding 7: rebase-before-commit в harvest
- Finding 8: --force-with-lease + retry для publish
- Finding 9: unique branch names

**Phase 3 (Architecture, 3-5 дней):**
- Finding 6: log.md advisory lock
- Finding 12: full agent coordination protocol

---

## Что НЕ является проблемой

- **Внутрипроцессная конкурентность:** В reefiki.py нет threading/multiprocessing — все проблемы только inter-process (разные CLI invocations).
- **WAL mode:** Уже используется в `build_index()` — это правильно, просто нужно расширить на все connections.
- **Markdown как source of truth:** SQLite — rebuildable cache, поэтому corruption индекса не катастрофа (можно пересобрать). Но data loss в wiki/inbox/plans — реальная потеря.
- **harvest-commit с temp index:** Использование `GIT_INDEX_FILE` — хороший паттерн для изоляции staging area, но commit всё равно идёт в общий repo.
