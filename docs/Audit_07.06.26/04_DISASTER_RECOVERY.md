# REEFIKI — Аудит: Disaster Recovery и бэкап-стратегия

> Дата: 4 июня 2026. Часть комплексного аудита незатронутых тем.

## 4.1 Текущее состояние защиты данных

```
Единственная защита: git push в origin (private remote)
Частота: ручная, после каждого /harvest или по желанию
Автоматизация: отсутствует
Мониторинг: отсутствует
```

## 4.2 Что теряется при разных сценариях отказа

| Сценарий | Что теряется | Восстановимо? |
|---|---|---|
| Повреждение `index.sqlite` | Только индекс | ✅ `/reindex` пересоздаёт |
| Случайное удаление wiki-страницы | Страница | ✅ `git checkout HEAD -- <file>` |
| Случайный `git reset --hard` | Незакоммиченные изменения | ❌ Безвозвратно |
| Потеря локального репозитория (диск) | Всё незапушенное | ❌ Безвозвратно |
| Компрометация GitHub/GitLab аккаунта | Весь репозиторий | ⚠️ Только если есть локальная копия |
| Случайная публикация приватного проекта | Утечка данных | ❌ Нельзя «забыть» из интернета |

## 4.3 Integrity check для sqlite

```python
def check_index_integrity(project: Path) -> bool:
    db = db_path(project)
    if not db.exists():
        return False
    try:
        conn = sqlite3.connect(db)
        result = conn.execute("PRAGMA integrity_check").fetchone()
        return result[0] == "ok"
    except sqlite3.DatabaseError:
        return False

# В build_index() или search_existing():
if not check_index_integrity(project):
    db_path(project).unlink(missing_ok=True)
    build_index(project)
```

## 4.4 Стратегия бэкапов — уровни защиты

**Уровень 1 — Git (уже есть, но не автоматизирован):**

```bash
# cron каждые 6 часов:
0 */6 * * * cd /path/to/reefiki && git add -A && git commit -m "auto-backup $(date +%Y-%m-%d-%H%M)" && git push origin main
```

**Уровень 2 — Локальный бэкап:**

```python
def backup_project(project: Path, backup_dir: Path) -> Path:
    import tarfile
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{project.name}_{timestamp}.tar.gz"
    with tarfile.open(backup_path, "w:gz") as tar:
        tar.add(project / "wiki", arcname="wiki")
        tar.add(project / "raw", arcname="raw")
        tar.add(project / "seen", arcname="seen")
    return backup_path
```

**Уровень 3 — Стратегия 3-2-1:**

```
3 копии данных
2 разных носителя (локальный диск + git remote)
1 offsite (второй git remote: Codeberg, Gitea self-hosted, или зашифрованный S3)

git remote add backup git@codeberg.org:user/reefiki-backup.git
git push backup main
```

## 4.5 Recovery Runbook (добавить в docs/RECOVERY.md)

```markdown
## Сценарий 1: Повреждён index.sqlite
python scripts/reefiki.py --project <name> index

## Сценарий 2: Случайно удалена wiki-страница
git log --oneline -- projects/<name>/wiki/<path>.md
git checkout <commit-hash> -- projects/<name>/wiki/<path>.md

## Сценарий 3: Потерян локальный репозиторий
git clone git@github.com:user/reefiki.git
python scripts/reefiki.py --project <name> index

## Сценарий 4: Откат последних N коммитов
git log --oneline -10
git revert HEAD~N..HEAD

## Сценарий 5: Утечка секрета в git history
pip install git-filter-repo
git filter-repo --invert-paths --path <file-with-secret>
git push origin --force --all
# Немедленно ротировать скомпрометированный секрет!
```

## Action plan

| ID | Действие | Сложность | Приоритет |
|---|---|---|---|
| DR-01 | Добавить `docs/RECOVERY.md` | S | **P0** |
| DR-02 | Добавить integrity check для sqlite | S | P1 |
| DR-03 | Добавить команду `backup` в CLI | M | P1 |
| DR-04 | Документировать стратегию 3-2-1 в README | S | P1 |
| DR-05 | Добавить проверку freshness бэкапа в `status --bootstrap` | S | P2 |
| DR-06 | Добавить cron/Task Scheduler инструкции в QUICKSTART | S | P2 |
