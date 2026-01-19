# 🎯 Философия Hyper-Porto Architecture

> **Версия:** 4.1 | **Дата:** Январь 2026  
> **Назначение:** Модульные монолиты, микросервисы, ML-бэкенды  
> **Оптимизировано для:** AI-Driven Development + Human-Friendly Code

---

## 🧠 Ключевая идея

**Hyper-Porto** — это синтез трёх архитектурных парадигм, усиленных функциональным программированием:

| Источник | Что берём | Результат |
|----------|-----------|-----------|
| **Porto** | Структура папок, Container/Ship, Actions/Tasks | Детерминированная навигация |
| **Cosmic Python** | Repository, UoW, Domain Events | Чистота бизнес-логики |
| **Returns** | Result[T, E], Railway-oriented programming | Явная обработка ошибок |
| **anyio** | Structured Concurrency, TaskGroups | Безопасная конкурентность |

---

## 📜 Конституция архитектуры

### Статья I: Спецификация — первична

```
Код — производная спецификации.
Спецификация — источник истины.
Изменение требований = изменение спецификации → регенерация кода.
```

**Следствие:** Используем Spec-Driven Development. Сначала `/speckit.specify`, потом код.

---

### Статья II: Явное лучше неявного (Explicit > Implicit)

```python
# ❌ Неявное — исключения "где-то там"
def create_user(data: dict) -> User:
    user = User(**data)  # может кинуть ValidationError
    db.save(user)        # может кинуть DBError
    return user

# ✅ Явное — Result показывает все возможные исходы (РЕАЛЬНЫЙ КОД)
async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
    # Проверяем, существует ли пользователь
    existing_user = await self.uow.users.find_by_email(data.email)
    if existing_user is not None:
        return Failure(UserAlreadyExistsError(email=data.email))
    
    # Хеширование пароля (offload to thread)
    password_hash = await anyio.to_thread.run_sync(
        self.hash_password.run, data.password
    )
    
    # Создание и сохранение
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

---

### Статья III: Без велосипедов

```
Если библиотека решает проблему — используй библиотеку.
Кастомный код = кастомные баги + кастомная документация.
```

| Проблема | Библиотека | НЕ делай |
|----------|------------|----------|
| Result/Maybe | `returns` | Свой Result класс |
| Async I/O | `anyio` | Чистый asyncio |
| DI | `dishka` | Service Locator |
| Validation | `pydantic` | Ручные проверки |
| DTO (все типы) | `pydantic.BaseModel` | `dataclass` |
| Value Objects | `pydantic` (frozen=True) | `dataclass(frozen=True)` |
| ORM | `piccolo` | Сырые SQL запросы |
| Web | `litestar` | FastAPI обёртки |
| GraphQL | `strawberry` | Graphene, Ariadne |
| CLI | Litestar `CLIPlugin` + Click | Typer |
| Background | `taskiq` | Celery |
| Retry | `tenacity` | Свой @retryable декоратор |
| HTTP Cache | Litestar `ResponseCache` | Свой @cached для endpoints |
| Event Bus | `litestar.events` + UoW | Свой MessageBus / EventBus |
| DTO (Piccolo) | `litestar.contrib.piccolo.PiccoloDTO` | Ручная сериализация |
| Result iterables | `returns.iterables.Fold` | Свой gather_results |

---

### Статья IV: Локальность контекста

```
Весь код фичи — в одной папке.
Открыл папку Container → понял всё о фиче.
```

```
Containers/AppSection/UserModule/
├── Actions/           # Use Cases (CreateUserAction, AuthenticateAction)
├── Tasks/             # Атомарные операции (HashPasswordTask, GenerateTokenTask)
├── Queries/           # CQRS Queries (GetUserQuery, ListUsersQuery)
├── Data/              # Repositories + Schemas + UnitOfWork
│   ├── Repositories/  # UserRepository
│   ├── Schemas/       # Request/Response DTOs
│   └── UnitOfWork.py  # UserUnitOfWork
├── Models/            # Domain Models (Piccolo Tables) + Migrations
├── UI/                # Controllers + Routes
│   ├── API/           # HTTP REST Controllers
│   ├── GraphQL/       # Strawberry Resolvers
│   ├── CLI/           # Click Commands
│   ├── WebSocket/     # Litestar Channels Handlers
│   └── Workers/       # TaskIQ Background Tasks
├── Events.py          # Domain Events (UserCreated, UserUpdated)
├── Listeners.py       # Event Listeners
├── Errors.py          # Ошибки модуля (Pydantic frozen)
└── Providers.py       # DI регистрация (Dishka)
```

---

### Статья IV.1: Абсолютные импорты — ВСЕГДА

```
Относительные импорты (from ....) — ЗАПРЕЩЕНЫ.
Абсолютные от корня src/ — ОБЯЗАТЕЛЬНЫ.
```

```python
# ❌ ЗАПРЕЩЕНО — нечитаемо, хрупко, путает AI
from ....Actions.CreateUserAction import CreateUserAction
from ....Data.Schemas.Requests import CreateUserRequest
from ....Errors import UserNotFoundError

# ✅ ОБЯЗАТЕЛЬНО — явно, читаемо, AI-friendly (РЕАЛЬНЫЙ КОД)
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
from src.Containers.AppSection.UserModule.Errors import UserNotFoundError
from src.Containers.AppSection.UserModule.Models.User import AppUser
```

**Причины:**
1. Явность — сразу видно откуда импорт
2. Рефакторинг — легче перемещать файлы
3. AI-friendly — нейросети легче понимают контекст
4. IDE — лучше работает автокомплит

---

### Статья IV.2: Explicit Configuration (Явная регистрация)

```
Никакой магии с автосканированием папок.
Каждый модуль явно экспортирует свои компоненты (Manifest pattern).
Стандартные механизмы библиотек (Router, Provider, AppRegistry) используются явно.
```

```python
# ❌ ПЛОХО — магия, скрывающая зависимости
discover_and_register_everything("src/Containers")

# ✅ ХОРОШО — явная композиция в App.py (РЕАЛЬНЫЙ КОД)
from src.Containers.AppSection.UserModule import user_router
from src.Containers.AppSection.UserModule.Listeners import (
    on_user_created,
    on_user_updated,
    on_user_deleted,
)

app = Litestar(
    route_handlers=[
        user_router,
        GraphQLController,
    ],
    listeners=[
        on_user_created,
        on_user_updated,
        on_user_deleted,
    ],
)

container = make_async_container(*get_all_providers())
setup_dishka(container, app)
```

**Принцип:**
1. Код должен быть доступен для статического анализа (IDE Go to definition)
2. Порядок загрузки должен быть детерминированным
3. Используем стандартные `AppRegistry` (Piccolo), `Router` (Litestar), `Provider` (Dishka)

> 📖 Подробнее: [10-registration.md](10-registration.md)

---

### Статья V: Railway-ориентированное программирование

```
Успех → Success track  
Ошибка → Failure track
Переключение между треками — явное.
```

```python
from returns.result import Result, Success, Failure

# РЕАЛЬНЫЙ КОД: CreateUserAction
async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
    # Step 1: Check if email exists (Failure track if exists)
    existing = await self.uow.users.find_by_email(data.email)
    if existing:
        return Failure(UserAlreadyExistsError(email=data.email))
    
    # Step 2: Hash password
    password_hash = await anyio.to_thread.run_sync(
        self.hash_password.run, data.password
    )
    
    # Step 3: Create and save (Success track)
    async with self.uow:
        user = AppUser(email=data.email, password_hash=password_hash, name=data.name)
        await self.uow.users.add(user)
        self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
        await self.uow.commit()
    
    return Success(user)
```

**Pattern Matching в Controller:**

```python
# РЕАЛЬНЫЙ КОД: UserController с @result_handler
@post("/")
@result_handler(UserResponse, success_status=HTTP_201_CREATED)
async def create_user(
    self,
    data: CreateUserRequest,
    action: FromDishka[CreateUserAction],
) -> Result[AppUser, UserError]:
    return await action.run(data)

# result_handler автоматически делает:
# - Success(user) → Response(UserResponse.from_entity(user), status=201)
# - Failure(error) → DomainException(error) → Problem Details (RFC 9457)
```

---

### Статья VI: Structured Concurrency

```
Никаких "fire and forget" задач.
Все задачи — под контролем TaskGroup.
Ошибка в одной → отмена всех.
```

```python
import anyio

# РЕАЛЬНЫЙ КОД: WebSocket handler с TaskGroup
async def _handle_websocket_session(socket, user_id, channels, query):
    async with channels.start_subscription([f"user:{user_id}"]) as subscriber:
        
        async def handle_commands():
            """Handle incoming commands from client."""
            while True:
                message = await socket.receive_json()
                match message.get("command"):
                    case "refresh":
                        user = await query.execute(GetUserQueryInput(user_id=user_id))
                        await socket.send_json({"event": "user_data", "user": ...})
                    case "ping":
                        await socket.send_json({"event": "pong"})
        
        async def handle_channel_messages():
            """Forward channel messages to WebSocket."""
            async for message in subscriber.iter_events():
                await socket.send_json(_decode_channel_message(message))
        
        # Обе задачи под контролем TaskGroup
        async with anyio.create_task_group() as tg:
            tg.start_soon(handle_commands)
            tg.start_soon(handle_channel_messages)
```

---

### Статья VII: Минимальный бойлерплейт

```
Метапрограммирование > копипаста.
Декораторы + дженерики + протоколы = меньше кода.
```

```python
# ❌ Бойлерплейт в каждом Controller
@post("/users")
async def create_user(data, action):
    result = await action.run(data)
    match result:
        case Success(user):
            return Response(content=UserResponse.from_entity(user), status_code=201)
        case Failure(UserAlreadyExistsError() as e):
            return Response(content={"error": e.message}, status_code=409)
        case Failure(error):
            return Response(content={"error": str(error)}, status_code=400)

# ✅ РЕАЛЬНЫЙ КОД: @result_handler делает всё автоматически
@post("/")
@result_handler(UserResponse, success_status=HTTP_201_CREATED)
async def create_user(
    self,
    data: CreateUserRequest,
    action: FromDishka[CreateUserAction],
) -> Result[AppUser, UserError]:
    return await action.run(data)
```

**Другие примеры сокращения бойлерплейта:**

```python
# EntitySchema — автоматическое from_entity
class UserResponse(EntitySchema):
    id: UUID
    email: str
    name: str
    # from_entity() уже есть из базового класса!

# ErrorWithTemplate — автоматическая генерация message
class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User with id {user_id} not found"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID
    # message генерируется автоматически: "User with id <uuid> not found"

# Dishka provide() — авторезолв зависимостей по type hints
class UserModuleProvider(Provider):
    scope = Scope.REQUEST
    create_user_action = provide(CreateUserAction)  # Dishka сама резолвит зависимости
```

---

### Статья VIII: Pattern Matching везде

```python
# РЕАЛЬНЫЙ КОД: AuthenticateAction
match result:
    case Success(user):
        return Success(AuthResult(tokens=tokens, user_id=str(user.id), email=user.email))
    case Failure(InvalidCredentialsError()):
        return Failure(InvalidCredentialsError())
    case Failure(UserInactiveError(user_id=uid)):
        return Failure(UserInactiveError(user_id=uid))

# РЕАЛЬНЫЙ КОД: GraphQL Resolver
match result:
    case Success(user):
        return CreateUserPayload(user=_user_to_graphql(user))
    case Failure(error):
        return CreateUserPayload(error=UserErrorType(message=error.message, code=error.code))
```

---

### Статья IX: AI-First Design

```
Структура должна быть понятна нейросети с первого взгляда.
Типы > комментарии.
Протоколы > наследование.
```

**Правила для AI:**
1. Все функции типизированы
2. Все DTOs — Pydantic модели с валидацией
3. Все зависимости — через DI (FromDishka)
4. Все ошибки — через Result
5. Именование предсказуемое: `{Verb}{Noun}Action`, `{Noun}Repository`

**РЕАЛЬНЫЕ примеры типизации:**

```python
# Action — полная типизация
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    def __init__(
        self,
        hash_password: HashPasswordTask,
        uow: UserUnitOfWork,
    ) -> None:
        ...
    
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        ...

# Query — полная типизация
class GetUserQuery(Query[GetUserQueryInput, AppUser | None]):
    async def execute(self, input: GetUserQueryInput) -> AppUser | None:
        ...

# Task — полная типизация
class HashPasswordTask(SyncTask[str, str]):
    def run(self, password: str) -> str:
        ...
```

---

## 🎨 Визуализация потока данных

```
┌─────────────────────────────────────────────────────────────┐
│                         REQUEST                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  UI Layer (Controller)                                      │
│  - Парсинг запроса                                          │
│  - Валидация входных данных (Pydantic)                      │
│  - Вызов Action (write) или Query (read)                    │
│  - @result_handler для автоматического преобразования       │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
           ┌───────────────┐    ┌───────────────┐
           │    Action     │    │    Query      │
           │  (Write ops)  │    │  (Read ops)   │
           │  CQRS Command │    │  CQRS Query   │
           └───────────────┘    └───────────────┘
                    │                   │
                    ▼                   │
┌───────────────────────┐               │
│  Tasks                │               │
│  - HashPasswordTask   │               │
│  - VerifyPasswordTask │               │
│  - GenerateTokenTask  │               │
└───────────────────────┘               │
                    │                   │
                    └─────────┬─────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Data Layer (Repository + UoW)                              │
│  - UserRepository (CRUD + domain queries)                   │
│  - UnitOfWork (транзакции + events)                        │
│  - События через Outbox → litestar.events                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Result[T, Error]                                           │
│  - Success → @result_handler → Response                     │
│  - Failure → DomainException → Problem Details (RFC 9457)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Сравнение подходов

| Аспект | Классический Porto | Hyper-Porto v4 |
|--------|-------------------|----------------|
| Обработка ошибок | Exceptions | Result[T, E] |
| Async | asyncio | anyio (structured) |
| Композиция | Императивная | Railway (flow, bind) |
| Типы | Generic | Generic + Protocols |
| DI | Service Locator | Dishka containers |
| Логирование | В каждом методе | Logfire + декораторы |
| Валидация | Вручную | Pydantic + декораторы |
| Ошибки | Строки / Exceptions | Pydantic frozen models |
| HTTP Errors | Manual mapping | http_status на классе + Problem Details |

---

## 🚀 Принципы масштабирования

### От монолита к микросервисам

```
1. Модульный монолит:
   - Containers = границы будущих сервисов
   - События через in-memory bus (litestar.events)
   
2. Distributed monolith:
   - Containers = отдельные процессы
   - События через Redis/Kafka (ChannelsPlugin + Redis backend)
   
3. Микросервисы:
   - Containers = отдельные репозитории
   - Полная изоляция данных
```

### Правило: Если Container может жить отдельно — он готов к выделению.

---

## 📚 Источники вдохновения

| Источник | Вклад |
|----------|-------|
| [Porto SAP](https://github.com/Mahmoudz/Porto) | Структура Container/Ship |
| [Cosmic Python](https://cosmicpython.com) | Repository, UoW, Events |
| [Returns](https://returns.readthedocs.io) | Функциональные контейнеры |
| [anyio](https://anyio.readthedocs.io) | Structured concurrency |
| [Spec Kit](https://github.com/github/spec-kit) | Spec-Driven Development |
| [Litestar](https://litestar.dev) | Современный ASGI фреймворк |
| [Dishka](https://dishka.readthedocs.io) | Dependency Injection |

---

<div align="center">

**Следующий раздел:** [01-architecture.md](01-architecture.md) — Слои, компоненты, потоки данных

</div>

---

<div align="center">

**Hyper-Porto v4.1**

*Функциональная архитектура для Python бэкендов*

🚢 Porto + 🐍 Cosmic + 🦀 Returns + ⚡ anyio = 🚀 Production-Ready

</div>
