# REEFIKI Backup, Recovery & Disaster Resilience Audit

> Аудит: 2026-06-02
> Репозиторий: `/tmp/reefiki`
> Основной скрипт: `scripts/reefiki.py` (3949 строк)
> Модуль: `scripts/reefiki_memory/__init__.py` (285 строк)

---

## Архитектурный контекст

REEFIKI — это «knowledge control plane». Данные хранятся на трёх уровнях:

| Уровень | Хранилище | Версионирование | Backup |
|---------|-----------|-----------------|--------|
| Wiki-страницы (Markdown) | `projects/<name>/wiki/**/*.md` | Git (commits) | Git remote |
| Поисковый индекс | `projects/<name>/.reefiki/index.sqlite` | Нет (rebuilt from Markdown) | Нет (gitignored) |
| Memoir-AI (working memory) | `C:\Users\kissl\.codex\memoir-stores\reefiki` (ENV override) | Неизвестно | Нет |

Дизайн-доктрина из docstring (строка 5-6):
> *«Markdown stays the source of truth. The SQLite database under .reefiki/ is a rebuildable search/cache layer.»*

---

## Finding 1: SQLite-индекс — нет integrity verification

**Описание:** `build_index()` (строка 257) полностью пересоздаёт БД: DROP TABLE + CREATE TABLE + INSERT. Нигде не вызывается `PRAGMA integrity_check`, нет проверки целостности после записи, нет checksum верификации записанных данных.

**Severity:** 🟡 Medium

**Сценарий эксплуатации:**
1. Процесс прерывается во время `build_index()` (kill, OOM, power loss).
2. SQLite WAL-файл остаётся незакоммиченным.
3. Следующий `search()` находит БД (файл существует), но таблицы могут быть неполными или отсутствовать.
4. `search_existing()` ловит `sqlite3.OperationalError: no such table` (строка 552) и перестраивает — **это работает**.
5. Но если таблицы существуют, но данные неполные — ошибки НЕ будет, поиск вернёт неполные результаты молча.

**Исправление:** Добавить `PRAGMA integrity_check` при открытии существующей БД; если fail — автоматический rebuild.

**Сложность:** 🟢 Low (5-10 строк кода)

---

## Finding 2: Нет backup механизма для SQLite WAL-файла

**Описание:** `PRAGMA journal_mode=WAL` (строка 260) используется при каждом `build_index()`. WAL-файл (`.reefiki/index.sqlite-wal`) может расти indefinitely если checkpoint не происходит. SQLite checkpointing happens automatically, but if the process crashes between a WAL write and checkpoint, data in WAL may be lost or orphaned.

**Severity:** 🟢 Low

**Сценарий эксплуатации:**
1. `build_index()` записывает данные в WAL.
2. Процесс умирает до checkpoint.
3. При следующем открытии SQLite автоматически replay WAL → данные восстанавливаются.
4. Если WAL-файл удалён вручную — теряются незакоммиченные транзакции, но `build_index()` вызовется заново.

**Вывод:** WAL-handling корректен для rebuildable cache. Нет реальной проблемы.

**Исправление:** Не требуется (SQLite auto-checkpoint достаточен для кэша).

**Сложность:** N/A

---

## Finding 3: .reefiki/ директория gitignored — нет remote backup индекса

**Описание:** `.gitignore` (строка 60) содержит `.reefiki/`. SQLite-индекс никогда не попадает в git.

**Severity:** 🟢 Low (by design)

**Сценарий эксплуатации:**
1. Удаляется `.reefiki/index.sqlite` (случайно, rm -rf, файловая ошибка).
2. Следующий вызов `search()` проверяет `database.exists()` (строка 458) → вызывает `build_index()`.
3. Индекс перестраивается из Markdown-файлов (~секунды для малых проектов, минуты для больших).

**Вывод:** Это **ожидаемое поведение** — индекс восстанавливаем из source of truth. Нет потери данных.

**Исправление:** Не требуется.

**Сложность:** N/A

---

## Finding 4: Git force-push на public remote — потенциальная потеря истории

**Описание:** `push_public_snapshot()` (строка 1418) выполняет:
```python
run_git(snapshot, ["push", public_remote, "HEAD:main", "--force-with-lease"])
```
Каждый публичный snapshot создаёт orphan branch с уникальным именем (`public-snapshot-{timestamp}`) и force-pushes на `main`. Предыдущая история public remote **полностью заменяется**.

**Severity:** 🟡 Medium

**Сценарий эксплуатации:**
1. Public remote — это «зеркало» для внешних потребителей.
2. Каждый force-push уничтожает предыдущий public main.
3. Если случайно удалили private project из `private-projects.txt` — он попадёт в public snapshot.
4. Нет механизма «откатить» public remote к предыдущему состоянию.

**Защитные меры:**
- `--force-with-lease` (не `--force`) — защищает от перезаписи чужих push-ей.
- Leak detection (строка 1434-1440): проверяет что private paths не попали в snapshot.
- Private remote push (строка 1409-1411) — обычный push, не force.

**Исправление:** Добавить tag перед force-push для отката; рассмотреть squash-merge вместо orphan branch.

**Сложность:** 🟡 Medium (архитектурное решение)

---

## Finding 5: Нет backup механизма для memoir-ai store

**Описание:** `GLOBAL_MEMOIR_STORE` (строка 133-134) указывает на `C:\Users\kissl\.codex\memoir-stores\reefiki` (Windows path hardcoded по умолчанию). Memoir-AI — внешний инструмент (`uvx --from memoir-ai memoir`), его store не versioned, не backed up, не в git.

**Severity:** 🔴 High

**Сценарий эксплуатации:**
1. Memoir store хранит «working memory» — промежуточные знания, которые ещё не promoted в wiki.
2. Если memoir store утерян (disk failure, accidental deletion, machine loss) — все working memories исчезают навсегда.
3. Нет export/import команд.
4. Нет связи между memoir memories и git commits.

**Исправление:**
- Добавить `reefiki memory export` / `reefiki memory import` команды.
- Periodic snapshot memoir store в `.reefiki/` или отдельный git repo.
- Документировать memoir store location и backup procedure.

**Сложность:** 🟡 Medium

---

## Finding 6: Нет documented recovery procedures

**Описание:** В README.md, COMMANDS.md, ROADMAP.md — нет упоминаний backup, recovery, restore, disaster. Единственная «recovery hint» — в шаблоне плана (строка 895-897):
```
## Recovery Notes
Read this file, `wiki/log.md`, and changed files before resuming.
```

**Severity:** 🟡 Medium

**Сценарий эксплуатации:**
1. Пользователь теряет данные и ищет инструкции по восстановлению.
2. Документации нет → восстановление через trial-and-error.
3. Для неопытного пользователя — потеря данных может быть permanent.

**Исправление:** Добавить раздел `RECOVERY.md` с процедурами:
- Восстановление wiki из git history
- Перестройка SQLite индекса (`reefiki index`)
- Восстановление из remote
- Проверка целостности

**Сложность:** 🟢 Low (документация)

---

## Finding 7: Wiki page overwrite — защита только через git history

**Описание:** Нет in-place versioning для wiki-страниц. `build_index()` (строка 339) сохраняет SHA256 каждой страницы, но это read-only checksum (для поиска дубликатов), не защита от overwrite. Единственная защита — git history.

**Severity:** 🟢 Low

**Сценарий эксплуатации:**
1. Агент или пользователь случайно перезаписывает wiki-страницу.
2. Если это произошло до git commit — предыдущая версия потеряна.
3. Если после git commit — можно восстановить через `git checkout HEAD~1 -- path`.

**Защитные меры:**
- Git commits (harvest workflow, строка 1245)
- Pre-commit hooks (validate_frontmatter)
- SHA256 в plan_check (строка 905-920) для plans

**Исправление:** Рассмотреть periodic auto-commit или файловые .bak копии для критических страниц.

**Сложность:** 🟡 Medium

---

## Finding 8: Удаление projects/<name>/ — восстановление из git

**Описание:** Весь контент проекта (wiki, inbox, plans) хранится в `projects/<name>/` и tracked в git. Удаление директории = потеря рабочей копии, но данные остаются в git history.

**Severity:** 🟢 Low

**Сценарий эксплуатации:**
1. `rm -rf projects/myproject/` — все файлы удалены локально.
2. `git checkout HEAD -- projects/myproject/` — восстановление из последнего commit.
3. Если не было commit — данные потеряны (только в рабочей копии).

**Исправление:** Не требуется (git protection достаточен при регулярных commits).

**Сложность:** N/A

---

## Finding 9: Нет health check / integrity verification tooling

**Описание:** Команда `reefiki status` (строка 769) показывает inbox count, stale pages, last lint — но не проверяет:
- Целостность SQLite (`PRAGMA integrity_check`)
- Консистентность индекса vs Markdown файлов (SHA256 mismatch)
- Статус memoir store
- Размер WAL-файла
- Наличие broken wiki links

**Severity:** 🟡 Medium

**Сценарий эксплуатации:**
1. SQLite повреждается тихо (bit rot, partial write).
2. `status` не обнаруживает проблему.
3. Поиск возвращает неполные/некорректные результаты.
4. Пользователь не знает что данные ненадёжны.

**Исправление:** Добавить `reefiki health` команду с:
- `PRAGMA integrity_check`
- SHA256 comparison: index vs actual files
- Memoir store connectivity check
- Broken link detection
- WAL file size check

**Сложность:** 🟡 Medium

---

## Finding 10: harvest_commit — temporary index pattern (хорошо!)

**Описание:** `harvest_commit_payload()` (строка ~1180-1256) использует temporary git index (`GIT_INDEX_FILE`) для staging коммитов. Это предотвращает загрязнение основного index. Scope validation (строка 1225-1232) гарантирует что только нужные файлы попадают в коммит.

**Severity:** ✅ Positive finding

---

## Сводная таблица

| # | Finding | Severity | Fix Complexity |
|---|---------|----------|---------------|
| 1 | Нет integrity verification для SQLite | 🟡 Medium | 🟢 Low |
| 2 | WAL-файл handling | 🟢 Low | N/A (OK) |
| 3 | .reefiki/ gitignored | 🟢 Low | N/A (by design) |
| 4 | Public remote force-push | 🟡 Medium | 🟡 Medium |
| 5 | **Нет backup для memoir-ai store** | 🔴 High | 🟡 Medium |
| 6 | Нет documented recovery procedures | 🟡 Medium | 🟢 Low |
| 7 | Wiki page overwrite protection | 🟢 Low | 🟡 Medium |
| 8 | Удаление project directory | 🟢 Low | N/A (git) |
| 9 | Нет health check tooling | 🟡 Medium | 🟡 Medium |
| 10 | Temporary index pattern (positive) | ✅ Good | N/A |

---

## Приоритетные рекомендации

### P0 — Критично
1. **Memoir store backup:** Добавить экспорт/импорт memoir-ai данных. Это единственный компонент с непосредственной потерей данных при сбое.

### P1 — Важно
2. **Health check команда:** `reefiki health` с integrity_check, SHA256 consistency, WAL status.
3. **Recovery documentation:** REEFIKI-RECOVERY.md с пошаговыми инструкциями.

### P2 — Желательно
4. **SQLite integrity check** при каждом открытии существующей БД.
5. **Public snapshot tagging** для возможности отката.
6. **Wiki versioning** — periodic auto-commit или .bak для критических страниц.
