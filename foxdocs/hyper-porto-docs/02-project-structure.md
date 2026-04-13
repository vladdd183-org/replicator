# 📁 Структура проекта Hyper-Porto

> **Версия:** 4.3 | **Дата:** Январь 2026

---

## 🗂️ Полная структура проекта

```
new_porto/                            # Root проекта
├── docs/                             # Документация архитектуры
│   ├── 00-philosophy.md              # Философия и принципы
│   ├── 01-architecture.md            # Архитектурные слои
│   ├── 02-project-structure.md       # ← Вы здесь
│   ├── 03-components.md              # Action, Task, Repository, Query, UoW
│   ├── 04-result-railway.md          # Result, Railway-oriented programming
│   ├── 05-concurrency.md             # anyio, TaskGroups, Structured Concurrency
│   ├── 06-metaprogramming.md         # Tenacity, Cashews, Pydantic validate_call
│   ├── 07-spec-driven.md             # Spec-Driven Development (Spec Kit)
│   ├── 08-libraries.md               # Tech Stack и обоснование
│   ├── 09-transports.md              # HTTP, GraphQL, CLI, WebSocket, Workers
│   ├── 10-registration.md            # Явная регистрация vs автосканирование
│   ├── 11-litestar-features.md       # Channels, Events, Middleware, Stores
│   └── 12-reducing-boilerplate.md    # Паттерны сокращения бойлерплейта
│
├── agent-os/                         # Agent OS стандарты и workflow
│   ├── specs/                        # Spec-Driven Development
│   └── ...
│
├── src/                              # Исходный код
│   ├── __init__.py
│   ├── App.py                        # Litestar Application Factory
│   ├── Main.py                       # Entry point (uvicorn запуск)
│   │
│   ├── Ship/                         # Инфраструктурный слой (общий)
│   │   ├── __init__.py
│   │   │
│   │   ├── Auth/                     # Аутентификация
│   │   │   ├── __init__.py
│   │   │   ├── Guards.py             # Litestar Guards (auth_guard)
│   │   │   ├── JWT.py                # JWT Service (создание/валидация)
│   │   │   └── Middleware.py         # Auth Middleware
│   │   │
│   │   ├── CLI/                      # Command Line Interface
│   │   │   ├── __init__.py
│   │   │   ├── Decorators.py         # @with_container, @async_command
│   │   │   ├── Main.py               # Click CLI entry point
│   │   │   └── MigrationCommands.py  # Миграции (Piccolo)
│   │   │
│   │   ├── Configs/                  # Конфигурация
│   │   │   ├── __init__.py
│   │   │   └── Settings.py           # Pydantic BaseSettings
│   │   │
│   │   ├── Core/                     # Ядро архитектуры
│   │   │   ├── __init__.py
│   │   │   ├── BaseSchema.py         # EntitySchema (Response DTOs)
│   │   │   ├── Errors.py             # BaseError, ErrorWithTemplate, DomainException
│   │   │   ├── Protocols.py          # typing.Protocol интерфейсы
│   │   │   ├── Types.py              # Type aliases
│   │   │   ├── PiccoloApp.py         # Piccolo App для Ship (для миграций)
│   │   │   └── migrations/           # Миграции Ship
│   │   │
│   │   ├── Decorators/               # Декораторы
│   │   │   ├── __init__.py
│   │   │   ├── audited.py            # @audited (автологирование Actions)
│   │   │   ├── cache_utils.py        # invalidate_cache
│   │   │   └── result_handler.py     # @result_handler (Result → Response)
│   │   │
│   │   ├── Events/                   # Ship-level события
│   │   │   ├── __init__.py
│   │   │   └── ActionEvents.py       # ActionExecuted (для аудита)
│   │   │
│   │   ├── Exceptions/               # Обработка исключений
│   │   │   ├── __init__.py
│   │   │   └── ProblemDetails.py     # RFC 9457 error handler
│   │   │
│   │   ├── GraphQL/                  # GraphQL инфраструктура
│   │   │   ├── __init__.py
│   │   │   ├── Context.py            # GraphQL context
│   │   │   ├── Helpers.py            # get_dependency, map_result
│   │   │   └── Schema.py             # Root Query + Mutation
│   │   │
│   │   ├── Infrastructure/           # Внешние сервисы
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── Cache/                # Кэширование
│   │   │   │   ├── __init__.py
│   │   │   │   ├── Cashews.py        # cashews настройка
│   │   │   │   └── Redis.py          # Redis клиент
│   │   │   │
│   │   │   ├── Concurrency/          # Конкурентность
│   │   │   │   ├── __init__.py
│   │   │   │   ├── Limiter.py        # CapacityLimiter
│   │   │   │   └── TaskGroup.py      # TaskGroup helpers
│   │   │   │
│   │   │   ├── Database/             # База данных
│   │   │   │   └── __init__.py
│   │   │   │
│   │   │   ├── HealthCheck.py        # Liveness/Readiness probes
│   │   │   │
│   │   │   ├── MessageBus/           # Event Bus (если нужен кастомный)
│   │   │   │   ├── __init__.py
│   │   │   │   └── Handlers.py
│   │   │   │
│   │   │   ├── RateLimiting.py       # Rate Limiting middleware
│   │   │   │
│   │   │   ├── Telemetry/            # Observability
│   │   │   │   ├── __init__.py
│   │   │   │   ├── Logfire.py        # Logfire настройка
│   │   │   │   └── RequestLoggingMiddleware.py
│   │   │   │
│   │   │   └── Workers/              # Background tasks
│   │   │       ├── __init__.py
│   │   │       └── Broker.py         # TaskIQ broker настройка
│   │   │
│   │   ├── Parents/                  # Базовые классы (Abstract)
│   │   │   ├── __init__.py
│   │   │   ├── Action.py             # Abstract Action[Input, Output, Error]
│   │   │   ├── Event.py              # DomainEvent base
│   │   │   ├── Model.py              # Model base (если нужен)
│   │   │   ├── Query.py              # Abstract Query[Input, Output]
│   │   │   ├── Repository.py         # Abstract Repository[T]
│   │   │   ├── Task.py               # Abstract Task[Input, Output]
│   │   │   └── UnitOfWork.py         # BaseUnitOfWork
│   │   │
│   │   ├── Plugins/                  # Litestar Plugins
│   │   │   └── __init__.py
│   │   │
│   │   └── Providers/                # Dishka Providers (общие)
│   │       ├── __init__.py
│   │       └── AppProvider.py        # Settings, JWT, Cache и т.д.
│   │
│   └── Containers/                   # Бизнес-модули
│       ├── __init__.py
│       │
│       ├── AppSection/               # Основные бизнес-модули
│       │   ├── __init__.py
│       │   ├── UserModule/           # Управление пользователями
│       │   ├── NotificationModule/   # Система уведомлений
│       │   ├── AuditModule/          # Логирование и аудит
│       │   ├── SearchModule/         # Полнотекстовый поиск
│       │   └── SettingsModule/       # Настройки и Feature Flags
│       │
│       └── VendorSection/            # Интеграции с внешними сервисами
│           ├── __init__.py
│           ├── EmailModule/          # Email интеграция (виртуальная)
│           ├── PaymentModule/        # Платёжная система (виртуальная)
│           └── WebhookModule/        # Входящие/исходящие вебхуки
│
│   # ─── Структура UserModule (пример) ───
│   #
│   #     UserModule/           # ←── ПРИМЕР МОДУЛЯ
│               ├── __init__.py       # user_router export
│               │
│               ├── Actions/          # Use Cases (CQRS Commands)
│               │   ├── __init__.py
│               │   ├── AuthenticateAction.py
│               │   ├── ChangePasswordAction.py
│               │   ├── CreateUserAction.py
│               │   ├── DeleteUserAction.py
│               │   ├── RefreshTokenAction.py
│               │   └── UpdateUserAction.py
│               │
│               ├── Activities/       # Temporal Activities (опционально)
│               │   ├── __init__.py   # Для модулей с Workflows
│               │   └── ...Activity.py
│               │
│               ├── Data/             # Data Access Layer
│               │   ├── __init__.py
│               │   │
│               │   ├── Repositories/ # Repository Pattern
│               │   │   ├── __init__.py
│               │   │   └── UserRepository.py
│               │   │
│               │   ├── Schemas/      # Pydantic DTOs
│               │   │   ├── __init__.py
│               │   │   ├── Requests.py   # CreateUserRequest, LoginRequest, etc.
│               │   │   └── Responses.py  # UserResponse, AuthResponse, etc.
│               │   │
│               │   └── UnitOfWork.py # UserUnitOfWork
│               │
│               ├── Errors.py         # Ошибки модуля (Pydantic frozen)
│               │
│               ├── Events.py         # Domain Events (UserCreated, etc.)
│               │
│               ├── Listeners.py      # Event Listeners (@listener)
│               │
│               ├── Models/           # Piccolo ORM Tables
│               │   ├── __init__.py
│               │   ├── PiccoloApp.py # Piccolo App для миграций
│               │   ├── User.py       # AppUser Table
│               │   └── migrations/   # Авто-генерируемые миграции
│               │       └── user_2026_01_06t18_26_49_171359.py
│               │
│               ├── Providers.py      # Dishka Providers модуля
│               │
│               ├── Queries/          # CQRS Queries (Read)
│               │   ├── __init__.py
│               │   ├── GetUserQuery.py
│               │   └── ListUsersQuery.py
│               │
│               ├── Tasks/            # Atomic Operations (локальные)
│               │   ├── __init__.py
│               │   ├── GenerateTokenTask.py
│               │   ├── HashPasswordTask.py
│               │   ├── SendWelcomeEmailTask.py
│               │   └── VerifyPasswordTask.py
│               │
│               ├── Workflows/        # Temporal Workflows (опционально)
│               │   ├── __init__.py   # Для модулей с Saga
│               │   └── ...Workflow.py
│               │
│               └── UI/               # Presentation Layer
│                   ├── __init__.py
│                   │
│                   ├── API/          # HTTP REST
│                   │   ├── __init__.py
│                   │   ├── Controllers/
│                   │   │   ├── __init__.py
│                   │   │   ├── AuthController.py
│                   │   │   └── UserController.py
│                   │   └── Routes.py # Router composition
│                   │
│                   ├── CLI/          # Command Line
│                   │   ├── __init__.py
│                   │   └── Commands.py
│                   │
│                   ├── GraphQL/      # Strawberry GraphQL
│                   │   ├── __init__.py
│                   │   ├── Resolvers.py
│                   │   └── Types.py
│                   │
│                   ├── WebSocket/    # Real-time
│                   │   ├── __init__.py
│                   │   └── Handlers.py
│                   │
│                   └── Workers/      # TaskIQ Background
│                       ├── __init__.py
│                       └── Tasks.py
│
├── tests/                            # Тесты (pytest)
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env                              # Environment variables
├── env.example                       # Шаблон .env
├── .cursor/                          # AI-правила для Cursor (rules/)
├── .gitignore
├── docker-compose.yml                # Docker (Postgres, Redis)
├── piccolo_conf.py                   # Piccolo ORM конфигурация
├── pyproject.toml                    # Python dependencies (uv / PEP 621)
└── README.md
```

---

## 🚢 Ship Layer — Инфраструктура

Ship содержит **общий код**, переиспользуемый всеми Container'ами.

### Parents/ — Базовые классы

```python
# src/Ship/Parents/Action.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from returns.result import Result

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")
ErrorT = TypeVar("ErrorT")

class Action(ABC, Generic[InputT, OutputT, ErrorT]):
    """
    Base Action class for Use Cases.
    
    - Single responsibility: одна бизнес-операция
    - Returns Result[OutputT, ErrorT] — явная обработка ошибок
    - Orchestrates Tasks and Repositories
    - Transport-agnostic: не знает о HTTP/GraphQL/CLI
    """
    
    @abstractmethod
    async def run(self, data: InputT) -> Result[OutputT, ErrorT]:
        """Execute the action with input data."""
        ...
```

```python
# src/Ship/Parents/Task.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

class Task(ABC, Generic[InputT, OutputT]):
    """
    Async atomic operation.
    Reusable across multiple Actions.
    """
    
    @abstractmethod
    async def run(self, data: InputT) -> OutputT:
        ...

class SyncTask(ABC, Generic[InputT, OutputT]):
    """
    Sync atomic operation (CPU-bound).
    Call via anyio.to_thread.run_sync().
    """
    
    @abstractmethod
    def run(self, data: InputT) -> OutputT:
        ...
```

```python
# src/Ship/Parents/Query.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

class Query(ABC, Generic[InputT, OutputT]):
    """
    CQRS Query — read-only операция (async для I/O).
    Bypasses UoW, returns plain values.
    """
    
    @abstractmethod
    async def execute(self, input: InputT) -> OutputT:
        ...

class SyncQuery(ABC, Generic[InputT, OutputT]):
    """
    Sync Query — для in-memory/cached операций.
    Используй когда не нужен async I/O.
    """
    
    @abstractmethod
    def execute(self, input: InputT) -> OutputT:
        ...
```

```python
# src/Ship/Parents/Repository.py
from abc import ABC
from typing import Generic, TypeVar
from piccolo.table import Table

T = TypeVar("T", bound=Table)

class Repository(ABC, Generic[T]):
    """
    Generic repository over Piccolo Table.
    Provides CRUD + lifecycle hooks.
    """
    _table: type[T]
    
    async def add(self, entity: T) -> T: ...
    async def get(self, id: Any) -> T | None: ...
    async def update(self, entity: T, data: dict[str, Any]) -> T: ...
    async def delete(self, entity: T) -> None: ...
    
    # Lifecycle hooks
    async def _on_add(self, entity: T) -> None: ...
    async def _on_update(self, entity: T, changes: dict) -> None: ...
    async def _on_delete(self, entity: T) -> None: ...
```

```python
# src/Ship/Parents/UnitOfWork.py
from dataclasses import dataclass, field
from typing import Callable
from piccolo.engine import engine_finder
from src.Ship.Parents.Event import DomainEvent

EventEmitter = Callable[[DomainEvent], None]

@dataclass
class BaseUnitOfWork:
    """
    Unit of Work pattern.
    - Manages DB transactions (Piccolo)
    - Collects and publishes Domain Events
    """
    _emit: EventEmitter | None = None
    _events: list[DomainEvent] = field(default_factory=list)
    _transaction: Any = None
    
    def add_event(self, event: DomainEvent) -> None:
        self._events.append(event)
    
    async def commit(self) -> None:
        if self._transaction:
            await self._transaction.__aexit__(None, None, None)
        # Publish events after successful commit
        if self._emit:
            for event in self._events:
                self._emit(event.event_name, event)
        self._events.clear()
    
    async def rollback(self) -> None:
        if self._transaction:
            await self._transaction.__aexit__(Exception, Exception(), None)
        self._events.clear()
```

---

### Core/ — Базовые утилиты

```python
# src/Ship/Core/Errors.py
from pydantic import BaseModel
from typing import ClassVar

class BaseError(BaseModel):
    """Base error with HTTP mapping."""
    model_config = {"frozen": True}
    
    message: str
    code: str = "UNKNOWN_ERROR"
    http_status: int = 400

class ErrorWithTemplate(BaseError):
    """Auto-generates message from template."""
    _message_template: ClassVar[str] = ""
    
    def __init__(self, **data):
        if "message" not in data and self._message_template:
            data["message"] = self._message_template.format(**data)
        super().__init__(**data)

class DomainException(Exception):
    """Wrapper to raise BaseError as exception."""
    def __init__(self, error: BaseError):
        self.error = error
        super().__init__(error.message)
```

```python
# src/Ship/Core/BaseSchema.py
from pydantic import BaseModel, ConfigDict
from typing import TypeVar, Type

T = TypeVar("T", bound="EntitySchema")

class EntitySchema(BaseModel):
    """
    Base Response DTO.
    Provides from_entity() for ORM model conversion.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
    
    @classmethod
    def from_entity(cls: Type[T], entity: object) -> T:
        """Create DTO from Entity (ORM model)."""
        return cls.model_validate(entity)
```

---

### Decorators/ — Общие декораторы

```python
# src/Ship/Decorators/result_handler.py
from functools import wraps
from returns.result import Success, Failure
from litestar import Response
from litestar.status_codes import HTTP_200_OK

def result_handler(response_dto: type, *, success_status: int = HTTP_200_OK):
    """
    Convert Result[T, E] to Litestar Response.
    
    Success(value) → Response(response_dto.from_entity(value), status=success_status)
    Failure(error) → DomainException(error) → Problem Details
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            match result:
                case Success(value):
                    if hasattr(response_dto, "from_entity"):
                        content = response_dto.from_entity(value)
                    else:
                        content = response_dto.model_validate(value)
                    return Response(content=content, status_code=success_status)
                case Failure(error):
                    raise DomainException(error)
        return wrapper
    return decorator
```

---

## 📦 Container Layer — Бизнес-модули

Каждый Container — изолированный бизнес-модуль.

### UserModule — Полный пример

#### Models/User.py

```python
from piccolo.table import Table
from piccolo.columns import Varchar, Boolean, Timestamptz, UUID

class AppUser(Table, tablename="app_users"):
    """User entity."""
    id = UUID(primary_key=True, default=UUID4())
    email = Varchar(length=255, unique=True, index=True)
    password_hash = Varchar(length=255)
    name = Varchar(length=100)
    is_active = Boolean(default=True)
    created_at = Timestamptz(auto_now_add=True)
    updated_at = Timestamptz(auto_now=True)
```

#### Errors.py

```python
from src.Ship.Core.Errors import BaseError, ErrorWithTemplate
from typing import ClassVar
from uuid import UUID

class UserError(BaseError):
    """Base error for UserModule."""
    pass

class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User with id {user_id} not found"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID

class UserAlreadyExistsError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User with email {email} already exists"
    code: str = "USER_ALREADY_EXISTS"
    http_status: int = 409
    email: str

class InvalidCredentialsError(UserError):
    message: str = "Invalid email or password"
    code: str = "INVALID_CREDENTIALS"
    http_status: int = 401
```

#### Actions/CreateUserAction.py

```python
from dataclasses import dataclass
from returns.result import Result, Success, Failure
import anyio

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import UserError, UserAlreadyExistsError
from src.Containers.AppSection.UserModule.Events import UserCreated
from src.Containers.AppSection.UserModule.Models.User import AppUser
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask

class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    """Use Case: Create a new user."""
    
    def __init__(
        self,
        hash_password: HashPasswordTask,
        uow: UserUnitOfWork,
    ) -> None:
        self.hash_password = hash_password
        self.uow = uow

    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        # Check if user exists
        existing = await self.uow.users.find_by_email(data.email)
        if existing:
            return Failure(UserAlreadyExistsError(email=data.email))
        
        # Hash password (offload to thread for CPU-bound operation)
        password_hash = await anyio.to_thread.run_sync(
            self.hash_password.run, data.password
        )
        
        # Create user within transaction
        async with self.uow:
            user = AppUser(
                email=data.email,
                password_hash=password_hash,
                name=data.name,
            )
            await self.uow.users.add(user)
            self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
            await self.uow.commit()
        
        return Success(user)
```

#### UI/API/Controllers/UserController.py

```python
from litestar import Controller, get, post, put, delete
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from dishka.integrations.litestar import FromDishka

from src.Ship.Decorators.result_handler import result_handler
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import UserResponse

class UserController(Controller):
    path = "/users"
    tags = ["Users"]

    @post("/")
    @result_handler(UserResponse, success_status=HTTP_201_CREATED)
    async def create_user(
        self,
        data: CreateUserRequest,
        action: FromDishka[CreateUserAction],
    ):
        return await action.run(data)
```

#### Providers.py

```python
from dishka import Provider, Scope, provide
from litestar import Request

from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask

class UserModuleProvider(Provider):
    """App-scoped providers (stateless)."""
    scope = Scope.APP
    
    hash_password = provide(HashPasswordTask)

class UserRequestProvider(Provider):
    """Request-scoped providers (stateful)."""
    scope = Scope.REQUEST
    
    @provide
    def user_repository(self) -> UserRepository:
        return UserRepository()
    
    @provide
    def user_uow(self, users: UserRepository, request: Request) -> UserUnitOfWork:
        return UserUnitOfWork(users=users, _emit=request.app.emit)
    
    create_user_action = provide(CreateUserAction)
```

---

## 📁 Правила именования файлов

| Компонент | Паттерн имени | Пример файла |
|-----------|---------------|--------------|
| Action | `{Verb}{Noun}Action.py` | `CreateUserAction.py` |
| Task | `{Verb}{Noun}Task.py` | `HashPasswordTask.py` |
| Query | `{Verb/Get}{Noun}Query.py` | `GetUserQuery.py`, `ListUsersQuery.py` |
| Repository | `{Noun}Repository.py` | `UserRepository.py` |
| Model | `{Noun}.py` | `User.py` |
| Controller | `{Noun}Controller.py` | `UserController.py` |
| Error | `Errors.py` | `Errors.py` (все ошибки модуля) |
| Event | `Events.py` | `Events.py` (все события модуля) |
| Listener | `Listeners.py` | `Listeners.py` (все слушатели) |
| Request DTO | `Requests.py` | `Data/Schemas/Requests.py` |
| Response DTO | `Responses.py` | `Data/Schemas/Responses.py` |
| Providers | `Providers.py` | `Providers.py` |

---

## 🔗 Импорты между компонентами

### ✅ Разрешённые импорты

```python
# Controller → Action, Query
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import GetUserQuery

# Action → Task, Repository, UoW, Error, Event
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import UserAlreadyExistsError
from src.Containers.AppSection.UserModule.Events import UserCreated

# Task → ничего domain-специфичного (атомарная операция)
# Repository → Model
from src.Containers.AppSection.UserModule.Models.User import AppUser

# Любой компонент → Ship
from src.Ship.Parents.Action import Action
from src.Ship.Core.Errors import BaseError
```

### ❌ Запрещённые импорты

```python
# Controller НЕ может напрямую в Repository
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository

# Container НЕ может импортировать другой Container напрямую
from src.Containers.AppSection.OrderModule.Actions.CreateOrderAction import CreateOrderAction

# Относительные импорты ЗАПРЕЩЕНЫ
from ....Actions.CreateUserAction import CreateUserAction
```

---

## 📊 Визуализация зависимостей

```
┌─────────────────────────────────────────────────────────────────────┐
│                             Ship Layer                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Parents  │ │  Core    │ │Decorators│ │  Infra   │ │ Providers│  │
│  │ Action   │ │ Errors   │ │ result_  │ │ Cache    │ │ App      │  │
│  │ Task     │ │ Schema   │ │ handler  │ │ Telemetry│ │ Provider │  │
│  │ Query    │ │ Types    │ │          │ │ Workers  │ │          │  │
│  │ Repo     │ │ Protocols│ │          │ │          │ │          │  │
│  │ UoW      │ │          │ │          │ │          │ │          │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ extends/uses
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                         Container Layer                              │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                         UserModule                             │  │
│  │                                                                │  │
│  │   ┌─────────┐      ┌─────────┐      ┌─────────────┐           │  │
│  │   │   UI    │ ───▶ │ Actions │ ───▶ │    Tasks    │           │  │
│  │   │Controller     │ Queries │      │ HashPassword │           │  │
│  │   │ GraphQL │      │         │      │ VerifyPass   │           │  │
│  │   │ CLI     │      │         │      │ GenerateToken│           │  │
│  │   │ WS      │      │         │      └─────────────┘           │  │
│  │   └─────────┘      └────┬────┘                                │  │
│  │                         │                                      │  │
│  │                         ▼                                      │  │
│  │   ┌─────────────────────────────────────────────────────────┐ │  │
│  │   │                   Data Layer                             │ │  │
│  │   │  ┌────────────┐  ┌────────────┐  ┌────────────────┐     │ │  │
│  │   │  │ Repository │  │ UnitOfWork │  │    Schemas     │     │ │  │
│  │   │  │            │◀─│            │  │ Requests.py    │     │ │  │
│  │   │  └──────┬─────┘  └─────┬──────┘  │ Responses.py   │     │ │  │
│  │   │         │              │         └────────────────┘     │ │  │
│  │   │         ▼              │                                │ │  │
│  │   │  ┌────────────┐        │                                │ │  │
│  │   │  │   Models   │        │  Events → Listeners            │ │  │
│  │   │  │  AppUser   │        │         ↓                      │ │  │
│  │   │  └────────────┘        │  litestar.events + Channels    │ │  │
│  │   └─────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

<div align="center">

**Следующий раздел:** [03-components.md](03-components.md) — Детальное описание компонентов

</div>
