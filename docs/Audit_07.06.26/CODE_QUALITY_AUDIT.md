# 🔍 REEFIKI Code Quality & Technical Debt Audit

**Файл:** `scripts/reefiki.py` — **3949 строк**, **126 функций**
**Дата:** 2026-06-02

---

## 1. Монолитный файл: 3949 строк в одном модуле

**Severity: CRITICAL**

**Описание:** Весь основной скрипт — один файл на 3949 строк с 126 функциями. Это делает код крайне сложным для навигации, ревью, тестирования и параллельной работы нескольких разработчиков. Средняя длина файла в Python-проектах — 200-400 строк; всё свыше 1000 считается проблемным.

**Статистика:**
- Всего функций: **126**
- Функций > 50 строк: **16**
- Функций > 100 строк: **5**
- Самая большая функция: `main()` — **319 строк**

**Исправление:** Разделить на 6-8 модулей:

| Модуль | Содержимое | Примерные строки |
|--------|-----------|-----------------|
| `cli.py` | `main()`, argparse, print_* функции | ~800 |
| `memory.py` | `memory_route`, `memory_preflight`, `memory_pack`, `memory_explain`, `memory_status`, `global_lookup` | ~600 |
| `promotion.py` | `promotion_dry_run`, `promotion_inbox`, `apply_promotion_draft`, `write_promotion_draft`, draft management | ~400 |
| `review.py` | `review_queue_scan`, `build_backlink_index`, `write_review_queue_report` | ~300 |
| `index.py` | `build_index`, `search`, `search_existing`, `db_path` | ~400 |
| `git_ops.py` | `harvest_commit_payload`, `publish_task_payload`, `_run_git`, `memory_diff` | ~400 |
| `golden.py` | `run_golden_queries` | ~150 |
| `utils.py` | `as_text`, `parse_frontmatter`, `slugify`, `project_root`, `repo_root` | ~300 |

**Сложность исправления:** ВЫСОКАЯ — требует осторожного рефакторинга с сохранением всех импортов и тестов.

---

## 2. Функция `main()` на 319 строк — мега-диспетчер

**Severity: HIGH**

**Описание:** Функция `main()` (строки 3627-3945) содержит:
- **~140 строк** определения argparse (один гигантский блок)
- **~120 строк** цепочки `if args.cmd == ...` диспетчеризации
- Прямой вызов бизнес-логики из CLI-диспетчера

**Исправление:**
1. Вынести argparse в отдельную функцию `_build_parser()` → `cli/parser.py`
2. Использовать dict-диспетчер вместо цепочки if:
```python
HANDLERS = {
    "index": handle_index,
    "search": handle_search,
    ...
}
handler = HANDLERS.get(args.cmd)
return handler(args) if handler else 2
```

**Сложность:** СРЕДНЯЯ

---

## 3. Дублирование: json/text форматирование (23 switch-блока)

**Severity: HIGH**

**Описание:** Паттерн `if fmt == "json": print(json.dumps(...)) else: print(...)` повторяется **23 раза**. Каждая `print_*` функция содержит свою реализацию одного и того же паттерна. Это:
- Увеличивает размер файла на ~300-400 строк
- Усложняет изменение формата вывода
- Увеличивает вероятность несогласованности

**Затронутые функции (19 штук):** `print_search`, `print_guard_staged`, `print_harvest_commit`, `print_publish_task`, `print_cleanup_worktree`, `print_tool_trigger`, `print_memory_route`, `print_memory_status`, `print_memory_explain`, `print_memory_preflight`, `print_global_lookup`, `print_memory_golden`, `print_memory_diff`, `print_memory_pack`, `print_global_promote`, `print_memory_promotion_inbox`, `print_review_queues`, `print_backlink_index`, `print_promotion_dry_run`

**Исправление:** Создать единый хелпер:
```python
def output_result(data: dict, text_formatter: Callable, fmt: str = "json") -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        text_formatter(data)
```

**Сложность:** НИЗКАЯ-СРЕДНЯЯ

---

## 4. Дублирование: subprocess.run() конфигурация

**Severity: MEDIUM**

**Описание:** Конфигурация `subprocess.run` с параметрами `check=False, capture_output=True, text=True, encoding="utf-8"` повторяется **5 раз** (строки 1033, 1056, 1072, 1203, 2179). Уже существуют `run_git()` и `_run_git()` — две разные обёртки!

**Исправление:** Оставить одну обёртку `_run_git(root, args, env=None)` и переиспользовать везде.

**Сложность:** НИЗКАЯ

---

## 5. Жёстко заданный путь Windows в `GLOBAL_MEMOIR_STORE`

**Severity: HIGH (Security)**

**Описание:** Строка 134:
```python
os.environ.get("REEFIKI_MEMOIR_STORE", r"C:\Users\kissl\.codex\memoir-stores\reefiki")
```
- Содержит **реальный username** (`kissl`) — утечка информации о разработчике
- Дефолтный путь **Windows-specific**, не работает на Linux/macOS
- Переменная окружения `GLOBAL_MEMOIR_STORE` упоминается, но **не используется** в коде напрямую (проверка ниже)

**Исправление:**
```python
GLOBAL_MEMOIR_STORE = Path(os.environ.get(
    "REEFIKI_MEMOIR_STORE",
    Path.home() / ".local" / "share" / "reefiki" / "memoir-stores"
))
```

**Сложность:** НИЗКАЯ

---

## 6. Отсутствие docstrings у всех 126 функций

**Severity: HIGH**

**Описание:** **Ни одна из 126 функций** не имеет docstring. Это критично для:
- Навигации по коду
- Генерации документации
- Понимания контрактов функций (что принимает, что возвращает, какие исключения)

**Примеры критичных функций без docstring:**
- `memory_pack()` — 188 строк, собирает контекст для промоции
- `review_queue_scan()` — 132 строки, определяет что попадает в очередь ревью
- `promotion_dry_run()` — решает promote/memoir-only/ignore
- `build_index()` — 134 строки, строит SQLite индекс

**Исправление:** Добавить docstrings минимум к 30 ключевым функциям (все бизнес-логические + все публичные).

**Сложность:** НИЗКАЯ (но объёмная)

---

## 7. SystemExit как механизм ошибок (28 вызовов)

**Severity: MEDIUM**

**Описание:** 28 мест в коде используют `raise SystemExit(...)` вместо кастомных исключений. Это:
- Делает тестирование сложнее (нужно ловить SystemExit)
- Невозможно дифференцировать ошибки (все одинаковы)
- Смешивает бизнес-логику с поведением CLI

**Исправление:** Ввести иерархию исключений:
```python
class ReefikiError(Exception): ...
class ProjectNotFoundError(ReefikiError): ...
class PolicyBlockError(ReefikiError): ...
class ValidationError(ReefikiError): ...
```
Ловить их в `main()` и конвертировать в exit codes.

**Сложность:** СРЕДНЯЯ

---

## 8. Чрезмерная защита через isinstance() — 53 вызова

**Severity: MEDIUM**

**Описание:** 53 вызова `isinstance()` — признак отсутствия типизации на уровне архитектуры. Код вручную проверяет типы данных, которые должны гарантироваться контрактами:
```python
if isinstance(result.get("assembly_trace"), dict) else []
if isinstance(item.get("review_queues"), dict) else {}
```

Это часто встречается в `print_memory_status()` — 8 isinstance-проверок.

**Исправление:** Использовать dataclasses/TypedDict для структурированных результатов. Уже есть `LookupResult`, `RouteDecision` — расширить подход на все возвращаемые значения.

**Сложность:** ВЫСОКАЯ

---

## 9. Некоторые импорты не используются

**Severity: LOW**

**Описание:** Следующие импорты имеют ≤2 вхождения в файле (включая строку импорта):

| Импорт | Вхождения | Статус |
|--------|-----------|--------|
| `parse_qsl` | 2 | Может быть нужен, но не видно использования |
| `urlunparse` | 2 | Аналогично |
| `posixpath` | 2 | Аналогично |
| `argparse` | 2 | Используется в `main()` |
| `annotations` | 1 | Используется (type hint syntax) |

**Примечание:** `annotations` — `from __future__ import annotations` — это lazy evaluation, работает корректно. Остальные нужно проверить глубже.

**Исправление:** Запустить `pylint --disable=all --enable=W0611` или `ruff check --select=F401`.

**Сложность:** НИЗКАЯ

---

## 10. Разделение ответственности нарушено

**Severity: HIGH**

**Описание:** Один файл содержит **все** слои:
- **CLI layer:** argparse, print_*, форматирование вывода
- **Business logic:** `promotion_dry_run()`, `review_queue_scan()`, `memory_pack()`
- **Data access:** `build_index()`, SQLite-операции, чтение markdown
- **Git operations:** `harvest_commit_payload()`, `publish_task_payload()`, `memory_diff()`
- **Security layer:** `memory_preflight()`, `memory_global_strict_preflight()`
- **Utility functions:** `as_text()`, `parse_frontmatter()`, `slugify()`

**Исправление:** См. разделение модулей в п.1. Каждый слой — отдельный модуль.

**Сложность:** ВЫСОКАЯ

---

## 11. Дублирование: log.md append pattern (6 раз)

**Severity: MEDIUM**

**Описание:** Паттерн записи в `wiki/log.md` повторяется 6 раз:
```python
log = project / "wiki" / "log.md"
with log.open("a", encoding="utf-8", newline="\n") as handle:
    handle.write(f"\n## [{date.today().isoformat()}] ...")
```

**Исправление:** Вынести в `append_to_log(project, heading, body)`.

**Сложность:** НИЗКАЯ

---

## 12. Нет тестов для основного модуля reefiki.py

**Severity: HIGH**

**Описание:** В директории `tests/` есть тесты только для:
- `test_validate_frontmatter.py` — валидатор
- `test_reefiki_memory_governance.py` — memory governance
- `test_reefiki_memory_contracts.py` — memory contracts
- `test_reefiki_dedup.py` — дедупликация
- `test_public_snapshot_guard.py` — публичный снапшот

**Нет тестов для:**
- `promotion_dry_run()` — критическая бизнес-логика
- `review_queue_scan()` — 132 строки без тестов
- `memory_pack()` — 188 строк без тестов
- `build_index()` — 134 строки без тестов
- `_suggest_target_type()` — влияет на тип промоции
- `parse_frontmatter()` — фундаментальный парсер

**Исправление:** Покрыть тестами ключевые бизнес-функции. Приоритет: `promotion_dry_run`, `parse_frontmatter`, `review_queue_scan`.

**Сложность:** СРЕДНЯЯ

---

## 13. Валидация входных данных непоследовательна

**Severity: MEDIUM**

**Описание:** Валидация входных данных неравномерна:
- `promotion_dry_run()` проверяет `if not text: raise SystemExit("Empty content.")` ✓
- `memory_pack()` не проверяет пустой task ✗
- `global_lookup()` не проверяет пустой query ✗
- `apply_promotion_draft()` проверяет наличие summary, но не проверяет target_type на допустимые значения ✗

**Исправление:** Добавить валидацию на входе каждой бизнес-функции. Рассмотреть библиотеку валидации (cerberus, pydantic).

**Сложность:** СРЕДНЯЯ

---

## 14. Жёстко закодированные ID в `memory_pack()`

**Severity: MEDIUM**

**Описание:** Функция `memory_pack()` (строки 2336-2344) содержит **жёстко закодированный** список `critical_order` из 5 ID:
```python
critical_order = [
    "reefiki-2-control-plane-spec",
    "reefiki-2-external-agent-research-synthesis",
    ...
]
```
Это делает `memory_pack()` привязанным к конкретному проекту, а не переиспользуемым инструментом.

**Исправление:** Вынести в конфигурацию (YAML/env) или в параметр функции.

**Сложность:** НИЗКАЯ

---

## 15. Типовые хинты: 100% покрытие (✅ хорошо)

**Severity: INFO**

**Описание:** **Все 126 функций** имеют return type hints. Всего **457 аннотаций** типов. Это единственная полностью позитивная находка.

---

## 16. Naming conventions: консистентны (✅ хорошо)

**Severity: INFO**

**Описание:** Все функции используют `snake_case`. Приватные функции корректно используют `_` префикс (18 из 126). Константы в `UPPER_CASE`.

---

## 17. Безопасность: нет SQL injection, есть path traversal

**Severity: MEDIUM (Security)**

**Описание:**
- ✅ SQL-запросы не используют f-strings (нет injection)
- ✅ subprocess.run не использует `shell=True`
- ⚠️ Проверки path traversal через `is_relative_to()` и `resolve()` есть в `_resolve_project_path()` и `promotion_inbox()`, но **не во всех точках ввода**
- ⚠️ Жёстко закодированный Windows-путь с username

---

## Сводная таблица

| # | Находка | Severity | Сложность |
|---|---------|----------|-----------|
| 1 | Монолит 3949 строк / 126 функций | CRITICAL | HIGH |
| 2 | main() на 319 строк | HIGH | MEDIUM |
| 3 | 23x дублирование json/text форматирования | HIGH | LOW-MEDIUM |
| 4 | 5x дублирование subprocess.run конфигурации | MEDIUM | LOW |
| 5 | Hardcoded Windows path с username | HIGH | LOW |
| 6 | 0/126 docstrings | HIGH | LOW |
| 7 | 28 SystemExit вместо кастомных исключений | MEDIUM | MEDIUM |
| 8 | 53 isinstance() — отсутствие типизированных контрактов | MEDIUM | HIGH |
| 9 | Возможно неиспользуемые импорты | LOW | LOW |
| 10 | Нет разделения на слои (CLI/BL/data/git) | HIGH | HIGH |
| 11 | 6x дублирование log.md append | MEDIUM | LOW |
| 12 | Нет unit-тестов для ключевых функций | HIGH | MEDIUM |
| 13 | Непоследовательная валидация входных данных | MEDIUM | MEDIUM |
| 14 | Жёстко закодированные ID в memory_pack | MEDIUM | LOW |
| 15 | Type hints: 100% покрытие | INFO ✅ | — |
| 16 | Naming conventions: консистентны | INFO ✅ | — |
| 17 | Path traversal проверки неполные | MEDIUM | MEDIUM |

---

## Рекомендуемый порядок исправления (ROI-based)

1. **Вынести hardcoded Windows path** (5 мин, убирает утечку username)
2. **Добавить docstrings** к 30 ключевым функциям (1-2 часа)
3. **Выделить `output_result()` helper** для json/text (1 час, убирает 300+ строк дублирования)
4. **Выделить `append_to_log()` helper** (15 мин)
5. **Разделить на модули** (1-2 дня, самый большой выигрыш в maintainability)
6. **Добавить unit-тесты** для `promotion_dry_run`, `parse_frontmatter`, `review_queue_scan` (1 день)
7. **Ввести кастомные исключения** (полдня)
8. **Довести path traversal проверки** до всех точек ввода (полдня)
