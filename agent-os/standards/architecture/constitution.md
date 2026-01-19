# 📜 Конституция Hyper-Porto — Краткая версия

> Неизменяемые правила архитектуры. Полная версия: [`specs/CONSTITUTION.md`](../../../specs/CONSTITUTION.md)

---

## 🔴 10 Ключевых правил

### 1. Porto Pattern — обязательно
```
src/
├── Ship/        # Общая инфраструктура
└── Containers/  # Бизнес-модули (изолированы друг от друга)
```

### 2. Containers НЕ импортируют друг друга
```python
# ❌ ЗАПРЕЩЕНО
from src.Containers.AppSection.OrderModule.Actions import CreateOrderAction

# ✅ Межмодульное общение — только через Events
self.uow.add_event(UserCreated(user_id=user.id))
```

### 3. Actions ВСЕГДА возвращают `Result[T, E]`
```python
async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
    if error:
        return Failure(UserNotFoundError(user_id=...))
    return Success(user)
```

### 4. Только абсолютные импорты
```python
# ✅ ПРАВИЛЬНО
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction

# ❌ ЗАПРЕЩЕНО
from ....Actions.CreateUserAction import CreateUserAction
```

### 5. Ошибки — Pydantic frozen модели
```python
class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User with id {user_id} not found"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID
```

### 6. Все DTO — Pydantic (НЕ dataclass)
```python
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
```

### 7. DI через Dishka (НЕ Service Locator)
```python
async def create_user(
    action: FromDishka[CreateUserAction],  # ✅
) -> Result[...]:
    ...
```

### 8. Structured Concurrency через anyio
```python
async with anyio.create_task_group() as tg:
    tg.start_soon(task1)
    tg.start_soon(task2)
# Все задачи завершены или отменены
```

### 9. События через UoW + litestar.events
```python
async with self.uow:
    await self.uow.users.add(user)
    self.uow.add_event(UserCreated(...))  # Добавить
    await self.uow.commit()               # Опубликовать
```

### 10. Явная регистрация (никакой магии)
```python
# App.py — явно регистрируем роутеры и listeners
app = Litestar(
    route_handlers=[user_router, order_router],
    listeners=[on_user_created, on_order_created],
)
```

---

## ⚠️ Запрещено

| Что | Почему |
|-----|--------|
| `raise Exception` в бизнес-логике | Используй `return Failure(...)` |
| `@dataclass` для DTO | Используй `pydantic.BaseModel` |
| Относительные импорты `from ....` | Используй абсолютные от `src.` |
| `asyncio.create_task()` | Используй `anyio.create_task_group()` |
| Импорт между Containers | Используй Events |
| Автосканирование папок | Явная регистрация |

---

## 📚 Полная документация

- **Конституция:** [`specs/CONSTITUTION.md`](../../../specs/CONSTITUTION.md) — все 12 статей
- **Философия:** [`docs/00-philosophy.md`](../../../docs/00-philosophy.md) — 9 принципов
- **Архитектура:** [`docs/01-architecture.md`](../../../docs/01-architecture.md) — слои и компоненты



