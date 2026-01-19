# 🔗 Кросс-модульное взаимодействие

> **Версия:** 4.2 | **Дата:** Январь 2026

---

## 📋 Содержание

1. [Принципы Porto](#принципы-porto)
2. [Event-Driven архитектура](#event-driven-архитектура)
3. [Ship Layer для общего кода](#ship-layer-для-общего-кода)
4. [Аудит система (@audited)](#аудит-система-audited)
5. [Примеры интеграций](#примеры-интеграций)

---

## 🏗️ Принципы Porto

Согласно Porto SAP, взаимодействие между контейнерами регулируется:

### Внутри секции (AppSection)

```
✅ Контейнеры могут зависеть друг от друга напрямую
✅ Actions могут вызывать Tasks из других контейнеров
✅ Models могут иметь relationships
```

### Между секциями (AppSection ↔ VendorSection)

```
✅ Event-driven коммуникация
❌ Прямые импорты запрещены
✅ Через Ship Layer абстракции
```

### Ship Layer

```
✅ Общие базовые классы (Parents/)
✅ Общие декораторы (Decorators/)
✅ Общие события (Events/)
✅ Общие интерфейсы (Core/Protocols.py)
```

---

## 📡 Event-Driven архитектура

### Поток событий

```
┌─────────────────────────────────────────────────────────────────┐
│                        Container A                               │
│   Action → UnitOfWork.add_event(Event) → UnitOfWork.commit()   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ emit() через Litestar Events
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Litestar Event Bus                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ @listener("EventName")
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Container B Listener                         │
│                   (слушает события Container A)                  │
└─────────────────────────────────────────────────────────────────┘
```

### Пример: UserModule → SearchModule

```python
# UserModule/Events.py
class UserCreated(DomainEvent):
    user_id: UUID
    email: str
    name: str

# UserModule/Actions/CreateUserAction.py
async with self.uow:
    await self.uow.users.add(user)
    self.uow.add_event(UserCreated(
        user_id=user.id,
        email=user.email,
        name=user.name,
    ))
    await self.uow.commit()

# SearchModule/Listeners.py
@listener("UserCreated")
async def on_user_created_index(
    user_id: str,
    email: str,
    name: str,
    **kwargs,
) -> None:
    task = IndexEntityTask()
    await task.run(IndexableEntity(
        entity_type="User",
        entity_id=user_id,
        title=name,
        content=f"{name} ({email})",
    ))
```

---

## 🚢 Ship Layer для общего кода

### Структура Ship Events

```
Ship/
├── Events/
│   ├── __init__.py
│   └── ActionEvents.py    # ActionExecuted event
├── Decorators/
│   ├── __init__.py
│   ├── audited.py         # @audited decorator
│   └── result_handler.py  # @result_handler
└── Parents/
    └── Event.py           # DomainEvent base
```

### Ship-level события

```python
# Ship/Events/ActionEvents.py
class ActionExecuted(DomainEvent):
    """Публикуется при выполнении @audited Action."""
    
    action_name: str
    entity_type: str | None = None
    entity_id: str | None = None
    actor_id: UUID | None = None
    status: str = "success"
    input_data: dict | None = None
    duration_ms: float | None = None
```

---

## 📝 Аудит система (@audited)

### Проблема

Если `AuditModule` содержит декоратор, а `UserModule` его импортирует:

```python
# ❌ НАРУШЕНИЕ: прямой импорт из другого Container
from src.Containers.AppSection.AuditModule.Decorators import audited
```

### Решение: Ship Layer + Event-Driven

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ship Layer                                │
│   Ship/Decorators/audited.py  →  Ship/Events/ActionExecuted     │
└─────────────────────────────────────────────────────────────────┘
                                          │
                                          │ emit() через UoW
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Containers Layer                             │
│                                                                  │
│  UserModule/              AuditModule/                          │
│  @audited("create")  →    Listeners.py                          │
│                           on_action_executed() → AuditLog       │
└─────────────────────────────────────────────────────────────────┘
```

### Использование

```python
# ✅ ПРАВИЛЬНО: импорт из Ship Layer
from src.Ship.Decorators import audited

@audited(action="create", entity_type="User")
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    
    def __init__(self, hash_password: HashPasswordTask, uow: UserUnitOfWork):
        self.hash_password = hash_password
        self.uow = uow
    
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        # ... бизнес-логика ...
        return Success(user)
```

### Параметры @audited

| Параметр | Тип | Описание |
|----------|-----|----------|
| `action` | `str` | Имя действия ("create", "update", "delete") |
| `entity_type` | `str \| None` | Тип сущности ("User", "Payment") |
| `capture_input` | `bool` | Логировать входные данные (default: True) |
| `capture_output` | `bool` | Логировать выходные данные (default: False) |

### Автоматическая редакция

Чувствительные поля автоматически редактируются:

```python
SENSITIVE_FIELDS = {
    "password", "secret", "token", "api_key",
    "access_token", "refresh_token", "private_key",
    "credit_card", "cvv", "ssn", "pin",
}
```

Результат в AuditLog:

```json
{
  "action": "create_success",
  "entity_type": "User",
  "new_values": {
    "email": "user@example.com",
    "password": "***REDACTED***",
    "name": "John Doe"
  }
}
```

---

## 🔗 Примеры интеграций

### NotificationModule → WebSocket

```python
# NotificationModule/Listeners.py
@listener("NotificationCreated")
async def on_notification_created(
    notification_id: str,
    user_id: str,
    app: Litestar | None = None,
    **kwargs,
) -> None:
    # Публикация в WebSocket канал
    channels = app.plugins.get(ChannelsPlugin)
    channels.publish(
        {"event": "notification_created", "id": notification_id},
        channels=[f"user:{user_id}"],
    )
```

### PaymentModule → WebhookModule

```python
# WebhookModule/Listeners.py
@listener("PaymentCreated")
async def on_payment_created_webhook(
    payment_id: str,
    amount: float,
    **kwargs,
) -> None:
    await _dispatch_to_webhooks("payment.created", {
        "payment_id": payment_id,
        "amount": amount,
    })
```

### UserModule → SearchModule

```python
# SearchModule/Listeners.py
@listener("UserCreated")
async def on_user_created_index(
    user_id: str,
    email: str,
    name: str,
    **kwargs,
) -> None:
    task = IndexEntityTask()
    await task.run(IndexableEntity(
        entity_type="User",
        entity_id=user_id,
        title=name,
        content=f"{name} ({email})",
    ))
```

---

## ✅ Чеклист кросс-модульной интеграции

```markdown
- [ ] Используется Ship Layer для общего кода
- [ ] Нет прямых импортов между секциями
- [ ] События определены как DomainEvent (Pydantic frozen)
- [ ] Listeners принимают **kwargs для совместимости
- [ ] Listeners зарегистрированы в App.py
- [ ] Чувствительные данные редактируются
- [ ] Ошибки в listeners не ломают основной поток
```

---

## 📚 Связанная документация

- [03-components.md](03-components.md) — Компоненты архитектуры
- [11-litestar-features.md](11-litestar-features.md) — Litestar Events
- [Porto Containers Dependencies](../foxdocs/Porto-master/docs/docs/Basics/Containers%20Dependencies.md)

---

<div align="center">

**Hyper-Porto v4.2**

*Event-Driven кросс-модульное взаимодействие*

</div>


