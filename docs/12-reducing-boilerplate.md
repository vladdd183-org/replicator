# 🔧 Reducing Boilerplate — Справочник решений

> **Версия:** 4.3 | **Дата:** Январь 2026

Этот документ — справочник техник и паттернов для сокращения бойлерплейта в Hyper-Porto.

---

## 📋 Обзор решений

| Проблема | Решение | Тип |
|----------|---------|-----|
| Result → HTTP Response | `@result_handler` | Кастомный декоратор |
| Entity → Response DTO | `EntitySchema` | Базовый класс |
| Транзакции + Events | `BaseUnitOfWork` | Базовый класс |
| Async CLI с DI | `@with_container` | Кастомный декоратор |
| Error message generation | `ErrorWithTemplate` | Базовый класс |
| GraphQL DI | `get_dependency` | Кастомный helper |
| CLI Result handling | `handle_cli_result` | Кастомный helper |
| Litestar + Dishka | `dishka.integrations.litestar` | Готовая интеграция |
| TaskIQ + Dishka | `dishka.integrations.taskiq` | Готовая интеграция |
| Strawberry + Litestar | `strawberry.litestar` | Готовая интеграция |

---

## 🎯 @result_handler — Result → Response

**Проблема:** Каждый Controller endpoint содержит повторяющийся код конвертации Result в Response.

**Решение:** Декоратор `@result_handler` автоматизирует:
- `Success(value)` → `Response(DTO.from_entity(value), status=success_status)`
- `Failure(error)` → `DomainException` → Problem Details (RFC 9457)

### Реализация

```python
# src/Ship/Decorators/result_handler.py
"""Result handler decorator for automatic Result -> Response conversion."""

from functools import wraps
from typing import TypeVar, Callable, Type, Any, Protocol, runtime_checkable

from litestar import Response
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Core.Errors import BaseError, DomainException

T = TypeVar("T")
E = TypeVar("E")


@runtime_checkable
class FromEntityProtocol(Protocol):
    """Protocol for DTOs that can be created from entities."""
    
    @classmethod
    def from_entity(cls, entity: object) -> "FromEntityProtocol":
        ...


def result_handler(
    response_dto: Type[BaseModel] | None,
    success_status: int = 200,
) -> Callable[[Callable[..., Result[T, E]]], Callable[..., Any]]:
    """Decorator for automatic Result -> Response conversion.
    
    On Success: returns HTTP response with serialized DTO.
    On Failure: raises DomainException for Problem Details handling.
    
    DTO conversion priority:
    1. If response_dto is None → empty response (204)
    2. If DTO has from_entity() method → use it
    3. If value is already a BaseModel → use directly
    4. Otherwise → use model_validate with from_attributes
    
    Args:
        response_dto: Pydantic model for serializing Success value
        success_status: HTTP status code for successful response
        
    Example:
        @post("/users")
        @result_handler(UserResponse, success_status=201)
        async def create_user(
            data: CreateUserRequest,
            action: FromDishka[CreateUserAction],
        ) -> Result[User, UserError]:
            return await action.run(data)
    """
    def decorator(func: Callable[..., Result[T, E]]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            
            match result:
                case Success(value):
                    if response_dto is None or value is None:
                        return Response(content=None, status_code=success_status)
                    
                    content = _convert_to_dto(response_dto, value)
                    return Response(content=content, status_code=success_status)
                
                case Failure(error):
                    if isinstance(error, BaseError):
                        raise DomainException(error)
                    else:
                        raise Exception(str(error))
        
        return wrapper
    return decorator


def _convert_to_dto(dto_class: Type[BaseModel], value: Any) -> BaseModel:
    """Convert value to DTO using the most appropriate method."""
    # If DTO has from_entity method, use it
    if isinstance(dto_class, type) and hasattr(dto_class, "from_entity"):
        return dto_class.from_entity(value)
    
    # If value is already the correct type
    if isinstance(value, dto_class):
        return value
    
    # If value is any BaseModel, convert via dict
    if isinstance(value, BaseModel):
        return dto_class.model_validate(value.model_dump())
    
    # Otherwise use from_attributes for ORM models
    return dto_class.model_validate(value, from_attributes=True)
```

### Использование

```python
# ❌ БЕЗ @result_handler — много бойлерплейта
@post("/users")
async def create_user(data: CreateUserRequest, action: FromDishka[CreateUserAction]):
    result = await action.run(data)
    match result:
        case Success(user):
            return Response(content=UserResponse.from_entity(user), status_code=201)
        case Failure(UserAlreadyExistsError() as e):
            return Response(content={"error": e.message}, status_code=409)
        case Failure(error):
            return Response(content={"error": str(error)}, status_code=400)


# ✅ С @result_handler — чисто и просто
@post("/users")
@result_handler(UserResponse, success_status=201)
async def create_user(data: CreateUserRequest, action: FromDishka[CreateUserAction]):
    return await action.run(data)
```

---

## 📦 EntitySchema — Entity → Response DTO

**Проблема:** Каждый Response DTO нуждается в методе конвертации из ORM entity.

**Решение:** Базовый класс `EntitySchema` с `from_entity()` и `from_entities()`.

### Реализация

```python
# src/Ship/Core/BaseSchema.py
"""Base schema classes for DTOs."""

from typing import TypeVar, Type
from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="EntitySchema")


class EntitySchema(BaseModel):
    """Base class for Response DTOs with automatic conversion from Entity.
    
    Uses Pydantic V2 from_attributes for automatic mapping from ORM objects.
    
    Example:
        class UserResponse(EntitySchema):
            id: UUID
            email: str
            name: str
            is_active: bool
            # from_entity() already available from base class!
            
        # Usage:
        user_response = UserResponse.from_entity(user)
        users_response = UserResponse.from_entities(users)
    """
    
    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode
        populate_by_name=True,  # Allow field aliases
    )
    
    @classmethod
    def from_entity(cls: Type[T], entity: object) -> T:
        """Create DTO from Entity (ORM model)."""
        return cls.model_validate(entity)
    
    @classmethod
    def from_entities(cls: Type[T], entities: list[object]) -> list[T]:
        """Create list of DTOs from list of Entities."""
        return [cls.model_validate(e) for e in entities]
```

### Использование

```python
# ❌ БЕЗ EntitySchema — ручная конвертация
class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    
    @classmethod
    def from_user(cls, user: AppUser) -> "UserResponse":
        return cls(id=user.id, email=user.email, name=user.name)


# ✅ С EntitySchema — автоматическая конвертация
class UserResponse(EntitySchema):
    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    # from_entity() уже есть!

# Использование
response = UserResponse.from_entity(user)
responses = UserResponse.from_entities(users)
```

---

## ⚠️ ErrorWithTemplate — Auto-generated Messages

**Проблема:** Каждая ошибка требует ручного формирования сообщения.

**Решение:** `ErrorWithTemplate` автоматически генерирует message из шаблона.

### Реализация

```python
# src/Ship/Core/Errors.py (фрагмент)
from typing import Any, ClassVar
from pydantic import BaseModel, model_validator


class BaseError(BaseModel):
    """Base error class for all domain errors."""
    
    model_config = {"frozen": True}
    
    message: str
    code: str = "ERROR"
    http_status: int = 400


class ErrorWithTemplate(BaseError):
    """Base error with automatic message generation from template.
    
    Subclasses define _message_template as class variable.
    Template uses field names as format keys.
    
    Example:
        class UserNotFoundError(ErrorWithTemplate):
            _message_template: ClassVar[str] = "User with id {user_id} not found"
            code: str = "USER_NOT_FOUND"
            http_status: int = 404
            user_id: UUID
            
        # Usage:
        error = UserNotFoundError(user_id=some_uuid)
        # error.message == "User with id <uuid> not found"
    """
    
    _message_template: ClassVar[str] = ""
    
    @model_validator(mode="before")
    @classmethod
    def auto_generate_message(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Auto-generate message from template if not provided."""
        if isinstance(data, dict) and "message" not in data and cls._message_template:
            try:
                data["message"] = cls._message_template.format(**data)
            except KeyError:
                data["message"] = cls._message_template
        return data
```

### Использование

```python
# ❌ БЕЗ ErrorWithTemplate — ручное формирование message
class UserNotFoundError(BaseError):
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID

# Каждый раз вручную:
error = UserNotFoundError(
    message=f"User with id {user_id} not found",
    user_id=user_id,
)


# ✅ С ErrorWithTemplate — автоматическая генерация
class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User with id {user_id} not found"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID

# message генерируется автоматически:
error = UserNotFoundError(user_id=user_id)
# error.message == "User with id <uuid> not found"
```

---

## 🔄 BaseUnitOfWork — Транзакции + Events

**Проблема:** Каждый UoW нуждается в логике транзакций и публикации событий.

**Решение:** `BaseUnitOfWork` с готовой реализацией.

### Реализация

```python
# src/Ship/Parents/UnitOfWork.py
"""Base Unit of Work implementation."""

from dataclasses import dataclass, field
from typing import Any, Callable
from piccolo.engine import engine_finder
from src.Ship.Parents.Event import DomainEvent

EventEmitter = Callable[[str, DomainEvent], None]


@dataclass
class BaseUnitOfWork:
    """Unit of Work with integrated event publishing.
    
    Features:
    - Database transaction management via Piccolo
    - Domain event collection and publishing
    - Context manager interface
    
    Events are published AFTER successful commit.
    """
    
    _emit: EventEmitter | None = None
    _events: list[DomainEvent] = field(default_factory=list)
    _transaction: Any = field(default=None, repr=False)
    
    def add_event(self, event: DomainEvent) -> None:
        """Queue event for publishing after commit."""
        self._events.append(event)
    
    async def commit(self) -> None:
        """Commit transaction and publish events."""
        if self._transaction:
            await self._transaction.__aexit__(None, None, None)
            self._transaction = None
        
        if self._emit:
            for event in self._events:
                self._emit(event.event_name, event.model_dump(mode="json"))
        
        self._events.clear()
    
    async def rollback(self) -> None:
        """Rollback transaction and discard events."""
        if self._transaction:
            await self._transaction.__aexit__(Exception, Exception(), None)
            self._transaction = None
        self._events.clear()
    
    async def __aenter__(self) -> "BaseUnitOfWork":
        """Start transaction."""
        engine = engine_finder()
        if engine:
            self._transaction = engine.transaction()
            await self._transaction.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Rollback if exception, otherwise noop."""
        if exc_type:
            await self.rollback()
```

### Использование

```python
# ❌ БЕЗ BaseUnitOfWork — вся логика вручную
@dataclass
class UserUnitOfWork:
    users: UserRepository
    _events: list = field(default_factory=list)
    _transaction = None
    
    def add_event(self, event): ...
    async def commit(self): ...
    async def rollback(self): ...
    async def __aenter__(self): ...
    async def __aexit__(self): ...


# ✅ С BaseUnitOfWork — только добавляем repositories
@dataclass
class UserUnitOfWork(BaseUnitOfWork):
    users: UserRepository = None  # Injected by Dishka
```

---

## 💻 @with_container — Async CLI с DI

**Проблема:** Click команды не поддерживают async и DI из коробки.

**Решение:** Декоратор `@with_container` для async CLI с Dishka.

### Реализация

```python
# src/Ship/CLI/Decorators.py
"""CLI decorators and utilities for DI integration."""

import asyncio
import functools
from typing import TypeVar, Callable, Any

import click
from rich.console import Console
from returns.result import Result, Success, Failure
from dishka import make_async_container

from src.Ship.Providers import get_cli_providers
from src.Ship.Infrastructure.Telemetry import ensure_logfire_configured

T = TypeVar("T")
console = Console()
_cli_container = None


def get_cli_container():
    """Get or create CLI DI container (singleton)."""
    global _cli_container
    if _cli_container is None:
        _cli_container = make_async_container(*get_cli_providers())
    return _cli_container


def setup_cli_container(ctx: click.Context) -> None:
    """Setup CLI environment (Logfire, etc.).
    
    Call in your CLI group with @click.pass_context.
    
    Example:
        @click.group()
        @click.pass_context
        def cli(ctx: click.Context):
            setup_cli_container(ctx)
    """
    ensure_logfire_configured()


def with_container(func: Callable[..., Any]) -> Callable[..., None]:
    """Decorator for async CLI commands with DI container.
    
    Properly manages async container lifecycle.
    
    Example:
        @click.command()
        @with_container
        async def my_command(container, arg1: str) -> None:
            action = await container.get(MyAction)
            result = await action.run(...)
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        async def run() -> Any:
            container = get_cli_container()
            async with container() as request_container:
                return await func(request_container, *args, **kwargs)
        
        try:
            result = asyncio.run(run())
            if isinstance(result, Result):
                handle_cli_result(result)
        except SystemExit:
            raise
        except Exception as e:
            console.print(f"[red]✗[/red] Unexpected error: {str(e)}")
            raise SystemExit(1)
    
    return wrapper


def handle_cli_result(
    result: Result[Any, Any],
    success_message: str = "Success",
    show_fields: list[str] | None = None,
) -> None:
    """Handle Result object for CLI output."""
    match result:
        case Success(value):
            console.print(f"[green]✓[/green] {success_message}")
            if value is not None:
                if show_fields:
                    for field in show_fields:
                        if hasattr(value, field):
                            console.print(f"  {field}: {getattr(value, field)}")
                elif hasattr(value, "__dict__"):
                    for key, val in vars(value).items():
                        if not key.startswith("_"):
                            console.print(f"  {key}: {val}")
        case Failure(error):
            msg = error.message if hasattr(error, "message") else str(error)
            console.print(f"[red]✗[/red] Error: {msg}")
            raise SystemExit(1)
```

### Использование

```python
# ❌ БЕЗ @with_container — сложная настройка
@click.command()
def create_user(email: str, password: str, name: str):
    async def _run():
        container = make_async_container(*get_all_providers())
        async with container() as request_container:
            action = await request_container.get(CreateUserAction)
            result = await action.run(CreateUserRequest(...))
            # ... handle result ...
        await container.close()
    
    asyncio.run(_run())


# ✅ С @with_container — чисто и просто
@click.command()
@with_container
async def create_user(container, email: str, password: str, name: str):
    action = await container.get(CreateUserAction)
    result = await action.run(CreateUserRequest(email=email, password=password, name=name))
    
    match result:
        case Success(user):
            console.print(f"[green]✓[/green] User created: {user.id}")
        case Failure(error):
            console.print(f"[red]✗[/red] Error: {error.message}")
            raise SystemExit(1)
```

---

## 🔮 get_dependency — GraphQL DI Helper

**Проблема:** dishka-strawberry не поддерживает Litestar, нужен workaround для DI.

**Решение:** Helper `get_dependency` для получения зависимостей из Dishka контейнера.

### Реализация

```python
# src/Ship/GraphQL/Helpers.py
"""GraphQL helpers for DI and error handling."""

from typing import TypeVar, Type
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import strawberry

T = TypeVar("T")


async def get_dependency(info: strawberry.Info, dep_type: Type[T]) -> T:
    """Get dependency from Dishka container in GraphQL context.
    
    This is the recommended way to get dependencies in Strawberry resolvers
    when using Litestar (dishka-strawberry requires FastAPI).
    
    Note: Uses request-scoped container that Dishka creates automatically
    for each HTTP request via LitestarProvider.
    
    Usage:
        action = await get_dependency(info, CreateUserAction)
    """
    container = info.context["request"].state.dishka_container
    return await container.get(dep_type)


@asynccontextmanager
async def get_container_context(info: strawberry.Info) -> AsyncGenerator[object, None]:
    """Get Dishka container context for multiple dependencies.
    
    Use when you need to resolve multiple dependencies in one resolver.
    
    Usage:
        async with get_container_context(info) as container:
            query1 = await container.get(Query1)
            query2 = await container.get(Query2)
    """
    container = info.context["request"].state.dishka_container
    async with container() as request_container:
        yield request_container
```

### Использование

```python
# ❌ БЕЗ get_dependency — ручной доступ к контейнеру
@strawberry.mutation
async def create_user(self, input: CreateUserInput, info: strawberry.Info):
    container = info.context["request"].state.dishka_container
    action = await container.get(CreateUserAction)
    return await action.run(input.to_pydantic())


# ✅ С get_dependency — чисто
@strawberry.mutation
async def create_user(self, input: CreateUserInput, info: strawberry.Info):
    action = await get_dependency(info, CreateUserAction)
    return await action.run(input.to_pydantic())

# ✅ С get_container_context — для нескольких зависимостей
@strawberry.mutation
async def complex_mutation(self, info: strawberry.Info):
    async with get_container_context(info) as container:
        action1 = await container.get(Action1)
        action2 = await container.get(Action2)
        # использовать обе зависимости
```

---

## 🔌 Готовые интеграции библиотек

### Dishka + Litestar

```python
# src/App.py
from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka, FromDishka

container = make_async_container(*get_all_providers())
setup_dishka(container, app)

# В Controller
@post("/users")
async def create_user(action: FromDishka[CreateUserAction]):
    ...
```

### Dishka + TaskIQ

```python
# src/Ship/Infrastructure/Workers/Broker.py
from dishka.integrations.taskiq import setup_dishka, FromDishka, inject

setup_dishka(container, broker)

# В Worker
@broker.task
@inject
async def send_email(task: FromDishka[SendEmailTask]):
    ...
```

### Strawberry + Litestar

```python
# src/App.py
from strawberry.litestar import make_graphql_controller

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    context_getter=get_graphql_context,
    graphql_ide="graphiql",
)

app = Litestar(route_handlers=[GraphQLController])
```

### Piccolo + Pydantic (EntitySchema)

```python
# EntitySchema использует from_attributes=True
class UserResponse(EntitySchema):
    id: UUID
    email: str
    name: str

# Автоматическая конвертация из Piccolo Table
user = await AppUser.objects().first()
response = UserResponse.from_entity(user)  # Works!
```

---

## 📊 Сводная таблица

| Проблема | Решение | Тип | Файл |
|----------|---------|-----|------|
| Result → Response | `@result_handler` | Декоратор | `Ship/Decorators/result_handler.py` |
| Entity → DTO | `EntitySchema.from_entity()` | Базовый класс | `Ship/Core/BaseSchema.py` |
| Error messages | `ErrorWithTemplate` | Базовый класс | `Ship/Core/Errors.py` |
| UoW + Events | `BaseUnitOfWork` | Базовый класс | `Ship/Parents/UnitOfWork.py` |
| Async CLI + DI | `@with_container` | Декоратор | `Ship/CLI/Decorators.py` |
| CLI Result output | `handle_cli_result()` | Helper | `Ship/CLI/Decorators.py` |
| CLI setup | `setup_cli_container()` | Helper | `Ship/CLI/Decorators.py` |
| GraphQL DI (1 dep) | `get_dependency()` | Helper | `Ship/GraphQL/Helpers.py` |
| GraphQL DI (N deps) | `get_container_context()` | Context Mgr | `Ship/GraphQL/Helpers.py` |
| HTTP DI | `FromDishka[T]` | Готовая | `dishka.integrations.litestar` |
| TaskIQ DI | `FromDishka[T]` + `@inject` | Готовая | `dishka.integrations.taskiq` |
| GraphQL Server | `make_graphql_controller()` | Готовая | `strawberry.litestar` |

---

## 💡 Принцип: Готовое > Кастомное

1. **Сначала** — ищи готовую интеграцию библиотеки
2. **Потом** — ищи готовое решение в Ship
3. **В крайнем случае** — пиши кастомное в Ship

```python
# Порядок предпочтения:
# 1. Готовая интеграция
from dishka.integrations.litestar import FromDishka  # ✅ Идеально

# 2. Готовый helper из Ship
from src.Ship.GraphQL.Helpers import get_dependency  # ✅ Хорошо

# 3. Кастомный код (только если нет альтернатив)
async def my_custom_di_helper():  # ⚠️ Избегай
    ...
```

---

<div align="center">

**Предыдущий раздел:** [11-litestar-features.md](11-litestar-features.md) — Litestar Features Integration

</div>
