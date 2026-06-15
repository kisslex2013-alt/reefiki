# REEFIKI — Аудит: Конкурентный анализ

> Дата: 4 июня 2026. Часть комплексного аудита незатронутых тем.

## 9.1 Карта конкурентного ландшафта

```
                    Локальный ←————————————→ Облачный
                         │                        │
Простой ←————————————————┼————————————————————→ Сложный
                         │                        │
         Obsidian        │    Notion AI           │
         Logseq          │    Roam Research        │
         [REEFIKI]       │    Capacities           │
                         │    Mem0 / Zep           │
```

## 9.2 Детальное сравнение

**Notion AI**

| Параметр | Notion AI | REEFIKI |
|---|---|---|
| Хранение | Облако Notion | Локально (git) |
| AI-интеграция | Встроенная (GPT-4) | Любой агент |
| Структура | Свободная (блоки) | Типизированная (6 типов) |
| Поиск | Семантический (векторный) | FTS5 (ключевые слова) |
| Offline | ❌ | ✅ |
| Цена | $8–16/мес | Бесплатно |
| Vendor lock-in | Высокий | Нет (markdown) |
| Governance | Нет | ✅ |
| **Ключевое отличие REEFIKI** | — | Дистилляция vs архивация; governance layer |

**Roam Research**

| Параметр | Roam Research | REEFIKI |
|---|---|---|
| Модель | Bidirectional links, daily notes | Типизированные страницы, нет daily notes |
| Хранение | Облако Roam | Локально |
| Цена | $15/мес | Бесплатно |
| **Ключевое отличие REEFIKI** | — | Agent-native; нет daily notes (принципиально) |

**Logseq**

| Параметр | Logseq | REEFIKI |
|---|---|---|
| Хранение | Локально (markdown/EDN) | Локально (markdown) |
| Модель | Outliner + bidirectional links | Типизированные страницы |
| AI | Плагины | Любой агент (нативно) |
| Цена | Бесплатно (open-source) | Бесплатно |
| **Ключевое отличие REEFIKI** | — | Agent-first дизайн; governance; dual-remote publish |

**Capacities**

| Параметр | Capacities | REEFIKI |
|---|---|---|
| Модель | Object-based (типы объектов) | Типизированные страницы |
| Хранение | Облако | Локально |
| Цена | Freemium | Бесплатно |
| **Ключевое отличие REEFIKI** | — | Offline-first; open-source; agent-agnostic |

**Mem0 / Zep**

| Параметр | Mem0/Zep | REEFIKI |
|---|---|---|
| Назначение | Memory для AI-агентов | Knowledge base + memory control plane |
| Хранение | Облако (векторная БД) | Локально (markdown + SQLite) |
| Governance | Нет | ✅ |
| Offline | ❌ | ✅ |
| **Ключевое отличие REEFIKI** | — | Человек контролирует что сохраняется; нет vendor lock-in |

**Obsidian**

| Параметр | Obsidian | REEFIKI |
|---|---|---|
| Назначение | PKM для людей | PKM для людей + AI-агентов |
| AI | Плагины (Copilot, Smart Connections) | Нативный agent contract |
| Governance | Нет | ✅ |
| **Ключевое отличие REEFIKI** | — | REEFIKI использует Obsidian как viewer, добавляя governance layer |

## 9.3 Уникальное позиционирование

```
"Единственный agent-native knowledge control plane,
который работает локально, с любым AI-агентом,
с типизированным governance и без vendor lock-in"
```

**Три уникальных дифференциатора:**
1. **Agent-agnostic contract** — один `AGENTS.md` работает с Claude, GPT, Gemini, Cursor, Windsurf
2. **Governance layer** — `useful_when`, карантин, типы страниц, dual-remote publish
3. **Local-first + markdown** — данные ваши, работает офлайн, читается любым редактором

## 9.4 Угрозы от конкурентов

| Угроза | Вероятность | Влияние | Митигация |
|---|---|---|---|
| Notion добавляет offline-режим | Средняя | Высокое | Углублять governance, agent-native |
| Obsidian добавляет нативный AI-агент | Высокая | Высокое | REEFIKI как governance layer поверх Obsidian |
| Mem0 добавляет local-first режим | Низкая | Среднее | Типизация и governance сложнее скопировать |
| Новый open-source конкурент | Средняя | Среднее | First mover advantage, community |

## Action plan

| ID | Действие | Сложность | Приоритет |
|---|---|---|---|
| CA-01 | Добавить раздел "Сравнение с альтернативами" в README | M | P2 |
| CA-02 | Создать landing page с позиционированием | L | P3 |
| CA-03 | Мониторить Obsidian AI-плагины как потенциальных конкурентов | S | P2 |
| CA-04 | Усилить governance как ключевой дифференциатор в документации | S | P1 |
