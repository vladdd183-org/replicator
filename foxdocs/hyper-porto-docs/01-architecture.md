# 🏗️ Архитектура Hyper-Porto

> **Версия:** 4.3 | **Дата:** Январь 2026  
> Детальное описание слоёв, компонентов и их взаимодействия

---

## 📐 Архитектурные слои

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRAMEWORK (Litestar)                        │
│  HTTP REST, WebSocket, CLI, GraphQL, TaskIQ — точки входа          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                              SHIP                                    │
│  Общая инфраструктура: Parents, Core, Providers, Decorators         │
│  Auth, CLI, Configs, Exceptions, GraphQL, Infrastructure, Plugins   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Container A   │       │   Container B   │       │   Container C   │
│   (UserModule)  │       │  (OrderModule)  │       │ (PaymentModule) │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ UI/             │       │ UI/             │       │ UI/             │
│ Actions/        │       │ Actions/        │       │ Actions/        │
│ Tasks/          │       │ Tasks/          │       │ Tasks/          │
│ Queries/        │       │ Queries/        │       │ Queries/        │
│ Data/           │       │ Data/           │       │ Data/           │
│ Models/         │       │ Models/         │       │ Models/         │
│ Events.py       │       │ Events.py       │       │ Events.py       │
│ Errors.py       │       │ Errors.py       │       │ Errors.py       │
│ Providers.py    │       │ Providers.py    │       │ Providers.py    │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

---

## 🚢 Ship Layer (Ядро)

Ship — "материнский корабль", содержащий общий код для всех Containers.

### Реальная структура Ship

```
Ship/
├── Auth/                       # Аутентификация
│   ├── Guards.py               # auth_guard, optional_auth_guard
│   ├── JWT.py                  # JWTService (создание/валидация токенов)
│   └── Middleware.py           # AuthenticationMiddleware, AuthUser
│
├── CLI/                        # Command Line Interface
│   ├── Decorators.py           # @with_container, handle_cli_result
│   ├── Main.py                 # Click CLI entry point
│   └── MigrationCommands.py    # Piccolo миграции
│
├── Configs/                    # Конфигурация
│   └── Settings.py             # Pydantic BaseSettings
│
├── Core/                       # Ядро системы
│   ├── BaseSchema.py           # EntitySchema (from_entity)
│   ├── Errors.py               # BaseError, ErrorWithTemplate, DomainException
│   ├── Protocols.py            # typing.Protocol интерфейсы
│   ├── Types.py                # Общие типы
│   └── PiccoloApp.py           # Piccolo App для Ship
│
├── Decorators/                 # Кастомные декораторы
│   ├── cache_utils.py          # invalidate_cache
│   └── result_handler.py       # @result_handler (Result → Response)
│
├── Exceptions/                 # Обработка исключений
│   └── ProblemDetails.py       # RFC 9457 Problem Details
│
├── GraphQL/                    # GraphQL инфраструктура
│   ├── Context.py              # GraphQL context
│   ├── Helpers.py              # get_dependency helper
│   └── Schema.py               # Root Query + Mutation
│
├── Infrastructure/             # Внешние сервисы
│   ├── Cache/                  # Cashews + Redis
│   ├── Concurrency/            # Limiter, TaskGroup helpers
│   ├── Database/               # DB utilities
│   ├── HealthCheck.py          # Liveness/Readiness
│   ├── MessageBus/             # (если нужен кастомный)
│   ├── RateLimiting.py         # Rate Limiter
│   ├── Telemetry/              # Logfire + RequestLoggingMiddleware
│   └── Workers/                # TaskIQ broker
│
├── Parents/                    # Базовые классы (Abstract)
│   ├── Action.py               # Action[Input, Output, Error]
│   ├── Event.py                # DomainEvent
│   ├── Model.py                # (если нужен базовый)
│   ├── Query.py                # Query[Input, Output]
│   ├── Repository.py           # Repository[T]
│   ├── Task.py                 # Task[Input, Output], SyncTask
│   └── UnitOfWork.py           # BaseUnitOfWork
│
├── Plugins/                    # Litestar plugins
│   └── __init__.py
│
└── Providers/                  # DI провайдеры
    └── AppProvider.py          # Settings, JWT, get_all_providers()
```

### Ключевые компоненты Ship

#### Parents/ — Базовые классы

```python
# src/Ship/Parents/Action.py
class Action(ABC, Generic[InputT, OutputT, ErrorT]):
    """Base Action class for Use Cases."""
    
    @abstractmethod
    async def run(self, data: InputT) -> Result[OutputT, ErrorT]:
        ...

# src/Ship/Parents/Task.py
class Task(ABC, Generic[InputT, OutputT]):
    """Async atomic operation."""
    
    @abstractmethod
    async def run(self, data: InputT) -> OutputT:
        ...

class SyncTask(ABC, Generic[InputT, OutputT]):
    """Sync atomic operation (CPU-bound)."""
    
    @abstractmethod
    def run(self, data: InputT) -> OutputT:
        ...

# src/Ship/Parents/Query.py
class Query(ABC, Generic[InputT, OutputT]):
    """CQRS Query — read-only операция (async для I/O)."""
    
    @abstractmethod
    async def execute(self, input: InputT) -> OutputT:
        ...

class SyncQuery(ABC, Generic[InputT, OutputT]):
    """Sync Query для in-memory/cached операций."""
    
    @abstractmethod
    def execute(self, input: InputT) -> OutputT:
        ...
```

#### Providers/ — DI провайдеры

```python
# src/Ship/Providers/AppProvider.py
class AppProvider(Provider):
    """Main application provider (APP scope)."""
    
    @provide(scope=Scope.APP)
    def provide_settings(self) -> Settings:
        return get_settings()
    
    @provide(scope=Scope.APP)
    def provide_jwt_service(self) -> JWTService:
        return get_jwt_service()


def get_all_providers() -> list[Provider]:
    """Get all providers for HTTP context."""
    from src.Containers.AppSection.UserModule.Providers import (
        UserModuleProvider,
        UserRequestProvider,
    )
    
    return [
        AppProvider(),
        LitestarProvider(),  # Provides Request in REQUEST scope
        UserModuleProvider(),
        UserRequestProvider(),
    ]


def get_cli_providers() -> list[Provider]:
    """Get providers for CLI context (without Request)."""
    from src.Containers.AppSection.UserModule.Providers import (
        UserModuleProvider,
        UserCLIProvider,
    )
    
    return [
        AppProvider(),
        UserModuleProvider(),
        UserCLIProvider(),
    ]
```

---

## 📦 Container Layer (Бизнес-модули)

Каждый Container — изолированный бизнес-модуль со своей доменной логикой.

### Реальная структура Container

```
Containers/AppSection/UserModule/
│
├── __init__.py                 # user_router export
│
├── Actions/                    # 🎬 Use Cases (CQRS Commands)
│   ├── AuthenticateAction.py   # Login
│   ├── ChangePasswordAction.py
│   ├── CreateUserAction.py
│   ├── DeleteUserAction.py
│   ├── RefreshTokenAction.py
│   └── UpdateUserAction.py
│
├── Tasks/                      # ⚙️ Атомарные операции
│   ├── GenerateTokenTask.py
│   ├── HashPasswordTask.py
│   ├── SendWelcomeEmailTask.py
│   └── VerifyPasswordTask.py
│
├── Queries/                    # 📖 CQRS Queries (Read)
│   ├── GetUserQuery.py
│   └── ListUsersQuery.py
│
├── Data/                       # 💾 Data Layer
│   ├── Repositories/
│   │   └── UserRepository.py
│   ├── Schemas/
│   │   ├── Requests.py         # CreateUserRequest, LoginRequest, etc.
│   │   └── Responses.py        # UserResponse, AuthResponse, etc.
│   └── UnitOfWork.py           # UserUnitOfWork
│
├── Models/                     # 📋 Domain Models (Piccolo)
│   ├── PiccoloApp.py           # For migrations
│   ├── User.py                 # AppUser Table
│   └── migrations/
│
├── UI/                         # 🖥️ Presentation Layer
│   ├── API/
│   │   ├── Controllers/
│   │   │   ├── AuthController.py
│   │   │   └── UserController.py
│   │   └── Routes.py
│   ├── CLI/
│   │   └── Commands.py
│   ├── GraphQL/
│   │   ├── Resolvers.py
│   │   └── Types.py
│   ├── WebSocket/
│   │   └── Handlers.py
│   └── Workers/
│       └── Tasks.py            # TaskIQ background tasks
│
├── Events.py                   # 📨 Domain Events (UserCreated, etc.)
├── Listeners.py                # 🎧 Event Listeners (@listener)
├── Errors.py                   # ❌ Ошибки модуля (Pydantic frozen)
└── Providers.py                # 💉 DI регистрация (Dishka)
```

### Providers модуля

```python
# src/Containers/AppSection/UserModule/Providers.py

class UserModuleProvider(Provider):
    """APP scope — stateless tasks."""
    scope = Scope.APP
    
    hash_password_task = provide(HashPasswordTask)
    verify_password_task = provide(VerifyPasswordTask)
    generate_token_task = provide(GenerateTokenTask)


class _BaseUserRequestProvider(Provider):
    """Base REQUEST scope — common dependencies."""
    scope = Scope.REQUEST
    
    user_repository = provide(UserRepository)
    list_users_query = provide(ListUsersQuery)
    get_user_query = provide(GetUserQuery)
    create_user_action = provide(CreateUserAction)
    # ... other actions


class UserRequestProvider(_BaseUserRequestProvider):
    """HTTP context — UoW with event emitter."""
    
    @provide
    def provide_user_uow(self, request: Request) -> UserUnitOfWork:
        return UserUnitOfWork(_emit=request.app.emit, _app=request.app)


class UserCLIProvider(_BaseUserRequestProvider):
    """CLI context — UoW without event emitter."""
    
    @provide
    def provide_user_uow(self) -> UserUnitOfWork:
        return UserUnitOfWork(_emit=None, _app=None)
```

---

## 🔄 Поток данных

### HTTP Request Flow

```python
# 1. Controller получает запрос, DI инъектирует Action
@post("/users")
@result_handler(UserResponse, success_status=201)
async def create_user(
    data: CreateUserRequest,           # Pydantic валидация
    action: FromDishka[CreateUserAction],  # DI инъекция
) -> Result[AppUser, UserError]:
    # 2. Вызов Action
    return await action.run(data)

# 3. @result_handler автоматически:
#    - Success(user) → Response(UserResponse.from_entity(user), 201)
#    - Failure(error) → DomainException → Problem Details (RFC 9457)
```

### Action Flow (реальный код)

```python
# src/Containers/AppSection/UserModule/Actions/CreateUserAction.py

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
        # Step 1: Check if user exists
        existing_user = await self.uow.users.find_by_email(data.email)
        if existing_user is not None:
            return Failure(UserAlreadyExistsError(email=data.email))
        
        # Step 2: Hash password (offload to thread for CPU-bound)
        password_hash = await anyio.to_thread.run_sync(
            self.hash_password.run, data.password
        )
        
        # Step 3: Create user within UoW transaction
        async with self.uow:
            user = AppUser(
                email=data.email,
                password_hash=password_hash,
                name=data.name,
            )
            await self.uow.users.add(user)
            
            # Step 4: Add event (published AFTER commit)
            self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
            
            await self.uow.commit()
        
        return Success(user)
```

---

## 🎯 Правила взаимодействия

### Что может вызывать что

```
┌─────────────┬───────────┬───────────┬────────────┬────────────┬──────────┐
│             │Controller │  Action   │   Task     │   Query    │Repository│
├─────────────┼───────────┼───────────┼────────────┼────────────┼──────────┤
│ Controller  │    ❌     │    ✅     │    ❌      │    ✅      │    ❌    │
│ Action      │    ❌     │    ❌*    │    ✅      │    ❌      │    ✅    │
│ Task        │    ❌     │    ❌     │    ❌      │    ❌      │    ⚠️    │
│ Query       │    ❌     │    ❌     │    ❌      │    ❌      │    ❌    │
│ Repository  │    ❌     │    ❌     │    ❌      │    ❌      │    ❌    │
└─────────────┴───────────┴───────────┴────────────┴────────────┴──────────┘

* Action может вызывать SubAction
⚠️ Task обычно не использует Repository напрямую (лучше через UoW)
```

### CQRS: Разделение чтения и записи

```python
# COMMAND (Write) → Action → UoW → Repository → Events
@post("/users")
@result_handler(UserResponse, success_status=201)
async def create_user(action: FromDishka[CreateUserAction]):
    return await action.run(data)  # Через UoW + Events

# QUERY (Read) → Query → прямой доступ к Model
@get("/users")
async def list_users(query: FromDishka[ListUsersQuery]):
    result = await query.execute(params)  # Напрямую, без UoW
    return UserListResponse(...)
```

### Правила импортов

```python
# ✅ Container может импортировать из Ship
from src.Ship.Parents.Action import Action
from src.Ship.Core.Errors import BaseError

# ✅ Container импортирует из того же Container (абсолютные пути!)
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork

# ❌ Container НЕ может импортировать из другого Container
from src.Containers.AppSection.OrderModule.Actions import CreateOrderAction  # ЗАПРЕЩЕНО!

# ✅ Для межмодульного общения — Events через litestar.events
# События публикуются из UoW после commit
self.uow.add_event(UserCreated(user_id=user.id))
await self.uow.commit()  # Здесь events уходят в litestar.events
```

---

## 🌐 Межмодульное взаимодействие

### Через Domain Events (UoW + litestar.events)

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   Container A    │      │     UoW          │      │   Listeners      │
│   CreateOrder    │      │                  │      │                  │
│                  │      │ add_event(       │      │ @listener(       │
│ uow.add_event(   │ ──▶  │   OrderCreated)  │ ──▶  │   "OrderCreated")│
│   OrderCreated)  │      │                  │      │ async def on_... │
│ uow.commit()     │      │ commit() →       │      │                  │
│                  │      │   app.emit(...)  │      │                  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                  │
                                  ▼
                          ┌──────────────────┐
                          │  Container B     │
                          │  Listener        │
                          │  updates stats   │
                          └──────────────────┘
```

### Реальный пример

```python
# Container A: UserModule публикует событие
# src/Containers/AppSection/UserModule/Actions/CreateUserAction.py
async with self.uow:
    user = AppUser(...)
    await self.uow.users.add(user)
    self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
    await self.uow.commit()  # Event публикуется здесь

# Container B (или тот же): Listener обрабатывает
# src/Containers/AppSection/UserModule/Listeners.py
@listener("UserCreated")
async def on_user_created(user_id: str, email: str, app: Litestar | None = None, **kwargs):
    logfire.info("🎉 User created", user_id=user_id, email=email)
    
    # Publish to WebSocket channel
    if app:
        channels = app.plugins.get(ChannelsPlugin)
        if channels:
            channels.publish({"event": "user_created", "user_id": user_id}, 
                           channels=[f"user:{user_id}"])
```

---

## 📊 Сравнение с классическим Porto

| Аспект | Porto (PHP) | Hyper-Porto (Python) |
|--------|-------------|---------------------|
| Типы возврата | Mixed / Exceptions | `Result[T, E]` |
| Ошибки | Exceptions | Pattern Matching + Pydantic |
| Async | - | anyio TaskGroups |
| Композиция | Императивная | `flow`, `bind`, `pipe` |
| Валидация | Validators | Pydantic + @result_handler |
| DI | Laravel Container | Dishka (scoped) |
| Events | Laravel Events | litestar.events + UoW |
| Трассировка | Manual | Logfire auto-instrumentation |
| HTTP Errors | Manual | Problem Details (RFC 9457) |

---

## 🔐 Изоляция данных

### Каждый Container владеет своими данными

```sql
-- UserModule владеет:
app_users

-- OrderModule владеет:
orders
order_items

-- Кросс-модульные данные через Events или Read Models
```

### Database Transactions через UoW

```python
async with self.uow:
    # Все операции в одной транзакции
    user = AppUser(...)
    await self.uow.users.add(user)
    
    # События публикуются ТОЛЬКО после успешного commit
    self.uow.add_event(UserCreated(...))
    
    await self.uow.commit()
    # Транзакция завершена + события отправлены
```

---

## 📝 Чеклист нового Container

```markdown
## Создание Container: {ModuleName}

- [ ] Создать структуру папок
- [ ] Определить Models (Piccolo Tables)
- [ ] Создать PiccoloApp.py для миграций
- [ ] Определить Errors.py (Pydantic frozen)
- [ ] Определить Events.py (DomainEvent subclasses)
- [ ] Создать Schemas (Request/Response DTOs)
- [ ] Создать Repository
- [ ] Создать UnitOfWork (наследник BaseUnitOfWork)
- [ ] Создать Tasks (атомарные операции)
- [ ] Создать Queries (CQRS read)
- [ ] Создать Actions (use cases)
- [ ] Создать Controllers (API endpoints)
- [ ] Создать Listeners (event handlers)
- [ ] Зарегистрировать в Providers.py
- [ ] Добавить в get_all_providers()
- [ ] Добавить роутер в App.py
- [ ] Написать тесты
```

---

<div align="center">

**Следующий раздел:** [02-project-structure.md](02-project-structure.md) — Полная структура проекта

</div>
