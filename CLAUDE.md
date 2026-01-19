# CLAUDE.md — AI Quick Reference for Hyper-Porto

> Компактный справочник для AI-агентов по архитектуре Hyper-Porto v4.3

---

## 🎯 Что это за проект

**Hyper-Porto** — функциональная архитектура для Python бэкендов, объединяющая:
- **Porto** (структура Container/Ship)
- **Cosmic Python** (Repository, UoW, Domain Events)
- **Returns** (Result[T, E], Railway-oriented programming)
- **anyio** (Structured Concurrency)

**Tech Stack:** Litestar, Piccolo ORM, Dishka DI, Strawberry GraphQL, TaskIQ, Temporal, Pydantic, Logfire

---

## 📁 Структура проекта

```
src/
├── App.py                    # Litestar application factory
├── Main.py                   # Entry point (uvicorn)
├── Ship/                     # Общая инфраструктура
│   ├── Auth/                 # JWT, Guards, Middleware
│   ├── CLI/                  # Click + @with_container
│   ├── Configs/Settings.py   # Pydantic BaseSettings
│   ├── Core/                 # BaseSchema, Errors, Protocols
│   ├── Decorators/           # @result_handler, cache_utils
│   ├── GraphQL/              # Schema, Helpers (get_dependency)
│   ├── Infrastructure/       # Cache, Telemetry, Workers
│   ├── Parents/              # Action, Task, Query, Repository, UoW
│   └── Providers/            # Dishka providers
│
└── Containers/AppSection/    # Бизнес-модули
    └── UserModule/           # Пример модуля
        ├── Actions/          # Use Cases (CQRS Commands)
        ├── Tasks/            # Атомарные операции
        ├── Queries/          # CQRS Queries (Read)
        ├── Data/             # Repository, Schemas, UoW
        ├── Models/           # Piccolo Tables + migrations
        ├── UI/               # API/GraphQL/CLI/WebSocket/Workers
        ├── Events.py         # Domain Events
        ├── Listeners.py      # Event handlers
        ├── Errors.py         # Pydantic frozen errors
        └── Providers.py      # Dishka providers
```

---

## 🔑 Ключевые правила

### 1. ИМПОРТЫ — ТОЛЬКО АБСОЛЮТНЫЕ

```python
# ✅ ПРАВИЛЬНО
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Ship.Parents.Action import Action

# ❌ ЗАПРЕЩЕНО
from ....Actions.CreateUserAction import CreateUserAction
```

### 2. Action ВСЕГДА возвращает Result[T, E]

```python
from returns.result import Result, Success, Failure

class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    """Use Case: Create new user."""
    
    def __init__(
        self,
        hash_password: HashPasswordTask,
        uow: UserUnitOfWork,
    ) -> None:
        self.hash_password = hash_password
        self.uow = uow

    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        existing = await self.uow.users.find_by_email(data.email)
        if existing:
            return Failure(UserAlreadyExistsError(email=data.email))
        
        password_hash = await anyio.to_thread.run_sync(
            self.hash_password.run, data.password
        )
        
        async with self.uow:
            user = AppUser(email=data.email, password_hash=password_hash, name=data.name)
            await self.uow.users.add(user)
            self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
            await self.uow.commit()
        
        return Success(user)
```

### 3. Controller с @result_handler

```python
from litestar import Controller, post
from dishka.integrations.litestar import FromDishka
from src.Ship.Decorators.result_handler import result_handler

class UserController(Controller):
    path = "/users"
    
    @post("/")
    @result_handler(UserResponse, success_status=201)
    async def create_user(
        self,
        data: CreateUserRequest,
        action: FromDishka[CreateUserAction],
    ) -> Result[AppUser, UserError]:
        return await action.run(data)
```

### 4. DTO — Pydantic (НЕ dataclass!)

```python
# Request DTO
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)

# Response DTO — наследует EntitySchema
from src.Ship.Core.BaseSchema import EntitySchema

class UserResponse(EntitySchema):
    id: UUID
    email: str
    name: str
    is_active: bool
```

### 5. Ошибки — Pydantic frozen с http_status

```python
from src.Ship.Core.Errors import BaseError, ErrorWithTemplate
from typing import ClassVar

class UserError(BaseError):
    code: str = "USER_ERROR"

class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User with id {user_id} not found"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID
```

### 6. Task для атомарных операций

```python
# Async Task (I/O)
class GenerateTokenTask(Task[GenerateTokenInput, AuthTokens]):
    async def run(self, data: GenerateTokenInput) -> AuthTokens:
        ...

# Sync Task (CPU-bound) — вызывай через anyio.to_thread.run_sync()
class HashPasswordTask(SyncTask[str, str]):
    def run(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
```

### 7. Query для чтения (CQRS)

```python
from dataclasses import dataclass

@dataclass
class GetUserQuery(Query[GetUserQueryInput, AppUser | None]):
    user_repository: UserRepository
    
    async def execute(self, input: GetUserQueryInput) -> AppUser | None:
        return await self.user_repository.get(input.user_id)
```

### 8. UnitOfWork для транзакций + Events

```python
from dataclasses import dataclass, field

@dataclass
class UserUnitOfWork(BaseUnitOfWork):
    users: UserRepository  # Обязательный, инжектируется через DI
    _app: Litestar | None = field(default=None)  # Для Channels

# Использование
async with self.uow:
    await self.uow.users.add(user)
    self.uow.add_event(UserCreated(user_id=user.id))
    await self.uow.commit()  # Events публикуются после commit
```

### 9. DI через Dishka

```python
# Providers.py
from dishka import Provider, Scope, provide

class UserModuleProvider(Provider):
    scope = Scope.APP
    hash_password = provide(HashPasswordTask)

class UserRequestProvider(Provider):
    scope = Scope.REQUEST
    
    @provide
    def user_uow(self, users: UserRepository, request: Request) -> UserUnitOfWork:
        return UserUnitOfWork(users=users, _app=request.app)
```

---

## 🚫 НЕ ДЕЛАЙ ЭТО

| ❌ НЕ делай | ✅ Используй |
|-------------|--------------|
| `from ....` (относительные) | `from src.Containers...` |
| `raise Exception(...)` | `return Failure(Error(...))` |
| `@dataclass` для DTO | `pydantic.BaseModel` |
| Свой Result класс | `returns.result.Result` |
| `asyncio.create_task()` | `anyio.create_task_group()` |
| Service Locator | Dishka DI |
| Свой @cached | `cashews` |
| Свой @retryable | `tenacity` |
| Свой EventBus | `litestar.events` + UoW |

---

## ⚠️ ЗАПРЕЩЁННЫЕ КОМАНДЫ (КРИТИЧЕСКИ ВАЖНО!)

> **Проект использует UV** — НЕ используй pip и НЕ активируй venv вручную!

| ❌ **ЗАПРЕЩЕНО**                     | ✅ **Используй**                       |
|--------------------------------------|----------------------------------------|
| `pip install X`                      | `uv add X`                             |
| `pip install -r requirements.txt`    | `uv sync`                              |
| `pip uninstall X`                    | `uv remove X`                          |
| `pip freeze > requirements.txt`      | `uv lock` (автоматически)              |
| `python script.py`                   | `uv run python script.py`              |
| `python3 script.py`                  | `uv run python script.py`              |
| `python -m pytest`                   | `uv run pytest`                        |
| `pytest`                             | `uv run pytest`                        |
| `source .venv/bin/activate`          | **Не нужно!** UV активирует сам        |
| `. .venv/bin/activate`               | **Не нужно!** UV активирует сам        |

---

## 🛠️ Команды проекта (Quick Reference)

### UV Package Management

```bash
uv add package-name           # Добавить зависимость
uv add --dev pytest          # Dev зависимость  
uv remove package-name       # Удалить
uv sync                      # Синхронизировать окружение
uv lock                      # Обновить lock файл
```

### Запуск Python

```bash
uv run python script.py      # Скрипт
uv run python -m module      # Модуль
uv run pytest               # Тесты
```

### Porto CLI Generator

```bash
uv run porto make:module Blog                    # Новый модуль
uv run porto make:action CreatePost --module=Blog
uv run porto make:task SendEmail --module=Notification
uv run porto make:query GetPost --module=Blog
uv run porto make:event PostPublished --module=Blog
```

### Piccolo Migrations

```bash
uv run piccolo migrations new ModuleName --auto  # Создать
uv run piccolo migrations forwards all          # Применить
```

### Сервер

```bash
uv run python -m src.Main                    # Запуск
uv run uvicorn src.App:create_app --reload  # Hot reload
```

> 📚 Полный справочник: `agent-os/standards/tooling/commands.md`

---

## 📋 Именование

| Компонент | Паттерн | Пример |
|-----------|---------|--------|
| Action | `{Verb}{Noun}Action` | `CreateUserAction` |
| Task | `{Verb}{Noun}Task` | `HashPasswordTask` |
| Query | `{Verb/Get}{Noun}Query` | `GetUserQuery` |
| Repository | `{Noun}Repository` | `UserRepository` |
| Controller | `{Noun}Controller` | `UserController` |
| Error | `{Noun}Error` | `UserNotFoundError` |
| Event | `{Noun}{PastVerb}` | `UserCreated` |
| Request DTO | `{Action}Request` | `CreateUserRequest` |
| Response DTO | `{Noun}Response` | `UserResponse` |

---

## 🔗 Зависимости компонентов

```
Controller → Action, Query
Action → Task, Repository, UoW
Task → (stateless, можно Repository)
Query → Repository (напрямую, без UoW)
Repository → Model (Piccolo Table)
```

**Container НЕ импортирует другой Container** — только через Events!

---

## 📚 Документация

| Нужно понять | Читай документ |
|--------------|----------------|
| Философия и принципы | `docs/00-philosophy.md` |
| Архитектура слоёв | `docs/01-architecture.md` |
| Структура папок | `docs/02-project-structure.md` |
| Компоненты детально | `docs/03-components.md` |
| Result и Railway | `docs/04-result-railway.md` |
| Async и TaskGroups | `docs/05-concurrency.md` |
| Библиотеки | `docs/08-libraries.md` |
| HTTP/GraphQL/CLI/WS | `docs/09-transports.md` |
| Litestar features | `docs/11-litestar-features.md` |
| Сокращение бойлерплейта | `docs/12-reducing-boilerplate.md` |
| Module Gateway Pattern | `docs/14-module-gateway-pattern.md` |
| Вынос в микросервис | `docs/16-microservice-extraction-guide.md` |
| Вынос в микросервис | `docs/17-microservice-extraction-guide.md` |
| Saga Patterns | `docs/15-saga-patterns.md` |

---

## 🛠️ Быстрый старт: новый Action

```python
# 1. Создай Action в Actions/
class DoSomethingAction(Action[DoSomethingRequest, SomeResult, SomeError]):
    """Use Case: Do something."""
    
    def __init__(
        self,
        some_task: SomeTask,
        uow: SomeUnitOfWork,
    ) -> None:
        self.some_task = some_task
        self.uow = uow

    async def run(self, data: DoSomethingRequest) -> Result[SomeResult, SomeError]:
        # Логика
        return Success(result)

# 2. Зарегистрируй в Providers.py
class ModuleRequestProvider(Provider):
    scope = Scope.REQUEST
    do_something_action = provide(DoSomethingAction)

# 3. Добавь endpoint в Controller
@post("/something")
@result_handler(SomeResponse, success_status=201)
async def do_something(
    self,
    data: DoSomethingRequest,
    action: FromDishka[DoSomethingAction],
) -> Result[SomeResult, SomeError]:
    return await action.run(data)
```

---

## 🔍 Полезные helpers

```python
# Result → Response (HTTP)
from src.Ship.Decorators.result_handler import result_handler

# Entity → DTO
from src.Ship.Core.BaseSchema import EntitySchema

# GraphQL DI
from src.Ship.GraphQL.Helpers import get_dependency, get_container_context

# CLI с DI
from src.Ship.CLI.Decorators import with_container, handle_cli_result

# Ошибки с шаблоном message
from src.Ship.Core.Errors import ErrorWithTemplate

# Temporal Saga (для распределённых транзакций)
# См. docs/15-saga-patterns.md
```

---

**Hyper-Porto v4.3** — Функциональная архитектура для Python бэкендов 🚀



