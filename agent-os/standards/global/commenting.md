# Commenting & Documentation — Hyper-Porto

> Стандарты комментирования и документации кода.

---

## 🎯 Основные принципы

1. **Типы > комментарии** — хорошие типы заменяют комментарии
2. **Docstrings** — Google style для публичных API
3. **Комментарии** — только для неочевидного
4. **README** — в каждом модуле (опционально)

---

## 📝 Docstrings (Google Style)

### Классы

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
        result = await action.run(CreateUserRequest(
            email="user@example.com",
            password="password123",
            name="John Doe",
        ))
        
        match result:
            case Success(user):
                print(f"Created user: {user.email}")
            case Failure(error):
                print(f"Error: {error.message}")
    """
```

### Методы

```python
async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
    """Execute the create user use case.
    
    Args:
        data: CreateUserRequest with user data
        
    Returns:
        Result[AppUser, UserError]: Success with created user or Failure with error
        
    Raises:
        Never raises exceptions — all errors returned as Failure
    """
```

### Модули

```python
"""User module request DTOs.

Request DTOs use Pydantic for validation.
All fields are typed and documented.

Example:
    from src.Containers.AppSection.UserModule.Data.Schemas.Requests import (
        CreateUserRequest,
    )
    
    request = CreateUserRequest(
        email="user@example.com",
        password="password123",
        name="John Doe",
    )
"""
```

---

## 📏 Pydantic Field Descriptions

```python
class CreateUserRequest(BaseModel):
    """Request DTO for creating a new user.
    
    Attributes:
        email: User's email address (normalized to lowercase)
        password: User's password (min 8 characters)
        name: User's display name (2-100 characters)
    """
    
    email: EmailStr = Field(description="User's email address")
    password: str = Field(
        ..., 
        min_length=8, 
        description="Password (min 8 characters)"
    )
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        description="Display name"
    )
```

---

## 💬 Inline Comments

### ✅ Когда комментировать

```python
# Step 1: Check if email already exists
existing_user = await self.uow.users.find_by_email(data.email)

# Hash password (offload to thread to avoid blocking event loop)
password_hash = await anyio.to_thread.run_sync(
    self.hash_password.run, data.password
)

# NOTE: events are published AFTER commit
self.uow.add_event(UserCreated(...))

# TODO: Add rate limiting for login attempts
# FIXME: This is a temporary workaround for #123
# HACK: Piccolo doesn't support this natively
```

### ❌ Когда НЕ комментировать

```python
# ❌ Очевидное
user = AppUser(email=data.email)  # Create user  <- Не нужно!

# ❌ Переформулировка кода
if user is None:  # If user is None  <- Не нужно!
    return Failure(...)

# ❌ Закомментированный код
# async def old_implementation():
#     ...
```

---

## 📚 Type Hints как документация

### Хорошие типы = меньше комментариев

```python
# ✅ Типы говорят сами за себя
async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
    ...

# Вместо:
# ❌ async def run(self, data):
#     """
#     Args:
#         data: dict with email, password, name
#     Returns:
#         User object or error dict
#     """
```

### Generic Types

```python
class Action(ABC, Generic[InputT, OutputT, ErrorT]):
    """Base Action class.
    
    Type parameters:
        InputT: Input data type (e.g., CreateUserRequest)
        OutputT: Success output type (e.g., AppUser)
        ErrorT: Error type (e.g., UserError)
    """
```

---

## 🏷️ Comment Tags

| Tag | Использование |
|-----|--------------|
| `TODO:` | Запланированная работа |
| `FIXME:` | Известный баг |
| `HACK:` | Временное решение |
| `NOTE:` | Важная информация |
| `XXX:` | Требует внимания |

---

## 📖 Module Documentation

### __init__.py

```python
"""User module — User management functionality.

This module provides:
- User CRUD operations (Actions)
- User authentication (Actions)
- Password hashing (Tasks)
- User queries (Queries)

Exports:
    user_router: Litestar router with all user endpoints
    
Example:
    from src.Containers.AppSection.UserModule import user_router
    
    app = Litestar(route_handlers=[user_router])
"""

from src.Containers.AppSection.UserModule.UI.API.Routes import user_api_router as user_router

__all__ = ["user_router"]
```

---

## 📊 OpenAPI Documentation

### Автоматическая генерация из типов

```python
class UserController(Controller):
    """HTTP API controller for User operations.
    
    Handles all user-related HTTP endpoints.
    Uses Actions for write operations and Queries for read operations.
    """
    
    path = "/users"
    tags = ["Users"]  # OpenAPI tag
    
    @post("/")
    @result_handler(UserResponse, success_status=HTTP_201_CREATED)
    async def create_user(
        self,
        data: CreateUserRequest,
        action: FromDishka[CreateUserAction],
    ) -> Result[AppUser, UserError]:
        """Create a new user.
        
        Args:
            data: CreateUserRequest with user data
            action: Injected CreateUserAction
            
        Returns:
            Created user as UserResponse (201) or error
        """
        return await action.run(data)
```

---

## ⚠️ Чего НЕ делать

```python
# ❌ Не документировать очевидное
class UserRepository:
    """Repository for User."""  # Слишком очевидно
    
    async def add(self, user: AppUser) -> AppUser:
        """Add user."""  # Слишком очевидно

# ❌ Не оставлять устаревшую документацию
# Docstring говорит одно, код делает другое

# ❌ Не переводить код в комментарии
# Increment counter by one
counter = counter + 1

# ❌ Не писать комментарии на другом языке (если проект на английском)
# Создаем пользователя  <- Должно быть на английском
```

---

## 📚 Дополнительно

- OpenAPI docs: `/api/docs`
- GraphQL Playground: `/graphql`
- Architecture docs: `docs/`
