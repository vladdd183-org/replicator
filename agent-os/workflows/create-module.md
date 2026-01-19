# 🏗️ Workflow: Create New Module

> Пошаговая инструкция создания нового Container (модуля) в Hyper-Porto.

---

## 📋 Входные данные

Перед началом определи:

| Параметр | Пример | Твоё значение |
|----------|--------|---------------|
| Section | `AppSection` | _____________ |
| Module name | `OrderModule` | _____________ |
| Main entity | `Order` | _____________ |
| Entity plural | `Orders` | _____________ |

---

## 🚀 Шаги

### Step 1: Создать структуру папок

```bash
mkdir -p src/Containers/{Section}/{Module}/{Actions,Tasks,Queries}
mkdir -p src/Containers/{Section}/{Module}/Data/{Repositories,Schemas}
mkdir -p src/Containers/{Section}/{Module}/Models/migrations
mkdir -p src/Containers/{Section}/{Module}/UI/API/Controllers
mkdir -p src/Containers/{Section}/{Module}/UI/{CLI,GraphQL,WebSocket,Workers}
```

**Пример для OrderModule:**
```bash
mkdir -p src/Containers/AppSection/OrderModule/{Actions,Tasks,Queries}
mkdir -p src/Containers/AppSection/OrderModule/Data/{Repositories,Schemas}
mkdir -p src/Containers/AppSection/OrderModule/Models/migrations
mkdir -p src/Containers/AppSection/OrderModule/UI/API/Controllers
mkdir -p src/Containers/AppSection/OrderModule/UI/{CLI,GraphQL,WebSocket,Workers}
```

---

### Step 2: Создать __init__.py файлы

Создать `__init__.py` в каждой папке:

```python
# src/Containers/{Section}/{Module}/__init__.py
"""${Module} - ${description}."""

from src.Containers.${Section}.${Module}.UI.API.Routes import ${module_lower}_router

__all__ = ["${module_lower}_router"]
```

---

### Step 3: Создать Model (Piccolo Table)

**Файл:** `Models/${Entity}.py`

Использовать шаблон: `templates/model.py.template`

```python
from piccolo.table import Table
from piccolo.columns import UUID, Varchar, Boolean, Timestamptz

class Order(Table, tablename="orders"):
    id = UUID(primary_key=True, default=uuid4)
    # ... поля
```

---

### Step 4: Создать PiccoloApp.py

**Файл:** `Models/PiccoloApp.py`

```python
import os
from piccolo.conf.apps import AppConfig, table_finder

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

APP_CONFIG = AppConfig(
    app_name="${module_lower}",
    table_classes=table_finder(
        modules=["src.Containers.${Section}.${Module}.Models.${Entity}"],
    ),
    migration_dependencies=[],
    commands=[],
)
```

---

### Step 5: Зарегистрировать в piccolo_conf.py

Добавить в `piccolo_conf.py` (корень проекта):

```python
APP_REGISTRY = AppRegistry(
    apps=[
        # ... existing apps
        "src.Containers.${Section}.${Module}.Models.PiccoloApp",
    ]
)
```

---

### Step 6: Создать миграцию

```bash
uv run piccolo migrations new ${module_lower} --auto
uv run piccolo migrations forwards ${module_lower}
```

---

### Step 7: Создать Errors.py

**Файл:** `Errors.py`

Использовать шаблон: `templates/error.py.template`

---

### Step 8: Создать Events.py

**Файл:** `Events.py`

Использовать шаблон: `templates/event.py.template` (первая часть)

---

### Step 9: Создать Schemas

**Файлы:**
- `Data/Schemas/Requests.py`
- `Data/Schemas/Responses.py`

Использовать шаблон: `templates/schemas.py.template`

---

### Step 10: Создать Repository

**Файл:** `Data/Repositories/${Entity}Repository.py`

Использовать шаблон: `templates/repository.py.template`

---

### Step 11: Создать UnitOfWork

**Файл:** `Data/UnitOfWork.py`

Использовать шаблон: `templates/unit-of-work.py.template`

---

### Step 12: Создать Queries

**Файлы:**
- `Queries/Get${Entity}Query.py`
- `Queries/List${Entities}Query.py`

Использовать шаблон: `templates/query.py.template`

---

### Step 13: Создать Actions

**Файлы:**
- `Actions/Create${Entity}Action.py`
- `Actions/Update${Entity}Action.py`
- `Actions/Delete${Entity}Action.py`

Использовать шаблон: `templates/action.py.template`

---

### Step 14: Создать Controller

**Файл:** `UI/API/Controllers/${Entity}Controller.py`

Использовать шаблон: `templates/controller.py.template`

---

### Step 15: Создать Routes.py

**Файл:** `UI/API/Routes.py`

```python
from litestar import Router

from src.Containers.${Section}.${Module}.UI.API.Controllers.${Entity}Controller import ${Entity}Controller

${module_lower}_router = Router(
    path="/api/v1",
    route_handlers=[${Entity}Controller],
)
```

---

### Step 16: Создать Listeners.py

**Файл:** `Listeners.py`

Использовать шаблон: `templates/event.py.template` (вторая часть)

---

### Step 17: Создать Providers.py

**Файл:** `Providers.py`

Использовать шаблон: `templates/providers.py.template`

---

### Step 18: Зарегистрировать Providers

**Файл:** `src/Ship/Providers/__init__.py`

```python
from src.Containers.${Section}.${Module}.Providers import (
    ${Module}Provider,
    ${Module}RequestProvider,
)

def get_all_providers() -> list[Provider]:
    return [
        # ... existing providers
        ${Module}Provider(),
        ${Module}RequestProvider(),
    ]
```

---

### Step 19: Зарегистрировать в App.py

**Файл:** `src/App.py`

```python
# Import router
from src.Containers.${Section}.${Module} import ${module_lower}_router

# Import listeners
from src.Containers.${Section}.${Module}.Listeners import (
    on_${entity_lower}_created,
    on_${entity_lower}_updated,
    on_${entity_lower}_deleted,
)

app = Litestar(
    route_handlers=[
        # ... existing routers
        ${module_lower}_router,
    ],
    listeners=[
        # ... existing listeners
        on_${entity_lower}_created,
        on_${entity_lower}_updated,
        on_${entity_lower}_deleted,
    ],
)
```

---

### Step 20: Создать тесты

```
tests/
├── unit/
│   └── containers/
│       └── ${module_lower}/
│           ├── test_actions.py
│           └── test_tasks.py
├── integration/
│   └── test_${module_lower}_api.py
└── e2e/
    └── test_${module_lower}_flow.py
```

---

## ✅ Чеклист завершения

- [ ] Model создан и зарегистрирован в PiccoloApp
- [ ] Миграция создана и применена
- [ ] Errors.py с основными ошибками
- [ ] Events.py с доменными событиями
- [ ] Schemas (Request/Response DTOs)
- [ ] Repository с domain queries
- [ ] UnitOfWork с repositories
- [ ] Queries (Get, List)
- [ ] Actions (Create, Update, Delete)
- [ ] Controller с endpoints
- [ ] Routes.py с Router
- [ ] Listeners для events
- [ ] Providers.py с DI
- [ ] Зарегистрирован в get_all_providers()
- [ ] Router добавлен в App.py
- [ ] Listeners добавлены в App.py
- [ ] Тесты написаны

---

## 🔗 Связанные документы

- **Templates:** `../templates/` — шаблоны кода
- **Checklist:** `../checklists/new-module.md` — краткий чеклист
- **Standards:** `../standards/` — правила написания



