# 📨 Workflow: Add Domain Event

> Пошаговая инструкция добавления нового Domain Event и Listener.

---

## 📋 Входные данные

| Параметр | Пример | Твоё значение |
|----------|--------|---------------|
| Event name | `UserActivated` | _____________ |
| Module | `UserModule` | _____________ |
| Trigger | `ActivateUserAction` | _____________ |

---

## 🚀 Шаги

### Step 1: Создать Event класс

**Файл:** `Events.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.Ship.Parents.Event import DomainEvent


@dataclass
class UserActivated(DomainEvent):
    """Event fired when user is activated.
    
    Published after UoW commit via litestar.events.
    """
    
    user_id: UUID
    activated_by: UUID | None = None
    reason: str | None = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def event_name(self) -> str:
        return "UserActivated"
```

---

### Step 2: Публиковать Event в Action

**Файл:** `Actions/ActivateUserAction.py`

```python
from src.Containers.AppSection.UserModule.Events import UserActivated

async def run(self, user_id: UUID, data: ActivateUserRequest) -> Result[AppUser, UserError]:
    async with self.uow:
        # ... business logic ...
        
        # Добавить событие в очередь
        self.uow.add_event(UserActivated(
            user_id=user.id,
            activated_by=data.activated_by,
            reason=data.reason,
        ))
        
        await self.uow.commit()
    # События публикуются после commit
    
    return Success(user)
```

---

### Step 3: Создать Listener

**Файл:** `Listeners.py`

```python
import logfire
from litestar import Litestar
from litestar.events import listener
from litestar.channels import ChannelsPlugin


@listener("UserActivated")
async def on_user_activated(
    user_id: str,
    activated_by: str | None = None,
    reason: str | None = None,
    app: Litestar | None = None,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle UserActivated event.
    
    Actions:
    - Log event
    - Send notification
    - Update cache
    - Publish to WebSocket
    """
    logfire.info(
        "✅ User activated",
        user_id=user_id,
        activated_by=activated_by,
        reason=reason,
    )
    
    # Send notification (optional)
    # await send_activation_email(user_id)
    
    # Publish to WebSocket (optional)
    if app:
        try:
            channels = app.plugins.get(ChannelsPlugin)
            if channels:
                channels.publish(
                    data={
                        "event": "user_activated",
                        "user_id": user_id,
                        "reason": reason,
                    },
                    channels=[f"user:{user_id}"],
                )
        except Exception as e:
            logfire.warning("Failed to publish to channel", error=str(e))
```

---

### Step 4: Зарегистрировать Listener в App.py

**Файл:** `src/App.py`

```python
from src.Containers.AppSection.UserModule.Listeners import (
    on_user_created,
    on_user_updated,
    on_user_deleted,
    on_user_activated,  # Новый listener
)

app = Litestar(
    route_handlers=[...],
    listeners=[
        on_user_created,
        on_user_updated,
        on_user_deleted,
        on_user_activated,  # Добавить сюда
    ],
)
```

---

## 🔄 Поток данных

```
Action.run()
    │
    ├── self.uow.add_event(UserActivated(...))
    │
    └── await self.uow.commit()
              │
              └── __aexit__()
                      │
                      ├── DB commit
                      │
                      └── self._emit("UserActivated", **event_data)
                                │
                                └── Litestar EventEmitter
                                        │
                                        └── @listener("UserActivated")
                                                │
                                                └── on_user_activated()
```

---

## 🎯 Типы Listeners

### 1. Простой listener

```python
@listener("UserActivated")
async def on_user_activated(user_id: str, **kwargs) -> None:
    logfire.info("User activated", user_id=user_id)
```

### 2. Listener с доступом к app

```python
@listener("UserActivated")
async def on_user_activated(
    user_id: str,
    app: Litestar | None = None,
    **kwargs,
) -> None:
    if app:
        # Access plugins, state, etc.
        channels = app.plugins.get(ChannelsPlugin)
```

### 3. Multiple events listener

```python
@listener("UserCreated", "UserUpdated", "UserActivated")
async def on_user_changed(user_id: str, **kwargs) -> None:
    # Handle any user change
    await invalidate_user_cache(user_id)
```

### 4. Cross-module listener

```python
# В другом модуле (например, NotificationModule)
@listener("UserActivated")
async def send_activation_notification(user_id: str, **kwargs) -> None:
    # Send notification from different module
    await notification_service.send(user_id, "account_activated")
```

---

## ⚠️ Важно

1. **События публикуются ПОСЛЕ commit** — если транзакция откатится, события НЕ публикуются

2. **Listeners асинхронны** — не блокируют основной запрос

3. **kwargs обязателен** — event может содержать дополнительные поля

4. **Типы — строки** — UUID передаётся как string, конвертируй если нужно:
   ```python
   user_uuid = UUID(user_id)
   ```

5. **app может быть None** — в CLI контексте или тестах

---

## ✅ Чеклист

- [ ] Event dataclass создан в Events.py
- [ ] Event публикуется в Action через `uow.add_event()`
- [ ] Listener создан в Listeners.py
- [ ] Listener зарегистрирован в App.py
- [ ] Тест написан

---

## 🔗 Связанные

- **Template:** `../templates/event.py.template`
- **Standards:** `../standards/backend/dependency-injection.md` (секция Listeners)
- **Docs:** `docs/11-litestar-features.md`



