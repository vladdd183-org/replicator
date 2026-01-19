# 🎮 Command: /add-event

> Создание Domain Event и Listener.

---

## Синтаксис

```
/add-event <EventName> [в <Module>] [с listener <ListenerName>]
```

## Параметры

| Параметр | Обязательный | Пример |
|----------|--------------|--------|
| EventName | ✅ | `UserCreated`, `OrderPaid`, `PaymentFailed` |
| Module | ❌ | `UserModule` |
| ListenerName | ❌ | `SendWelcomeEmail` |

---

## Ключевые правила

| Правило | Описание |
|---------|----------|
| **Event** | Pydantic frozen model в `Events.py` |
| **Listener** | Async функция в `Listeners.py` |
| **Publishing** | Через `uow.add_event()` перед commit |
| **Cross-module** | События — ЕДИНСТВЕННЫЙ способ коммуникации между Containers |
| **Registration** | В `App.py` через Litestar events |

---

## Примеры

### Базовый
```
/add-event UserCreated в UserModule
```
→ Создаст `UserCreated` event

### С listener
```
/add-event OrderPaid в OrderModule с listener NotifyWarehouse
```
→ Создаст Event + Listener

---

## Что создаётся

### 1. Event в Events.py

```python
"""Domain events for UserModule."""

from datetime import datetime, timezone
from uuid import UUID

from src.Ship.Parents.Event import DomainEvent


class UserCreated(DomainEvent):
    """Emitted when a new user is created.
    
    Listeners:
    - on_user_created_send_welcome_email: Sends welcome email
    - on_user_created_notify_admin: Notifies admin channel
    - on_user_created_init_settings: Creates default user settings
    """
    user_id: UUID
    email: str
    name: str


class UserUpdated(DomainEvent):
    """Emitted when user profile is updated."""
    user_id: UUID
    updated_fields: list[str]


class UserDeleted(DomainEvent):
    """Emitted when user is deleted."""
    user_id: UUID
    email: str
```

### 2. Listeners в Listeners.py

```python
"""Event listeners for UserModule."""

from src.Containers.AppSection.UserModule.Events import UserCreated, UserDeleted
from src.Containers.VendorSection.EmailModule.Tasks.SendEmailTask import SendEmailTask


async def on_user_created_send_welcome_email(
    event: UserCreated,
    send_email: SendEmailTask,
) -> None:
    """Send welcome email to new user."""
    await send_email.run(EmailPayload(
        to=event.email,
        subject="Welcome to Our App!",
        body=f"Hello {event.name}, welcome aboard!",
    ))


async def on_user_created_notify_admin(event: UserCreated) -> None:
    """Notify admin channel about new user."""
    # Publish to admin channel
    pass


async def on_user_deleted_cleanup(event: UserDeleted) -> None:
    """Cleanup user-related data after deletion."""
    # Remove user sessions, cache, etc.
    pass
```

### 3. Cross-module Event (OrderModule → NotificationModule)

**В OrderModule/Events.py:**

```python
"""Domain events for OrderModule."""

from decimal import Decimal
from uuid import UUID

from src.Ship.Parents.Event import DomainEvent


class OrderCreated(DomainEvent):
    """Emitted when a new order is placed.
    
    Cross-module listeners:
    - NotificationModule: Sends order confirmation
    - PaymentModule: Initiates payment processing
    - InventoryModule: Reserves stock
    """
    order_id: UUID
    user_id: UUID
    total_amount: Decimal
    items_count: int


class OrderPaid(DomainEvent):
    """Emitted when order payment is confirmed."""
    order_id: UUID
    payment_id: UUID
    amount: Decimal
```

**В NotificationModule/Listeners.py:**

```python
"""Listeners for events from other modules."""

from src.Containers.AppSection.OrderModule.Events import OrderCreated, OrderPaid


async def on_order_created_send_confirmation(event: OrderCreated) -> None:
    """Send order confirmation notification."""
    # Send push notification / email
    pass


async def on_order_paid_send_receipt(event: OrderPaid) -> None:
    """Send payment receipt."""
    pass
```

---

## Публикация Event в Action

```python
from returns.result import Result, Success

from src.Containers.AppSection.UserModule.Events import UserCreated


class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        user = AppUser(email=data.email, name=data.name, ...)
        
        async with self.uow:
            await self.uow.users.add(user)
            
            # Add event BEFORE commit
            self.uow.add_event(UserCreated(
                user_id=user.id,
                email=user.email,
                name=user.name,
            ))
            
            # Events are emitted AFTER successful commit
            await self.uow.commit()
        
        return Success(user)
```

---

## Регистрация Listeners в App.py

```python
# In App.py
from litestar import Litestar
from litestar.events import listener

from src.Containers.AppSection.UserModule.Events import UserCreated, UserDeleted
from src.Containers.AppSection.UserModule.Listeners import (
    on_user_created_send_welcome_email,
    on_user_created_notify_admin,
    on_user_deleted_cleanup,
)


# Register listeners
listeners = [
    listener(UserCreated)(on_user_created_send_welcome_email),
    listener(UserCreated)(on_user_created_notify_admin),
    listener(UserDeleted)(on_user_deleted_cleanup),
]

app = Litestar(
    ...,
    listeners=listeners,
)
```

**Или с декоратором:**

```python
# In Listeners.py
from litestar.events import listener
from src.Containers.AppSection.UserModule.Events import UserCreated


@listener(UserCreated)
async def on_user_created_send_welcome_email(event: UserCreated) -> None:
    """Send welcome email to new user."""
    pass
```

---

## DomainEvent базовый класс

```python
# In Ship/Parents/Event.py
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events."""
    
    model_config = {"frozen": True}
    
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def event_name(self) -> str:
        return self.__class__.__name__
```

---

## Cross-Module Communication

**ВАЖНО:** Containers НИКОГДА не импортируют друг друга напрямую!

```
❌ НЕПРАВИЛЬНО:
UserModule импортирует OrderModule напрямую

✅ ПРАВИЛЬНО:
OrderModule emits OrderCreated event
UserModule listens to OrderCreated event
```

**Поток:**

```
1. OrderModule.CreateOrderAction runs
2. UoW commits → emits OrderCreated
3. NotificationModule.on_order_created listener receives event
4. NotificationModule sends notification (без прямого импорта)
```

---

## Именование

### Events

| Действие | Паттерн | Пример |
|----------|---------|--------|
| Created | `{Entity}Created` | `UserCreated` |
| Updated | `{Entity}Updated` | `UserUpdated` |
| Deleted | `{Entity}Deleted` | `UserDeleted` |
| Status change | `{Entity}{NewStatus}` | `OrderPaid`, `OrderShipped` |
| Custom action | `{Entity}{PastVerb}` | `UserActivated`, `UserBanned` |

### Listeners

| Паттерн | Пример |
|---------|--------|
| `on_{event_snake_case}_{action}` | `on_user_created_send_welcome_email` |
| `on_{event_snake_case}_{target}` | `on_order_paid_notify_warehouse` |

---

## Действия после создания

1. ✅ Создать event class в `Events.py`
2. ✅ Унаследовать от `DomainEvent`
3. ✅ Добавить context fields (IDs, data)
4. ✅ Добавить docstring со списком Listeners
5. ✅ Создать listener(s) в `Listeners.py`
6. ✅ Зарегистрировать listeners в `App.py`
7. ✅ Публиковать через `uow.add_event()` в Action

---

## Типичные ошибки

| ❌ Неправильно | ✅ Правильно |
|----------------|-------------|
| Прямой импорт между модулями | Через events для cross-module |
| `emit()` до commit | `add_event()` до, emit после commit |
| Mutable event data | Events frozen (immutable) |
| Бизнес-логика в listener | Сложная логика в Actions |
| Sync listeners | Listeners должны быть async |

---

## Связанные ресурсы

- **Template:** `../templates/event.py.template`
- **Workflow:** `../workflows/add-domain-event.md`
- **Docs:** `docs/11-litestar-features.md`
