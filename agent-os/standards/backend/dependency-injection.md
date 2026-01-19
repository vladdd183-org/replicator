# Dependency Injection — Dishka

> Стандарты для Dependency Injection через библиотеку Dishka.

---

## 🎯 Основные принципы

1. **Scope-based** — зависимости привязаны к scope (APP, REQUEST)
2. **Type hints** — Dishka резолвит по типам автоматически
3. **Явная регистрация** — никакого автосканирования
4. **Providers в модулях** — каждый Container имеет свой `Providers.py`

---

## 📁 Расположение

```
Containers/{Section}/{Module}/Providers.py
Ship/Providers/AppProvider.py
```

---

## 🏗️ Структура Provider

```python
from dishka import Provider, Scope, provide
from litestar import Request

from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask


class UserModuleProvider(Provider):
    """APP scope — stateless services."""
    scope = Scope.APP
    
    # Tasks — stateless, reusable
    hash_password_task = provide(HashPasswordTask)


class UserRequestProvider(Provider):
    """REQUEST scope — per-request dependencies."""
    scope = Scope.REQUEST
    
    # Repository
    user_repository = provide(UserRepository)
    
    # Actions
    create_user_action = provide(CreateUserAction)
    
    @provide
    def provide_user_uow(self, request: Request) -> UserUnitOfWork:
        """UnitOfWork с event emitter из request."""
        return UserUnitOfWork(_emit=request.app.emit, _app=request.app)
```

---

## 🔧 Scopes

| Scope | Когда использовать | Примеры |
|-------|-------------------|---------|
| `Scope.APP` | Stateless сервисы, синглтоны | Tasks, Settings, JWT Service |
| `Scope.REQUEST` | Per-request state | Actions, Queries, UoW, Repository |

---

## 📋 Способы регистрации

### 1. provide() — автоматический резолв

```python
# Dishka сама резолвит зависимости по type hints конструктора
create_user_action = provide(CreateUserAction)
```

### 2. @provide — кастомная фабрика

```python
@provide
def provide_user_uow(self, request: Request) -> UserUnitOfWork:
    return UserUnitOfWork(_emit=request.app.emit, _app=request.app)
```

### 3. provide(source=...) — алиас

```python
# Когда нужен алиас типа
abstract_repo = provide(source=UserRepository, provides=AbstractRepository)
```

---

## 🎨 Использование в Controllers

### FromDishka injection

```python
from dishka.integrations.litestar import FromDishka

class UserController(Controller):
    @post("/")
    async def create_user(
        self,
        data: CreateUserRequest,
        action: FromDishka[CreateUserAction],  # DI injection
    ) -> Response:
        return await action.run(data)
```

### @inject НЕ нужен!

```python
# ❌ НЕ нужно с DishkaRouter
@inject
async def create_user(action: CreateUserAction): ...

# ✅ Правильно
async def create_user(action: FromDishka[CreateUserAction]): ...
```

---

## 🔗 Регистрация в App

### get_all_providers()

```python
# src/Ship/Providers/__init__.py
from src.Ship.Providers.AppProvider import AppProvider
from src.Containers.AppSection.UserModule.Providers import (
    UserModuleProvider,
    UserRequestProvider,
)

def get_all_providers() -> list[Provider]:
    return [
        AppProvider(),
        UserModuleProvider(),
        UserRequestProvider(),
        # ... другие модули
    ]
```

### Setup в App.py

```python
from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka

container = make_async_container(*get_all_providers())
app = Litestar(...)
setup_dishka(container, app)
```

---

## 📦 Паттерны Provider

### Base Provider + HTTP/CLI variants

```python
class _BaseUserRequestProvider(Provider):
    """Base — общие зависимости."""
    scope = Scope.REQUEST
    
    user_repository = provide(UserRepository)
    create_user_action = provide(CreateUserAction)


class UserRequestProvider(_BaseUserRequestProvider):
    """HTTP context — с event emitter."""
    
    @provide
    def provide_user_uow(self, request: Request) -> UserUnitOfWork:
        return UserUnitOfWork(_emit=request.app.emit, _app=request.app)


class UserCLIProvider(_BaseUserRequestProvider):
    """CLI context — без event emitter."""
    
    @provide
    def provide_user_uow(self) -> UserUnitOfWork:
        return UserUnitOfWork(_emit=None, _app=None)
```

---

## 🛠️ Ship-level Providers

```python
# src/Ship/Providers/AppProvider.py
from dishka import Provider, Scope, provide

from src.Ship.Configs import Settings, get_settings
from src.Ship.Auth.JWT import JWTService


class AppProvider(Provider):
    """Ship-level APP scope dependencies."""
    scope = Scope.APP
    
    @provide
    def settings(self) -> Settings:
        return get_settings()
    
    jwt_service = provide(JWTService)
```

---

## ⚠️ Чего НЕ делать

```python
# ❌ Service Locator pattern
container.resolve(CreateUserAction)  # Нет!

# ❌ Global state
_action = CreateUserAction(...)  # Нет!

# ❌ Прямой импорт зависимостей в Controller
from src.Containers...UserRepository import UserRepository
async def create_user(self):
    repo = UserRepository()  # Нет!

# ❌ Автосканирование
discover_providers("src/Containers")  # Нет!
```

---

## 📐 Типизация

### Generic Providers

```python
from typing import TypeVar
from src.Ship.Parents.Repository import Repository

T = TypeVar("T")

class BaseModuleProvider(Provider, Generic[T]):
    @provide
    def repository(self) -> Repository[T]:
        ...
```

### Protocol-based

```python
from typing import Protocol

class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Provider
email_sender = provide(source=SMTPEmailSender, provides=EmailSender)
```

---

---

## 👂 Listeners (Event Handlers)

Listeners регистрируются в App.py и обрабатывают Domain Events:

```python
# Listeners.py
from litestar.events import listener
from src.Ship.Infrastructure.Channels import publish_to_user_channel

@listener("UserCreated")
async def on_user_created(
    user_id: str,
    email: str,
    app: Litestar | None = None,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle UserCreated event."""
    logfire.info("🎉 User created", user_id=user_id, email=email)
    publish_to_user_channel(app, user_id, "user_created", {"email": email})
```

### Регистрация в App.py

```python
from src.Containers.AppSection.UserModule.Listeners import (
    on_user_created,
    on_user_updated,
    on_user_deleted,
)

app = Litestar(
    listeners=[
        on_user_created,
        on_user_updated,
        on_user_deleted,
    ],
)
```

### Multiple Events

```python
@listener("UserCreated", "UserDeleted", "UserUpdated")
async def on_user_changed(user_id: str, **kwargs) -> None:
    """Handle any user change for audit."""
    ...
```

---

## 📚 Дополнительно

- `src/Ship/Providers/` — Ship-level providers
- `src/Ship/Infrastructure/Channels.py` — WebSocket helpers
- `docs/10-registration.md` — явная регистрация
- `docs/11-litestar-features.md` — Litestar Events, Channels
- <https://dishka.dev/> — документация Dishka

