# REEFIKI — Аудит: Mobile и capture-flow

> Дата: 4 июня 2026. Часть комплексного аудита незатронутых тем.

## 6.1 Текущее состояние

CHANGELOG упоминает: «Sprint 4: mobile capture через GitHub Actions/Pipedream flow.» Архитектура:

```
Telegram Bot → Pipedream → GitHub Actions → inbox/ в репозитории
```

## 6.2 Аудит безопасности Telegram-бота

**Риск 1 — Отсутствие аутентификации отправителя (CRITICAL):**

Если бот принимает сообщения от любого пользователя Telegram — любой, кто знает username бота, может добавлять контент в вашу вики.

```python
# Необходимая проверка в webhook handler:
ALLOWED_TELEGRAM_USER_IDS = {123456789}  # ваш Telegram user_id

def handle_message(update):
    if update.message.from_user.id not in ALLOWED_TELEGRAM_USER_IDS:
        update.message.reply_text("Доступ запрещён.")
        return
    # ... обработка сообщения
```

**Риск 2 — Контент без валидации:**

Сообщение из Telegram попадает в `inbox/` без проверок `/save`:
- Нет проверки на секреты (SECRET_PATTERNS)
- Нет проверки размера
- Нет dedup-проверки

**Риск 3 — Токен бота:**

| Место хранения | Безопасность |
|---|---|
| GitHub Actions secrets | ✅ Безопасно |
| Pipedream environment variables | ✅ Безопасно |
| Hardcoded в workflow YAML | ❌ Критическая утечка |
| В `.env` файле в репозитории | ❌ Критическая утечка |

## 6.3 Аудит надёжности Pipedream pipeline

**Проблема 1 — Single point of failure:**
```
Telegram → Pipedream → GitHub API → Actions → git push
```
Каждое звено может упасть. Нет retry-логики, нет dead letter queue.

**Проблема 2 — Latency:**
```
Отправка в Telegram → появление в inbox/: 30 сек – 5 минут
```

**Проблема 3 — Vendor lock-in:**
Pipedream — платный сервис. При превышении лимитов pipeline перестаёт работать.

## 6.4 Альтернативы

| Решение | Плюсы | Минусы | Сложность |
|---|---|---|---|
| Telegram + Pipedream (текущее) | Быстро настроить | Vendor lock-in, платный | — |
| Telegram + self-hosted bot | Контроль, бесплатно | Нужен сервер | M |
| Email → inbox/ | Универсально | Нужен email-парсер | M |
| iOS Shortcut / Android Tasker | Нативно, без сервера | Платформозависимо | S |
| Obsidian Mobile + git | Уже в экосистеме | Требует git на телефоне | M |

**iOS Shortcut (без сервера):**
```
1. Получить текст/URL из Share Sheet
2. POST на GitHub API: создать файл в inbox/
3. Показать уведомление «Сохранено в копилку»
```

## 6.5 Необходимая документация

Нет ни одного файла, описывающего как настроить mobile capture. Необходимо создать `docs/mobile-capture.md` с:
- Инструкцией по настройке Telegram бота
- Обязательным шагом: ограничение по user_id
- Альтернативами для iOS/Android
- Инструкцией по хранению токенов

## Action plan

| ID | Действие | Сложность | Приоритет |
|---|---|---|---|
| MOB-01 | Создать `docs/mobile-capture.md` | M | P1 |
| MOB-02 | Добавить аутентификацию по user_id в Telegram bot | S | **P0** |
| MOB-03 | Добавить валидацию контента (SECRET_PATTERNS) в webhook | M | P1 |
| MOB-04 | Добавить retry-логику и уведомление об ошибках | M | P2 |
| MOB-05 | Создать iOS Shortcut как альтернативу | M | P2 |
| MOB-06 | Документировать альтернативы Pipedream | S | P2 |
