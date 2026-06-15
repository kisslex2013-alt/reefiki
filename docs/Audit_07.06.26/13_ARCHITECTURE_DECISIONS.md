# REEFIKI — Аудит: Архитектурные решения: Obsidian и Pipedream

> Дата: 4 июня 2026. Стратегические вопросы по внешним зависимостям.

---

## 13.1 Отказаться от Obsidian?

### Решение: не отказываться, но сделать необязательным

Дашборд закрывает значительную часть функциональности Obsidian, но не всю.

### Что дашборд закрывает

| Функция | Obsidian | Дашборд |
|---|---|---|
| Поиск по вики | ✅ | ✅ (лучше — морфология) |
| Список страниц с фильтрами | ✅ | ✅ |
| Быстрое открытие страницы | ✅ | ✅ |
| Метрики здоровья | ❌ | ✅ |
| Копилка (inbox) | ❌ | ✅ |
| CLI-прозрачность | ❌ | ✅ |
| Онбординг wizard | ❌ | ✅ |

### Что дашборд НЕ закроет без серьёзных вложений

**Редактирование markdown:**
Dashboard read-only по философии — агент пишет, пользователь читает. Obsidian — полноценный редактор с live preview, vim-mode, таблицами.

**Граф связей:**
d3-force даст базовый граф, но Obsidian граф интерактивнее, красивее, с группировкой и физикой. Догнать — месяцы работы.

**Мобильное приложение:**
Obsidian Mobile уже есть, нативное. Свой мобильный клиент — отдельный продукт.

**Экосистема плагинов:**
Dataview, Templater, Calendar — годами разрабатывались.

### Целевая модель

```
Нетехнарь:   Дашборд (100% времени)  →  Obsidian не нужен
Технарь:    Дашборд (метрики, статус) + Obsidian (граф, редактирование)
Продвинутый: Только CLI + Obsidian  →  Дашборд не нужен
```

**Вывод:** дашборд делает Obsidian **необязательным**, а не ненужным. Убирает барьер входа, не убирает возможность.

Единственный сценарий полного отказа — если REEFIKI вырастет в продукт со своим редактором. Но это другой масштаб и другие ресурсы.

---

## 13.2 Отказаться от Pipedream?

### Решение: да, заменить — это несложно

Pipedream решает одну задачу: принять webhook от Telegram и положить файл в git. Это единственная внешняя платная зависимость в capture-flow.

### Три варианта замены

**Вариант A — GitHub Actions напрямую (рекомендуется):**

```
Telegram Bot → webhook → лёгкий сервер → GitHub repository_dispatch → Actions → inbox/
```

Telegram бот хостится бесплатно на Railway/Render/Fly.io. Принимает сообщение, вызывает `repository_dispatch` через GitHub API. GitHub Actions кладёт файл в inbox.

```python
# bot.py (минимальный Telegram бот)
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

ALLOWED_USER_IDS = {int(os.environ["TELEGRAM_USER_ID"])}
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPO"]  # "user/reefiki"

async def handle_message(update: Update, context):
    if update.effective_user.id not in ALLOWED_USER_IDS:
        return

    text = update.message.text or ""
    url = None
    for entity in (update.message.entities or []):
        if entity.type == "url":
            url = text[entity.offset:entity.offset + entity.length]

    # Вызвать GitHub Actions
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.github.com/repos/{REPO}/dispatches",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
            json={
                "event_type": "reefiki_save",
                "client_payload": {
                    "source": url or text,
                    "type": "url" if url else "text"
                }
            }
        )
    await update.message.reply_text("✅ Сохранено в копилку")
```

```yaml
# .github/workflows/reefiki-save.yml
name: REEFIKI Save from Telegram
on:
  repository_dispatch:
    types: [reefiki_save]

jobs:
  save:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - name: Save to inbox
        run: |
          python scripts/reefiki.py \
            --project projects/${{ vars.DEFAULT_PROJECT }} \
            save "${{ github.event.client_payload.source }}"
      - name: Commit
        run: |
          git config user.name "REEFIKI Bot"
          git config user.email "bot@reefiki"
          git add projects/
          git commit -m "inbox: save from Telegram" || exit 0
          git push
```

**Вариант B — Дашборд как webhook-приёмник (самый элегантный):**

```
Telegram Bot → webhook → reefiki dashboard (localhost) → inbox/ напрямую
```

Дашборд уже запущен локально. Добавить один endpoint:

```python
# В reefiki_dashboard.py
@app.post("/api/telegram/webhook")
async def telegram_webhook(update: dict):
    user_id = update.get("message", {}).get("from", {}).get("id")
    if user_id not in ALLOWED_USER_IDS:
        return {"ok": False}

    text = update["message"].get("text", "")
    entities = update["message"].get("entities", [])

    # Извлечь URL если есть
    source = text
    for entity in entities:
        if entity["type"] == "url":
            source = text[entity["offset"]:entity["offset"] + entity["length"]]
            break

    # Сохранить напрямую через reefiki.py
    result = save_source(get_project_path(config["last_project"]), source)
    return {"ok": result == 0}
```

Для публичного URL нужен Cloudflare Tunnel (бесплатно) или ngrok:

```bash
# Cloudflare Tunnel (бесплатно, без регистрации)
cloudflared tunnel --url http://localhost:7777
# → https://random-name.trycloudflare.com

# Зарегистрировать webhook в Telegram:
curl https://api.telegram.org/bot<TOKEN>/setWebhook \
  -d url=https://random-name.trycloudflare.com/api/telegram/webhook
```

**Вариант C — iOS Shortcut / Android (без сервера вообще):**

```
Share Sheet → Shortcut → GitHub API → inbox/
```

Никакого бота, никакого сервера. Shortcut делает прямой POST на GitHub API:

```
iOS Shortcut логика:
1. Получить вход из Share Sheet (URL или текст)
2. Сформировать имя файла: inbox-{timestamp}.md
3. Содержимое: входные данные как текст
4. POST https://api.github.com/repos/{REPO}/contents/projects/{PROJECT}/inbox/{filename}
   Authorization: Bearer {GITHUB_TOKEN}
   Body: {"message": "inbox: save from iOS", "content": base64(content)}
5. Показать уведомление: "✅ Сохранено в копилку"
```

### Сравнение вариантов

| Решение | Сложность | Стоимость | Надёжность | Зависимости |
|---|---|---|---|---|
| Pipedream (текущее) | S | $0–19/мес | Средняя | Pipedream |
| GitHub Actions напрямую | M | $0 | Высокая | GitHub |
| Дашборд как webhook | M | $0 | Высокая | ngrok/CF |
| iOS Shortcut | S | $0 | Высокая | GitHub API |

### Рекомендуемая стратегия

```
По умолчанию (всем):  iOS/Android Shortcut + GitHub API
  → Нуль внешних сервисов, работает всегда

Для пользователей с дашбордом:  Дашборд webhook + Cloudflare Tunnel
  → Самый элегантный, всё локально

Для пользователей без дашборда:  GitHub Actions напрямую
  → Надёжно, бесплатно, нужен лёгкий сервер для бота
```

---

## 13.3 Итоговая карта зависимостей

```
Текущее состояние:
  Обязательные:  Python, git
  Желательные:  Obsidian, uv, pre-commit
  Внешние:    Pipedream (платный), GitHub (hosting)

Целевое состояние:
  Обязательные:  Python, git
  Желательные:  uv, pre-commit
  Опциональные: Obsidian (для технарей), GitHub (hosting)
  Удалено:    Pipedream → iOS Shortcut / дашборд webhook
```

---

## 13.4 Action plan

| ID | Действие | Сложность | Приоритет |
|---|---|---|---|
| ARD-01 | Создать iOS Shortcut для сохранения в inbox через GitHub API | S | P1 |
| ARD-02 | Добавить `/api/telegram/webhook` в дашборд | S | P2 |
| ARD-03 | Создать `.github/workflows/reefiki-save.yml` для GitHub Actions | M | P2 |
| ARD-04 | Документировать настройку Cloudflare Tunnel для дашборд-webhook | S | P2 |
| ARD-05 | Удалить упоминания Pipedream из документации | S | P2 |
| ARD-06 | Обновить `docs/mobile-capture.md` с новыми вариантами | S | P2 |
| ARD-07 | Обновить README: Obsidian опционален, не обязателен | S | P3 |
