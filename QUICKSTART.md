# QUICKSTART

Languages: [Русский](#русский) · [English](#english) · [中文](#中文)

## Русский

Короткий старт для REEFIKI без знания внутренних команд.

## English

Quick start for REEFIKI without learning internal commands.

1. Open the `REEFIKI/` folder in Codex, Claude Code, Cursor, Windsurf, or another agent that reads `AGENTS.md`.
2. If you already have a code project, tell the agent: `Connect H:\Projects\MyApp to the wiki`.
3. If you want a new wiki, tell the agent: `Create a new project metrica about product analytics`.
4. Work with plain phrases: "put this in the inbox", "process the inbox", "remember this as a decision", "save this as a skill", "show status".
5. Use Obsidian only as a viewer/editor layer; REEFIKI markdown and git remain the source of truth.

The detailed canonical runbook continues below in Russian.

## 中文

REEFIKI 快速开始，不需要先学习内部命令。

1. 在 Codex、Claude Code、Cursor、Windsurf 或其他会读取 `AGENTS.md` 的代理中打开 `REEFIKI/` 文件夹。
2. 如果已经有代码项目，告诉代理：`把 H:\Projects\MyApp 连接到 wiki`。
3. 如果要创建新 wiki，告诉代理：`创建一个名为 metrica 的新项目，主题是产品分析`。
4. 用自然语言工作：“把这个放进收件箱”、“处理收件箱”、“把这个记为决策”、“保存成技能”、“显示状态”。
5. Obsidian 只作为查看/编辑层；REEFIKI 的 markdown 和 git 仍然是事实来源。

下面继续保留俄语的详细 canonical runbook。

## 1. Открой REEFIKI

Открой папку `REEFIKI/` в Codex, Claude Code, Cursor, Windsurf или другом агенте, который читает `AGENTS.md`.

Если агент находится в корне REEFIKI, это диспетчерский режим: здесь создают или подключают проекты, но не пишут wiki-страницы напрямую.

## 2. Создай или подключи проект

Если уже есть кодовый проект, скажи агенту:

```text
Подключи проект H:\Projects\MyApp к вики
```

Агент создаст wiki-проект и ссылку `_wiki/` в кодовом проекте.

Если проекта ещё нет, скажи:

```text
Создай новый проект metrica про продуктовую аналитику
```

Агент создаст папку `projects/metrica/` из шаблона.

## 3. Работай бытовыми фразами

| Что хочешь | Как сказать |
|---|---|
| Сохранить ссылку на потом | "положи это в копилку" |
| Разобрать сохранённое | "разбери копилку" |
| Зафиксировать решение | "запомни это как решение" |
| Сохранить повторяемый приём | "сохрани как навык" |
| Поднять старое знание | "что у нас по sync?" |
| Проверить состояние | "покажи статус" |

Агент сам выберет нужную операцию и обновит wiki/log/index там, где это положено.

## 4. Что где лежит

| Папка | Простое значение |
|---|---|
| `inbox/` | копилка: сохранено, но ещё не разобрано |
| `wiki/` | долговременная база знаний проекта |
| `seen/` | отложено или отказано с причиной |
| `raw/` | неизменяемый архив исходников |
| `plans/` | временные отчёты и черновики на проверку |

Не редактируй `raw/`. Старые строки в `wiki/log.md` тоже не переписываются: новые события добавляются в конец.

## 5. Проверь здоровье перед важной работой

Перед публикацией, большим разбором копилки или восстановлением после сбоя попроси:

```text
сделай health check проекта
```

Агент проверит индекс, структуру wiki, битые ссылки, зависшие элементы в копилке и очереди на ручной разбор.

## 6. Obsidian и мобильный capture

- Настрой Obsidian по [docs/obsidian-setup.md](docs/obsidian-setup.md).
- Для сохранения ссылок с телефона смотри [docs/mobile-capture.md](docs/mobile-capture.md).
- Для восстановления после проблем смотри [docs/RECOVERY.md](docs/RECOVERY.md).
- Полная карта команд и возможностей — в [COMMANDS.md](COMMANDS.md).

Главное правило: REEFIKI лучше работает, когда агент пишет durable pages, а Obsidian используется как viewer/editor с осторожностью.
