# Actions & Tasks — Business Logic

> Стандарты для Actions (Use Cases) и Tasks (атомарные операции) в Hyper-Porto.

---

## 🎯 Разделение ответственности

| Компонент | Назначение | Return Type |
|-----------|------------|-------------|
| **Action** | Use Case, оркестрация | `Result[T, Error]` |
| **Task** | Атомарная операция | `T` (plain value) |

---

## 📁 Расположение

```
Containers/{Section}/{Module}/
├── Actions/
│   ├── __init__.py
│   ├── CreateUserAction.py
│   ├── UpdateUserAction.py
│   └── DeleteUserAction.py
│
└── Tasks/
    ├── __init__.py
    ├── HashPasswordTask.py
    ├── VerifyPasswordTask.py
    └── GenerateTokenTask.py
```

---

## 🏗️ Action — Use Case

### Базовый шаблон

```python
from returns.result import Result, Success, Failure
import anyio

from src.Ship.Parents.Action import Action
from src.Ship.Decorators import audited
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import UserError, UserAlreadyExistsError
from src.Containers.AppSection.UserModule.Events import UserCreated
from src.Containers.AppSection.UserModule.Models.User import AppUser
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask


@audited(action="create", entity_type="User")
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    """Use Case: Create a new user.
    
    Steps:
    1. Check if email already exists
    2. Hash password
    3. Create user entity
    4. Save to database
    5. Publish UserCreated event
    """
    
    def __init__(
        self,
        hash_password: HashPasswordTask,
        uow: UserUnitOfWork,
    ) -> None:
        self.hash_password = hash_password
        self.uow = uow
    
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        # Step 1: Validation
        existing_user = await self.uow.users.find_by_email(data.email)
        if existing_user is not None:
            return Failure(UserAlreadyExistsError(email=data.email))
        
        # Step 2: Hash password (CPU-bound → offload to thread)
        password_hash = await anyio.to_thread.run_sync(
            self.hash_password.run, data.password
        )
        
        # Step 3-5: Create, save, publish event
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

## ⚡ Task — Атомарная операция

### Async Task

```python
from dataclasses import dataclass

from src.Ship.Parents.Task import Task


@dataclass
class SendWelcomeEmailTask(Task[str, bool]):
    """Send welcome email to new user."""
    
    email_service: EmailService
    
    async def run(self, email: str) -> bool:
        return await self.email_service.send_template(
            to=email,
            template="welcome",
        )
```

### Sync Task (CPU-bound)

```python
import bcrypt

from src.Ship.Parents.Task import SyncTask
from src.Ship.Configs import get_settings


class HashPasswordTask(SyncTask[str, str]):
    """Hash password using bcrypt.
    
    CPU-bound operation — call via anyio.to_thread.run_sync().
    Bcrypt rounds configured via Settings.bcrypt_rounds.
    """
    
    def __init__(self) -> None:
        settings = get_settings()
        self.rounds = settings.bcrypt_rounds
    
    def run(self, password: str) -> str:
        salt = bcrypt.gensalt(rounds=self.rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
```

### Вызов SyncTask из Action

```python
# Offload CPU-bound task to thread pool
password_hash = await anyio.to_thread.run_sync(
    self.hash_password.run, data.password
)
```

---

## 📏 Naming Conventions

| Компонент | Паттерн | Пример |
|-----------|---------|--------|
| Action class | `{Verb}{Noun}Action` | `CreateUserAction` |
| Task class | `{Verb}{Noun}Task` | `HashPasswordTask` |
| Action method | `run` | `async def run(...)` |
| Task method | `run` | `def run(...)` или `async def run(...)` |

---

## 🔧 Base Classes

### Action[Input, Output, Error]

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from returns.result import Result

class Action(ABC, Generic[InputT, OutputT, ErrorT]):
    @abstractmethod
    async def run(self, data: InputT) -> Result[OutputT, ErrorT]:
        ...
```

### Task[Input, Output]

```python
class Task(ABC, Generic[InputT, OutputT]):
    @abstractmethod
    async def run(self, data: InputT) -> OutputT:
        ...

class SyncTask(ABC, Generic[InputT, OutputT]):
    @abstractmethod
    def run(self, data: InputT) -> OutputT:
        ...
```

---

## 🎨 @audited декоратор

```python
from src.Ship.Decorators import audited

@audited(action="create", entity_type="User")
class CreateUserAction(Action[...]):
    ...
```

Автоматически:
- Логирует начало/конец выполнения
- Публикует `ActionExecuted` event
- Записывает в аудит

---

## 🔗 Правила вызовов

```
Controller → Action (ТОЛЬКО!)
     ↓
Action → Tasks, Repository, UoW, SubActions
     ↓
Task → Repository (опционально, лучше через UoW)
```

### ✅ Разрешено

```python
# Action вызывает Task
password_hash = await anyio.to_thread.run_sync(self.hash_password.run, password)

# Action использует UoW
async with self.uow:
    await self.uow.users.add(user)
    await self.uow.commit()

# Action вызывает SubAction
result = await self.validate_user.run(data)
```

### ❌ Запрещено

```python
# Controller напрямую к Task
@post("/")
async def create_user(self, task: FromDishka[HashPasswordTask]):
    task.run(...)  # Нет!

# Action вызывает другой Action из другого модуля
await self.create_order_action.run(...)  # Используй Events!
```

---

## 📦 UnitOfWork в Action

```python
async with self.uow:
    # 1. Операции с данными
    user = AppUser(...)
    await self.uow.users.add(user)
    
    # 2. Добавление события (публикуется ПОСЛЕ commit)
    self.uow.add_event(UserCreated(user_id=user.id))
    
    # 3. Commit (здесь события уходят)
    await self.uow.commit()
```

---

## ⚠️ Чего НЕ делать

```python
# ❌ Action без Result
async def run(self, data) -> User:  # Должен быть Result[User, Error]
    ...

# ❌ Task с Result (используй Action)
def run(self, data) -> Result[str, Error]:  # Task возвращает plain value
    ...

# ❌ Бизнес-логика в Task
def run(self, data):
    if not user.is_active:  # Бизнес-логика → в Action
        raise UserInactiveError()

# ❌ Action знает о HTTP
async def run(self, data) -> Response:  # Action transport-agnostic
    return Response(...)
```

---

## 📚 Дополнительно

- `src/Ship/Parents/Action.py` — базовый класс Action
- `src/Ship/Parents/Task.py` — базовые классы Task/SyncTask
- `src/Ship/Decorators/audited.py` — @audited декоратор
- `docs/03-components.md` — детальное описание компонентов

