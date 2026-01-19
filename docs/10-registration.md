# 📋 Явная регистрация

> **Версия:** 4.3 | **Дата:** Январь 2026  
> Explicit is better than implicit — принципы явной регистрации компонентов

---

## 🎯 Принцип

```
Никакого autodiscovery или магических импортов.
Каждый компонент регистрируется явно в одном месте.
```

**Почему:**
- Полная прозрачность — видно всё что зарегистрировано
- Контроль порядка загрузки
- Простая отладка — нет скрытых зависимостей
- IDE может найти все использования

---

## 🔌 Что регистрируется явно

| Компонент | Где регистрируется |
|-----------|-------------------|
| HTTP Routers | `App.py` → `route_handlers` |
| DI Providers | `AppProvider.get_all_providers()` |
| GraphQL Queries/Mutations | `GraphQL/Schema.py` |
| Event Listeners | `App.py` → `listeners` |
| CLI Commands | `CLI/main.py` |
| Piccolo Apps | `piccolo_conf.py` → `APP_REGISTRY` |
| TaskIQ Tasks | `worker.py` → `broker.include_router()` |

---

## 📡 HTTP Routers

### Регистрация в App.py

```python
# src/App.py

from litestar import Litestar

# Явный импорт роутеров
from src.Containers.AppSection.UserModule.UI.API.Routes import (
    user_router,
    auth_router,
)
from src.Containers.AppSection.ProductModule.UI.API.Routes import (
    product_router,
)

app = Litestar(
    route_handlers=[
        user_router,      # /api/users/*
        auth_router,      # /api/auth/*
        product_router,   # /api/products/*
    ],
)
```

### Роутер модуля

```python
# src/Containers/AppSection/UserModule/UI/API/Routes.py

from litestar import Router

from src.Containers.AppSection.UserModule.UI.API.Controllers.UserController import (
    UserController,
)
from src.Containers.AppSection.UserModule.UI.API.Controllers.AuthController import (
    AuthController,
)

user_router = Router(
    path="/api/users",
    route_handlers=[UserController],
    tags=["Users"],
)

auth_router = Router(
    path="/api/auth",
    route_handlers=[AuthController],
    tags=["Authentication"],
)
```

---

## 💉 DI Providers (Dishka)

### Структура провайдеров

```
src/
├── Ship/
│   └── Providers/
│       └── AppProvider.py       # Общие провайдеры + сборка
└── Containers/
    └── AppSection/
        └── UserModule/
            └── Providers.py     # Провайдеры модуля
```

### AppProvider.py — центральная сборка

```python
# src/Ship/Providers/AppProvider.py

from dishka import Provider, Scope, provide, make_async_container
from collections.abc import AsyncIterable

from src.Ship.Core.Settings import Settings
from src.Containers.AppSection.UserModule.Services.JWTService import JWTService

# Импорт провайдеров модулей
from src.Containers.AppSection.UserModule.Providers import (
    UserModuleProvider,
    UserRequestProvider,
    UserCLIProvider,
)


class AppProvider(Provider):
    """Провайдер общих зависимостей."""
    
    scope = Scope.APP
    
    @provide
    def get_settings(self) -> Settings:
        return Settings()
    
    @provide
    def get_jwt_service(self, settings: Settings) -> JWTService:
        return JWTService(settings=settings)


def get_all_providers() -> list[Provider]:
    """Провайдеры для HTTP приложения."""
    return [
        AppProvider(),
        UserModuleProvider(),
        UserRequestProvider(),
    ]


def get_cli_providers() -> list[Provider]:
    """Провайдеры для CLI."""
    return [
        AppProvider(),
        UserModuleProvider(),
        UserCLIProvider(),
    ]


def get_worker_providers() -> list[Provider]:
    """Провайдеры для TaskIQ workers."""
    return [
        AppProvider(),
        UserModuleProvider(),
        UserRequestProvider(),  # Workers тоже могут публиковать события
    ]
```

### Providers.py модуля

```python
# src/Containers/AppSection/UserModule/Providers.py

from dishka import Provider, Scope, provide
from litestar import Request

from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository
from src.Containers.AppSection.UserModule.Data.UnitOfWork.UserUnitOfWork import UserUnitOfWork


class UserModuleProvider(Provider):
    """Stateless компоненты (APP scope)."""
    
    scope = Scope.APP
    
    # Tasks — stateless, singleton
    hash_password_task = provide(HashPasswordTask)
    verify_password_task = provide(VerifyPasswordTask)


class _BaseUserRequestProvider(Provider):
    """Базовые request-scoped компоненты."""
    
    scope = Scope.REQUEST
    
    # Repository
    user_repository = provide(UserRepository)
    
    # Actions
    create_user_action = provide(CreateUserAction)
    authenticate_action = provide(AuthenticateAction)


class UserRequestProvider(_BaseUserRequestProvider):
    """HTTP контекст — с event emitter."""
    
    @provide
    def get_user_uow(
        self,
        repository: UserRepository,
        request: Request,
    ) -> UserUnitOfWork:
        return UserUnitOfWork(
            users=repository,
            event_emitter=request.app.emit,
        )


class UserCLIProvider(_BaseUserRequestProvider):
    """CLI контекст — без event emitter."""
    
    @provide
    def get_user_uow(self, repository: UserRepository) -> UserUnitOfWork:
        return UserUnitOfWork(users=repository)
```

---

## 📊 GraphQL Schema

### Явная сборка схемы

```python
# src/Containers/AppSection/UserModule/UI/GraphQL/Schema.py

import strawberry

# Явный импорт резолверов
from src.Containers.AppSection.UserModule.UI.GraphQL.Resolvers import (
    UserQuery,
    UserMutation,
)
from src.Containers.AppSection.ProductModule.UI.GraphQL.Resolvers import (
    ProductQuery,
    ProductMutation,
)


@strawberry.type
class Query(UserQuery, ProductQuery):
    """Объединение всех Query."""
    pass


@strawberry.type
class Mutation(UserMutation, ProductMutation):
    """Объединение всех Mutation."""
    pass


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
```

### Регистрация в App.py

```python
# src/App.py

from litestar.contrib.strawberry import make_graphql_controller

from src.Containers.AppSection.UserModule.UI.GraphQL.Schema import schema

GraphQLController = make_graphql_controller(
    schema=schema,
    path="/graphql",
    graphql_ide="graphiql",
)

app = Litestar(
    route_handlers=[
        GraphQLController,
        # ... HTTP routers
    ],
)
```

---

## 📢 Event Listeners

### Явная регистрация слушателей

```python
# src/App.py

from litestar import Litestar
from litestar.events import listener

# Явный импорт слушателей
from src.Containers.AppSection.UserModule.Listeners import (
    on_user_created,
    on_user_deleted,
    on_user_updated,
)

app = Litestar(
    listeners=[
        on_user_created,
        on_user_deleted,
        on_user_updated,
    ],
)
```

### Listeners.py модуля

```python
# src/Containers/AppSection/UserModule/Listeners.py

from litestar.events import listener

from src.Containers.AppSection.UserModule.Events import (
    UserCreated,
    UserDeleted,
    UserUpdated,
)


@listener(UserCreated)
async def on_user_created(event: UserCreated) -> None:
    """Обработка события создания пользователя."""
    logger.info("User created", user_id=str(event.user_id))
    # WebSocket notification, email, etc.


@listener(UserDeleted)
async def on_user_deleted(event: UserDeleted) -> None:
    """Обработка события удаления пользователя."""
    logger.info("User deleted", user_id=str(event.user_id))


@listener(UserUpdated)
async def on_user_updated(event: UserUpdated) -> None:
    """Обработка события обновления пользователя."""
    logger.info("User updated", user_id=str(event.user_id))
```

---

## 🖥️ CLI Commands

### Явная регистрация команд

```python
# src/CLI/main.py

import click
from dishka import make_async_container
from dishka.integrations.click import setup_dishka

from src.Ship.Providers.AppProvider import get_cli_providers

# Явный импорт групп команд
from src.Containers.AppSection.UserModule.UI.CLI.Commands import users_group
from src.Containers.AppSection.ProductModule.UI.CLI.Commands import products_group


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Hyper-Porto CLI."""
    container = make_async_container(*get_cli_providers())
    setup_dishka(container, ctx, auto_inject=True)


# Явная регистрация групп
cli.add_command(users_group)
cli.add_command(products_group)


if __name__ == "__main__":
    cli()
```

---

## 🗄️ Piccolo ORM Apps

### piccolo_conf.py

```python
# piccolo_conf.py

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

from src.Ship.Core.Settings import Settings

settings = Settings()

DB = PostgresEngine(
    config={
        "host": settings.db_host,
        "port": settings.db_port,
        "database": settings.db_name,
        "user": settings.db_user,
        "password": settings.db_password,
    }
)

# Явная регистрация Piccolo Apps
APP_REGISTRY = AppRegistry(
    apps=[
        "src.Containers.AppSection.UserModule.PiccoloApp",
        "src.Containers.AppSection.ProductModule.PiccoloApp",
        # Добавляй новые модули здесь
    ]
)
```

### PiccoloApp.py модуля

```python
# src/Containers/AppSection/UserModule/PiccoloApp.py

from piccolo.conf.apps import AppConfig, table_finder

APP_CONFIG = AppConfig(
    app_name="user_module",
    table_classes=table_finder(
        modules=[
            "src.Containers.AppSection.UserModule.Models.AppUser",
        ]
    ),
    migration_dependencies=[],
    commands=[],
)
```

---

## ⚡ TaskIQ Workers

### worker.py

```python
# src/worker.py

import taskiq_redis
from taskiq import TaskiqScheduler
from dishka import make_async_container
from dishka.integrations.taskiq import setup_dishka

from src.Ship.Providers.AppProvider import get_worker_providers

# Явный импорт задач
from src.Containers.AppSection.UserModule.UI.Workers import Tasks as UserTasks

# Брокер
broker = taskiq_redis.ListQueueBroker(redis_url="redis://localhost:6379")

# Явная регистрация задач через include
broker.include_router(UserTasks.user_tasks_router)

# DI
@broker.on_startup
async def setup_di() -> None:
    container = make_async_container(*get_worker_providers())
    setup_dishka(container, broker)
```

### Tasks.py модуля

```python
# src/Containers/AppSection/UserModule/UI/Workers/Tasks.py

from taskiq import TaskiqRouter
from dishka import FromDishka
from dishka.integrations.taskiq import inject

user_tasks_router = TaskiqRouter()


@user_tasks_router.task()
@inject
async def send_welcome_email_task(
    user_id: str,
    email_service: FromDishka[EmailService],
) -> None:
    await email_service.send_welcome(user_id)


@user_tasks_router.task()
@inject
async def bulk_create_users_task(
    users_data: list[dict],
    action: FromDishka[CreateUserAction],
) -> list[str]:
    # ...
```

---

## 🧩 Module Manifest (паттерн)

Для упрощения регистрации можно использовать манифест модуля:

```python
# src/Containers/AppSection/UserModule/__init__.py

from src.Containers.AppSection.UserModule.UI.API.Routes import (
    user_router,
    auth_router,
)
from src.Containers.AppSection.UserModule.UI.GraphQL.Resolvers import (
    UserQuery,
    UserMutation,
)
from src.Containers.AppSection.UserModule.Listeners import (
    on_user_created,
    on_user_deleted,
    on_user_updated,
)
from src.Containers.AppSection.UserModule.Providers import (
    UserModuleProvider,
    UserRequestProvider,
    UserCLIProvider,
)


class UserModuleManifest:
    """Манифест модуля для упрощения регистрации."""
    
    # HTTP
    routers = [user_router, auth_router]
    
    # GraphQL
    query = UserQuery
    mutation = UserMutation
    
    # Events
    listeners = [on_user_created, on_user_deleted, on_user_updated]
    
    # DI
    providers = [UserModuleProvider]
    request_providers = [UserRequestProvider]
    cli_providers = [UserCLIProvider]
```

### Использование манифеста

```python
# src/App.py

from src.Containers.AppSection.UserModule import UserModuleManifest
from src.Containers.AppSection.ProductModule import ProductModuleManifest

# Сборка из манифестов
modules = [UserModuleManifest, ProductModuleManifest]

route_handlers = [r for m in modules for r in m.routers]
listeners = [l for m in modules for l in m.listeners]
providers = [p for m in modules for p in m.providers + m.request_providers]

app = Litestar(
    route_handlers=route_handlers + [GraphQLController],
    listeners=listeners,
)
```

---

## ✅ Чеклист регистрации нового модуля

```markdown
- [ ] Создать структуру папок модуля
- [ ] Создать PiccoloApp.py и добавить в piccolo_conf.py
- [ ] Создать Providers.py и добавить в get_all_providers()
- [ ] Создать роутеры и добавить в App.py
- [ ] Создать GraphQL резолверы и добавить в Schema.py
- [ ] Создать слушатели и добавить в App.py listeners
- [ ] Создать CLI команды и добавить в cli.add_command()
- [ ] Создать TaskIQ задачи и добавить router в worker.py
```

---

## 🚫 Антипаттерны

| ❌ Не делай | ✅ Делай |
|------------|---------|
| Autodiscovery (scan packages) | Явные импорты |
| `__all__` для экспорта | Прямые импорты |
| Динамическая загрузка модулей | Статическая регистрация |
| Magic strings для путей | Type-safe импорты |
| Регистрация в __init__.py | Регистрация в App.py |

---

<div align="center">

**Следующий раздел:** [11-litestar-features.md](11-litestar-features.md) — Возможности Litestar

</div>
