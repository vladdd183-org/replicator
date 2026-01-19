# Models — Piccolo ORM Tables

> Стандарты для моделей базы данных на Piccolo ORM.

---

## 📁 Расположение

```
Containers/{Section}/{Module}/Models/
├── __init__.py
├── PiccoloApp.py         # Piccolo App для миграций
├── {Entity}.py           # Table definition
└── migrations/           # Авто-генерируемые миграции
    └── {entity}_2026_01_06t18_26_49.py
```

---

## 🏗️ Базовый шаблон Table

```python
from piccolo.columns import UUID, Varchar, Boolean, Timestamptz
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.defaults.timestamptz import TimestamptzNow

from src.Ship.Parents.Model import Model


class AppUser(Model):
    """User entity.
    
    Named AppUser to avoid SQL reserved word 'user'.
    
    Attributes:
        id: Primary key UUID
        email: Unique email address
        password_hash: Hashed password
        name: Display name
        is_active: Account status
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    id = UUID(primary_key=True, default=UUID4())
    email = Varchar(length=255, unique=True, required=True, index=True)
    password_hash = Varchar(length=255, required=True)
    name = Varchar(length=100, required=True)
    is_active = Boolean(default=True)
    created_at = Timestamptz(default=TimestamptzNow())
    # Note: auto_update removed due to SQLite incompatibility
    # updated_at is set manually in repository.update()
    updated_at = Timestamptz(default=TimestamptzNow())
    
    class Meta:
        tablename = "app_users"
```

### ⚠️ SQLite Compatibility

`TimestamptzNow` с `auto_update` не работает в SQLite. Обновление `updated_at` делается вручную в Repository:

```python
async def update(self, user: AppUser) -> AppUser:
    await AppUser.update({
        # ...
        AppUser.updated_at: datetime.now(timezone.utc),
    }).where(AppUser.id == user.id)
```

---

## 📏 Naming Conventions

| Элемент | Паттерн | Пример |
|---------|---------|--------|
| Class name | `{Entity}` или `App{Entity}` | `AppUser`, `Notification` |
| Table name | `{entities}` (plural, snake_case) | `app_users`, `notifications` |
| Column name | `snake_case` | `created_at`, `user_id` |
| Foreign Key | `{entity}_id` или `{entity}` | `user_id`, `user` |

---

## 🔑 Обязательные поля

### ID (Primary Key)

```python
id = UUID(primary_key=True, default=UUID4())
```

### Timestamps (для аудита)

```python
created_at = Timestamptz(default=TimestamptzNow())
updated_at = Timestamptz(
    default=TimestamptzNow(),
    auto_update=TimestamptzNow(),
)
```

---

## 🔗 Связи (Foreign Keys)

### One-to-Many

```python
class Notification(Table, tablename="notifications"):
    user = ForeignKey(references=AppUser)  # notification.user → AppUser
```

### Запрос с join

```python
notifications = await Notification.select(
    Notification.all_columns(),
    Notification.user.email,  # JOIN
).where(Notification.user.id == user_id)
```

---

## 📦 PiccoloApp для миграций

```python
# Containers/{Section}/{Module}/Models/PiccoloApp.py
from piccolo.conf.apps import AppConfig, table_finder

APP_CONFIG = AppConfig(
    app_name="user_module",
    table_classes=table_finder(
        modules=["src.Containers.AppSection.UserModule.Models.User"],
    ),
    migration_folder_path="src/Containers/AppSection/UserModule/Models/migrations",
)
```

### Регистрация в piccolo_conf.py

```python
# piccolo_conf.py
from piccolo.conf.apps import AppRegistry

APP_REGISTRY = AppRegistry(
    apps=[
        "src.Containers.AppSection.UserModule.Models.PiccoloApp",
        "src.Containers.AppSection.NotificationModule.Models.PiccoloApp",
        # ...
    ],
)
```

---

## 🔄 Миграции

### Создание миграции

```bash
uv run piccolo migrations new ModuleName --auto
```

### Применение миграций

```bash
uv run piccolo migrations forwards all
```

### Откат миграции

```bash
uv run piccolo migrations backwards ModuleName 1
```

---

## 📐 Типы колонок

| Python тип | Piccolo Column | Пример |
|------------|----------------|--------|
| UUID | `UUID` | `id = UUID(primary_key=True)` |
| str | `Varchar(length=N)` | `name = Varchar(length=100)` |
| str (long) | `Text` | `description = Text()` |
| bool | `Boolean` | `is_active = Boolean(default=True)` |
| int | `Integer` | `count = Integer(default=0)` |
| datetime | `Timestamptz` | `created_at = Timestamptz()` |
| Decimal | `Decimal` | `price = Decimal(digits=(10, 2))` |
| JSON | `JSONB` | `metadata = JSONB()` |
| Enum | `Varchar` + validator | `status = Varchar(length=20)` |

---

## 🛡️ Constraints

### Unique

```python
email = Varchar(length=255, unique=True)
```

### Index

```python
email = Varchar(length=255, index=True)
```

### Unique + Index

```python
email = Varchar(length=255, unique=True, index=True)
```

### Nullable

```python
bio = Text(null=True, default=None)
```

---

## ⚠️ Чего НЕ делать

```python
# ❌ Не использовать dataclass для моделей
@dataclass
class User:
    ...

# ❌ Не использовать SQLAlchemy
from sqlalchemy import Column

# ❌ Не именовать таблицу в единственном числе
class User(Table, tablename="user"):  # Должно быть "users" или "app_users"
```

---

## 📚 Дополнительно

- `piccolo_conf.py` — конфигурация Piccolo
- `src/Ship/CLI/MigrationCommands.py` — CLI команды миграций
- `docs/03-components.md` — Repository и UnitOfWork
- <https://piccolo-orm.com/docs/> — документация Piccolo
