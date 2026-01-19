---
name: extract-module
description: Guide for extracting Hyper-Porto Container into a separate microservice. Use when the user wants to выделить модуль, extract microservice, разделить на сервисы, микросервис из модуля.
---

# Extract Module to Microservice

Выделение Porto Container в отдельный микросервис.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Docs** | `docs/16-extract-module-to-microservice.md` |
| **Docs** | `docs/17-microservice-extraction-guide.md` |
| **Docs** | `docs/18-unified-event-bus.md` |

## Phases

| Phase | Steps |
|-------|-------|
| **1. Prepare** | Identify boundaries, dependencies |
| **2. Decouple** | Replace imports with events |
| **3. Extract** | Create new service |
| **4. Integrate** | Set up communication |
| **5. Deploy** | Configure infrastructure |

## Действие

1. **Загрузи** полные гайды из docs/
2. **Проверь** готовность модуля к извлечению
3. **Выполни** пошаговое извлечение

## Checklist: Ready for Extraction?

```
- [ ] Module has clear domain boundary
- [ ] Minimal direct imports from other modules
- [ ] Communication already via Events
- [ ] Has own database tables
- [ ] Has own API endpoints
- [ ] No circular dependencies
- [ ] Can run with eventual consistency
```

## Key Steps

### 1. Replace direct imports with Events

```python
# ❌ Before (coupled)
from src.Containers.AppSection.UserModule.Queries import GetUserQuery

# ✅ After (decoupled)
from src.Containers.VendorSection.UserClient import UserServiceClient
```

### 2. Create Service Client

```python
class UserServiceClient:
    async def get_user(self, user_id: UUID) -> UserDTO | None:
        response = await self.client.get(f"/api/v1/users/{user_id}")
        if response.status_code == 404:
            return None
        return UserDTO(**response.json())
```

### 3. Set up Event Bus

```python
# Events distributed via RabbitMQ/Redis
await event_bus.publish(UserCreated(...))
```

## Anti-patterns

| ❌ Anti-pattern | ✅ Correct |
|-----------------|-----------|
| Shared database | Each service owns data |
| Sync HTTP in transactions | Async events |
| Tight coupling via shared libs | API contracts |
| Big bang migration | Gradual strangler pattern |
