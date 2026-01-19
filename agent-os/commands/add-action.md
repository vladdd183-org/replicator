# 🎮 Command: /add-action

> Создание нового Action (Use Case).

---

## Синтаксис

```
/add-action <ActionName> [в <Module>] [с событием <EventName>]
```

## Параметры

| Параметр | Обязательный | Пример |
|----------|--------------|--------|
| ActionName | ✅ | `ActivateUser`, `ProcessPayment` |
| Module | ❌ | `UserModule` |
| EventName | ❌ | `UserActivated` |

---

## Примеры

### Базовый
```
/add-action ActivateUser в UserModule
```
→ Создаст `ActivateUserAction` с базовой структурой

### С событием
```
/add-action ApproveOrder в OrderModule с событием OrderApproved
```
→ Создаст Action + Event + Listener

### Без указания модуля
```
/add-action ResetPassword
```
→ Спросит, в каком модуле создать

---

## Что создаётся

### 1. Action файл

`Actions/ActivateUserAction.py`:

```python
"""ActivateUserAction - Use case for activating user."""

from uuid import UUID
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Ship.Decorators import audited
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import ActivateUserRequest
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import UserError, UserNotFoundError
from src.Containers.AppSection.UserModule.Events import UserActivated
from src.Containers.AppSection.UserModule.Models.User import AppUser


@audited(action="activate", entity_type="User")
class ActivateUserAction(Action[ActivateUserRequest, AppUser, UserError]):
    """Use Case: Activate a user account."""
    
    def __init__(self, uow: UserUnitOfWork) -> None:
        self.uow = uow
    
    async def run(self, user_id: UUID, data: ActivateUserRequest) -> Result[AppUser, UserError]:
        user = await self.uow.users.get(user_id)
        if not user:
            return Failure(UserNotFoundError(user_id=user_id))
        
        async with self.uow:
            user.is_active = True
            await self.uow.users.update(user)
            
            self.uow.add_event(UserActivated(user_id=user.id))
            
            await self.uow.commit()
        
        return Success(user)
```

### 2. Request DTO (если нужен)

`Data/Schemas/Requests.py`:

```python
class ActivateUserRequest(BaseModel):
    reason: str | None = None
```

### 3. Event (если указан)

`Events.py`:

```python
@dataclass
class UserActivated(DomainEvent):
    user_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)
```

### 4. Listener (если указан Event)

`Listeners.py`:

```python
@listener("UserActivated")
async def on_user_activated(user_id: str, **kwargs) -> None:
    logfire.info("User activated", user_id=user_id)
```

### 5. Регистрация в Providers

```python
activate_user_action = provide(ActivateUserAction)
```

---

## Действия после создания

1. ✅ Зарегистрировать в `Providers.py`
2. ✅ Добавить endpoint в Controller (если нужен)
3. ✅ Добавить listener в `App.py` (если есть Event)
4. ✅ Написать тест

---

## Связанные ресурсы

- **Workflow:** `../workflows/add-api-endpoint.md`
- **Template:** `../templates/action.py.template`
- **Checklist:** `../checklists/action-implementation.md`



