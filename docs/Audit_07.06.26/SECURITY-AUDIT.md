# Аудит безопасности REEFIKI

> **Дата:** 2026-06-02
> **Версия репозитория:** main @ latest
> **Инструменты:** ручной код-ревью + автоматизированный grep/scan
> **Охват:** scripts/reefiki.py (~3949 строк), scripts/reefiki_memory/\_\_init\_\_.py, scripts/validate_frontmatter.py, .gitignore, .pre-commit-config.yaml, AGENTS.md, CLAUDE.md

---

## Итоговая таблица: severity × category

| # | Категория | Severity | Краткое описание |
|---|-----------|----------|------------------|
| 4 | Path traversal / symlink | **HIGH** | `save_source()` и `plan_check()` не проверяют containment |
| 6 | Data leakage (publish-task) | **HIGH** | Нет content-scanning на секреты перед публикацией |
| 7 | Git history safety | **HIGH** | Нет secret-scanning hook'а в pre-commit |
| 10 | Privacy model | **HIGH** | `publish-task` не использует `memory_preflight`, privacy guard и publish-flow разорваны |
| 10 | Privacy model | **MEDIUM** | `--base` может указывать на приватную ветку без review |
| 10 | Privacy model | **MEDIUM** | Нет audit log для publish операций |
| 6 | Data leakage (publish-task) | **MEDIUM** | `.env`-подобные секреты обходятся переименованием |
| 6 | Data leakage (publish-task) | **MEDIUM** | Inline API keys в markdown не отсекаются |
| 2 | Secrets & credentials | **MEDIUM** | `.gitignore` защищает только по именам файлов |
| 12 | YAML validation | **MEDIUM** | Кастомный парсер ломает вложенные/сложные YAML-структуры |
| 9 | File permissions | **MEDIUM** | `.reefiki/index.sqlite` без явного hardening |
| 8 | Network exposure | **MEDIUM** | `uvx memoir-ai` — внешняя сеть и supply-chain поверхность |
| 13 | Denial of Service | **HIGH** | Нет лимитов на размер/число файлов при индексировании |
| 13 | Denial of Service | **MEDIUM** | SQLite/FTS5 может расти без ограничений |
| 13 | Denial of Service | **MEDIUM** | subprocess.run() без timeout |
| 5 | Subprocess security | **LOW** | Нет timeout и лимитов на размер output |
| 11 | Supply chain | **LOW** | `memoir-ai` не зафиксирована в lockfile |
| 8 | Network exposure | **LOW** | Push-remote не валидируется |
| 9 | File permissions | **LOW** | Все write-файлы с default mode |
| 3 | SQL injection / FTS5 | **INFO** | Классической SQL-инъекции не найдено |
| 1 | Data inventory | **INFO** | Данные: wiki, plans, inbox, seen, SQLite-индекс |
| 2 | Secrets & credentials | **INFO** | Hardcoded secrets не найдены |

---

## Шаг 1: Инвентаризация данных

### Что хранится

- **Wiki-страницы** `projects/<name>/wiki/*.md` — Markdown + YAML frontmatter
- **Входящие** `projects/<name>/inbox/` — исходные файлы, копируемые командой `/save`
- **Просмотренные** `projects/<name>/seen/` — обработанные inbox-файлы
- **Лог действий** `projects/<name>/wiki/log.md` — append-only Markdown
- **Планы** `projects/<name>/plans/*.md` — Markdown
- **Индекс поиска** `projects/<name>/.reefiki/index.sqlite` — SQLite + FTS5 (не в git, `.reefiki/` в .gitignore)

### Форматы

- Markdown + YAML frontmatter (wiki, plans, log)
- Text/binary (inbox, seen — оригинальные файлы)
- SQLite FTS5 (поисковый индекс)

### Структура SQLite FTS5

```
Таблица pages:   id, title, type, tags, useful_when, sources, file, date_added, use_count, last_used, body, sha256
Индекс pages_fts: id, title, tags, useful_when, body
Таблица chunks:  page_id, heading_path, content, file, start_line
Индекс chunks_fts: page_id, heading_path, content
Таблица links:   source_id, target_id, kind, resolved, file, line
```

### Что попадает в git history

Все committed markdown-артефакты: wiki, log, планы, public snapshot. `index.sqlite` НЕ попадает (`.reefiki/` в .gitignore).

### Сенситивность

Потенциально: личные заметки, ссылки, выводы сессий, пути к локальным файлам, содержимое файлов из `/save`. SQLite-индекс дублирует текст wiki.

---

## Шаг 2: Secrets и credentials

**Severity: INFO** — Hardcoded secrets не найдены.

- Поиск по `api_key/token/password/secret/credential/auth` — совпадений в коде нет
- Нет явной загрузки `.env`-файлов; используется только `os.environ`
- `.env.example` отсутствует

**Severity: MEDIUM** — `.gitignore` защищает только по именам файлов.

- Файл: `.gitignore:19-25`
- Игнорирует: `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`
- **Не защищает** от секретов, встроенных в обычные `.md`/`.txt` файлы

**Exploit:** агент сохраняет API key в wiki-странице → файл не блокируется `.gitignore` → попадает в commit и public snapshot.

**Решение:** добавить content-based secret scanning для markdown/logs/plans перед commit/push.
**Сложность:** M

---

## Шаг 3: SQL injection / FTS5

**Severity: INFO** — Классической SQL-инъекции не найдено.

- FTS-запросы параметризованы через `MATCH ?`, не конкатенацией
- `LIMIT` передаётся параметром
- Динамические части SQL ограничены фиксированными значениями (`pages_fts`/`chunks_fts`)

**`escape_fts()` — `scripts/reefiki.py:439-443`:**
- Извлекает только `\w+` токены и соединяет через `OR`
- Пользователь не может вставить операторы `NEAR`, кавычки, SQL-метки: они вырезаются regex'ом

**Обработка ошибок SQLite:**
- `search_existing()` ловит `sqlite3.OperationalError`
- При `"no such table"` индекс пересобирается и поиск повторяется
- Другие ошибки не маскируются

**Решение:** текущая реализация безопасна; усилить можно тестами на FTS5-операторные payloads.
**Сложность:** S

---

## Шаг 4: Path traversal

### **Severity: HIGH — Path traversal при чтении/копировании локальных файлов**

- Файл: `scripts/reefiki.py:644-667, 721-725, 826-866, 905-920`
- `save_source()` принимает `source` от пользователя/агента
- Если путь не абсолютный, делает `path = project / path`, но **не проверяет**, что результат внутри проекта
- Затем читает `path.read_bytes()` и пишет в `inbox/`
- `plan_check()` тоже читает `path_arg` без проверки containment

**Exploit:** агент передаёт `../../.ssh/id_rsa` → код читает и копирует в `inbox/` → может попасть в git history.

### **Symlink attacks**

- Нет проверки на symlink для входных/выходных артефактов
- Если `inbox/`, `plans/` или `wiki/log.md` подменены symlink'ом, запись может уйти наружу

### Позитивный момент

- `harvest-commit` scope защищён: нормализация путей и проверка префикса `projects/<target>/wiki/`

**Решение:**
- Перед чтением/записью делать `resolve()` + проверка `is_relative_to(project.resolve())`
- Запретить symlink-пути для входных/выходных артефактов

**Сложность:** M

---

## Шаг 5: Subprocess security

**Severity: INFO** — `subprocess.run()` в list form, без `shell=True`.

- Явного shell injection-паттерна нет
- Аргументы идут в argv, не в shell-строку

**Severity: LOW** — Нет timeout и лимитов на размер output.

- Файл: `scripts/reefiki.py:1030-1087, 1203-1248, 1409-1447`
- `run_memoir()`, `git_*` helpers, validator-bridge и push/commit flows используют `capture_output=True`, но без `timeout=`

**Exploit:** зависший внешний инструмент блокирует выполнение или съедает память.

**Решение:** добавить `timeout=`, стримить большие выводы, нормализовать ошибки.
**Сложность:** S/M

---

## Шаг 6: Data leakage через publish-task

### **Severity: HIGH — Нет content-scanning на секреты перед публикацией**

- Файл: `scripts/reefiki.py:1124-1256, 1171-1177, 1185-1198, 1219-1248`
- Guard проверяет только префикс `projects/<target>/wiki/` и staged paths
- Содержимое файлов **не анализируется**

**Exploit:** API key в markdown-файле внутри разрешённого wiki-пути будет принят и закоммичен.

**Решение:** content-scanning на staged-файлы (regex/secret-scanner).
**Сложность:** M

### **Severity: MEDIUM — `.env`-подобные секреты обходятся переименованием**

- Файл: `scripts/reefiki.py:79-92, 644-667`; `.gitignore:19-26`
- `data.env`, `config.env.backup`, `prod.credentials.env` не совпадают с шаблонами

**Решение:** расширить denylist (`*.env*`, `*.secret*`, `*.credentials*`) + content scan.
**Сложность:** S

### **Severity: MEDIUM — Inline API keys в markdown не отсекаются**

- Файл: `scripts/reefiki.py:1171-1248, 645-667`
- Нет проверки содержимого `.md` на секреты

**Решение:** запускать content scan перед publish-task и harvest-commit.
**Сложность:** M

---

## Шаг 7: Git history safety

### **Severity: HIGH — Нет secret-scanning hook'а**

- Файл: `.pre-commit-config.yaml:1-20`
- Есть только `check-yaml`, whitespace и frontmatter validator
- Нет `detect-secrets`, `gitleaks`, `trufflehog`

**Решение:** добавить pre-commit hook для secret scanning + CI job.
**Сложность:** M

### **Severity: MEDIUM — История git не защищена от уже закоммиченных секретов**

- Нет механизма history scanning / rewrite workflow
- В `.git/hooks` только стандартные `.sample`

**Решение:** документировать процедуру: rotate → `git filter-repo`/BFG → force-push.
**Сложность:** M

### **Severity: LOW — `.gitignore` — лишь safety net**

- Не предотвращает добавление уже tracked файла или обход через переименование

**Решение:** сочетать с pre-commit/CI secret scanning.
**Сложность:** S

---

## Шаг 8: Network exposure

### **Severity: MEDIUM — `uvx --from memoir-ai memoir` — внешняя сеть**

- Файл: `scripts/reefiki.py:1018-1052`
- `_memoir_base_command()` запускает `uvx --from memoir-ai memoir --json ...`
- Потенциально тянет пакет из сети

**Решение:** pin/вендоринг зависимости, offline mode, allowlist для сетевых вызовов.
**Сложность:** M

### **Severity: LOW — Push-remote не валидируется**

- Файл: `scripts/reefiki.py:1409-1415`
- Не проверяет URL remote'а на embedded credentials или неожиданный хост

**Решение:** проверять `git remote get-url`, запрещать credentials в URL, allowlist host'ов.
**Сложность:** S

### **Severity: INFO — Телеметрия не найдена**

- Нет `requests/aiohttp/httpx/urllib` клиентов в коде

---

## Шаг 9: Права доступа к файлам

### **Severity: MEDIUM — SQLite без hardening permissions**

- Файл: `scripts/reefiki.py:247-260, 322-340`
- `.reefiki/index.sqlite` создаётся без `chmod`, `umask` или ACL
- На multi-user системе другой пользователь может прочитать индекс

**Решение:** после создания выставлять `0600`, либо хранить в user-private directory.
**Сложность:** M

### **Severity: LOW — Все write-файлы с default mode**

- Файл: `scripts/reefiki.py:855-861, 3315-3360, 3570-3613, 3477-3483`
- `Path.write_text()`/`write_bytes()` без явной настройки прав

**Позитивное:** temp-каталоги удаляются через `TemporaryDirectory` и `finally: worktree remove`.

**Решение:** policy на права файлов/директорий.
**Сложность:** S/M

---

## Шаг 10: Privacy model (private/project/public tiers)

### **Severity: HIGH — Privacy guard и publish-flow разорваны**

- Файл: `scripts/reefiki.py:1342-1415, 1858-1901`
- `memory_preflight()` принимает `visibility` как параметр, но `publish-task` его **не использует**
- `publish_task_payload()` делает только path-prefix classification

**Exploit:** приватная ветка с чувствительным контентом в "публичных" путях пройдёт как `public-safe` и будет отправлена в public remote.

**Решение:** перед public push запускать privacy preflight + content scan + explicit review gate.
**Сложность:** L

### **Severity: MEDIUM — `--base` может указывать на приватную ветку**

- Файл: `scripts/reefiki.py:1363-1415, 3667-3674`
- Проверяется только существование и ancestry, не privacy-смысл ref'а

**Решение:** связать `base` с политикой приватности.
**Сложность:** M

### **Severity: MEDIUM — Нет audit log для publish операций**

- Файл: `scripts/reefiki.py:1388-1415, 1450-1475`
- `publish-task` печатает payload, но не пишет в `wiki/log.md` или audit trail
- Для `save`, `reject`, `prune` лог есть, для публикации — нет

**Решение:** писать запись в audit log: branch, base, remote, diff_class, actions, outcome, actor, timestamp.
**Сложность:** S/M

---

## Шаг 11: Dependency supply chain

### **Severity: LOW — `memoir-ai` не зафиксирована**

- Файл: `scripts/reefiki.py:1018-1052`
- Нет `pyproject.toml`, `requirements*.txt` или `*.lock`
- `uvx --from memoir-ai memoir` — нет pinning версии/хэша

**Exploit:** компрометация пакета в PyPI, неожиданный апгрейд, yanked-релиз.

**Решение:** зафиксировать версию (lockfile, exact version pin, hashes).
**Сложность:** S

---

## Шаг 12: Input validation (YAML frontmatter)

### **Severity: MEDIUM — Кастомный парсер не является YAML-парсером**

- Файл: `scripts/reefiki.py:138-173`, `scripts/validate_frontmatter.py:69-92, 110-281`
- `parse_frontmatter()` разбирает только `key: value` и простые списки
- Nested mappings, anchors/aliases, multiline scalars не поддерживаются
- Broken YAML может быть частично принят

**Позитивное:** прямого RCE через `!!python/object` нет — PyYAML не используется, такие теги трактуются как обычный текст.

**Решение:** перейти на `safe_load` + явную схему/JSON-schema валидацию + лимиты на размер/число полей.
**Сложность:** M

---

## Шаг 13: Denial of Service

### **Severity: HIGH — Нет лимитов на размер/число файлов**

- Файл: `scripts/reefiki.py:238-244, 257-365, 705-785`
- Скрипт читает файлы целиком через `read_text()`
- Нет лимита на размер файла, число файлов в inbox/seen/wiki
- Эвристика `large-file > 5MB` в `classify_path()` не защищает build/index/status/dedup

**Exploit:** один файл 500MB или 100K файлов в inbox → OOM или hang.

**Решение:** hard caps на размер файла, суммарный объём, число файлов; инкрементальный индекс.
**Сложность:** M

### **Severity: MEDIUM — SQLite/FTS5 может расти без ограничений**

- Файл: `scripts/reefiki.py:257-317, 341-365, 528-557`
- Индекс пересобирается целиком без квот
- WAL может раздуваться при частых операциях

**Решение:** лимитировать объём данных, контроль размера БД/WAL, периодический checkpoint/vacuum.
**Сложность:** M

### **Severity: MEDIUM — subprocess.run() без timeout**

- Файл: `scripts/reefiki.py:1030-1052, 1055-1088, 1200-1217, 2178-2189`
- `uvx`, `git`, validator — без `timeout=`

**Решение:** добавить таймауты, retry-policy, понятные ошибки.
**Сложность:** S

---

## Рекомендации по приоритету исправлений

### Приоритет 1 (CRITICAL/HIGH, выполнить немедленно)

1. **Path traversal** — `resolve()` + containment check в `save_source()` и `plan_check()`
2. **Content-based secret scanning** — перед commit/push проверять содержимое файлов
3. **Pre-commit secret hook** — добавить `detect-secrets` или `gitleaks`
4. **Privacy preflight в publish-task** — интегрировать `memory_preflight` перед public push

### Приоритет 2 (MEDIUM, выполнить в ближайшее время)

5. Расширить denylist для `.env`-подобных файлов (`*.env*`, `*.secret*`)
6. Audit log для publish операций
7. File permissions hardening для `.reefiki/`
8. Лимиты на размер файлов и число файлов при индексировании
9. Timeout для subprocess вызовов
10. YAML-валидация: перейти на `safe_load` + schema

### Приоритет 3 (LOW/INFO, запланировать)

11. Dependency pinning для `memoir-ai`
12. Remote URL validation перед push
13. `.env.example` с placeholder'ами
14. Тесты на FTS5-операторные payloads
15. Процедура incident response для секретов в git history
