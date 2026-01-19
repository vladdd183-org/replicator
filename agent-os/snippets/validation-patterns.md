# 🧩 Snippets: Validation Patterns

> Готовые паттерны валидации с Pydantic.

---

## Request DTO валидация

### Базовые Field constraints
```python
from pydantic import BaseModel, Field, EmailStr

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=18, le=120)
    password: str = Field(..., min_length=8, max_length=128)
    tags: list[str] = Field(default_factory=list, max_length=10)
```

### Опциональные поля (для Update)
```python
class UpdateUserRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    age: int | None = Field(None, ge=18, le=120)
    bio: str | None = Field(None, max_length=500)
```

---

## Custom Validators

### field_validator (одно поле)
```python
from pydantic import BaseModel, field_validator

class CreateUserRequest(BaseModel):
    username: str
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        if v.lower() in ["admin", "root", "system"]:
            raise ValueError("Username is reserved")
        return v.lower()  # Нормализация
```

### model_validator (несколько полей)
```python
from pydantic import BaseModel, model_validator

class DateRangeRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    
    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self
```

---

## Computed Fields

### computed_field
```python
from pydantic import BaseModel, computed_field

class UserResponse(BaseModel):
    first_name: str
    last_name: str
    
    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

---

## Паттерны для конкретных типов

### UUID валидация
```python
from uuid import UUID
from pydantic import BaseModel

class GetUserRequest(BaseModel):
    user_id: UUID  # Автоматическая валидация UUID
```

### Enum валидация
```python
from enum import Enum
from pydantic import BaseModel

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

class CreateUserRequest(BaseModel):
    role: UserRole = UserRole.USER
```

### URL валидация
```python
from pydantic import BaseModel, HttpUrl

class WebhookRequest(BaseModel):
    callback_url: HttpUrl
```

### Regex валидация
```python
from pydantic import BaseModel, Field
from typing import Annotated

PhoneNumber = Annotated[str, Field(pattern=r"^\+?[1-9]\d{10,14}$")]

class ContactRequest(BaseModel):
    phone: PhoneNumber
```

---

## Nested Validation

### Вложенные модели
```python
class AddressRequest(BaseModel):
    street: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    zip_code: str = Field(..., pattern=r"^\d{5,6}$")

class CreateUserRequest(BaseModel):
    name: str
    address: AddressRequest  # Вложенная валидация
```

### Список вложенных моделей
```python
class OrderItemRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(..., ge=1, le=100)

class CreateOrderRequest(BaseModel):
    items: list[OrderItemRequest] = Field(..., min_length=1, max_length=50)
```

---

## Query Parameters

### Pagination
```python
class PaginationParams(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
```

### Фильтры
```python
class UserFilterParams(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    is_active: bool | None = None
    role: UserRole | None = None
    search: str | None = Field(None, min_length=1, max_length=100)
    created_after: datetime | None = None
```

---

## Immutable DTOs (для Query Input)

### frozen=True
```python
from pydantic import BaseModel, ConfigDict

class GetUserQueryInput(BaseModel):
    model_config = ConfigDict(frozen=True)  # Immutable!
    
    user_id: UUID
```

---

## Alias для JSON keys

### Camel case ↔ snake case
```python
from pydantic import BaseModel, Field

class ExternalAPIRequest(BaseModel):
    user_name: str = Field(..., alias="userName")
    created_at: datetime = Field(..., alias="createdAt")
    
    model_config = ConfigDict(populate_by_name=True)
```



