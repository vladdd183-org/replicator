# Coding Style — Hyper-Porto

> Стандарты стиля кода для Hyper-Porto проектов.

---

## 📏 Formatting

| Правило | Значение |
|---------|----------|
| Line length | 100 символов |
| Indentation | 4 пробела |
| Quotes | Double quotes `"..."` |
| Trailing commas | Да |
| Target Python | 3.12+ |

### Инструменты

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4", "SIM", "RUF"]
```

---

## 📐 Naming Conventions

### Classes

| Тип | Паттерн | Пример |
|-----|---------|--------|
| Action | `{Verb}{Noun}Action` | `CreateUserAction` |
| Task | `{Verb}{Noun}Task` | `HashPasswordTask` |
| Query | `{Verb}{Noun}Query` | `GetUserQuery`, `ListUsersQuery` |
| Repository | `{Noun}Repository` | `UserRepository` |
| Controller | `{Noun}Controller` | `UserController` |
| Error | `{Description}Error` | `UserNotFoundError` |
| Event | `{Noun}{PastVerb}` | `UserCreated`, `OrderCompleted` |
| Request DTO | `{Action}Request` | `CreateUserRequest` |
| Response DTO | `{Noun}Response` | `UserResponse` |
| Provider | `{Module}Provider` | `UserModuleProvider` |

### Functions & Methods

```python
# snake_case для функций и методов
async def create_user(data: CreateUserRequest) -> Result[User, UserError]:
    ...

# Приватные методы с _
async def _validate_email(self, email: str) -> bool:
    ...
```

### Variables

```python
# snake_case для переменных
user_repository = UserRepository()
password_hash = await hash_password.run(password)
```

### Constants

```python
# UPPER_SNAKE_CASE для констант
MAX_RETRIES = 3
DEFAULT_PAGE_SIZE = 20
```

---

## 🔗 Import Rules

### ✅ ТОЛЬКО абсолютные импорты

```python
# Правильно — абсолютные от src/
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Ship.Core.Errors import BaseError
from src.Ship.Parents.Action import Action
```

### ❌ Относительные импорты ЗАПРЕЩЕНЫ

```python
# ЗАПРЕЩЕНО
from ....Actions.CreateUserAction import CreateUserAction
from ...Errors import UserNotFoundError
from ..Data.Schemas import CreateUserRequest
```

### Порядок импортов (ruff auto-sorts)

```python
# 1. Standard library
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar
from uuid import UUID

# 2. Third-party
from dishka import Provider, Scope, provide
from litestar import Controller, get, post
from pydantic import BaseModel, Field
from returns.result import Result, Success, Failure

# 3. Local application (absolute)
from src.Ship.Parents.Action import Action
from src.Containers.AppSection.UserModule.Errors import UserError
```

---

## 📝 Documentation

### Docstrings (Google style)

```python
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    """Use Case: Create a new user.
    
    Steps:
    1. Check if email already exists
    2. Hash password
    3. Create user entity
    4. Save to database
    5. Publish UserCreated event
    
    Example:
        action = CreateUserAction(hash_password, uow)
        result = await action.run(CreateUserRequest(...))
    """
    
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        """Execute the create user use case.
        
        Args:
            data: CreateUserRequest with user data
            
        Returns:
            Result[AppUser, UserError]: Success with created user or Failure
        """
        ...
```

### Type Hints — ОБЯЗАТЕЛЬНЫ

```python
# ✅ Полная типизация
async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
    ...

# ✅ Generic types
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    ...

# ❌ Без типов
async def run(self, data):
    ...
```

---

## 🏗️ Class Structure

```python
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    """Docstring."""
    
    # 1. Class variables
    _cache_ttl: ClassVar[int] = 300
    
    # 2. Constructor
    def __init__(
        self,
        hash_password: HashPasswordTask,
        uow: UserUnitOfWork,
    ) -> None:
        self.hash_password = hash_password
        self.uow = uow
    
    # 3. Public methods
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        ...
    
    # 4. Private methods
    async def _validate_email(self, email: str) -> bool:
        ...
```

---

## 🎯 Best Practices

### Small, Focused Functions

```python
# ✅ Одна функция — одна задача
async def _check_email_exists(self, email: str) -> bool:
    existing = await self.uow.users.find_by_email(email)
    return existing is not None

# ❌ Слишком много в одной функции
async def run(self, data):
    # 100 строк логики...
```

### DRY — Don't Repeat Yourself

```python
# ✅ Переиспользование через Tasks
class HashPasswordTask(SyncTask[str, str]):
    def run(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Используется в CreateUserAction, ChangePasswordAction и т.д.
```

### Remove Dead Code

```python
# ❌ НЕ оставлять закомментированный код
# async def old_implementation(self):
#     ...

# ✅ Удалять неиспользуемый код
```

---

## 🔧 Type Checking

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
plugins = [
    "returns.contrib.mypy.returns_plugin",
    "pydantic.mypy",
]
```

---

## 📚 Дополнительно

- `ruff check --fix` — автоисправление lint ошибок
- `ruff format` — форматирование кода
- `mypy src/` — проверка типов
