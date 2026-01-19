---
name: add-endpoint
description: Create HTTP API endpoints for Hyper-Porto with Litestar. Generates Controllers with @result_handler for write operations (POST, PATCH, DELETE) and direct returns for read operations (GET). Use when user asks to add endpoint, create route, new api, добавь endpoint, новый api, создай роут.
---

# Add Endpoint (Hyper-Porto + Litestar)

Создание HTTP API endpoint.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Инструкция** | `agent-os/commands/add-endpoint.md` |
| **Template** | `agent-os/templates/controller.py.template` |
| **Workflow** | `agent-os/workflows/add-api-endpoint.md` |
| **Standard** | `agent-os/standards/backend/api.md` |

## Быстрая справка

| Операция | Method | Status | Использует | Returns |
|----------|--------|--------|------------|---------|
| Create | POST | 201 | Action + `@result_handler` | `Result[T, E]` |
| Read | GET | 200 | Query (direct return) | DTO |
| Update | PATCH | 200 | Action + `@result_handler` | `Result[T, E]` |
| Delete | DELETE | 204 | Action + `@result_handler` | `Result[None, E]` |

## Ключевые правила

- **Write operations** (POST, PATCH, DELETE): `@result_handler` + `Result[T, E]`
- **Read operations** (GET): прямой return DTO, `DomainException` для ошибок
- **DI**: `FromDishka[Action]` или `FromDishka[Query]`
- **DELETE workaround**: `status_code=HTTP_200_OK` в декораторе

## Действие

1. **Загрузи** полную инструкцию из `agent-os/commands/add-endpoint.md`
2. **Используй** template из `agent-os/templates/controller.py.template`
3. **Создай/обнови** Controller в `UI/API/Controllers/`
4. **Зарегистрируй** router в `UI/API/Routes.py`
5. **Добавь** router в `App.py` если новый Controller

## Структура endpoint

```python
# Write (POST) - с @result_handler
@post("/")
@result_handler(ResponseDTO, success_status=HTTP_201_CREATED)
async def create(self, data: RequestDTO, action: FromDishka[Action]) -> Result[Entity, Error]:
    return await action.run(data)

# Read (GET) - без @result_handler
@get("/{id:uuid}")
async def get(self, id: UUID, query: FromDishka[Query]) -> ResponseDTO:
    result = await query.execute(Input(id=id))
    if not result:
        raise DomainException(NotFoundError(id=id))
    return ResponseDTO.from_entity(result)
```
