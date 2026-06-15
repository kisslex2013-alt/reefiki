# REEFIKI — `_user/` контекст и Wizard: скорректированный анализ

> **Версия:** 2.0 | **Дата:** 2026-06-04
> **Основано на:** 19 файлах аудита включая `11_Onboarding_Wizard.md`,
> `12_DASHBOARD.md`, `13_ARCHITECTURE_DECISIONS.md`, `REEFIKI_AUDIT_ERRATA.md`,
> `REEFIKI_SECURITY_AUDIT.md`, `REEFIKI_CROSSPLATFORM_AUDIT.md` и других.
> **Статус:** Корректирует и дополняет первоначальный ответ о `_user/`.

---

## Содержание

1. [Что изменилось после прочтения всех файлов](#1-что-изменилось-после-прочтения-всех-файлов)
2. [Противоречия между аудитами — сводка](#2-противоречия-между-аудитами--сводка)
3. [Скорректированная архитектура `_user/`](#3-скорректированная-архитектура-_user)
4. [Wizard: полная интеграция `_user/`](#4-wizard-полная-интеграция-_user)
5. [Как `_user/` взаимодействует с Dashboard](#5-как-_user-взаимодействует-с-dashboard)
6. [Безопасность и приватность `_user/`](#6-безопасность-и-приватность-_user)
7. [Логичность и сочетаемость с другими частями REEFIKI](#7-логичность-и-сочетаемость-с-другими-частями-reefiki)
8. [Action plan](#8-action-plan)

---

## 1. Что изменилось после прочтения всех файлов

### 1.1 Что подтвердилось

Идея `_user/` как отдельного слоя (не `projects/`) правильная и согласуется с
архитектурой из аудитов. Wizard уже спроектирован в `11_Onboarding_Wizard.md` как
полноценный интерактивный инструмент — это меняет то, **где и когда** собирается
user context.

### 1.2 Что нужно скорректировать

**Коррекция 1: Wizard уже существует как детальная спецификация**

`11_Onboarding_Wizard.md` описывает wizard с языком, режимами, проверкой окружения,
`~/.reefiki/config.json`. `_user/` должен создаваться **внутри этого wizard**,
а не отдельно. В первоначальном ответе wizard описан упрощённо — теперь нужно
встраиваться в существующую спецификацию.

**Коррекция 2: Dashboard — это реальный компонент, не абстракция**

`12_DASHBOARD.md` описывает FastAPI + HTMX + приветствие по времени суток +
health score + серию активности. `_user/` является **источником данных для dashboard**:
имя, язык, стиль — всё это dashboard уже использует. В первоначальном ответе
эта связь не была описана.

**Коррекция 3: Security — `_user/` содержит чувствительные данные**

`REEFIKI_SECURITY_AUDIT.md` фиксирует что publish-task не сканирует содержимое файлов
(SEC-010). `_user/patterns.md` и `_user/context.md` содержат личные паттерны,
цели, активные проекты. Это **не должно попадать в публичный snapshot** ни при каких
условиях. В первоначальном ответе упомянут `.gitignore` но без привязки к реальной
архитектуре dual-remote.

**Коррекция 4: Python минимум 3.11, не 3.9**

`REEFIKI_AUDIT_ERRATA.md` явно разрешает противоречие между аудитами:
минимум Python **3.11** (не 3.9, как предлагал deps-аудит). Любой новый код
(включая user context модуль) пишется под 3.11+.

**Коррекция 5: Pipedream — отказываемся, не упоминаем**

`13_ARCHITECTURE_DECISIONS.md` рекомендует отказаться от Pipedream в пользу
iOS Shortcut / GitHub Actions / Dashboard webhook. В первоначальном ответе
Telegram+Pipedream упоминался как данность — это устарело.

---

## 2. Противоречия между аудитами — сводка

Ниже противоречия между 19 файлами которые влияют на `_user/` и wizard.

### 2.1 Python: 3.9 vs 3.11 → RESOLVED: 3.11

| Файл | Утверждение |
|---|---|
| `REEFIKI_DEPS_AUDIT.md` (Шаг 3) | Предлагает полифил `StrEnum` для поддержки Python 3.9 |
| `REEFIKI_CROSSPLATFORM_AUDIT.md` | Фиксирует реальный минимум 3.11 как факт |
| `REEFIKI_AUDIT_ERRATA.md` | Явно разрешает: "фиксировать минимум 3.11, без polyfill" |

**Вывод:** `_user/` модуль — только Python 3.11+. В wizard явная проверка с блокером.

### 2.2 `parse_frontmatter` — два несовместимых парсера → НЕ RESOLVED

| Файл | Утверждение |
|---|---|
| `REEFIKI_SECURITY_AUDIT.md` (SEC-018) | Описывает парсер как "без CRLF-проблемы" (неверно) |
| `REEFIKI_AUDIT_ERRATA.md` (2.1) | Оба файла уязвимы к CRLF по разным механизмам |
| `REEFIKI_AUDIT_ERRATA.md` (4.1) | Два парсера `parse_frontmatter` могут расходиться в edge-cases |

**Влияние на `_user/`:** `_user/profile.md` и `_user/patterns.md` будут читаться
существующим парсером. Если файл создан на Windows (CRLF), парсер может его не распознать.
**Фикс:** `_user/` файлы создаются wizard'ом с явным `newline="\n"` в Python.

```python
# В wizard при создании _user/ файлов:
path.write_text(content, encoding="utf-8", newline="\n")  # всегда LF
```

### 2.3 `os.umask(0o077)` — глобальный vs точечный → RESOLVED: точечный

| Файл | Утверждение |
|---|---|
| `REEFIKI_SECURITY_AUDIT.md` (SEC-014) | Рекомендует `os.umask(0o077)` в `main()` |
| `REEFIKI_AUDIT_ERRATA.md` (3.4) | Глобальный umask затронет git-операции; нужен `chmod(0o700)` на `.reefiki/` |

**Влияние на `_user/`:** `_user/` папка должна быть защищена точечно:
```python
_user_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
```

### 2.4 Lицензия: MIT vs Apache 2.0 vs BSL → RESOLVED: Apache 2.0 для core

| Файл | Утверждение |
|---|---|
| `01_LICENSING.md` | Apache 2.0 для core + BSL для premium |
| `reefiki-audit-supplement.md` | MIT для кода + CC BY 4.0 для контента |
| `REEFIKI_Infrastructure_UX_Audit.md` | Apache 2.0 или MIT |
| `REEFIKI_AUDIT_ERRATA.md` (8.1) | MIT/Apache-2.0 максимизируют adoption; BSL если планируется Sync |
| `gemini-code-1780552836103.md` | Apache 2.0 |

**Консенсус:** **Apache 2.0 для core** (патентная защита важна). BSL рассматривается
только для future premium-компонентов. `_user/` модуль — часть core → Apache 2.0.

### 2.5 SEC-011 severity: HIGH vs MEDIUM → RESOLVED: MEDIUM

`REEFIKI_AUDIT_ERRATA.md` понижает до MEDIUM. Файл `public-snapshot.private-projects.txt`
существует и заполнен. `_user/` должен добавляться в него автоматически при создании.

### 2.6 Obsidian: обязателен vs опционален → RESOLVED: опционален

`13_ARCHITECTURE_DECISIONS.md` решает: Obsidian опционален. Dashboard закрывает
большинство use cases. `_user/` не зависит от Obsidian.

### 2.7 Pipedream: использовать vs заменить → RESOLVED: заменить

`13_ARCHITECTURE_DECISIONS.md`: iOS Shortcut + GitHub API как default,
Dashboard webhook как элегантная альтернатива. В `_user/` не упоминаем Pipedream.

---

## 3. Скорректированная архитектура `_user/`

### 3.1 Расположение и структура

```
~/REEFIKI/                    ← корень репозитория
├── AGENTS.md                 ← читается агентом первым
├── _user/                    ← ВНЕ projects/, читается вторым
│   ├── profile.md            ← стабильное ядро (wizard → редко)
│   ├── context.md            ← текущий фокус (агент обновляет)
│   ├── patterns.md           ← наблюдения агента (накапливается)
│   └── log.md                ← append-only лог (агент, не пользователь)
├── projects/
│   ├── myproject/
│   └── skills-core/
└── ~/.reefiki/config.json    ← ВНЕ репозитория (wizard config)
```

**Почему `_user/` в корне репо, а не в `~/.reefiki/`:**

`config.json` в `~/.reefiki/` хранит технические настройки (путь, порт, язык).
`_user/` хранит knowledge-контекст — это часть базы знаний пользователя, должна
версионироваться git'ом вместе с wiki, но **не публиковаться**.

### 3.2 Защита от публикации (dual-remote safety)

`_user/` добавляется в `scripts/public-snapshot.private-projects.txt` автоматически
при создании wizard'ом. Это закрывает SEC-011 для user context:

```
# scripts/public-snapshot.private-projects.txt
_user
Hermes
reefiki
metrica
security-guidance-lite
Suno
```

Дополнительно — в `.gitignore` НЕ добавляем (должно версионироваться в private remote),
но в AGENTS.md явная инструкция:

```markdown
## _user/ — User Context Layer

_user/ содержит персональный контекст пользователя.
НИКОГДА не включать в публичный snapshot.
НИКОГДА не читать содержимое при работе в публичном контексте.
```

### 3.3 Формат файлов (скорректированный)

**`_user/profile.md`** — создаётся wizard'ом, меняется только явно:

```yaml
---
type: user-profile
schema_version: "1.0"
created: 2026-06-04
updated: 2026-06-04
wizard_mode: quick          # quick | full (из какого режима создан)
---

## Коммуникация

language: ru
explanation_style: concise
autonomy: high              # low | medium | high
                            # high = агент делает и кратко сообщает

## Технический контекст

expertise_self_reported: intermediate  # из wizard
primary_stack: []           # заполняется агентом по ходу работы
current_ides: []            # заполняется агентом

## Рабочие предпочтения

decision_style: fast-then-refine
feedback_preference: direct
```

**`_user/context.md`** — агент обновляет при смене фокуса:

```yaml
---
type: user-context
updated: 2026-06-04
---

## Сейчас в фокусе

active_projects: []
current_goal: ""
horizon: ""

## Что сейчас не важно (не поднимать)

[]
```

**`_user/patterns.md`** — агент дописывает, никогда не удаляет без подтверждения:

```markdown
---
type: user-patterns
note: "Ведётся агентом. Правь или удаляй записи по желанию."
---

## Рабочие паттерны

<!-- Агент добавляет сюда наблюдения по формату: -->
<!-- [YYYY-MM-DD] Наблюдение. confidence: low|medium|high -->
```

**`_user/log.md`** — только append, агент не редактирует старые записи:

```markdown
# User Context Log
<!-- append-only: агент добавляет снизу, никогда не редактирует выше -->
```

### 3.4 Правила в корневом AGENTS.md

Новая секция в корневом `AGENTS.md` (добавляется wizard'ом при создании `_user/`):

```markdown
## _user/ — User Context Layer

### При старте каждой сессии
1. Читать `_user/profile.md` — применять язык, стиль, autonomy
2. Читать `_user/context.md` — знать активные проекты, текущую цель
3. Читать `_user/patterns.md` — только записи с confidence: high
4. НЕ читать `_user/log.md` при старте (только при записи наблюдений)

### Принципы обновления
- `profile.md` — только по явному запросу пользователя
- `context.md` — агент обновляет при смене фокуса, объявляет кратко:
  "Обновил context: active_projects → [myproject, skills-core]"
- `patterns.md` — добавлять наблюдение если видел паттерн 2+ раза
  ИЛИ пользователь сказал явно. Помечать [устарело: дата] если изменилось.
- `log.md` — только append, без редактирования предыдущих записей

### Что НЕ делать
- Не читать `_user/` при работе в публичном контексте
- Не включать содержимое `_user/` в ответы как цитаты
- Не обновлять `profile.md` автоматически даже если кажется очевидным
- Не хранить пароли, токены, личные данные (имя, возраст, локация)

### Drift detection
При старте: если `_user/context.md` не обновлялся > 14 дней →
объявить: "Context не обновлялся 14 дней. Обновить active_projects?"
```

---

## 4. Wizard: полная интеграция `_user/`

Опираясь на спецификацию `11_Onboarding_Wizard.md`, `_user/` встраивается
в существующий поток — не добавляет новый шаг, а расширяет существующие.

### 4.1 Место в потоке wizard

```
Шаг 0: Выбор языка           ← уже есть → сохраняется в config.json И _user/profile.md
Шаг 1: Проверка окружения    ← уже есть → без изменений
Шаг 2: Выбор режима          ← уже есть
  ├── Режим 1: Быстрый старт  ← РАСШИРЯЕМ: +2 вопроса после имени проекта
  ├── Режим 2: Полная настройка ← РАСШИРЯЕМ: +блок User Profile
  ├── Режим 3: Открыть проект  ← без изменений (_user/ уже есть)
  └── Режим 4: Только дашборд  ← без изменений
```

### 4.2 Режим 1 — Быстрый старт: минимальные вопросы

После "Как назвать первый проект?" добавляются **2 вопроса**, не больше:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Быстрый старт
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Где создать REEFIKI?
  [~/REEFIKI]: ↵

Как назвать первый проект?
  > заметки

Последние два вопроса — для AI-агентов:

Насколько самостоятельно должен действовать агент?
  1) Спрашивай перед каждым шагом
  2) Делай и кратко сообщи  ←  рекомендуется
  3) Буду говорить сам когда нужно

Выбор [2]: ↵

Как объяснять — коротко или подробно?
  1) Коротко и по делу  ←  рекомендуется
  2) С примерами и деталями
  3) Сам разберусь

Выбор [1]: ↵

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Настраиваю...

  ✅ Создана папка ~/REEFIKI
  ✅ git инициализирован
  ✅ Создан проект "заметки"
  ✅ Создан профиль агента (_user/)
  ✅ Построен поисковый индекс
  ✅ Дашборд запущен → http://localhost:7777
```

**Что сохраняется в `_user/profile.md` из Быстрого старта:**
- `language` — из Шага 0
- `autonomy` — из вопроса 1 (high/medium/low)
- `explanation_style` — из вопроса 2 (concise/detailed)
- `wizard_mode: quick`

**Всё остальное** (expertise, stack, patterns) — агент выводит сам по ходу первых сессий.

### 4.3 Режим 2 — Полная настройка: расширенный блок

В Полной настройке после "Создать первый проект?" — новый блок:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Профиль для AI-агентов (опционально, Enter чтобы пропустить)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Насколько самостоятельно должен действовать агент?
  1) Спрашивай перед каждым шагом
  2) Делай и кратко сообщи
  3) Делай молча
Выбор [2]: ↵

Как объяснять?
  1) Коротко и по делу
  2) С примерами
  3) Подробно с деталями
Выбор [1]: ↵

Технический уровень (агент будет подстраивать объяснения)?
  1) Начинающий
  2) Средний
  3) Уверенный
  4) Эксперт
Выбор [3]: ↵

Основные инструменты (через запятую, Enter чтобы пропустить)?
  Пример: Python, git, SQLite
  > Python, git, SQLite, markdown

Текущая цель (одно предложение, Enter чтобы пропустить)?
  > Построить личную базу знаний для AI-проектов

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ Профиль агента создан (_user/)
```

### 4.4 Реализация wizard-модуля для `_user/`

```python
# scripts/wizard.py — дополнение к существующей спецификации

from pathlib import Path
from datetime import date
import json

USER_CONTEXT_TEMPLATE = """\
---
type: user-profile
schema_version: "1.0"
created: {today}
updated: {today}
wizard_mode: {mode}
---

## Коммуникация

language: {language}
explanation_style: {explanation_style}
autonomy: {autonomy}

## Технический контекст

expertise_self_reported: {expertise}
primary_stack: {stack}
current_ides: []

## Рабочие предпочтения

decision_style: fast-then-refine
feedback_preference: direct
"""

CONTEXT_TEMPLATE = """\
---
type: user-context
updated: {today}
---

## Сейчас в фокусе

active_projects: [{project}]
current_goal: "{goal}"
horizon: ""

## Что сейчас не важно (не поднимать)

[]
"""

PATTERNS_TEMPLATE = """\
---
type: user-patterns
note: "Ведётся агентом. Правь или удаляй записи по желанию."
---

## Рабочие паттерны

<!-- Агент добавляет наблюдения по мере работы -->
<!-- Формат: [YYYY-MM-DD] Наблюдение. confidence: low|medium|high -->
"""

LOG_TEMPLATE = """\
# User Context Log
<!-- append-only: агент добавляет снизу, никогда не редактирует выше -->

## {today}

- Профиль создан wizard'ом (режим: {mode})
"""


def create_user_context(
    reefiki_path: Path,
    language: str,
    autonomy: str,
    explanation_style: str,
    expertise: str = "intermediate",
    stack: list[str] | None = None,
    first_project: str = "",
    goal: str = "",
    mode: str = "quick"
) -> None:
    """
    Создаёт _user/ структуру в корне REEFIKI-репозитория.
    Вызывается из wizard после базовой настройки.
    """
    today = date.today().isoformat()
    user_dir = reefiki_path / "_user"

    # Создать папку с правами 700 — только владелец
    user_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    stack_yaml = json.dumps(stack or [], ensure_ascii=False)

    # profile.md
    profile = USER_CONTEXT_TEMPLATE.format(
        today=today, mode=mode, language=language,
        explanation_style=explanation_style, autonomy=autonomy,
        expertise=expertise, stack=stack_yaml
    )
    (user_dir / "profile.md").write_text(profile, encoding="utf-8", newline="\n")

    # context.md
    context = CONTEXT_TEMPLATE.format(
        today=today,
        project=first_project,
        goal=goal
    )
    (user_dir / "context.md").write_text(context, encoding="utf-8", newline="\n")

    # patterns.md
    (user_dir / "patterns.md").write_text(
        PATTERNS_TEMPLATE, encoding="utf-8", newline="\n"
    )

    # log.md
    log = LOG_TEMPLATE.format(today=today, mode=mode)
    (user_dir / "log.md").write_text(log, encoding="utf-8", newline="\n")

    # Защита от публикации: добавить _user в private-projects.txt
    private_file = reefiki_path / "scripts" / "public-snapshot.private-projects.txt"
    if private_file.exists():
        content = private_file.read_text(encoding="utf-8")
        if "_user" not in content:
            private_file.write_text(content.rstrip() + "\n_user\n", encoding="utf-8")

    print(f"  ✅ Создан профиль агента ({user_dir.relative_to(reefiki_path)})")


def collect_user_context_quick(lang: str) -> dict:
    """Сбор минимального контекста для режима Быстрый старт (2 вопроса)."""

    AUTONOMY_MAP = {"1": "low", "2": "high", "3": "medium"}
    STYLE_MAP = {"1": "concise", "2": "detailed", "3": "concise"}

    labels = {
        "ru": {
            "autonomy_q": "Насколько самостоятельно должен действовать агент?",
            "autonomy_1": "Спрашивай перед каждым шагом",
            "autonomy_2": "Делай и кратко сообщи  ← рекомендуется",
            "autonomy_3": "Буду говорить сам когда нужно",
            "style_q": "Как объяснять?",
            "style_1": "Коротко и по делу  ← рекомендуется",
            "style_2": "С примерами и деталями",
            "style_3": "Сам разберусь",
        },
        "en": {
            "autonomy_q": "How independently should the agent act?",
            "autonomy_1": "Ask before each step",
            "autonomy_2": "Do and briefly report  ← recommended",
            "autonomy_3": "I'll tell you when needed",
            "style_q": "How should I explain things?",
            "style_1": "Short and direct  ← recommended",
            "style_2": "With examples and detail",
            "style_3": "I'll figure it out",
        },
        "zh": {
            "autonomy_q": "智能体应该多独立地行动？",
            "autonomy_1": "每步都询问",
            "autonomy_2": "执行并简短汇报 ← 推荐",
            "autonomy_3": "我会主动告知",
            "style_q": "如何解释？",
            "style_1": "简短直接 ← 推荐",
            "style_2": "有示例和细节",
            "style_3": "我自己搞定",
        },
    }
    L = labels.get(lang, labels["en"])

    print(f"\n  {L['autonomy_q']}")
    print(f"    1) {L['autonomy_1']}")
    print(f"    2) {L['autonomy_2']}")
    print(f"    3) {L['autonomy_3']}")
    autonomy_raw = input("  Выбор [2]: ").strip() or "2"

    print(f"\n  {L['style_q']}")
    print(f"    1) {L['style_1']}")
    print(f"    2) {L['style_2']}")
    print(f"    3) {L['style_3']}")
    style_raw = input("  Выбор [1]: ").strip() or "1"

    return {
        "autonomy": AUTONOMY_MAP.get(autonomy_raw, "high"),
        "explanation_style": STYLE_MAP.get(style_raw, "concise"),
    }


def collect_user_context_full(lang: str) -> dict:
    """Расширенный сбор для режима Полная настройка."""
    quick = collect_user_context_quick(lang)

    EXPERTISE_MAP = {"1": "beginner", "2": "intermediate", "3": "advanced", "4": "expert"}
    print("\n  Технический уровень?")
    print("    1) Начинающий")
    print("    2) Средний")
    print("    3) Уверенный")
    print("    4) Эксперт")
    exp_raw = input("  Выбор [3]: ").strip() or "3"

    print("\n  Основные инструменты (через запятую, Enter пропустить)?")
    print("  Пример: Python, git, SQLite")
    stack_raw = input("  > ").strip()
    stack = [s.strip() for s in stack_raw.split(",") if s.strip()] if stack_raw else []

    print("\n  Текущая цель (одно предложение, Enter пропустить)?")
    goal = input("  > ").strip()

    return {
        **quick,
        "expertise": EXPERTISE_MAP.get(exp_raw, "advanced"),
        "stack": stack,
        "goal": goal,
    }
```

### 4.5 Геймификация wizard + `_user/`

`11_Onboarding_Wizard.md` описывает приветствие после завершения wizard.
С `_user/` оно становится персональным:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 REEFIKI готов к работе!

  AI-агенты теперь знают:
    • Язык общения: русский
    • Стиль: коротко и по делу
    • Самостоятельность: высокая

  Первый шаг — скажи агенту что тебя интересует,
  или сохрани ссылку:
    reefiki save https://example.com/article

  Дашборд: http://localhost:7777
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 5. Как `_user/` взаимодействует с Dashboard

`12_DASHBOARD.md` описывает приветствие которое зависит от `health_score` и времени суток.
С `_user/profile.md` dashboard получает дополнительный контекст:

### 5.1 Приветствие с персонализацией

```python
# scripts/reefiki_dashboard.py

def get_greeting(health_score: str, user_profile: dict) -> str:
    """Персонализированное приветствие из _user/profile.md"""
    from datetime import datetime
    hour = datetime.now().hour
    lang = user_profile.get("language", "ru")

    time_greet = {
        "ru": "Доброе утро" if hour < 12 else "Добрый день" if hour < 18 else "Добрый вечер",
        "en": "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening",
        "zh": "早上好" if hour < 12 else "下午好" if hour < 18 else "晚上好",
    }.get(lang, "Добрый день")

    status = {
        "excellent": "Вики в отличной форме 🌟",
        "good":      "Вики в хорошем состоянии",
        "fair":      "Есть что улучшить",
        "poor":      "Вики требует внимания ⚠️",
    }.get(health_score, "")

    return f"{time_greet} 👋\n{status}"


def load_user_profile(reefiki_path: Path) -> dict:
    """Читает _user/profile.md и возвращает словарь настроек."""
    profile_path = reefiki_path / "_user" / "profile.md"
    if not profile_path.exists():
        return {"language": "ru", "autonomy": "high"}

    from reefiki import parse_frontmatter
    text = profile_path.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(text)
    return fm
```

### 5.2 Настройки dashboard из `_user/`

Dashboard использует `_user/profile.md` для:

| Поле в profile.md | Применение в dashboard |
|---|---|
| `language` | Язык интерфейса (EN/RU/ZH из `12_DASHBOARD.md` DASH-13) |
| `autonomy` | Показывать ли подтверждения перед действиями |
| `explanation_style` | Краткие или развёрнутые описания в рекомендациях |
| `current_ides` | Показывать раздел skills с фильтром по IDE |

### 5.3 Активный проект из `_user/context.md`

```python
@app.get("/")
async def home(request: Request, project: str = None):
    config = load_config()
    user_profile = load_user_profile(Path(config["reefiki_path"]))
    user_context = load_user_context(Path(config["reefiki_path"]))

    # Приоритет: URL param > _user/context.md > config.json
    active_project = (
        project
        or user_context.get("active_projects", [None])[0]
        or config.get("last_project")
    )
    # ...
```

---

## 6. Безопасность и приватность `_user/`

На основе `REEFIKI_SECURITY_AUDIT.md` и `REEFIKI_AUDIT_ERRATA.md`:

### 6.1 Что защищает `_user/` от утечки

```python
# 1. Права на папку (точечный chmod, не глобальный umask)
(_user_dir).mkdir(mode=0o700, parents=True, exist_ok=True)

# 2. Автоматическое добавление в private-projects.txt (SEC-011)
# → _user никогда не попадает в publish-task

# 3. Явный запрет в AGENTS.md на чтение в публичном контексте

# 4. Не хранить в _user/:
# - пароли, токены, API ключи
# - полные имя/фамилия, дата рождения
# - финансовую информацию
# - медицинские данные
```

### 6.2 Чего НЕ хранить в `_user/`

Явные примеры для пользователя (добавить в wizard как предупреждение):

```
ℹ️  Профиль хранит только рабочие предпочтения.

  Не добавляй в _user/:
    ❌ Пароли и токены (используй менеджер паролей)
    ❌ Личные данные (имя, адрес, телефон)
    ❌ Финансовую информацию

  Агент сам наполнит профиль по ходу работы.
```

### 6.3 `_user/` и CRLF-проблема из errata

Файлы создаются wizard'ом с явным `newline="\n"` — исключает CRLF-баг
(описан в `REEFIKI_AUDIT_ERRATA.md` §2.1).

```python
# Все write_text в create_user_context используют newline="\n"
path.write_text(content, encoding="utf-8", newline="\n")
```

---

## 7. Логичность и сочетаемость с другими частями REEFIKI

### 7.1 Соответствие философии

| Принцип REEFIKI | Соответствие `_user/` |
|---|---|
| Дистилляция, не архивация | `patterns.md` накапливает только подтверждённые паттерны (2+ раза) |
| Useful when обязателен | `_user/` не использует wiki-схему — свои типы, без `useful_when` |
| Агент пишет, человек решает | `profile.md` — человек; `patterns.md`, `context.md` — агент |
| Local-first, open format | `_user/` — plain markdown в git, читается любым редактором |
| Governance | Явные правила в AGENTS.md, автозащита от публикации |

### 7.2 Связь с 3-layer memory

```
Существующая модель памяти REEFIKI:
  memoir     ← краткосрочная (session)
  wiki       ← долгосрочная (durable knowledge)
  graphify   ← структурная (code/concept graph)

_user/ добавляет четвёртый слой:
  _user/     ← контекст интерпретации (meta-layer)
              читается до всего остального
              не является knowledge о предметной области
              является knowledge об интерпретаторе (пользователе)
```

Это не противоречит существующей модели — это ортогональный слой,
как `AGENTS.md` ортогонален wiki-страницам.

### 7.3 Связь со skills-core

Из предыдущих разговоров: `skills-core` хранит cross-IDE паттерны.
`_user/profile.md` поле `current_ides` — источник для skills-core:

```yaml
# _user/profile.md
current_ides: [claude-code, codex, cursor]

# skills-core при /skill-port автоматически знает
# для каких IDE искать implementations
```

### 7.4 Связь с Health metrics

`10_KNOWLEDGE_HEALTH_METRICS.md` описывает `knowledge_health()` функцию.
`_user/context.md` поле `current_goal` может использоваться как контекст
для интерпретации метрик:

```
Здоровье вики: GOOD
Текущая цель: "построить skills систему"
→ Рекомендация: skills страниц 12, synthesis только 1 — есть куда расти
```

### 7.5 Совместимость с wizard из `11_Onboarding_Wizard.md`

Полная совместимость:
- `~/.reefiki/config.json` хранит `lang` — wizard уже читает его
- `_user/profile.md` дублирует `lang` для агентов без доступа к config.json
- Режимы wizard (quick/full) отражаются в `wizard_mode` поле profile.md
- Геймификация (серия, уровни) из wizard дополняется персональным приветствием

---

## 8. Action plan

Интегрирован с существующими action plans из аудитов.

| ID | Действие | Сложность | Приоритет | Зависит от |
|---|---|---|---|---|
| UC-01 | Добавить `create_user_context()` в `scripts/wizard.py` | S | P1 | WIZ-01 |
| UC-02 | Добавить 2 вопроса в режим Быстрый старт (WIZ-06) | S | P1 | WIZ-06 |
| UC-03 | Добавить блок User Profile в режим Полная настройка (WIZ-07) | S | P2 | WIZ-07 |
| UC-04 | Добавить `_user` в `public-snapshot.private-projects.txt` автоматически | S | P0 | UC-01 |
| UC-05 | Добавить секцию `_user/` в корневой `AGENTS.md` | S | P1 | UC-01 |
| UC-06 | Интегрировать `load_user_profile()` в dashboard (DASH-02) | S | P2 | DASH-01, UC-01 |
| UC-07 | Персонализировать приветствие dashboard из `_user/` | S | P3 | DASH-02, UC-06 |
| UC-08 | Добавить `_user/context.md` как источник active_project в dashboard | S | P2 | DASH-02 |
| UC-09 | Добавить предупреждение в wizard: что не хранить в `_user/` | S | P1 | UC-01 |
| UC-10 | Добавить drift detection для `_user/context.md` (>14 дней → напоминание) | S | P2 | UC-05 |
| UC-11 | Схема `_user/` в `SCHEMA_CHANGELOG.md` как v1.0 | S | P1 | MIG-04, UC-01 |

### Последовательность

```
WIZ-01 (wizard.py base)
  └─→ UC-01 (create_user_context)
        ├─→ UC-02 (quick mode вопросы)
        ├─→ UC-03 (full mode вопросы)
        ├─→ UC-04 (private-projects.txt) ← P0 безопасность
        ├─→ UC-05 (AGENTS.md секция)
        └─→ UC-09 (предупреждение в wizard)

DASH-01 (dashboard base)
  └─→ UC-06 (load_user_profile)
        ├─→ UC-07 (персональное приветствие)
        └─→ UC-08 (active_project из context)

MIG-04 (SCHEMA_CHANGELOG)
  └─→ UC-11 (_user/ в changelog)
```

---

## Итог: что изменилось vs первоначальный ответ

| Аспект | Первоначальный ответ | Скорректированный |
|---|---|---|
| Wizard | 3 простых вопроса отдельным блоком | Встроен в `11_Onboarding_Wizard.md`: 2 вопроса в Quick, блок в Full |
| Python версия | Не оговорена | Явно 3.11+, проверка в wizard |
| CRLF | Не упомянут | `newline="\n"` при всех write_text |
| Защита от публикации | "добавить в .gitignore" | Автоматически в `private-projects.txt` + права `0o700` |
| Dashboard | Абстрактно упомянут | Конкретная интеграция с FastAPI/Jinja2 из `12_DASHBOARD.md` |
| Pipedream | Упомянут как вариант | Не упоминается; только iOS Shortcut / Dashboard webhook |
| Obsidian | Обязателен для настройки | Опционален (решение из `13_ARCHITECTURE_DECISIONS.md`) |
| Лицензия модуля | Не упомянута | Apache 2.0 как часть core |
| Связь с skills-core | Не описана | `current_ides` → источник для /skill-port |
| Связь с health metrics | Не описана | `current_goal` → контекст для рекомендаций |

---

*Документ основан на 19 файлах аудита REEFIKI датированных 1–4 июня 2026.*
*Противоречия разрешены согласно `REEFIKI_AUDIT_ERRATA.md` как основному арбитру.*
