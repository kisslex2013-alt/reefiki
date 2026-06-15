# REEFIKI — Аудит: Obsidian-интеграция

> Дата: 4 июня 2026. Часть комплексного аудита незатронутых тем.

## 7.1 Конфликты при одновременном редактировании

**Сценарий конфликта:**
```
1. Пользователь открывает wiki-страницу в Obsidian
2. Редактирует её (добавляет заметку)
3. Одновременно агент выполняет /process и пишет в ту же страницу
4. Obsidian сохраняет свою версию → перезаписывает изменения агента
   ИЛИ агент сохраняет свою версию → перезаписывает изменения Obsidian
```

Obsidian сохраняет файл при каждом изменении (autosave ~2 сек). REEFIKI агент пишет файл через `path.write_text()`. Нет механизма блокировки файлов, нет merge-логики.

**Реальный риск:** при активном использовании Obsidian + агента одновременно — потеря данных.

## 7.2 Проблемы с `.obsidian/` настройками

**Проблема 1 — `.obsidian/` в `.gitignore`:**

Если `.obsidian/` исключён из git, настройки не синхронизируются между устройствами.

**Рекомендация:** включить в git только стабильные конфиги:
```gitignore
.obsidian/workspace.json         # исключить (открытые вкладки)
.obsidian/workspace-mobile.json  # исключить
# .obsidian/app.json и graph.json — включить в git
```

**Проблема 2 — Obsidian Sync vs git:**

Конфликт двух систем синхронизации. Нужна явная документация: использовать либо git, либо Obsidian Sync, не оба.

**Проблема 3 — Служебные файлы Obsidian:**

`.obsidian/plugins/`, `.obsidian/snippets/`, `.obsidian/themes/` могут случайно попасть в git commit.

## 7.3 Рекомендуемая конфигурация

**Готовый `.obsidian/app.json`:**
```json
{
  "useMarkdownLinks": false,
  "newLinkFormat": "shortest",
  "attachmentFolderPath": "assets",
  "showUnsupportedFiles": false,
  "defaultViewMode": "source",
  "livePreview": true
}
```

**Готовый `.obsidian/graph.json` с фильтрами:**
```json
{
  "search": "-path:\"projects/_template/\" -path:\"/raw/\" -path:\"/inbox/\" -path:\"/seen/\" -path:\"/deep-research/\" -path:\"/.claude/\" -path:\"/plans/\" -file:CLAUDE -file:_domain -file:README -file:log -file:index",
  "showTags": true,
  "showAttachments": false,
  "colorGroups": [
    {"query": "path:wiki/sources", "color": {"a": 1, "rgb": 14701138}},
    {"query": "path:wiki/decisions", "color": {"a": 1, "rgb": 16744272}},
    {"query": "path:wiki/skills", "color": {"a": 1, "rgb": 5614830}},
    {"query": "path:wiki/synthesis", "color": {"a": 1, "rgb": 9699539}},
    {"query": "path:wiki/concepts", "color": {"a": 1, "rgb": 3394815}},
    {"query": "path:wiki/entities", "color": {"a": 1, "rgb": 16711782}}
  ]
}
```

## 7.4 Рекомендуемые плагины

| Плагин | Зачем | Конфликты с REEFIKI? |
|---|---|---|
| **Dataview** | Запросы по frontmatter | ✅ Нет |
| **Tag Wrangler** | Управление тегами | ✅ Нет |
| **Templater** | Шаблоны страниц | ⚠️ Может конфликтовать с агентом |
| **Git** (obsidian-git) | Автокоммит из Obsidian | ❌ **НЕСОВМЕСТИМ** |
| **Calendar** | Навигация по датам | ✅ Нет |

**КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ:** плагин `obsidian-git` **несовместим** с REEFIKI. Он коммитит изменения в обход `guard-staged` и `harvest-commit`, нарушая dual-remote publish safety.

## 7.5 Защита от конфликтов редактирования

```python
def safe_write(path: Path, content: str) -> None:
    """Атомарная запись с защитой от конфликтов."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)  # атомарная операция на большинстве FS
```

## Action plan

| ID | Действие | Сложность | Приоритет |
|---|---|---|---|
| OBS-01 | Добавить готовый `.obsidian/app.json` в репозиторий | S | P1 |
| OBS-02 | Добавить готовый `.obsidian/graph.json` с фильтрами | S | P1 |
| OBS-03 | Создать `docs/obsidian-setup.md` с инструкцией | S | P1 |
| OBS-04 | Предупредить о несовместимости obsidian-git плагина | S | **P0** |
| OBS-05 | Уточнить `.gitignore` для `.obsidian/` | S | P1 |
| OBS-06 | Добавить атомарную запись файлов в CLI | M | P2 |
| OBS-07 | Документировать конфликт Obsidian Sync vs git | S | P1 |
