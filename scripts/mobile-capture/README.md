# Mobile Capture — руководство

> Два способа — оба используют один GitHub Action backend.
> Выбери любой или оба.

---

## Способ A — Telegram бот (рекомендуется)

Отправляешь ссылку в чат → файл появляется в `inbox/`. Работает на Android и iOS.

### A1. Создать бота

1. Открой Telegram → `@BotFather` → `/newbot`
2. Название: `REEFIKI Capture`, username: `reefiki_capture_bot` (или любой свободный)
3. Скопируй **Telegram Bot Token** вида `7123456789:AAF...`

### A2. Настроить Pipedream workflow

1. Зарегистрируйся на [pipedream.com](https://pipedream.com) (бесплатно, 100 запусков/день)
2. `New Project → New Workflow`
3. **Trigger:** `Telegram Bot API → New Message`
   - Вставь Telegram Bot Token
4. **Step 1:** `Python` (или Node.js) — код ниже
5. Сохрани и задеплой

**Код для шага Python:**

```python
import os, requests

msg = steps["trigger"]["event"]["message"]
text = msg.get("text", "").strip()
chat_id = msg["chat"]["id"]

# Извлечь URL (первое слово если начинается с http)
parts = text.split(None, 1)
url = parts[0] if parts and parts[0].startswith("http") else text
note = parts[1] if len(parts) > 1 else ""

# Определить проект: первое слово после URL если это имя проекта
# Например: "https://... metrica заметка" → project=metrica
PROJECTS = ["reefiki", "metrica"]
note_parts = note.split(None, 1)
if note_parts and note_parts[0] in PROJECTS:
    project = note_parts[0]
    note = note_parts[1] if len(note_parts) > 1 else ""
else:
    project = "reefiki"  # проект по умолчанию

PAT = os.environ["GITHUB_PAT"]
REPO = "kisslex2013-alt/reefiki-personal"

resp = requests.post(
    f"https://api.github.com/repos/{REPO}/dispatches",
    headers={
        "Authorization": f"Bearer {PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    json={
        "event_type": "inbox-capture",
        "client_payload": {"project": project, "url": url, "note": note},
    },
)

# Подтвердить пользователю
requests.post(
    f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
    json={"chat_id": chat_id, "text": f"✅ Сохранено в {project}/inbox" if resp.status_code == 204 else f"❌ Ошибка {resp.status_code}"},
)
```

6. В Pipedream → **Environment Variables** добавь:
   - `GITHUB_PAT` — твой PAT (из Шага 1 основного README)
   - `TELEGRAM_TOKEN` — токен бота из A1

### A3. Использование

Просто отправь ссылку боту:

```text
https://example.com/article
```

Или с проектом и заметкой:

```text
https://example.com/article metrica важная статья про sync
```
Бот ответит `✅ Сохранено в reefiki/inbox`.

---

Отправляет URL или заметку прямо в `inbox/` репозитория с телефона — без IDE, без сервера.

## Как это работает

1. Ты отправляешь HTTP-запрос к GitHub API с GitHub Actions dispatch
2. GitHub Actions создаёт файл в `projects/<project>/inbox/<timestamp>-<slug>.md`
3. Коммитит и пушит — файл появляется в репо

**Не нужен:** сервер, бот-хостинг, платные сервисы.

---

## Шаг 1 — Создать GitHub PAT

1. Открой `github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens`
2. `Generate new token`
3. Настройки:
   - **Repository access:** только `kisslex2013-alt/reefiki-personal`
   - **Permissions → Contents:** `Read and write`
   - **Permissions → Actions:** `Read and write`
4. Скопируй токен — он нужен на Шаге 2

---

## Шаг 2 — iOS Shortcut

### Создание

1. Открой приложение **Быстрые команды (Shortcuts)**
2. Создай новую команду `+`
3. Добавь действие **«Текст»** — введи свой PAT токен (скопируй из Шага 1)
4. Добавь действие **«Получить содержимое URL»** со следующими параметрами:

**URL:**
```
https://api.github.com/repos/kisslex2013-alt/reefiki-personal/dispatches
```

**Метод:** POST

**Заголовки:**
```
Authorization: Bearer <вставь токен>
Accept: application/vnd.github+json
Content-Type: application/json
X-GitHub-Api-Version: 2022-11-28
```

**Тело (JSON):**
```json
{
  "event_type": "inbox-capture",
  "client_payload": {
    "project": "metrica",
    "url": "Ввод при запуске",
    "note": ""
  }
}
```

5. Замени `"Ввод при запуске"` на переменную **«Спросить каждый раз»** из Shortcuts
6. Сохрани команду — назови `REEFIKI Save`

### Использование

- Поделись ссылкой из Safari/Chrome → выбери `REEFIKI Save`
- Или запусти вручную и введи URL

---

## Шаг 3 — Проверка

Сделай тестовый захват. Через 30-60 секунд файл должен появиться в:
```
projects/metrica/inbox/YYYYMMDD-HHMMSS-<slug>.md
```

Проверь на github.com или при следующем `git pull`.

---

## Curl-тест (с компьютера)

```powershell
$PAT = "ghp_ваш_токен"
$body = @{
  event_type = "inbox-capture"
  client_payload = @{
    project = "metrica"
    url = "https://example.com/test"
    note = "тест из curl"
  }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod `
  -Uri "https://api.github.com/repos/kisslex2013-alt/reefiki-personal/dispatches" `
  -Method POST `
  -Headers @{
    "Authorization" = "Bearer $PAT"
    "Accept" = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
  } `
  -Body $body `
  -ContentType "application/json"
```

---

## Формат файла в inbox

```
https://example.com/article

опциональная заметка
```

Минимально: одна строка с URL. Агент разберёт при `/process`.

---

## Безопасность

- PAT храни только в iOS Shortcuts Keychain (не в тексте заметок)
- Создай отдельный PAT с минимальными правами (только этот репо)
- При компрометации — удали PAT на github.com, создай новый
