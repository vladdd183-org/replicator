# Error Handling — Railway-Oriented Programming

> Обработка ошибок через `Result[T, E]` из библиотеки `returns`. Исключения НЕ используются для бизнес-логики.

---

## 🎯 Основной принцип

```
Успех → Success track  
Ошибка → Failure track
Переключение между треками — ЯВНОЕ.
```

---

## ✅ Result Pattern

### Actions ВСЕГДА возвращают Result

```python
from returns.result import Result, Success, Failure

class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        # Проверка условий → Failure при ошибке
        existing = await self.uow.users.find_by_email(data.email)
        if existing:
            return Failure(UserAlreadyExistsError(email=data.email))
        
        # Успешный путь → Success
        user = AppUser(...)
        return Success(user)
```

### Pattern Matching в Controller

```python
@post("/")
@result_handler(UserResponse, success_status=HTTP_201_CREATED)
async def create_user(
    self,
    data: CreateUserRequest,
    action: FromDishka[CreateUserAction],
) -> Result[AppUser, UserError]:
    return await action.run(data)
```

---

## 📦 Ошибки как Pydantic модели

### BaseError с http_status

```python
from pydantic import BaseModel
from typing import ClassVar

class BaseError(BaseModel):
    """Base error с маппингом на HTTP статус."""
    model_config = {"frozen": True}
    
    message: str
    code: str = "UNKNOWN_ERROR"
    http_status: int = 400  # HTTP статус для API
```

### ErrorWithTemplate — автогенерация message

```python
class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User with id {user_id} not found"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID
    # message генерируется автоматически!
```

---

## 🎨 Правила именования ошибок

| Тип | Паттерн | Пример |
|-----|---------|--------|
| Base | `{Module}Error` | `UserError`, `PaymentError` |
| Not Found | `{Entity}NotFoundError` | `UserNotFoundError` |
| Already Exists | `{Entity}AlreadyExistsError` | `UserAlreadyExistsError` |
| Invalid | `Invalid{What}Error` | `InvalidCredentialsError` |
| Forbidden | `{Entity}{Action}ForbiddenError` | `UserDeleteForbiddenError` |

---

## 🔄 Преобразование Result → HTTP Response

### @result_handler декоратор

```python
from src.Ship.Decorators.result_handler import result_handler

@post("/")
@result_handler(UserResponse, success_status=HTTP_201_CREATED)
async def create_user(...) -> Result[AppUser, UserError]:
    return await action.run(data)

# Success(user) → Response(UserResponse.from_entity(user), status=201)
# Failure(error) → DomainException(error) → Problem Details (RFC 9457)
```

### RFC 9457 Problem Details

```json
{
  "type": "about:blank",
  "title": "User Already Exists",
  "status": 409,
  "detail": "User with email user@example.com already exists",
  "instance": "/api/v1/users",
  "code": "USER_ALREADY_EXISTS"
}
```

---

## ❌ Чего НЕ делать

### НЕ бросать исключения в бизнес-логике

```python
# ❌ ПЛОХО
async def run(self, data):
    if user_exists:
        raise UserAlreadyExistsException()  # Нет!

# ✅ ХОРОШО
async def run(self, data) -> Result[User, UserError]:
    if user_exists:
        return Failure(UserAlreadyExistsError(...))
```

### НЕ использовать try/except для бизнес-ошибок

```python
# ❌ ПЛОХО
try:
    result = await action.run(data)
except UserError as e:
    return Response(...)

# ✅ ХОРОШО
result = await action.run(data)
match result:
    case Success(user): ...
    case Failure(error): ...
```

---

## 📍 Где МОЖНО использовать исключения

1. **Инфраструктурные ошибки** (DB connection failed)
2. **Программные ошибки** (assertion errors, type errors)
3. **DomainException** — обёртка для преобразования Result → HTTP

```python
class DomainException(Exception):
    """Обёртка для BaseError → HTTP Exception."""
    def __init__(self, error: BaseError):
        self.error = error
        super().__init__(error.message)
```

---

## 🔗 Цепочка обработки ошибок

```
Action.run()
    ↓
Result[T, Error]
    ↓
@result_handler
    ↓
Success → Response(DTO, status)
Failure → raise DomainException(error)
    ↓
ProblemDetails exception handler
    ↓
RFC 9457 JSON response
```

---

## 📤 События и UnitOfWork

### Порядок выполнения

```python
async with self.uow:
    await self.uow.users.add(user)
    self.uow.add_event(UserCreated(...))  # 1. Событие добавлено в очередь
    await self.uow.commit()               # 2. Флаг _committed = True
# 3. __aexit__: DB commit → события публикуются через app.emit()
```

### Важно

- `commit()` только ставит флаг `_committed = True`
- Реальный DB commit происходит в `__aexit__`
- События публикуются **ПОСЛЕ** успешного DB commit
- Если исключение — rollback, события НЕ публикуются

---

## 📚 Дополнительно

- `src/Ship/Core/Errors.py` — BaseError, ErrorWithTemplate, DomainException
- `src/Ship/Decorators/result_handler.py` — @result_handler
- `src/Ship/Exceptions/ProblemDetails.py` — RFC 9457 handler
- `docs/04-result-railway.md` — полная документация
