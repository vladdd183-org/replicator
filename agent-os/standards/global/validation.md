# Validation — Pydantic DTOs

> Стандарты валидации данных через Pydantic модели.

---

## 🎯 Основные принципы

1. **Pydantic для всех DTO** — никаких dataclass
2. **Валидация на границе** — в Request DTOs
3. **Типизация** — все поля типизированы
4. **Field constraints** — min_length, max_length, regex и т.д.

---

## 📋 Request DTOs

### Базовый шаблон

```python
from pydantic import BaseModel, Field, EmailStr, field_validator


class CreateUserRequest(BaseModel):
    """Request DTO for creating a new user.
    
    Attributes:
        email: User's email address (normalized to lowercase)
        password: User's password (min 8 characters)
        name: User's display name
    """
    
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    name: str = Field(..., min_length=2, max_length=100, description="Display name")
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()
```

### Optional Fields

```python
class UpdateUserRequest(BaseModel):
    """Request DTO for updating a user.
    
    All fields are optional — only provided fields will be updated.
    """
    
    name: str | None = Field(None, min_length=2, max_length=100)
    is_active: bool | None = None
```

---

## 📤 Response DTOs

### EntitySchema

```python
from src.Ship.Core.BaseSchema import EntitySchema


class UserResponse(EntitySchema):
    """Response DTO for User entity.
    
    Inherits from_entity() from EntitySchema.
    Uses from_attributes=True for automatic ORM mapping.
    """
    
    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # from_entity() уже есть из базового класса!

# Использование:
user_response = UserResponse.from_entity(user)

# Для списков — вручную:
responses = [UserResponse.from_entity(u) for u in users]
```

### List Response

```python
class UserListResponse(BaseModel):
    """Response DTO for paginated user list."""
    
    users: list[UserResponse]
    total: int
    limit: int
    offset: int
```

---

## 🔧 Common Validators

### Email normalization

```python
@field_validator("email")
@classmethod
def normalize_email(cls, v: str) -> str:
    return v.strip().lower()
```

### Password strength

```python
@field_validator("password")
@classmethod
def validate_password(cls, v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isupper() for c in v):
        raise ValueError("Password must contain uppercase letter")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain digit")
    return v
```

### Slug validation

```python
@field_validator("slug")
@classmethod
def validate_slug(cls, v: str) -> str:
    import re
    if not re.match(r"^[a-z0-9-]+$", v):
        raise ValueError("Slug must contain only lowercase letters, numbers, hyphens")
    return v
```

---

## 📏 Field Constraints

| Constraint | Использование | Пример |
|------------|--------------|--------|
| `min_length` | Строки | `Field(..., min_length=2)` |
| `max_length` | Строки | `Field(..., max_length=100)` |
| `ge` | Числа (>=) | `Field(..., ge=0)` |
| `le` | Числа (<=) | `Field(..., le=100)` |
| `gt` | Числа (>) | `Field(..., gt=0)` |
| `lt` | Числа (<) | `Field(..., lt=1000)` |
| `regex` | Паттерн | `Field(..., pattern=r"^\d{4}$")` |

---

## 🛡️ Error Models (frozen)

```python
from pydantic import BaseModel
from typing import ClassVar


class UserError(BaseModel):
    """Base error for UserModule."""
    model_config = {"frozen": True}  # Immutable!
    
    message: str
    code: str = "USER_ERROR"
    http_status: int = 400


class UserNotFoundError(UserError):
    """Error raised when user is not found."""
    
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID
    
    # Auto-generate message
    @property
    def message(self) -> str:
        return f"User with id {self.user_id} not found"
```

---

## ⚙️ Model Config

### Request DTOs

```python
class CreateUserRequest(BaseModel):
    model_config = {
        "str_strip_whitespace": True,  # Автотрим строк
        "str_min_length": 1,           # Минимум 1 символ
    }
```

### Response DTOs (from ORM)

```python
class UserResponse(BaseModel):
    model_config = {
        "from_attributes": True,  # ORM mode
    }
```

### Errors (immutable)

```python
class UserError(BaseModel):
    model_config = {"frozen": True}
```

---

## 🆚 Pydantic vs dataclass

| Аспект | Pydantic | dataclass |
|--------|----------|-----------|
| Валидация | ✅ Встроенная | ❌ Нет |
| Сериализация | ✅ model_dump() | ❌ Вручную |
| ORM mode | ✅ from_attributes | ❌ Нет |
| JSON Schema | ✅ Автогенерация | ❌ Нет |
| OpenAPI | ✅ Интеграция | ❌ Нет |

### Вердикт: ВСЕГДА используй Pydantic для DTO

---

## ⚠️ Чего НЕ делать

```python
# ❌ dataclass для DTO
@dataclass
class CreateUserRequest:
    email: str
    password: str

# ❌ Dict без типизации
def create_user(data: dict):
    ...

# ❌ Валидация в Action
async def run(self, data):
    if len(data.password) < 8:  # Должно быть в DTO!
        return Failure(...)

# ❌ Optional без None default
name: str | None  # Должно быть: name: str | None = None
```

---

## 📚 Дополнительно

- `src/Ship/Core/BaseSchema.py` — EntitySchema
- `src/Ship/Core/Errors.py` — BaseError, ErrorWithTemplate
- <https://docs.litestar.dev/> — интеграция с Litestar
