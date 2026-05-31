# Schema — форматы записей

Читай только когда создаёшь/правишь страницу.

## Frontmatter wiki-страницы

| Поле | Тип | Обязательно | Заметки |
|---|---|---|---|
| `id` | string | да | == имя файла без `.md`, kebab-case. Для URL/репо вычисляется по правилу `source_id` (см. `process.md`) для дедупликации. |
| `type` | enum | да | `source` \| `entity` \| `concept` \| `synthesis` \| `decision` \| `skill` |
| `title` | string | да | человекочитаемый |
| `tags` | list | да | минимум 1 |
| `useful_when` | list | **да** | ≥1 конкретный сценарий применения — без этого поля страница не создаётся |
| `sources` | list | для `source`/`synthesis` | имена файлов из `raw/` или URL |
| `verified` | YYYY-MM-DD \| null | для `skill` | дата последней проверки процедуры |
| `date_added` | YYYY-MM-DD | да | |
| `use_count` | int | да | стартует с 0, +1 в `/query` (батчится в ближайший `/process`/`/lint`/`/harvest`) |
| `last_used` | YYYY-MM-DD \| null | да | обновляется вместе с `use_count` |

## Правило валидности

Страница валидна, если `useful_when` содержит ≥1 конкретный сценарий применения — не `TBD`, не «может пригодиться».

Знание без сценария применения = заметка, не wiki-страница. Это главный фильтр против разрастания «мысии».

Если на `/process` `useful_when` сформулировать не получается:

1. Спроси пользователя одной фразой: «Когда эта страница пригодится?»
2. Если молчит / «не знаю» → отправь источник в `seen/` с `reason: unclear-use`. Не сохраняй в wiki.

`related`/`[[Related]]` — расставляются в теле страницы в секции `## Related`. Во frontmatter не дублируются.

## Тело страницы

Базовые секции для всех типов:

- `## Суть` — что и как (2–4 предложения)
- `## Дельта` — что уникального относительно wiki
- `## Применение` — конкретный сценарий
- `## Conflicting claims` — только при конфликте: каждый блок начинается со строки `[YYYY-MM-DD]` (дата фиксации), затем `<тезис new> (source: new) vs <тезис old> (source: old)`. Закрывается через `/resolve` после ≥30 дней.
- `## Related` — `[[slug]] — короткое объяснение связи`

**Для `source`** дополнительно: `## Ключевые тезисы` (3–7 пунктов) и `## Цитата-ссылка: raw/<file> (lines X–Y)`.

**Для `decision` (ADR)** тело заменяется на: `## Контекст` / `## Варианты` / `## Решение` / `## Последствия`.

**Для `skill`** тело заменяется на: `## Когда применять` / `## Шаги` (нумерованный список) / `## Проверено` (дата + где проверено). Опционально: `## Подводные камни`.

## Запись в `seen/`

```yaml
---
source: <filename или URL>
date: YYYY-MM-DD
reason: duplicate | off-topic | low-value | no-access | unclear-use
duplicate_of: <slug>   # только если reason=duplicate
quarantine_until: YYYY-MM-DD   # date + 30 дней
---
```

По истечении `quarantine_until` запись попадает в отчёт `/status` (истёкшие). Пересмотр — manual: вернуть источник в `inbox/` или продлить `quarantine_until` в `seen/<slug>.md`. Без auto-renewal.

## Запись в `wiki/index.md`

```markdown
### <id>
- type: <type>
- tags: [...]
- useful_when: ["..."]
- file: wiki/<subdir>/<id>.md
- date_added: YYYY-MM-DD
- use_count: N
```

Группировка по типам: `## Sources`, `## Entities`, `## Concepts`, `## Synthesis`, `## Decisions`, `## Skills`.

## Лог

Append-only: `## [YYYY-MM-DD] <op> | <краткий результат>`. `op` ∈ `/save | /process | /query | /harvest | /lint | /status | /new | /reindex | /resolve | conflict | refactor | meta`.

## Имена

- Wiki-страницы и файлы в `raw/`: `lowercase-with-hyphens` + расширение.
- Wiki-ссылки: `[[lowercase-with-hyphens]]`.
- `id` == имя файла без `.md`.
