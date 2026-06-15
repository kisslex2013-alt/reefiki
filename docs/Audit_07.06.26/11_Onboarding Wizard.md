# REEFIKI — Аудит: Onboarding Wizard и установка

> Дата: 4 июня 2026. Дополнительная тема по результатам анализа UX и accessibility.

---

## 11.1 Текущее состояние

Установка REEFIKI требует от пользователя самостоятельно:
- Установить Python 3.11+, git, pre-commit, опционально uv
- Клонировать репозиторий
- Настроить git remotes, memoir store, pre-commit хуки
- Создать первый проект вручную

**Реальное время для нетехнического пользователя: 30–60 минут.** Главная проблема не в количестве шагов, а в том, что пользователь не понимает зачем каждый шаг — он следует инструкции вслепую.

---

## 11.2 Концепция: одна команда

Единственное, что нужно знать пользователю:

**macOS / Linux:**
```bash
curl -fsSL https://reefiki.dev/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://reefiki.dev/install.ps1 | iex
```

Дальше — интерактивный wizard прямо в терминале. Никаких файлов скачивать вручную, никаких инструкций читать заранее. Паттерн проверен: Homebrew, uv, Rust (`rustup`), Deno используют ровно эту модель.

---

## 11.3 Шаг 0 — Выбор языка

Первое, что видит пользователь — выбор языка интерфейса wizard. Это важно: нетехнический пользователь может не читать по-английски, а технарь может предпочесть EN для консистентности с документацией.

```
╔══════════════════════════════════════════════╗
║              REEFIKI  v0.1.0                 ║
╚══════════════════════════════════════════════╝

Select language / Выберите язык / 选择语言:

  1) English
  2) Русский
  3) 中文

[1]:
```

После выбора — весь дальнейший wizard на выбранном языке. Выбор сохраняется в `~/.reefiki/config.json` и используется при повторных запусках.

**Реализация:**

```python
# scripts/wizard.py

LANGUAGES = {
    "1": "en",
    "2": "ru",
    "3": "zh",
}

STRINGS = {
    "en": {
        "welcome": "Welcome to REEFIKI!",
        "checking_env": "Checking environment...",
        "choose_mode": "How would you like to start?",
        "quick_start": "Quick start — defaults, ready in 2 minutes",
        "full_setup": "Full setup — choose folder, remotes, memoir",
        "open_project": "Open existing project",
        "dashboard": "Launch dashboard in browser",
        # ...
    },
    "ru": {
        "welcome": "Добро пожаловать в REEFIKI!",
        "checking_env": "Проверяю окружение...",
        "choose_mode": "Как хочешь начать?",
        "quick_start": "Быстрый старт — всё по умолчанию, 2 минуты",
        "full_setup": "Полная настройка — папка, remotes, memoir",
        "open_project": "Открыть существующий проект",
        "dashboard": "Запустить дашборд в браузере",
        # ...
    },
    "zh": {
        "welcome": "欢迎使用 REEFIKI！",
        "checking_env": "检查环境...",
        "choose_mode": "您想如何开始？",
        "quick_start": "快速开始 — 默认设置，2分钟内完成",
        "full_setup": "完整设置 — 选择文件夹、远程仓库、memoir",
        "open_project": "打开现有项目",
        "dashboard": "在浏览器中启动仪表板",
        # ...
    },
}

def t(key: str, lang: str) -> str:
    """Возвращает строку на выбранном языке."""
    return STRINGS.get(lang, STRINGS["en"]).get(key, key)
```

---

## 11.4 Шаг 1 — Проверка окружения

После выбора языка wizard автоматически проверяет всё необходимое:

```
╔══════════════════════════════════════════════╗
║         REEFIKI — Добро пожаловать!          ║
╚══════════════════════════════════════════════╝

Проверяю окружение...

  ✅ Python 3.12.1
  ✅ git 2.43.0
  ⚠️  uv не найден (memoir-слой будет недоступен)
     Установить сейчас? [Y/n]: Y
     Устанавливаю uv... ✅ готово

  ⚠️  pre-commit не найден (проверки при коммите отключены)
     Установить сейчас? [Y/n]: n
     ℹ️  Можно установить позже: pip install pre-commit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Логика проверок:**

```python
import shutil, subprocess, sys

def check_environment(lang: str) -> dict:
    results = {}

    # Python — уже запущен, просто проверяем версию
    v = sys.version_info
    results["python"] = {
        "ok": v >= (3, 11),
        "version": f"{v.major}.{v.minor}.{v.micro}",
        "fix": "https://python.org — установи Python 3.11+"
    }

    # git
    git = shutil.which("git")
    results["git"] = {
        "ok": git is not None,
        "version": _run_version("git", "--version"),
        "fix": "https://git-scm.com"
    }

    # uv (опционально)
    results["uv"] = {
        "ok": shutil.which("uvx") is not None,
        "optional": True,
        "install_cmd": {
            "unix": "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "win":  "powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
        }
    }

    # pre-commit (опционально)
    results["pre_commit"] = {
        "ok": shutil.which("pre-commit") is not None,
        "optional": True,
        "install_cmd": "pip install pre-commit"
    }

    return results

def offer_install(tool: str, results: dict, lang: str) -> bool:
    """Предлагает установить опциональный инструмент."""
    if results[tool]["ok"]:
        return True
    answer = input(f"     Установить сейчас? [Y/n]: ").strip().lower()
    if answer in ("", "y", "yes", "д", "да"):
        cmd = results[tool]["install_cmd"]
        platform_cmd = cmd["win"] if sys.platform == "win32" else cmd["unix"]
        subprocess.run(platform_cmd, shell=True)
        return shutil.which(tool) is not None
    return False
```

**Критический блокер** — если Python < 3.11 или git отсутствует, wizard останавливается с понятным сообщением:

```
  ❌ Python 3.10.6 — нужна версия 3.11 или новее.

  Как обновить:
    Windows:  https://python.org/downloads/
    macOS:    brew install python@3.11
    Ubuntu:   sudo add-apt-repository ppa:deadsnakes/ppa
              sudo apt install python3.11

  После обновления запусти установку снова.
```

---

## 11.5 Шаг 2 — Выбор режима

Ключевой момент: **выбор режима естественно разделяет аудитории** без вопроса "вы технарь?":

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Как хочешь начать?

  1) 🚀 Быстрый старт     — всё по умолчанию, готово за 2 минуты
  2) 🔧 Полная настройка  — выбрать папку, git remote, memoir и т.д.
  3) 📂 Открыть проект    — уже есть папка REEFIKI на этом компьютере
  4) 🌐 Только дашборд    — запустить веб-интерфейс без настройки

Выбор [1]:
```

Нетехнарь жмёт Enter → Быстрый старт.
Технарь выбирает 2 → Полная настройка.
Уже есть REEFIKI → выбирает 3.

---

## 11.6 Режим 1 — Быстрый старт

Минимум вопросов, максимум автоматики:

```
🚀 Быстрый старт
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Где создать REEFIKI?
  [~/REEFIKI]: ↵

Как назвать первый проект?
  Примеры: работа, учёба, исследование, заметки
  > заметки

Запускать дашборд в браузере? [Y/n]: ↵

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Настраиваю...

  ✅ Создана папка ~/REEFIKI
  ✅ Инициализирован git репозиторий
  ✅ Создан проект "заметки"
  ✅ Построен поисковый индекс
  ✅ Дашборд запущен → http://localhost:7777

Открываю браузер...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Готово! Что дальше:

  • Открой http://localhost:7777 в браузере
  • Или скажи AI-агенту: "сохрани эту ссылку"
  • Справка: reefiki help
```

**Что происходит под капотом:**

```python
def quick_start(lang: str) -> None:
    # 1. Папка
    default_path = Path.home() / "REEFIKI"
    raw = input(f"  [{default_path}]: ").strip()
    reefiki_path = Path(raw) if raw else default_path
    reefiki_path.mkdir(parents=True, exist_ok=True)

    # 2. git init
    subprocess.run(["git", "init"], cwd=reefiki_path, capture_output=True)

    # 3. Клонировать шаблон или скачать архив
    _bootstrap_from_template(reefiki_path)

    # 4. Первый проект
    project_name = input("  > ").strip() or "my-wiki"
    _create_project(reefiki_path, project_name)

    # 5. Индекс
    subprocess.run(
        [sys.executable, "scripts/reefiki.py",
         "--project", f"projects/{project_name}", "index"],
        cwd=reefiki_path
    )

    # 6. Сохранить конфиг
    _save_config({
        "reefiki_path": str(reefiki_path),
        "lang": lang,
        "dashboard_autostart": True,
        "last_project": project_name,
    })

    # 7. Дашборд
    _launch_dashboard(reefiki_path)
```

---

## 11.7 Режим 2 — Полная настройка

Для технарей — все опции:

```
🔧 Полная настройка
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Папка для REEFIKI:
  [~/REEFIKI]: /data/wiki

Git remote (origin) — приватный репозиторий:
  Введи URL или Enter чтобы пропустить:
  > git@github.com:user/reefiki.git
  ✅ Remote "origin" добавлен

Второй remote (public snapshot):
  Введи URL или Enter чтобы пропустить:
  > ↵

Memoir store (слой краткосрочной памяти):
  1) Стандартный (~/.local/share/memoir/reefiki)
  2) Указать путь вручную
  3) Пропустить
  [1]: ↵
  ✅ Memoir store: ~/.local/share/memoir/reefiki

Установить pre-commit хуки? [Y/n]: Y
  ✅ pre-commit install — готово

Запускать дашборд при старте? [y/N]: n

Создать первый проект сейчас? [Y/n]: Y
  Название: research
  ✅ Проект "research" создан

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Готово!

  Запуск:         reefiki status
  Дашборд:        reefiki dashboard
  Документация:   reefiki help
  Конфиг:         ~/.reefiki/config.json
```

---

## 11.8 Режим 3 — Открыть существующий проект

Для пользователей, которые уже клонировали REEFIKI вручную или переносят на новый компьютер:

```
📂 Открыть существующий проект
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Путь к папке REEFIKI:
  > /home/user/REEFIKI

Проверяю структуру...
  ✅ Найдено 3 проекта: research, notes, work
  ✅ git репозиторий
  ⚠️  Индекс устарел (последнее обновление: 5 дней назад)
     Пересобрать сейчас? [Y/n]: Y
     ✅ Индекс пересобран (127 страниц)

Запустить дашборд? [Y/n]: Y
  ✅ Дашборд → http://localhost:7777
```

---

## 11.9 Режим 4 — Только дашборд

Для случая когда REEFIKI уже настроен и нужно просто открыть интерфейс:

```
🌐 Запуск дашборда
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Найден конфиг: ~/.reefiki/config.json
  Путь: ~/REEFIKI
  Проекты: research, notes, work

  ✅ Дашборд запущен → http://localhost:7777

  Остановить: Ctrl+C
```

---

## 11.10 Повторный запуск и глобальная команда

После установки `reefiki` становится глобальной командой:

```bash
# Показать статус (как сейчас)
reefiki status

# Повторный wizard
reefiki wizard

# Только дашборд
reefiki dashboard

# Создать новый проект
reefiki new <имя>

# Обновить REEFIKI
reefiki update

# Справка
reefiki help
```

**Умный запуск без аргументов:**

```python
# Если запустить просто "reefiki" без аргументов:
def smart_default():
    config = load_config()

    if not config:
        # Первый запуск — запустить wizard
        run_wizard()
    elif config.get("dashboard_autostart"):
        # Настроен автозапуск дашборда
        launch_dashboard()
    else:
        # Показать статус всех проектов
        show_status_all()
```

---

## 11.11 Конфигурационный файл

Wizard сохраняет настройки в `~/.reefiki/config.json` — вне репозитория, чтобы не попасть в git:

```json
{
  "version": "0.1.0",
  "lang": "ru",
  "reefiki_path": "/home/user/REEFIKI",
  "last_project": "research",
  "dashboard_autostart": false,
  "dashboard_port": 7777,
  "memoir_store": "/home/user/.local/share/memoir/reefiki",
  "setup_completed": true,
  "setup_mode": "full",
  "created_at": "2026-06-04T10:00:00"
}
```

---

## 11.12 Установочные скрипты

**`install.sh` (macOS/Linux) — минимальный:**

```bash
#!/usr/bin/env bash
set -euo pipefail

REEFIKI_VERSION="0.1.0"
INSTALL_DIR="$HOME/.local/bin"

echo "Устанавливаю REEFIKI $REEFIKI_VERSION..."

# Проверка Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python не найден. Установи Python 3.11+: https://python.org"
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PY_MINOR" -lt 11 ]; then
    echo "❌ Python $PY_VERSION — нужна версия 3.11+."
    exit 1
fi

# Скачать и установить через pipx или pip
if command -v pipx &>/dev/null; then
    pipx install reefiki
elif command -v pip3 &>/dev/null; then
    pip3 install --user reefiki
else
    echo "❌ pip не найден."
    exit 1
fi

echo "✅ REEFIKI установлен."
echo ""
echo "Запусти wizard:"
echo "  reefiki wizard"
```

**`install.ps1` (Windows):**

```powershell
$ErrorActionPreference = "Stop"

Write-Host "Устанавливаю REEFIKI..." -ForegroundColor Cyan

# Проверка Python
try {
    $pyVersion = python --version 2>&1
    $minor = [int]($pyVersion -replace "Python 3\.(\d+)\..*", '$1')
    if ($minor -lt 11) {
        Write-Host "❌ $pyVersion — нужна версия 3.11+" -ForegroundColor Red
        Write-Host "Скачай: https://python.org/downloads/"
        exit 1
    }
    Write-Host "✅ $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден. Скачай: https://python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Установка
pip install reefiki --quiet
Write-Host "✅ REEFIKI установлен." -ForegroundColor Green
Write-Host ""
Write-Host "Запусти wizard:" -ForegroundColor Yellow
Write-Host "  reefiki wizard"
```

---

## 11.13 Геймификация в wizard

Wizard — первое впечатление от продукта. Небольшие элементы геймификации здесь уместны:

**Прогресс-бар при настройке:**
```
Настраиваю REEFIKI...

  [████████████████████░░░░] 80%

  ✅ Папка создана
  ✅ git инициализирован
  ✅ Шаблон скопирован
  ✅ Проект создан
  ⏳ Строю индекс...
```

**Приветствие после завершения:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 REEFIKI готов к работе!

  Твоя вики пока пустая — это нормально.
  Первый шаг: сохрани что-нибудь интересное.

  Попробуй прямо сейчас:
    reefiki save https://example.com/article

  Или открой дашборд: http://localhost:7777
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Уровень при первом `/status` после наполнения:**
```
📊 Статус: заметки

  Страниц: 12  |  🌱 Начинающий
  ─────────────────────────────
  До уровня "Практик": ещё 38 страниц
  (или улучши качество: 4 страницы без useful_when)
```

---

## 11.14 Action plan

| ID | Действие | Сложность | Приоритет |
|---|---|---|---|
| WIZ-01 | Создать `scripts/wizard.py` с выбором языка и режима | M | P1 |
| WIZ-02 | Создать `install.sh` для macOS/Linux | S | P1 |
| WIZ-03 | Создать `install.ps1` для Windows | S | P1 |
| WIZ-04 | Добавить `~/.reefiki/config.json` как конфиг wizard | S | P1 |
| WIZ-05 | Реализовать проверку окружения с предложением установки | M | P1 |
| WIZ-06 | Реализовать режим "Быстрый старт" | M | P1 |
| WIZ-07 | Реализовать режим "Полная настройка" | M | P2 |
| WIZ-08 | Реализовать режим "Открыть существующий проект" | S | P2 |
| WIZ-09 | Добавить `reefiki` как глобальную команду (pyproject.toml) | S | P1 |
| WIZ-10 | Добавить прогресс-бар и геймификацию в wizard | S | P3 |
| WIZ-11 | Добавить строки локализации для EN/RU/ZH | M | P2 |
| WIZ-12 | Зарегистрировать домен reefiki.dev и разместить install-скрипты | M | P2 |