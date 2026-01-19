# 🚫 Anti-patterns: Common Mistakes

> Топ ошибок в Hyper-Porto и как их исправить.

---

## 1. ❌ Exceptions вместо Result

### Плохо
```python
async def run(self, data) -> User:
    user = await self.repo.get(data.user_id)
    if not user:
        raise UserNotFoundException()  # ❌ Exception!
    return user
```

### Хорошо
```python
async def run(self, data) -> Result[User, UserError]:
    user = await self.uow.users.get(data.user_id)
    if not user:
        return Failure(UserNotFoundError(user_id=data.user_id))  # ✅ Result
    return Success(user)
```

---

## 2. ❌ Относительные импорты

### Плохо
```python
from ....Actions.CreateUserAction import CreateUserAction  # ❌
from ...Errors import UserNotFoundError  # ❌
```

### Хорошо
```python
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction  # ✅
from src.Containers.AppSection.UserModule.Errors import UserNotFoundError  # ✅
```

---

## 3. ❌ Импорт между Containers

### Плохо
```python
# В UserModule импортируем из OrderModule
from src.Containers.AppSection.OrderModule.Actions import CreateOrderAction  # ❌
```

### Хорошо
```python
# Используем Events для межмодульного общения
self.uow.add_event(UserCreated(user_id=user.id))  # ✅

# OrderModule слушает UserCreated через Listener
```

---

## 4. ❌ dataclass для DTO

### Плохо
```python
from dataclasses import dataclass

@dataclass  # ❌ Нет валидации!
class CreateUserRequest:
    email: str
    name: str
```

### Хорошо
```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):  # ✅ Валидация из коробки
    email: EmailStr
    name: str = Field(..., min_length=2)
```

---

## 5. ❌ Action без Result типа

### Плохо
```python
class CreateUserAction(Action[CreateUserRequest, User, UserError]):
    async def run(self, data) -> User:  # ❌ Должен быть Result!
        ...
```

### Хорошо
```python
class CreateUserAction(Action[CreateUserRequest, User, UserError]):
    async def run(self, data) -> Result[User, UserError]:  # ✅
        ...
```

---

## 6. ❌ Бизнес-логика в Controller

### Плохо
```python
@post("/users")
async def create_user(self, data: CreateUserRequest, repo: FromDishka[UserRepository]):
    # ❌ Бизнес-логика в Controller!
    existing = await repo.find_by_email(data.email)
    if existing:
        return Response(status_code=409)
    
    user = User(email=data.email)
    await repo.add(user)
    return UserResponse.from_entity(user)
```

### Хорошо
```python
@post("/users")
@result_handler(UserResponse, success_status=HTTP_201_CREATED)
async def create_user(self, data: CreateUserRequest, action: FromDishka[CreateUserAction]):
    return await action.run(data)  # ✅ Логика в Action
```

---

## 7. ❌ fire-and-forget tasks

### Плохо
```python
import asyncio

async def run(self, data):
    asyncio.create_task(send_email(data.email))  # ❌ Fire-and-forget!
    return Success(user)
```

### Хорошо
```python
import anyio

async def run(self, data):
    async with anyio.create_task_group() as tg:  # ✅ Structured concurrency
        tg.start_soon(send_email, data.email)
    return Success(user)

# Или через Events
self.uow.add_event(WelcomeEmailRequested(user_id=user.id))  # ✅
```

---

## 8. ❌ Service Locator

### Плохо
```python
async def run(self, data):
    action = container.resolve(CreateUserAction)  # ❌ Service Locator!
    return await action.run(data)
```

### Хорошо
```python
def __init__(self, action: CreateUserAction):  # ✅ Constructor injection
    self.action = action
```

---

## 9. ❌ События публикуются до commit

### Плохо
```python
async with self.uow:
    await self.uow.users.add(user)
    await app.emit("UserCreated", user_id=user.id)  # ❌ До commit!
    await self.uow.commit()
```

### Хорошо
```python
async with self.uow:
    await self.uow.users.add(user)
    self.uow.add_event(UserCreated(user_id=user.id))  # ✅ Добавляем в очередь
    await self.uow.commit()  # ✅ Событие уходит ПОСЛЕ commit
```

---

## 10. ❌ Забыл FromDishka

### Плохо
```python
async def create_user(self, action: CreateUserAction):  # ❌ Не будет инъектирован!
    ...
```

### Хорошо
```python
async def create_user(self, action: FromDishka[CreateUserAction]):  # ✅
    ...
```

---

## 📊 Сводка

| ❌ Ошибка | ✅ Решение |
|----------|-----------|
| `raise Exception` | `return Failure(Error)` |
| `from ....` | `from src.Containers...` |
| Import между Containers | Events |
| `@dataclass` для DTO | `pydantic.BaseModel` |
| Action → `T` | Action → `Result[T, E]` |
| Логика в Controller | Логика в Action |
| `asyncio.create_task()` | `anyio.create_task_group()` |
| `container.resolve()` | Constructor injection |
| `app.emit()` до commit | `uow.add_event()` |
| `action: Action` | `action: FromDishka[Action]` |



