# REEFIKI — Аудит: Локализация и мультиязычность

> Дата: 4 июня 2026. Часть комплексного аудита незатронутых тем.

## 2.1 Текущее состояние

Проект имеет документацию на трёх языках (RU, EN, ZH-CN), но **поисковый движок (SQLite FTS5) не настроен для мультиязычной работы**. Пользователь ведёт вики на русском, но поиск работает некорректно.

## 2.2 Как FTS5 токенизирует текст по умолчанию

```sql
-- Создание таблицы в build_index():
CREATE VIRTUAL TABLE pages_fts USING fts5(
    id, title, tags, useful_when, body
    -- tokenize не указан → используется unicode61 по умолчанию
);
```

**Токенизатор `unicode61`:**
- Разбивает текст по пробелам и знакам препинания
- Поддерживает Unicode (кириллица, китайский — как символы)
- **НЕ выполняет морфологический анализ**
- Поиск регистронезависимый для ASCII, но зависимый для кириллицы в некоторых конфигурациях SQLite

## 2.3 Проблемы поиска на русском языке

**Проблема 1 — Словоформы не матчатся:**

```
Запрос: "решение"
Не найдёт: "решения", "решению", "решений", "решениях"

Запрос: "сохранять"
Не найдёт: "сохранил", "сохраняет", "сохранение"
```

**Проблема 2 — Регистр кириллицы:**

SQLite `unicode61` выполняет case-folding для кириллицы начиная с версии 3.39.0 (2022). На более старых версиях поиск регистрозависим.

**Проблема 3 — Китайский язык (ZH-CN):**

Китайский не использует пробелы между словами. `unicode61` разбивает текст посимвольно:

```
Текст: "机器学习" (машинное обучение)
unicode61 токены: ["机", "器", "学", "习"] — каждый иероглиф отдельно
Правильные токены: ["机器", "学习"] — биграммы или слова
```

## 2.4 Решения

**Вариант A — Prefix queries (минимальный):**

```python
def escape_fts(query: str) -> str:
    FTS5_KEYWORDS = {"and", "or", "not", "near"}
    tokens = [
        f'"{t}"*'  # звёздочка = prefix match
        for t in re.findall(r"\w+", query, flags=re.UNICODE)
        if t.lower() not in FTS5_KEYWORDS
    ]
    return " OR ".join(tokens) if tokens else ""
```

**Вариант B — Внешний стеммер (рекомендуется для RU):**

```python
# pip install pymorphy3
import pymorphy3

morph = pymorphy3.MorphAnalyzer()

def stem_russian(word: str) -> str:
    parsed = morph.parse(word)
    if parsed:
        return parsed[0].normal_form
    return word

def escape_fts_multilang(query: str) -> str:
    FTS5_KEYWORDS = {"and", "or", "not", "near"}
    tokens = []
    for t in re.findall(r"\w+", query, flags=re.UNICODE):
        if t.lower() in FTS5_KEYWORDS:
            continue
        if re.search(r"[а-яёА-ЯЁ]", t):
            t = stem_russian(t)
        tokens.append(f'"{t}"')
    return " OR ".join(tokens) if tokens else ""
```

**Вариант C — jieba для китайского:**

```python
import jieba

def tokenize_chinese(text: str) -> str:
    return " ".join(jieba.cut(text))
```

## 2.5 Детектирование языка

```python
def detect_language(text: str) -> str:
    cyrillic = len(re.findall(r"[а-яёА-ЯЁ]", text))
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[a-zA-Z]", text))
    total = max(cyrillic + chinese + latin, 1)
    if cyrillic / total > 0.3:
        return "ru"
    if chinese / total > 0.3:
        return "zh"
    return "en"
```

## 2.6 Аудит документации

| Файл | Язык | Полнота | Проблемы |
|---|---|---|---|
| `README.md` | RU | ~100% | Основной, актуальный |
| `README.en.md` | EN | ~85% | Может отставать от RU |
| `README.zh-CN.md` | ZH | ~70% | Вероятно машинный перевод |
| `AGENTS.md` | RU | 100% | Только RU — критично для EN-агентов |
| `COMMANDS.md` | RU | 100% | Только RU |

**Критическая проблема:** `AGENTS.md` только на русском. Англоязычный агент (GPT, Gemini) получает контракт на языке, который может интерпретировать неточно.

## Action plan

| ID | Действие | Сложность | Приоритет |
|---|---|---|---|
| L10-01 | Добавить prefix wildcard в `escape_fts()` | S | P1 |
| L10-02 | Добавить `pymorphy3` для стемминга RU | M | P1 |
| L10-03 | Добавить `jieba` для токенизации ZH | M | P2 |
| L10-04 | Создать `AGENTS.en.md` или EN-секцию в `AGENTS.md` | M | P1 |
| L10-05 | Верифицировать `README.zh-CN.md` носителем языка | M | P2 |
| L10-06 | Добавить детектор языка в pipeline индексирования | M | P2 |
