---
name: debug-migration
description: Debug Piccolo ORM migration issues in Hyper-Porto. Use when the user mentions миграция не работает, ошибка piccolo, migration error, database error, таблица не создана, поле не добавилось.
---

# Debug Piccolo Migration Issues

Отладка проблем с миграциями Piccolo ORM.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Troubleshooting** | `agent-os/troubleshooting/import-errors.md` |
| **Standard** | `agent-os/standards/backend/migrations.md` |
| **Library docs** | <https://piccolo-orm.com/docs/> |

## Quick Diagnostic

| Симптом | Причина | Решение |
|---------|---------|---------|
| `Table not found` | Migration не применена | `uv run piccolo migrations forwards` |
| `Column not found` | Missing migration | Создать новую миграцию |
| `Migration failed` | Syntax/constraint error | Проверить migration file |
| `Duplicate column` | Migration run twice | `uv run piccolo migrations check` |
| `Foreign key error` | Wrong table order | Fix migration dependencies |

## Действие

1. **Загрузи** полный гайд из `agent-os/standards/backend/migrations.md`
2. **Проверь** статус: `uv run piccolo migrations check`
3. **Определи** тип проблемы
4. **Исправь** по инструкции

## Команды

```bash
# Check status
uv run piccolo migrations check

# Create migration
uv run piccolo migrations new {app_name} --auto

# Apply migrations
uv run piccolo migrations forwards {app_name}

# Rollback
uv run piccolo migrations backwards {app_name}

# Mark as applied (fake)
uv run piccolo migrations forwards {app_name} --fake
```

## Common Fixes

### PiccoloApp не зарегистрирован

```python
# In piccolo_conf.py
APP_REGISTRY = AppRegistry(
    apps=[
        "src.Containers.AppSection.UserModule.Models.PiccoloApp",  # Add!
    ]
)
```

### PiccoloApp.py отсутствует

```python
# Create Models/PiccoloApp.py
from piccolo.conf.apps import AppConfig, table_finder

APP_CONFIG = AppConfig(
    app_name="user",  # Unique name
    table_classes=table_finder(["src.Containers.AppSection.UserModule.Models"]),
    migration_module="src.Containers.AppSection.UserModule.Models.migrations",
)
```

## Checklist

```
- [ ] uv run piccolo migrations check выполнен
- [ ] PiccoloApp.py существует в Models/
- [ ] PiccoloApp зарегистрирован в piccolo_conf.py
- [ ] DB connection settings корректны
- [ ] Migration file проверен
- [ ] uv run piccolo migrations forwards выполнен
```
