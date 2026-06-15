# REEFIKI — Аудит безопасности данных

> Дата: 2 июня 2026. Срез main-ветки `kisslex2013-alt/reefiki`.
> Аудитор: статический анализ кода, grep-сканирование, трассировка data flow.

---

## Содержание

1. [Шаг 1 — Инвентаризация данных](#шаг-1--инвентаризация-данных)
2. [Шаг 2 — Секреты и учётные данные](#шаг-2--секреты-и-учётные-данные)
3. [Шаг 3 — SQL-инъекция и FTS5](#шаг-3--sql-инъекция-и-fts5)
4. [Шаг 4 — Path traversal](#шаг-4--path-traversal)
5. [Шаг 5 — Безопасность subprocess](#шаг-5--безопасность-subprocess)
6. [Шаг 6 — Утечка данных через publish-task](#шаг-6--утечка-данных-через-publish-task)
7. [Шаг 7 — Безопасность git-истории](#шаг-7--безопасность-git-истории)
8. [Шаг 8 — Сетевое воздействие](#шаг-8--сетевое-воздействие)
9. [Шаг 9 — Права доступа к файлам](#шаг-9--права-доступа-к-файлам)
10. [Шаг 10 — Privacy model (private/project/public tiers)](#шаг-10--privacy-model)
11. [Шаг 11 — Supply chain](#шаг-11--supply-chain)
12. [Шаг 12 — Валидация YAML frontmatter](#шаг-12--валидация-yaml-frontmatter)
13. [Шаг 13 — Denial of Service](#шаг-13--denial-of-service)
14. [Итоговая таблица findings](#итоговая-таблица-findings)

---

## Шаг 1 — Инвентаризация данных

### 1.1 Какие данные хранятся

| Категория данных | Что содержит | Формат | Расположение |
|---|---|---|---|
| **Wiki-страницы** | Знания, заметки, ссылки, источники | Markdown + YAML frontmatter | `projects/<name>/wiki/**/*.md` |
| **Inbox** | Необработанные источники (URL-ссылки, скопированные файлы) | Текст / `.md` | `projects/<name>/inbox/*.md` |
| **Seen-записи** | Отметки об уже обработанных источниках | Markdown | `projects/<name>/seen/*.md` |
| **Log** | Хронология команд `/save`, ссылки на источники | Markdown append-only | `projects/<name>/wiki/log.md` |
| **Plans** | SHA256-подписанные планы задач | Markdown с checksumом | `projects/<name>/plans/*.md` |
| **SQLite FTS5 индекс** | Зеркало wiki: id, title, tags, body, sources, use_count | SQLite | `.reefiki/index.sqlite` |
| **Memoir store** | Долгосрочная AI-память (векторная/текстовая) | Формат memoir-ai | `$REEFIKI_MEMOIR_STORE` |
| **public-snapshot config** | Список приватных проектов, не публикуемых в public remote | Plain text | `scripts/public-snapshot.private-projects.txt` |
| **AGENTS.md** | Инструкции для AI-агентов, включая данные о проектах | Markdown | корень репозитория |

### 1.2 Что попадает в SQLite FTS5

`build_index()` индексирует в FTS5:
- `id`, `title`, `tags`, `useful_when`, `body` — весь текст страницы

Дополнительно в обычных (не FTS5) таблицах хранится:
- `sources` (список URL-источников)
- `date_added`, `last_used`, `use_count`
- `sha256` хеш файла
- Полный индекс ссылок (`links` таблица): `source_id → target_id`

**Чувствительное содержимое, которое может попасть в индекс:**
Если wiki-страница содержит embedded секреты (API key в markdown body), они будут проиндексированы в `body` поле — включая полнотекстовый поиск.

### 1.3 Что попадает в git-историю

REEFIKI управляет git-историей через изолированный `GIT_INDEX_FILE` в `harvest_commit_payload`:
- Коммиты создаются только для файлов в `projects/<target>/wiki/`
- Обычный `git commit` напрямую не используется — только через `harvest-commit` команду
- Однако если пользователь делает `git add` вручную, ничто не запрещает добавить что угодно

**Данные, которые по архитектуре попадают в историю:**
- Все версии wiki-страниц — содержимое и метаданные
- `log.md` — хронология команд `/save` с URL-источниками

**Данные, которые НЕ должны попасть в историю:**
- `.reefiki/index.sqlite` — в `.gitignore` ✅
- `plans/` — в `.gitignore` ✅
- `.reefiki/` — в `.gitignore` ✅

---

## Шаг 2 — Секреты и учётные данные

### 2.1 Результаты grep-сканирования исходников

#### `scripts/reefiki.py`

| Строка | Паттерн | Содержимое | Оценка |
|---|---|---|---|
| L79–92 | `SECRET_PATTERNS` | Список fnmatch-паттернов имён файлов | ✅ — это защитный механизм |
| L93 | `SECRET_PARTS` | `{".aws", ".ssh"}` | ✅ — защитный механизм |
| **L134** | `os.environ.get(...)` | `r"C:\Users\kissl\.codex\memoir-stores\reefiki"` | ⚠️ **HARDCODED** личный путь |
| L658–662 | `SECRET_PARTS`, `SECRET_PATTERNS` | Использование в `classify_path()` | ✅ |
| L1872, 1893, 2299, 2848 | `"secrets"` | `forbidden_scopes=["secrets", ...]` | ✅ — защитный scope |

#### `scripts/reefiki_memory/__init__.py`

| Строка | Содержимое | Оценка |
|---|---|---|
| L162–163 | `SECRET_PATTERNS = [re.compile(r"(?i)\b(api[_-]?key\|token\|password\|secret)\b\s*[:=]\s*\S+")]` | ✅ — Content-based детектор (только для memory preflight) |
| L189–190 | `if any(pattern.search(content) for pattern in self.SECRET_PATTERNS)` | ✅ — В `memory_preflight()` |

#### `.gitignore`

Охваченные паттерны:
```
.env         ✅ (но НЕ *.env)
.env.*       ✅
*.pem        ✅
*.key        ✅
*.pfx        ✅
id_rsa*      ✅
*.zip/.tar   ✅
*.log        ✅
.reefiki/    ✅
plans/       ✅
```

Отсутствующие паттерны:
```
*.env        ❌  data.env, config.env, app.env не исключены
*.sqlite     ❌  db в других местах (хотя .reefiki/*.sqlite исключён через .reefiki/)
*.db         ❌
CLAUDE.md    ❌  может содержать контекст проекта
.env.local   частично ✅ через .env.*
```

#### Заключение Шага 2

---

### SEC-001 — Жёстко захардкоженный личный путь как default
> **Severity: MEDIUM**

**Описание:**

```python
# reefiki.py, строка 134
GLOBAL_MEMOIR_STORE = Path(
    os.environ.get("REEFIKI_MEMOIR_STORE", r"C:\Users\kissl\.codex\memoir-stores\reefiki")
)
```

Дефолтное значение содержит личный путь разработчика на Windows. На любой другой машине этот путь не существует. При запуске команд memoir на macOS/Linux memoir попытается обратиться к несуществующей директории и упадёт с неинформативной ошибкой.

**Exploit scenario:**

```
# Linux пользователь без REEFIKI_MEMOIR_STORE в env:
python scripts/reefiki.py memory lookup --layer memoir "Python async"
→ memoir: path C:\Users\kissl\... does not exist (FileNotFoundError)
```

**Решение:**

```python
GLOBAL_MEMOIR_STORE = Path(
    os.environ.get(
        "REEFIKI_MEMOIR_STORE",
        Path.home() / ".local" / "share" / "memoir" / "reefiki",
    )
)
```

**Сложность исправления: S** (1 строка)

---

### SEC-002 — `.gitignore` не покрывает `*.env` варианты
> **Severity: LOW**

```
# .gitignore содержит:
.env
.env.*

# Не содержит:
*.env     ← data.env, config.env, secrets.env не исключены из git
```

**Exploit scenario:** разработчик создаёт `projects/myproject/wiki/config.env` → не исключён gitignore → попадает в `git add -A` → может попасть в историю.

**Решение:** добавить в `.gitignore`:
```gitignore
*.env
*.db
*.sqlite
```

**Сложность: S**

---

## Шаг 3 — SQL-инъекция и FTS5

### 3.1 Как строятся FTS5-запросы

```python
# reefiki.py, строки 439–443
def escape_fts(query: str) -> str:
    tokens = re.findall(r"\w+", query, flags=re.UNICODE)
    return " OR ".join(tokens) if tokens else query  # ← ПРОБЛЕМА здесь
```

```python
# reefiki.py, строки 513–515
fts_query = escape_fts(query)
# ...
where_sql = (f"{fts_table} MATCH ?" + (f" AND {where_sql}" if where_sql else ""))
params = [fts_query, *params]
# ...
rows = conn.execute(f"SELECT ... WHERE {where_sql} ...", (*params, limit))
```

### 3.2 Параметризация SQL

**Все остальные SQL execute вызовы:**

| Строка | Запрос | Параметры | Безопасность |
|---|---|---|---|
| 350 | `SELECT rowid FROM pages WHERE id = ?` | `(page_id,)` | ✅ |
| 492 | `p.type = ?` | `params.append(page_type)` | ✅ |
| 495 | `p.tags LIKE ?` | `params.append(f"%{tag}%")` | ✅ |
| 500 | `links l WHERE l.target_id = ?` | `params.append(...)` | ✅ |
| 504 | `links l WHERE l.source_id = ?` | `params.append(...)` | ✅ |
| FTS MATCH | `pages_fts MATCH ?` | `params = [fts_query, ...]` | ✅ (FTS query параметризован) |

**SQL-инъекция в классическом смысле невозможна** — все пользовательские строки идут через параметры `?`.

### 3.3 Проблема `escape_fts` — FTS5 keyword crash

---

### SEC-003 — `escape_fts()` передаёт raw query в FTS5 при отсутствии word-токенов
> **Severity: MEDIUM**

**Описание:**

```python
def escape_fts(query: str) -> str:
    tokens = re.findall(r"\w+", query, flags=re.UNICODE)
    return " OR ".join(tokens) if tokens else query  # ← fallback!
```

Если запрос содержит **только специальные символы** (`---`, `"*"`, `+/-+`), `tokens` пустой и возвращается исходный `query` без изменений. Этот raw запрос передаётся в FTS5 MATCH — и вызывает `sqlite3.OperationalError`, который **не перехватывается**:

```python
except sqlite3.OperationalError as exc:
    if "no such table" not in str(exc):
        raise  # ← любой другой OperationalError re-raises → crash
```

Дополнительная проблема: `escape_fts` возвращает `\w+` токены без кавычек. FTS5 keywords (`AND`, `OR`, `NOT`, `NEAR`) — это допустимые `\w+` токены. Запрос `"python AND NOT"` → `escape_fts` → `"python OR AND OR NOT"` → FTS5 парсит `AND`, `OR`, `NOT` как операторы → `"python OR <operator> OR <operator>"` → синтаксическая ошибка FTS5 → `OperationalError` → crash.

**Exploit scenario:**

```bash
# Вход из AI-агента (нормальный вопрос с пунктуацией):
python scripts/reefiki.py --project myproject search "C++ AND Python"
# → escape_fts("C++ AND Python") → ["C", "AND", "Python"]
# → "C OR AND OR Python"
# → FTS5: "C OR [operator] OR Python" → OperationalError → crash

# Или:
python scripts/reefiki.py --project myproject search "---"
# → escape_fts("---") → tokens=[] → returns "---"
# → FTS5 MATCH "---" → OperationalError → crash
```

**Решение:**

```python
def escape_fts(query: str) -> str:
    """Return a safe FTS5 MATCH expression for the given query string.
    
    Strips all FTS5 operators and special syntax; builds plain OR query
    from word tokens. Returns None-equivalent empty string for empty input.
    """
    FTS5_KEYWORDS = {"and", "or", "not", "near"}
    tokens = [
        f'"{t}"'  # quote each token to prevent operator interpretation
        for t in re.findall(r"\w+", query, flags=re.UNICODE)
        if t.lower() not in FTS5_KEYWORDS  # skip FTS5 keywords as literals
    ]
    return " OR ".join(tokens) if tokens else ""

# В search_existing() обновить условие:
if query.strip() and escape_fts(query):   # добавить проверку на не-пустой результат
```

**Сложность: S**

---

### SEC-004 — Неограниченный LIMIT через `args.limit`
> **Severity: LOW**

```python
# reefiki.py CLI args:
parser.add_argument("--limit", type=int, default=7)
# ...
rows = search_existing(..., limit=args.limit, ...)
```

Нет верхней границы `limit`. Вызов с `--limit 100000` на большой wiki вернёт огромный набор данных.

**Решение:**

```python
parser.add_argument("--limit", type=int, default=7)
# После парсинга:
if args.limit > 200:
    raise SystemExit("--limit cannot exceed 200")
```

**Сложность: S**

---

## Шаг 4 — Path traversal

### 4.1 Инвентаризация принимаемых путей

| Команда / функция | Пользовательский ввод | Куда идёт |
|---|---|---|
| `save <source>` | URL или путь к файлу | `classify_path()` → `save_source()` |
| `harvest-commit --path` | Repo-relative пути | `normalize_repo_path()` → проверка prefix |
| `memory promote --path` | Путь к draft | `_resolve_project_path()` → `.resolve()` + confinement check |
| `memory promote-write --path` | Путь к draft | `_resolve_project_path()` — то же |
| `plan create --path` | Путь к плану | прямой `Path(args.path)` |

### 4.2 Анализ `_resolve_project_path` — правильно ✅

```python
# reefiki.py, строки 3435–3443
def _resolve_project_path(project: Path, path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = project / path
    resolved = path.resolve()          # раскрывает symlinks и ../
    project_root = project.resolve()
    if project_root not in [resolved, *resolved.parents]:
        raise SystemExit(f"{path_text}: outside project scope")  # ✅
    return path
```

Используется: `memory promote`, `memory promote-write` (строки 3447, 3573).

### 4.3 Анализ `classify_path` — **УЯЗВИМ** к path traversal

---

### SEC-005 — Path traversal в `save_source` через `../` пути
> **Severity: HIGH**

**Описание:**

`classify_path` проверяет имена директорий против `FORBIDDEN_PARTS` и `SECRET_PARTS`:

```python
# reefiki.py, строки 644–667
def classify_path(value: str, project: Path) -> tuple[bool, str]:
    # ...URL ветка пропущена...
    path = Path(value)
    if not path.is_absolute():
        path = project / path
    name = path.name
    lower_parts = {part.lower() for part in path.parts}
    if lower_parts & FORBIDDEN_PARTS:    # {'.git','node_modules',...}
        return False, "forbidden-directory"
    if lower_parts & SECRET_PARTS:       # {'.aws', '.ssh'}
        return False, "secret-directory"
    for pattern in SECRET_PATTERNS:
        if fnmatch.fnmatch(name.lower(), pattern.lower()):
            return False, "secret-name"
    # ...
    return True, "ok"  # ← ВОТ ПРОБЛЕМА
```

`".."`  не входит в `FORBIDDEN_PARTS`. Пути вида `../../etc/passwd` пройдут проверку и будут прочитаны в `save_source`:

```python
def save_source(project: Path, source: str) -> int:
    ok, reason = classify_path(source, project)  # ← возвращает True для ../
    if not ok:
        return 2
    # ...
    path = Path(source)
    if not path.is_absolute():
        path = project / path           # /projects/myproject/../../etc/passwd
    destination.write_bytes(path.read_bytes())  # ← копирует /etc/passwd в inbox!
```

**Exploit scenario:**

```bash
# AI-агент или пользователь:
python scripts/reefiki.py --project /home/user/wiki/projects/myproject \
    save "../../.ssh/id_rsa"

# Результат:
# Saved: inbox/id_rsa--<hash>.md  ← содержимое ~/.ssh/id_rsa в inbox!
# Inbox entries: 1
```

После этого файл в inbox → `index` команда → индексируется в SQLite FTS5 → включая полный текст приватного ключа.

**Решение — добавить `.resolve()` проверку в `classify_path`:**

```python
def classify_path(value: str, project: Path) -> tuple[bool, str]:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        ext = Path(parsed.path).suffix.lower()
        if ext in BINARY_EXTS:
            return False, f"binary-url:{ext}"
        return True, "ok"
    path = Path(value)
    if not path.is_absolute():
        path = project / path
    # ─── ДОБАВИТЬ: confinement check ───
    resolved = path.resolve()
    project_resolved = project.resolve()
    if project_resolved not in [resolved, *resolved.parents]:
        return False, "path-outside-project"
    # ───────────────────────────────────
    name = path.name
    lower_parts = {part.lower() for part in path.parts}
    # ... остальные проверки ...
```

**Сложность: S**

---

### SEC-006 — Отсутствие проверки symlink в `save_source`
> **Severity: MEDIUM**

Даже с фиксом SEC-005, `.resolve()` раскрывает symlinks. Если внутри wiki создан symlink `wiki/external → /etc/`, то:

```python
classify_path("wiki/external/passwd", project)
# resolved = /etc/passwd — НАХОДИТСЯ ВНЕ project → заблокировано с фиксом SEC-005
```

С правильным `resolve()` + confinement check — `symlink traversal` автоматически блокируется. Текущий код без `resolve()` — уязвим к обоим видам traversal.

**Решение:** тот же fix что SEC-005 (`.resolve()` check).

---

## Шаг 5 — Безопасность subprocess

### 5.1 Все 5 subprocess.run вызовов

| Строка | Команда | shell= | Пользовательский ввод | Проблемы |
|---|---|---|---|---|
| L1033 | `uvx memoir ...` | `False` | Нет (store path из env) | FileNotFoundError, нет timeout |
| L1056 | `git diff --cached ...` | `False` | Нет | FileNotFoundError, нет timeout |
| L1072 | `git *args` | `False` | `message` через `["-m", message]` | FileNotFoundError, нет timeout |
| L1203 | `sys.executable validate_frontmatter.py` | `False` | Нет (validator path hardcoded) | нет timeout |
| L2179 | `git *args` | `False` | Нет (только даты) | FileNotFoundError, нет timeout |

**Все вызовы используют list form, не `shell=True`** → shell-инъекция невозможна ✅

### 5.2 Инъекция через `--message`

```python
# harvest_commit_payload(), строка 1245:
require_git_success(run_git(repo, ["commit", "-m", message], env=env), "...")
```

`message` — строка из `args.message` CLI аргумента. Передаётся как единый элемент списка `["-m", message]`. Subprocess передаёт это как один аргумент — **shell-инъекция невозможна** ✅.

Единственная проверка: `if not message.strip(): raise SystemExit(...)` — нет ограничения длины. 1MB сообщение технически пройдёт (git его примет).

### 5.3 Ошибки stderr — утечка данных

```python
# run_memoir(), строки 1041–1043:
if completed.returncode != 0:
    detail = completed.stderr.strip() or completed.stdout.strip() or "memoir command failed"
    raise SystemExit(detail)
```

```python
# git_status_paths(), строки 1093–1095:
if completed.returncode != 0:
    detail = completed.stderr.strip() or ... or "git status scan failed"
    raise SystemExit(detail)
```

Весь stderr от subprocess прямо передаётся в вывод. Если memoir или git выводят в stderr чувствительные данные (например, remote URL с embedded credentials: `https://user:token@github.com/...`), они появятся в выводе CLI.

---

### SEC-007 — Отсутствие timeout на все subprocess вызовы
> **Severity: MEDIUM**

**Описание:**

Ни один из 5 вызовов `subprocess.run` не имеет `timeout=`. При использовании с AI-агентами это особенно критично:

```python
# run_git(), строка 1072 — нет timeout:
completed = subprocess.run(
    ["git", *args],
    cwd=repo, check=False, capture_output=True, text=True, encoding="utf-8",
)

# run_memoir(), строка 1033 — нет timeout:
completed = subprocess.run(
    _memoir_base_command(store) + args,
    check=False, capture_output=True, text=True, encoding="utf-8", env=env,
)
```

**Exploit scenarios:**

1. `git push` к недоступному remote → бесконечное ожидание → агент заблокирован
2. `uvx --from memoir-ai memoir` + медленная сеть → долгая загрузка PyPI пакета → агент завис
3. Атакованный remote git-сервер намеренно медлит с ответом → зависание процесса

**Решение:**

```python
# run_git() — добавить timeout:
completed = subprocess.run(
    ["git", *args],
    cwd=repo, check=False, capture_output=True, text=True, encoding="utf-8",
    timeout=120,  # 2 минуты для git push
)

# run_memoir() — короче:
completed = subprocess.run(
    _memoir_base_command(store) + args,
    check=False, capture_output=True, text=True, encoding="utf-8", env=env,
    timeout=30,
)

# Перехватить TimeoutExpired:
try:
    completed = subprocess.run([...], timeout=120)
except subprocess.TimeoutExpired:
    raise SystemExit("git operation timed out after 120s")
```

**Сложность: S**

---

### SEC-008 — `FileNotFoundError` при отсутствии `git` или `uvx`
> **Severity: MEDIUM**

**Описание:**

При отсутствии `git` или `uvx` в PATH все 5 subprocess вызовов падают с неперехваченным `FileNotFoundError`:

```
FileNotFoundError: [Errno 2] No such file or directory: 'git'
Traceback (most recent call last):
  File "scripts/reefiki.py", line 1072, in run_git
    completed = subprocess.run(["git", ...], ...)
```

Для AI-агента это — необработанное исключение вместо структурированного JSON ответа.

**Решение:**

```python
import shutil

def run_git(repo: Path, args: list[str], env=None):
    if not shutil.which("git"):
        raise SystemExit(
            "git not found. Install git: https://git-scm.com\n"
            "Commands without git: index, search, status, save, dedup, "
            "plan, timeline, review-queues, backlinks, memory (except diff)"
        )
    # ... existing code ...

def run_memoir(store: Path, args: list[str]):
    if not shutil.which("uvx"):
        raise SystemExit(
            "uvx not found. Install uv: https://docs.astral.sh/uv/\n"
            "memoir layer unavailable; use --layer reefiki instead"
        )
    # ... existing code ...
```

**Сложность: S**

---

## Шаг 6 — Утечка данных через publish-task

### 6.1 Pipeline от коммита до public remote

```
harvest-commit
  ↓ guard: paths ∈ projects/<target>/wiki/
  ↓ guard: isolated GIT_INDEX_FILE (не трогает реальный index)
  ↓ validate_frontmatter.py (если --validate)
  ↓ git commit (в изолированный temp index)

publish-task
  ↓ проверка: worktree clean
  ↓ classify_publish_diff → "public-safe" / "mixed" / "private-only"
  ↓ push_public_snapshot
       ↓ git add -A (всё!)
       ↓ git rm -r --cached projects/<private>/ (удаление приватных)
       ↓ scan staged для приватных путей
       ↓ git commit + push --force-with-lease
```

### 6.2 Guard против расширений файлов

В `guard_staged_payload` и `harvest_commit_payload` — **нет проверки расширений**. Единственный guard — путь должен начинаться с `projects/<target>/wiki/`. Таким образом, файл `projects/myproject/wiki/secret.env` пройдёт `harvest-commit`.

**Проверка расширений в `classify_path`** применяется только к команде `save`, **не к `harvest-commit`**.

### 6.3 Детальный анализ bypass сценариев

---

### SEC-009 — `data.env` и нестандартные env-файлы обходят `SECRET_PATTERNS`
> **Severity: HIGH**

**Описание:**

`classify_path()` проверяет `name.lower()` против `SECRET_PATTERNS` через fnmatch:

```python
SECRET_PATTERNS = [
    ".env",        # fnmatch ".env" matches ONLY exactly ".env"
    ".env.*",      # fnmatch ".env.*" matches ".env.local", ".env.prod"
    "secrets.*",   # matches "secrets.md", "secrets.json"
    "credentials.*",
    "id_rsa", "id_rsa.pub", "*.pem", "*.key", "*.pfx", "*.p12",
    ".npmrc", ".netrc",
]
```

Эти паттерны проверяются **только в `classify_path()`** (команда `save`). В `harvest-commit` нет аналогичной проверки.

Даже в `save`: `fnmatch("data.env", ".env")` → **False** (нет wildcard `*` перед `.env`). `fnmatch("data.env", ".env.*")` → **False** (требует точку после `.env`).

**Примеры bypass:**

| Имя файла | Blocked? | Почему |
|---|---|---|
| `.env` | ✅ заблокирован | точное совпадение |
| `.env.local` | ✅ заблокирован | `.env.*` |
| `secrets.md` | ✅ заблокирован | `secrets.*` |
| `data.env` | ❌ **пропускает** | `.env` не match, `.env.*` не match |
| `config.env` | ❌ **пропускает** | то же |
| `api_keys.md` | ❌ **пропускает** | не совпадает ни с одним паттерном |
| `my-secrets.md` | ❌ **пропускает** | `secrets.*` не match (нет `*secrets*`) |
| `passwords.txt` | ❌ **пропускает** | нет паттерна для `password*` |
| `auth_tokens.json` | ❌ **пропускает** | нет паттерна |

**Exploit scenario (через `save`):**

```bash
python reefiki.py --project myproject save "data.env"
# data.env содержит DATABASE_URL=postgres://user:pass@host/db
# → classify_path("data.env") → True, "ok"  ← BYPASS
# → Скопирован в inbox/
# → build_index → проиндексирован в SQLite
# → DATABASE_URL попал в FTS5 body
```

**Exploit scenario (через `harvest-commit`):**

```bash
# В harvest-commit нет НИКАКОЙ проверки расширений/имён
python reefiki.py --project myproject harvest-commit \
    --path "projects/myproject/wiki/config.env" \
    --message "add config"
# → path проверяется только на префикс projects/myproject/wiki/ → pass
# → файл закоммичен в git history
```

**Решения:**

1. Расширить `SECRET_PATTERNS`:
```python
SECRET_PATTERNS = [
    ".env", ".env.*", "*.env",      # ← добавить *.env
    "*secret*",                      # ← добавить
    "*credential*",                  # ← добавить
    "*password*",                    # ← добавить
    "*api_key*", "*api-key*",        # ← добавить
    "*token*",                       # ← можно, осторожно (много ложных срабатываний)
    "secrets.*", "credentials.*",
    "id_rsa", "id_rsa.pub", "*.pem",
    "*.key", "*.pfx", "*.p12",
    ".npmrc", ".netrc",
]
```

2. Добавить проверку расширений и имён в `harvest_commit_payload`:
```python
for path in normalized_paths:
    name = Path(path).name
    _, reason = classify_path_name(name)   # только name-check без fs access
    if reason != "ok":
        return 1, {**base_payload, "outcome": "block", "reason": reason, "blocking_paths": [path]}
```

**Сложность: S**

---

### SEC-010 — Отсутствие контентного сканирования секретов перед публикацией в public remote
> **Severity: HIGH**

**Описание:**

`push_public_snapshot()` исключает только **директории приватных проектов** по имени. Содержимое публикуемых файлов **не проверяется** на наличие секретов:

```python
def push_public_snapshot(repo: Path, public_remote: str, private_projects: list[str]) -> None:
    with tempfile.TemporaryDirectory(...) as tempdir:
        # ...
        require_git_success(run_git(snapshot, ["add", "-A"]), ...)
        for name in private_projects:
            require_git_success(run_git(snapshot, ["rm", "-r", "--cached", f"projects/{name}"]), ...)
        # ← Нет сканирования содержимого файлов!
        staged = ...
        leaked = [path for path in staged.splitlines()
                  if any(path.startswith(f"projects/{name}/") for name in private_projects)]
        # ← Проверяется только path, не content
        require_git_success(run_git(snapshot, ["commit", ...], "..."))
        require_git_success(run_git(snapshot, ["push", public_remote, "HEAD:main", "--force-with-lease"]), ...)
```

`PolicySafetyLayer.SECRET_PATTERNS` существует в `reefiki_memory/__init__.py` и используется в `memory_preflight()` — но **не вызывается** в publish pipeline.

**Exploit scenario:**

```markdown
<!-- projects/public-project/wiki/synthesis/api-notes.md -->
---
id: api-notes
title: API Integration Notes
---

Working notes on external APIs.

Temporary credential placeholder for testing: <redacted-demo-key>

Will clean up before publishing...
```

```bash
python reefiki.py --project public-project harvest-commit \
    --path "projects/public-project/wiki/synthesis/api-notes.md" \
    --message "add api notes"

python reefiki.py publish-task --dry-run false
# push_public_snapshot запускается
# redacted demo key placeholder would be copied into public GitHub remote
```

**Решение — добавить content scan в `push_public_snapshot`:**

```python
import re

# Переиспользовать SECRET_PATTERNS из reefiki_memory или дублировать
_CONTENT_SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|password|secret|private[_-]?key)\b\s*[:=]\s*\S+"
)

def _scan_staged_content_for_secrets(snapshot: Path, staged_paths: list[str]) -> list[str]:
    """Return list of paths where file content contains secret-like patterns."""
    leaks: list[str] = []
    for rel_path in staged_paths:
        abs_path = snapshot / rel_path
        if not abs_path.is_file():
            continue
        try:
            text = abs_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _CONTENT_SECRET_RE.search(text):
            leaks.append(rel_path)
    return leaks

# В push_public_snapshot(), после удаления приватных проектов:
content_leaks = _scan_staged_content_for_secrets(snapshot, staged.splitlines())
if content_leaks:
    raise SystemExit(
        f"public snapshot contains secret-like content in:\n"
        + "\n".join(f"  {p}" for p in content_leaks)
    )
```

**Сложность: M** (нужно интегрировать, написать тесты)

---

### SEC-011 — Пустой файл `public-snapshot.private-projects.txt` → утечка всех проектов
> **Severity: HIGH**

**Описание:**

```python
def private_project_names(repo: Path) -> list[str]:
    config_path = repo / "scripts" / "public-snapshot.private-projects.txt"
    if not config_path.exists():
        return []   # ← если файл ОТСУТСТВУЕТ — нет приватных проектов!
    names: list[str] = []
    for line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            names.append(stripped)
    return names
```

Если файл:
- **Не существует** → возвращает `[]` → `classify_publish_diff` считает всё `"public-safe"` → `push_public_snapshot` с пустым `private_projects` → публикует **ВСЕ проекты** в public remote
- **Пуст** (только комментарии или whitespace) → то же

**Exploit scenario:**

```bash
# Разработчик удалил/не создал конфиг:
rm scripts/public-snapshot.private-projects.txt

# Запускает publish:
python scripts/reefiki.py publish-task
# → private_project_names() → []
# → classify_publish_diff([...], []) → "public-safe" (всё публично!)
# → push_public_snapshot с private_projects=[]
# → git add -A → всё попадает в public remote
# → projects/personal-notes/ публикован
# → projects/work-secrets/ публикован
```

**Решение — fail-safe default (запрещать, а не разрешать):**

```python
def private_project_names(repo: Path) -> list[str]:
    config_path = repo / "scripts" / "public-snapshot.private-projects.txt"
    if not config_path.exists():
        raise SystemExit(
            f"Missing: {config_path.relative_to(repo)}\n"
            "Create this file listing projects that must NOT be published.\n"
            "Leave empty only if ALL projects are intentionally public.\n"
            "To explicitly allow all-public: add a comment line '# all-public-intentional'"
        )
    names = [
        line.strip()
        for line in config_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return names
```

**Сложность: S**

---

## Шаг 7 — Безопасность git-истории

### 7.1 Механизмы защиты git-истории

| Механизм | Статус | Описание |
|---|---|---|
| `harvest-commit` изолированный index | ✅ | `GIT_INDEX_FILE` в tempdir — не трогает реальный git index |
| Prefix guard в `harvest_commit_payload` | ✅ | Только `projects/<target>/wiki/` проходит |
| `git push --force-with-lease` | ✅ | Блокирует force-push при расхождении remote |
| Append-only policy для опубликованных страниц | ✅ (задокументировано) | Редактирование опубликованного блокировано |
| Never-delete policy | ✅ (задокументировано) | Удаление страниц блокировано |
| Secret scanning в pre-commit | ❌ **ОТСУТСТВУЕТ** | |
| `git filter-branch` инструкции при утечке | ❌ **ОТСУТСТВУЕТ** | |

### 7.2 Анализ `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: check-yaml      # синтаксис YAML
      - id: trailing-whitespace
      - id: end-of-file-fixer

  - repo: local
    hooks:
      - id: reefiki-frontmatter
        entry: python scripts/validate_frontmatter.py  # ← 'python' не 'python3'
        language: python
        files: ^projects/.*/wiki/.*\.md$
```

Нет хуков: `detect-secrets`, `gitleaks`, `trufflehog`, `bandit`, `semgrep`.

---

### SEC-012 — Отсутствие secret-scanning хука в pre-commit
> **Severity: HIGH**

**Описание:**

Pre-commit конфиг не содержит ни одного инструмента для обнаружения секретов в коммитируемых файлах. Разработчик может случайно закоммитить API ключ в wiki-страницу — и это пройдёт через все хуки без ошибки.

**Exploit scenario:**

```markdown
<!-- projects/myproject/wiki/tools/openai-setup.md — случайно включён ключ -->
## Настройка OpenAI

redacted_demo_key = "<redacted-demo-key>"

Запомнить: использовать этот ключ для тестирования...
```

```bash
git add projects/myproject/wiki/tools/openai-setup.md
git commit -m "add openai setup notes"
# pre-commit запускается:
# ✓ check-yaml
# ✓ trailing-whitespace
# ✓ end-of-file-fixer
# ✓ reefiki-frontmatter
# ← Ни один хук не обнаружил sk-proj-... в содержимом
# Коммит проходит. Секрет в истории.
```

**Решение — добавить detect-secrets в pre-commit:**

```yaml
# .pre-commit-config.yaml — добавить:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: ^(\.reefiki/|tests/fixtures/)
```

Или gitleaks (более современный):
```yaml
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.1
    hooks:
      - id: gitleaks
```

**Создать baseline:**
```bash
detect-secrets scan > .secrets.baseline
git add .secrets.baseline
```

**Сложность: S**

---

### SEC-013 — Нет инструкций по удалению секретов из git-истории
> **Severity: MEDIUM**

Если секрет попал в `git log` — нет документированного процесса его удаления. Рекомендуется добавить в `AGENTS.md` раздел «История и безопасность»:

```markdown
## Если секрет попал в git history

1. Немедленно ротировать скомпрометированный секрет
2. Удалить из истории с помощью git-filter-repo:
   pip install git-filter-repo
   git filter-repo --invert-paths --path projects/myproject/wiki/file-with-secret.md

3. Force-push всех веток:
   git push origin --force --all

4. Для public remote — немедленно удалить и пересоздать
5. Проверить что GitHub не кешировал файл
```

**Сложность: M**

---

## Шаг 8 — Сетевое воздействие

### 8.1 HTTP-запросы

```python
# reefiki.py, единственный urllib импорт:
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
```

`urllib.request` НЕ импортирован. HTTP-запросы в коде отсутствуют:
- `save_source` для URL — пишет только URL как текст: `destination.write_text(f"{source}\n")` ✅
- Нет SSRF, нет HTTP-fetch, нет polling ✅

### 8.2 Listening ports

Нет HTTP-сервера, нет открытых портов ✅

### 8.3 git remote URLs

```python
# publish_task_payload():
require_git_success(run_git(repo, ["push", private_remote, f"HEAD:{branch}"]), ...)
require_git_success(run_git(repo, ["push", private_remote, "HEAD:main"]), ...)
require_git_success(run_git(snapshot, ["push", public_remote, "HEAD:main", "--force-with-lease"]), ...)
```

`private_remote` и `public_remote` — строки из CLI args. Git использует их для push. Если в config git remote URL содержит embedded credentials (`https://user:token@github.com/...`), `run_git` stderr при ошибке передаст URL в вывод CLI.

**Рекомендация:** использовать SSH remotes или GitHub CLI (gh) для push вместо HTTPS с токеном.

### 8.4 uvx memoir-ai — сетевые запросы

`uvx --from memoir-ai memoir` при отсутствии локального кеша:
1. Загружает `memoir-ai` с PyPI
2. Memoir может делать запросы к внешним API для AI-функций (зависит от конфигурации memoir store)
3. Нет документированного network isolation для memoir

**Нет телеметрии, нет phone-home в reefiki.py** ✅

---

## Шаг 9 — Права доступа к файлам

### 9.1 Создаваемые файлы и их permissions

| Файл/директория | Создаётся через | Permissions | Видимость |
|---|---|---|---|
| `wiki/*.md` | `path.write_text()` | umask-зависимо (типично 0644) | Группа/другие могут читать |
| `inbox/*.md` | `destination.write_text()` | umask-зависимо (0644) | Группа/другие могут читать |
| `.reefiki/index.sqlite` | `sqlite3.connect()` | umask-зависимо (0644) | Группа/другие могут читать |
| `tempfile.TemporaryDirectory` | `tempfile.TemporaryDirectory()` | 0700 (tempfile default) | ✅ только владелец |
| `log.md` | `log.open("a")` | umask-зависимо | Группа/другие могут читать |

**Нет ни одного вызова `os.chmod()` или `os.umask()`** в codebase.

---

### SEC-014 — SQLite index и wiki файлы читаемы другими пользователями на shared системах
> **Severity: LOW**

**Описание:**

На multi-user Linux системах (сервер, CI, shared workstation) с umask 0022:
- `wiki/*.md` создаются с permissions `0644` → `-rw-r--r--`
- `.reefiki/index.sqlite` создаётся с permissions `0644`

Любой другой пользователь на системе может прочитать весь wiki и FTS5-индекс.

**Exploit scenario:**

```bash
# Другой пользователь на сервере:
cat /home/alice/wiki/projects/myproject/wiki/synthesis/api-notes.md
sqlite3 /home/alice/wiki/.reefiki/index.sqlite "SELECT body FROM pages"
```

**Решение:**

```python
# В build_index() и create_inbox_dir():
import stat
db_path_obj = db_path(project)
db_path_obj.parent.mkdir(parents=True, exist_ok=True)
db_path_obj.parent.chmod(0o700)  # .reefiki/ только для владельца

# Или через umask в начале main():
import os
os.umask(0o077)  # все новые файлы 0600, директории 0700
```

**Сложность: S**

---

### 9.2 Временные файлы

```python
# harvest_commit_payload():
with tempfile.TemporaryDirectory(prefix="reefiki-harvest-index-") as tempdir:
    env["GIT_INDEX_FILE"] = str(Path(tempdir) / "index")
    # ... git operations ...
# ← автоматически удаляется при выходе из context manager ✅

# push_public_snapshot():
with tempfile.TemporaryDirectory(prefix="reefiki-public-snapshot-") as tempdir:
    # ... git worktree operations ...
    finally:
        run_git(repo, ["worktree", "remove", "--force", str(snapshot)])
# ← cleanup в finally + context manager ✅
```

Tempdir создаётся `tempfile.TemporaryDirectory()` → Python использует `os.makedirs(name, 0o700)` → только владелец имеет доступ ✅

---

## Шаг 10 — Privacy model

### 10.1 Три уровня приватности

```
private (нет публикации)   → проекты в public-snapshot.private-projects.txt
project (default)          → может публиковаться как wiki-страница
public  (публикуется)      → передаётся в public remote
```

### 10.2 Как работает preflight guard в memory layer

```python
# reefiki_memory/__init__.py, PolicySafetyLayer:
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|token|password|secret)\b\s*[:=]\s*\S+"),
]

def preflight(self, operation: str, scope: str, content: str) -> ...:
    if any(pattern.search(content) for pattern in self.SECRET_PATTERNS):
        blocking_reasons.append("secret_like_content")
    # ...
```

Этот guard проверяет `content` — строку, переданную в `memory route` / `memory preflight`. **Он не вызывается автоматически при записи wiki-файлов или коммитах.**

### 10.3 Data flow private → public без guard

```
publish_task_payload()
  → classify_publish_diff(changed_paths, private_projects)
    → проверяет: начинается ли путь с "projects/<private>/"
    → если нет → "public-safe"
  → push_public_snapshot()
    → исключает директории приватных проектов
    → НЕ сканирует содержимое файлов (SEC-010)
    → НЕ проверяет backlinks из публичных страниц на приватные данные
```

**Уязвимость:** публичная wiki-страница может содержать цитату или reference из приватного проекта. Такая страница пройдёт все path-based guards и будет опубликована.

### 10.4 `--base` pointing к приватной ветке

```python
# publish_task_payload(), строка 1363:
if not git_ref_exists(repo, base):
    return 1, {"outcome": "block", "reason": "base_ref_missing", ...}
# ...
changed_paths = git_changed_paths(repo, base)
```

`base` — это ref для вычисления diff. Если агент передаст `--base main~1000` (или любой другой существующий ref), `classify_publish_diff` посчитает все файлы от этого ref до HEAD. Если там окажутся файлы приватных проектов, `diff_class = "mixed"` → `push_public_snapshot` запустится. Но `push_public_snapshot` корректно удалит приватные директории перед push ✅.

Однако файлы вне `projects/` (например, `AGENTS.md`, `scripts/`) не удаляются при `push_public_snapshot` — они публикуются всегда.

---

### SEC-015 — `AGENTS.md` публикуется в public remote без проверок
> **Severity: MEDIUM**

**Описание:**

`push_public_snapshot` исключает только `projects/<private>/` директории. Файлы в корне репозитория — `AGENTS.md`, `README.md`, `scripts/` — публикуются полностью.

`AGENTS.md` (16 КБ) содержит:
- Детальные инструкции по архитектуре системы
- Описание private/public boundaries
- Имена проектов, стратегии работы с данными

Это само по себе не секрет, но `AGENTS.md` может содержать проектоспецифичные данные (имена клиентов, проектов, задач), которые не должны быть публичными.

**Решение — добавить exclusion list для `push_public_snapshot`:**

```python
# В конфиге или hardcoded:
PUBLIC_SNAPSHOT_EXCLUDES = [
    "AGENTS.md",          # project-specific agent instructions
    "scripts/public-snapshot.private-projects.txt",
]

# В push_public_snapshot():
for exclude in PUBLIC_SNAPSHOT_EXCLUDES:
    if (snapshot / exclude).exists():
        run_git(snapshot, ["rm", "--cached", exclude])
```

**Сложность: S**

---

### 10.5 Audit log publish операций

```python
# append_save_log() — только для 'save' команды:
def append_save_log(project: Path, source: str) -> None:
    log = project / "wiki" / "log.md"
    handle.write(f"\n## [{date.today().isoformat()}] /save | {source}\n")
```

**Для publish-task, harvest-commit, push_public_snapshot нет audit log.** Нет способа узнать: когда, что и куда публиковалось.

---

### SEC-016 — Отсутствие audit log для publish операций
> **Severity: MEDIUM**

**Решение:**

```python
# Добавить функцию:
def append_publish_log(repo: Path, action: str, detail: str) -> None:
    log = repo / "scripts" / "publish.log"
    with log.open("a", encoding="utf-8", newline="\n") as f:
        f.write(f"{datetime.now().isoformat()} | {action} | {detail}\n")
    # Не добавлять publish.log в git — он локальный

# В publish_task_payload():
append_publish_log(repo, "publish-task", f"branch={branch} diff_class={diff_class}")

# В push_public_snapshot():
append_publish_log(repo, "push-public-snapshot", f"remote={public_remote} paths={len(staged.splitlines())}")
```

**Сложность: S**

---

## Шаг 11 — Supply chain

### 11.1 Зависимости проекта

| Зависимость | Источник | Pinned? | Проверка целостности? |
|---|---|---|---|
| `stdlib` Python | CPython | ✅ (версия Python) | ✅ |
| `pre-commit-hooks v6.0.0` | GitHub | ✅ `rev: v6.0.0` | ❌ нет `rev:` SHA hash |
| `memoir-ai` (через uvx) | PyPI | ❌ **нет версии** | ❌ нет hash pinning |

### 11.2 memoir-ai — supply chain риск

```python
# reefiki.py, строка 1020–1023:
def _memoir_base_command(store: Path) -> list[str]:
    return ["uvx", "--from", "memoir-ai", "memoir", "--json", "--store", str(store)]
```

`uvx --from memoir-ai` — каждый раз загружает **последнюю версию** `memoir-ai` с PyPI (или из кеша uvx). Нет `memoir-ai==0.x.y` — нет pinning.

---

### SEC-017 — Непривязанная версия `memoir-ai` в `uvx`
> **Severity: MEDIUM**

**Exploit scenario:**

1. Злоумышленник публикует компрометированную `memoir-ai 2.0.0` на PyPI (typosquatting или компрометация аккаунта)
2. uvx кеш устарел → загружает 2.0.0
3. Новая версия memoir-ai при вызове исполняет произвольный код с правами пользователя

**Решение — пинить версию:**

```python
def _memoir_base_command(store: Path) -> list[str]:
    return ["uvx", "--from", "memoir-ai==0.5.2", "memoir", "--json", "--store", str(store)]
    #                                  ^^^^^^^^^^ пинить проверенную версию
```

И добавить в документацию:
```markdown
## Зависимости

- memoir-ai: 0.5.2 (проверена командой)
  Обновлять вручную после проверки changelog.
```

**Сложность: S**

---

### 11.3 pre-commit hooks — нет SHA pinning

```yaml
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v6.0.0   # ← tag, не SHA
```

Tags могут быть перемещены (force-tagged). Безопаснее использовать SHA коммита:

```yaml
  rev: 4b863f127cfb361d9f5cf76f7c77a7e3dd7b26b  # v6.0.0
```

**Сложность: S**

---

## Шаг 12 — Валидация YAML frontmatter

### 12.1 `parse_frontmatter()` — custom parser

```python
def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 4:]
    data: dict[str, object] = {}
    current_key = ""
    for line in raw.splitlines():
        key_match = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if key_match:
            current_key = key_match.group(1)
            value = key_match.group(2).strip()
            data[current_key] = parse_value(value)
            # ...
    return data, body
```

**`parse_value()` поддерживает только:**
- `None` (null/Null/NULL)
- `int` (только `.isdigit()` — только неотрицательные числа)
- Inline списки `[a, b, c]`
- Строки (strip кавычек)

**Не поддерживает:**
- Отрицательные числа (`-1` → строка)
- Float (`3.14` → строка)
- Bool (`true`/`false` → строки, не Python bool)
- Multiline strings (`|`, `>`)
- YAML anchors (`&anchor`, `*alias`)
- `!!python/object` — **НЕВОЗМОЖНО** (custom parser, не PyYAML) ✅

### 12.2 Code execution через YAML — НЕВОЗМОЖНО

**PyYAML не используется. `yaml.load()` не вызывается нигде.** Пользовательский parser в `parse_frontmatter()` обрабатывает только скалярные значения и простые списки. YAML-десериализация произвольных типов (`!!python/object/apply:os.system`) невозможна ✅.

### 12.3 Найденные проблемы парсера

---

### SEC-018 — Нет ограничения на размер frontmatter (DoS)
> **Severity: LOW**

```python
def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    # ← raw может быть сколь угодно большим: нет size check
    for line in raw.splitlines():   # ← O(N) итерация по всем строкам
```

Если wiki-файл содержит frontmatter в 50 МБ (или искусственно сгенерированный), `build_index` обработает его полностью.

**Решение:**

```python
MAX_FRONTMATTER_BYTES = 64 * 1024  # 64 KB
def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    if end > MAX_FRONTMATTER_BYTES:
        return {}, text  # или raise ValueError
    raw = text[4:end]
```

**Сложность: S**

---

## Шаг 13 — Denial of Service

### 13.1 Ограничения на размер файлов

| Место | Ограничение | Применяется к |
|---|---|---|
| `classify_path()`, строка 665 | `> 5 * 1024 * 1024` (5 МБ) | команда `save` — локальные файлы |
| `build_index()` / `iter_pages()` | ❌ **НЕТ** | индексирование wiki |
| `parse_frontmatter()` | ❌ **НЕТ** | parses everything |
| FTS5 body индексирование | ❌ **НЕТ** | SQLite поглотит всё |

**Дисбаланс:** `save` с 5МБ файлом заблокирован, но уже существующий 100МБ `.md` в `wiki/` будет полностью проиндексирован при `index`.

---

### SEC-019 — Нет ограничения размера файлов в `build_index`
> **Severity: LOW**

```python
# build_index(), строка 323:
for page in iter_pages(project):
    text = page.read_text(encoding="utf-8")   # ← нет size check
    fm, body = parse_frontmatter(text)
    # ...
    conn.execute("INSERT INTO ...", {..., "body": body})   # ← 100MB в SQLite
```

**Exploit scenario (через git):**

```bash
# Создать огромную wiki-страницу (вне reefiki CLI, через git напрямую):
python -c "print('---\nid: bomb\ntitle: x\n---\n' + 'x' * 50_000_000)" > projects/myproject/wiki/concepts/bomb.md
git add . && git commit -m "test"

python scripts/reefiki.py --project myproject index
# → read_text() читает 50 МБ
# → вставляет 50 МБ в SQLite FTS5 body
# → FTS5 индексирует 50 МБ → занимает несколько минут и сотни МБ в sqlite
```

**Решение:**

```python
# В build_index() iter_pages loop:
MAX_PAGE_SIZE = 1 * 1024 * 1024  # 1 MB
for page in iter_pages(project):
    if page.stat().st_size > MAX_PAGE_SIZE:
        # log предупреждение, пропустить или индексировать только frontmatter
        continue
    text = page.read_text(encoding="utf-8")
```

**Сложность: S**

---

### SEC-020 — Нет timeout на subprocess → зависание при недоступном remote
> **Severity: MEDIUM** (дублирует SEC-007)

Покрыто в SEC-007. Прямое отношение к DoS: `git push` к недоступному host блокирует весь процесс на неопределённое время.

---

### 13.2 Inbox flooding

```python
# save_source():
inbox_count = len([path for path in (project / "inbox").iterdir() if path.is_file()])
```

Нет ограничения на количество файлов в inbox. Можно добавлять бесконечно.

**Практическое влияние:** при `build_index` `iter_project_text_files()` включает `inbox/*.md`. Очень большой inbox замедляет индексирование.

**Решение:** предупреждение при inbox > N (например 500) — не блокирование, только warn.

---

## Итоговая таблица findings

| ID | Severity | Категория | Описание | Сложность |
|---|---|---|---|---|
| SEC-005 | **HIGH** | Path Traversal | `save_source` принимает `../` пути → копирование файлов вне project | S |
| SEC-009 | **HIGH** | Guard Bypass | `data.env`, `api_keys.md` и большинство нестандартных имён не блокируются `SECRET_PATTERNS` | S |
| SEC-010 | **HIGH** | Data Leakage | Content-based сканирование секретов отсутствует в publish pipeline | M |
| SEC-011 | **HIGH** | Data Leakage | Отсутствующий `public-snapshot.private-projects.txt` → ВСЕ проекты публикуются | S |
| SEC-012 | **HIGH** | Supply Chain / Git | Нет secret-scanning hook в pre-commit → секреты могут попасть в git history | S |
| SEC-003 | MEDIUM | DoS / Crash | `escape_fts()` передаёт raw query при пустых токенах → FTS5 OperationalError → crash | S |
| SEC-006 | MEDIUM | Path Traversal | Symlink traversal в `save_source` (нет `.resolve()`) | S |
| SEC-007 | MEDIUM | DoS | Нет `timeout=` на subprocess → бесконечное зависание | S |
| SEC-008 | MEDIUM | Robustness | `FileNotFoundError` при отсутствии `git`/`uvx` → неструктурированный crash | S |
| SEC-013 | MEDIUM | Git Safety | Нет инструкций по удалению секретов из git history | M |
| SEC-015 | MEDIUM | Data Leakage | `AGENTS.md` и другие корневые файлы публикуются без проверок | S |
| SEC-016 | MEDIUM | Audit | Нет audit log для publish операций | S |
| SEC-017 | MEDIUM | Supply Chain | `memoir-ai` без version pinning → risk PyPI compromise | S |
| SEC-001 | LOW | Config | Hardcoded личный Windows-путь как default для memoir store | S |
| SEC-002 | LOW | Secrets | `.gitignore` не покрывает `*.env` (только `.env` и `.env.*`) | S |
| SEC-004 | LOW | DoS | Нет верхнего ограничения на `--limit` в поиске | S |
| SEC-014 | LOW | Permissions | Wiki файлы и SQLite DB создаются с umask-зависимыми permissions (0644 на shared системах) | S |
| SEC-018 | LOW | DoS | Нет ограничения размера frontmatter → DoS через огромный YAML | S |
| SEC-019 | LOW | DoS | Нет ограничения размера файлов в `build_index` | S |

### Распределение по severity

```
CRITICAL:  0
HIGH:      5  (SEC-005, SEC-009, SEC-010, SEC-011, SEC-012)
MEDIUM:    8  (SEC-003, SEC-006, SEC-007, SEC-008, SEC-013, SEC-015, SEC-016, SEC-017)
LOW:       6  (SEC-001, SEC-002, SEC-004, SEC-014, SEC-018, SEC-019)
```

### Что работает хорошо ✅

| Механизм | Оценка |
|---|---|
| Все SQL запросы параметризованы (`?`) | ✅ SQL-инъекция невозможна |
| `harvest_commit_payload` с изолированным `GIT_INDEX_FILE` | ✅ не загрязняет реальный index |
| `guard_staged_payload` — prefix validation через `re.fullmatch` | ✅ target_project validated |
| `normalize_repo_path` — блокирует `../` в repo-relative путях | ✅ |
| `_resolve_project_path` — `.resolve()` + confinement check | ✅ для draft операций |
| Custom YAML parser — нет `yaml.load()`, нет !! exploitation | ✅ |
| `push_public_snapshot` — двойная проверка leaked paths | ✅ (path-based) |
| `git push --force-with-lease` | ✅ |
| Все subprocess — list form, `shell=False` | ✅ нет shell injection |
| tempfile с context manager → cleanup | ✅ |
| PolicySafetyLayer.SECRET_PATTERNS в memory preflight | ✅ (ограниченно) |

---

## Приоритизированный action plan

### Критичные (исправить немедленно)

```
1. SEC-011: fail-safe для public-snapshot.private-projects.txt (S, 1 строка)
2. SEC-005: добавить .resolve() + confinement check в classify_path (S, 5 строк)
3. SEC-012: добавить detect-secrets/gitleaks в pre-commit (S, 5 строк yaml)
```

### Важные (исправить в ближайшем релизе)

```
4. SEC-009: расширить SECRET_PATTERNS + добавить name-check в harvest-commit (S)
5. SEC-010: content scan в push_public_snapshot (M — требует тестирования)
6. SEC-007: добавить timeout= во все subprocess.run (S, 5 строк)
7. SEC-003: исправить escape_fts fallback + кавычить токены (S)
8. SEC-008: shutil.which() guards для git и uvx (S)
```

### Рекомендуемые улучшения

```
9.  SEC-017: пинить версию memoir-ai в uvx команде (S)
10. SEC-016: добавить publish audit log (S)
11. SEC-015: исключить AGENTS.md из public snapshot (S)
12. SEC-013: документировать git-filter-repo процесс (M)
13. SEC-002: добавить *.env в .gitignore (S)
14. SEC-001: убрать hardcoded Windows path (S)
```
