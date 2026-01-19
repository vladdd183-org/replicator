# 🎮 Command: /add-endpoint

> Добавление нового REST API endpoint.

---

## Синтаксис

```
/add-endpoint <METHOD> <path> [для <ActionName>] [в <Module>]
```

## Параметры

| Параметр | Обязательный | Пример |
|----------|--------------|--------|
| METHOD | ✅ | `POST`, `GET`, `PATCH`, `DELETE` |
| path | ✅ | `/users/{id}/activate` |
| ActionName | ❌ (для write) | `ActivateUserAction` |
| Module | ❌ | `UserModule` |

---

## Примеры

### POST endpoint (write)
```
/add-endpoint POST /orders для CreateOrderAction в OrderModule
```
→ Создаст:
- `CreateOrderRequest` DTO
- `CreateOrderAction`
- Endpoint в `OrderController`

### GET endpoint (read)
```
/add-endpoint GET /users/active в UserModule
```
→ Создаст:
- `GetActiveUsersQuery`
- Endpoint в `UserController`

### PATCH endpoint
```
/add-endpoint PATCH /users/{id}/status для UpdateUserStatusAction
```

### DELETE endpoint
```
/add-endpoint DELETE /orders/{id} для DeleteOrderAction
```

---

## Что создаётся

### Для Write операций (POST, PATCH, DELETE)

1. **Request DTO** (если не существует)
```python
class ActivateUserRequest(BaseModel):
    reason: str | None = None
```

2. **Action**
```python
@audited(action="activate", entity_type="User")
class ActivateUserAction(Action[ActivateUserRequest, User, UserError]):
    async def run(self, user_id: UUID, data: ActivateUserRequest) -> Result[User, UserError]:
        ...
```

3. **Endpoint в Controller**
```python
@post("/{user_id:uuid}/activate")
@result_handler(UserResponse, success_status=HTTP_200_OK)
async def activate_user(
    self,
    user_id: UUID,
    data: ActivateUserRequest,
    action: FromDishka[ActivateUserAction],
) -> Result[User, UserError]:
    return await action.run(user_id, data)
```

4. **Регистрация в Providers**

### Для Read операций (GET)

1. **Query Input**
```python
class GetActiveUsersQueryInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    limit: int = Field(default=20, ge=1, le=100)
```

2. **Query**
```python
class GetActiveUsersQuery(Query[GetActiveUsersQueryInput, list[User]]):
    async def execute(self, params: GetActiveUsersQueryInput) -> list[User]:
        ...
```

3. **Endpoint в Controller**
```python
@get("/active")
async def get_active_users(
    self,
    query: FromDishka[GetActiveUsersQuery],
    limit: int = 20,
) -> list[UserResponse]:
    users = await query.execute(GetActiveUsersQueryInput(limit=limit))
    return [UserResponse.from_entity(u) for u in users]
```

---

## HTTP методы и статусы

| Операция | Method | Status | Return |
|----------|--------|--------|--------|
| Create | POST | 201 | Entity |
| Read | GET | 200 | Entity/List |
| Update | PATCH | 200 | Entity |
| Delete | DELETE | 204 | None |
| Action | POST | 200 | Entity/Result |

---

## Связанные ресурсы

- **Workflow:** `../workflows/add-api-endpoint.md`
- **Templates:** `../templates/action.py.template`, `../templates/controller.py.template`



