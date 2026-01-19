# Database Migrations — Piccolo ORM

> Стандарты миграций базы данных для Piccolo ORM.

---

## 📁 Структура

```
Containers/{Section}/{Module}/Models/
├── PiccoloApp.py         # Piccolo App конфигурация
├── {Entity}.py           # Table definition
└── migrations/           # Авто-генерируемые миграции
    ├── __init__.py
    └── {table}_{timestamp}.py
```

---

## 🔧 PiccoloApp.py

```python
# Containers/AppSection/UserModule/Models/PiccoloApp.py
from piccolo.conf.apps import AppConfig, table_finder

APP_CONFIG = AppConfig(
    app_name="user_module",
    table_classes=table_finder(
        modules=["src.Containers.AppSection.UserModule.Models.User"],
    ),
    migration_folder_path="src/Containers/AppSection/UserModule/Models/migrations",
)
```

---

## 📋 Регистрация в piccolo_conf.py

```python
# piccolo_conf.py (root)
from piccolo.conf.apps import AppRegistry
from piccolo.engine.sqlite import SQLiteEngine
from src.Ship.Configs import get_settings

settings = get_settings()
DB = SQLiteEngine(path=settings.db_url.replace("sqlite:///", ""))

APP_REGISTRY = AppRegistry(
    apps=[
        "src.Containers.AppSection.UserModule.Models.PiccoloApp",
        "src.Containers.AppSection.NotificationModule.Models.PiccoloApp",
        # ... другие модули
    ],
)
```

---

## 🚀 CLI Команды

### Создание миграции

```bash
# Автогенерация из изменений моделей
litestar db make-migrations --auto

# С кастомным описанием
litestar db make-migrations --auto --description "add user roles"
```

### Применение миграций

```bash
# Применить все pending миграции
litestar db migrate

# Проверить статус
litestar db status
```

### Откат

```bash
# Откатить последнюю миграцию
litestar db migrate --reverse

# Откатить до конкретной миграции
litestar db migrate --target {migration_id}
```

---

## 📏 Best Practices

### ✅ Делай

1. **Reversible Migrations** — всегда реализуй `forwards()` и `backwards()`
2. **Small Changes** — одна миграция = одно логическое изменение
3. **Descriptive Names** — `add_user_roles`, `create_notifications_table`
4. **Version Control** — всегда коммить миграции
5. **Test Migrations** — проверяй на dev перед prod

### ❌ Не делай

1. **Не редактируй** applied миграции
2. **Не удаляй** миграции из VCS
3. **Не делай** data migration в schema migration
4. **Не используй** `auto_update` с SQLite (баг Piccolo)

---

## ⚠️ SQLite Limitations

### TimestamptzNow auto_update

```python
# ❌ НЕ работает с SQLite
updated_at = Timestamptz(
    default=TimestamptzNow(),
    auto_update=TimestamptzNow(),  # Баг!
)

# ✅ Обновляй вручную в Repository
updated_at = Timestamptz(default=TimestamptzNow())

# В repository.update():
await Model.update({
    Model.updated_at: datetime.now(timezone.utc),
}).where(Model.id == entity.id)
```

---

## 📊 Пример миграции

```python
# migrations/user_2026_01_06t18_26_49.py
from piccolo.apps.migrations.auto.migration_manager import MigrationManager

ID = "2026-01-06T18:26:49:171359"
VERSION = "1.0.0"

async def forwards():
    manager = MigrationManager(migration_id=ID)
    
    manager.add_table(
        class_name="AppUser",
        tablename="app_users",
    )
    
    manager.add_column(
        table_class_name="AppUser",
        column_name="email",
        column_class_name="Varchar",
        params={"length": 255, "unique": True},
    )
    
    return manager

async def backwards():
    # Откат — удаление таблицы
    ...
```

---

## 📚 Дополнительно

- `src/Ship/CLI/MigrationCommands.py` — CLI команды
- `piccolo_conf.py` — конфигурация Piccolo
- `foxdocs/piccolo-master/docs/` — документация Piccolo
