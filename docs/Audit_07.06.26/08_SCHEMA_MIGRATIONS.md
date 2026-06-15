# REEFIKI — Аудит: Эволюция схемы (migrations)

> Дата: 4 июня 2026. Часть комплексного аудита незатронутых тем.

## 8.1 Масштаб проблемы

```
Текущий проект reefiki: ~100 страниц
После Phase 1: ~500 страниц
После Phase 2: ~2000+ страниц

Добавление одного обязательного поля = 2000 невалидных страниц
Ручное исправление: ~2 минуты на страницу = 66+ часов работы
```

## 8.2 Типы изменений схемы

| Тип изменения | Пример | Сложность миграции |
|---|---|---|
| Новое опциональное поле с дефолтом | `confidence: medium` | ✅ Тривиально |
| Новое обязательное поле | `derived_from: []` | ❌ Требует миграции всех страниц |
| Переименование поля | `importance` → `priority` | ⚠️ Поиск и замена |
| Изменение типа поля | `tags: string` → `tags: list` | ❌ Требует парсинга |
| Удаление поля | убрать `importance` | ✅ Просто |
| Изменение допустимых значений | добавить тип `antipattern` | ✅ Обратно совместимо |

## 8.3 Версионирование схемы

**Добавить в `_domain.md`:**
```yaml
schema_version: "1.0"
```

**Добавить в `validate_frontmatter.py`:**
```python
CURRENT_SCHEMA_VERSION = "1.0"

def check_schema_version(domain_path: Path) -> str:
    fm, _ = parse_frontmatter(domain_path.read_text())
    return str(fm.get("schema_version", "0.0"))
```

## 8.4 Система миграций

```python
# scripts/migrate.py

MIGRATIONS = {}

def migration(from_version: str, to_version: str):
    def decorator(func):
        MIGRATIONS[(from_version, to_version)] = func
        return func
    return decorator

@migration("1.0", "1.1")
def add_confidence_field(page_path: Path, fm: dict, body: str) -> dict:
    if "confidence" not in fm:
        fm["confidence"] = "medium"
    return fm

@migration("1.1", "1.2")
def rename_importance_to_priority(page_path: Path, fm: dict, body: str) -> dict:
    if "importance" in fm:
        fm["priority"] = fm.pop("importance")
    return fm

def migrate_project(project: Path, from_version: str, to_version: str,
                    dry_run: bool = True) -> list[Path]:
    migration_key = (from_version, to_version)
    if migration_key not in MIGRATIONS:
        raise ValueError(f"Нет миграции {from_version} → {to_version}")

    migrate_fn = MIGRATIONS[migration_key]
    changed = []

    for page in iter_pages(project):
        text = page.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        new_fm = migrate_fn(page, fm.copy(), body)
        if new_fm != fm:
            changed.append(page)
            if not dry_run:
                new_text = serialize_frontmatter(new_fm) + body
                page.write_text(new_text, encoding="utf-8")

    return changed
```

**CLI-команда:**
```bash
# Dry-run: показать что изменится
python scripts/reefiki.py --project myproject migrate --from 1.0 --to 1.1 --dry-run

# Применить миграцию
python scripts/reefiki.py --project myproject migrate --from 1.0 --to 1.1 --yes
```

## 8.5 Принципы безопасной эволюции схемы

**Правило 1 — Новые поля всегда опциональные сначала:**
```
Фаза 1: добавить поле как опциональное (warn при отсутствии)
Фаза 2: через N месяцев — сделать обязательным + запустить миграцию
```

**Правило 2 — Graceful degradation в коде:**
```python
# Вместо:
confidence = fm["confidence"]  # KeyError если поля нет

# Использовать:
confidence = fm.get("confidence", "medium")  # дефолт
```

**Правило 3 — Changelog схемы (`SCHEMA_CHANGELOG.md`):**
```markdown
## v1.2 (2026-07-01)
- Добавлено поле `derived_from` (опциональное)
- Добавлено поле `confidence` (опциональное, default: medium)

## v1.1 (2026-06-01)
- Переименовано `importance` → `priority`

## v1.0 (2026-05-01)
- Начальная версия схемы
```

## Action plan

| ID | Действие | Сложность | Приоритет |
|---|---|---|---|
| MIG-01 | Добавить `schema_version` в `_domain.md` | S | P1 |
| MIG-02 | Добавить проверку версии схемы в `/lint` | S | P1 |
| MIG-03 | Создать `scripts/migrate.py` с базовой инфраструктурой | M | P1 |
| MIG-04 | Создать `SCHEMA_CHANGELOG.md` в шаблоне | S | P1 |
| MIG-05 | Добавить graceful defaults во все `fm.get()` вызовы | M | P2 |
| MIG-06 | Документировать процесс добавления новых полей | S | P2 |
