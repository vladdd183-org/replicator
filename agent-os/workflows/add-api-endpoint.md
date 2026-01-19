# 🌐 Workflow: Add API Endpoint

> Пошаговая инструкция добавления нового REST API endpoint.

---

## 📋 Входные данные

| Параметр | Пример | Твоё значение |
|----------|--------|---------------|
| HTTP Method | `POST`, `GET`, `PATCH`, `DELETE` | _____________ |
| Path | `/users/{id}/activate` | _____________ |
| Operation | `Activate user` | _____________ |
| Module | `UserModule` | _____________ |

---

## 🎯 Определи тип операции

| Тип | Метод | Компонент | Return |
|-----|-------|-----------|--------|
| **Write** | POST, PATCH, DELETE | Action | `Result[T, E]` |
| **Read** | GET | Query | `T` или `T \| None` |

---

## 🚀 Для WRITE операции (POST/PATCH/DELETE)

### Step 1: Создать Request DTO

**Файл:** `Data/Schemas/Requests.py`

```python
class ActivateUserRequest(BaseModel):
    """Request for activating user."""
    reason: str | None = None
```

### Step 2: Создать/обновить Response DTO

**Файл:** `Data/Schemas/Responses.py`

```python
# Если нужен специфичный response, иначе используй существующий UserResponse
```

### Step 3: Создать Error (если нужен новый)

**Файл:** `Errors.py`

```python
class UserAlreadyActiveError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User {user_id} is already active"
    code: str = "USER_ALREADY_ACTIVE"
    http_status: int = 409
    user_id: UUID
```

### Step 4: Создать Action

**Файл:** `Actions/ActivateUserAction.py`

```python
@audited(action="activate", entity_type="User")
class ActivateUserAction(Action[ActivateUserRequest, AppUser, UserError]):
    def __init__(self, uow: UserUnitOfWork) -> None:
        self.uow = uow
    
    async def run(self, user_id: UUID, data: ActivateUserRequest) -> Result[AppUser, UserError]:
        async with self.uow:
            user = await self.uow.users.get(user_id)
            if not user:
                return Failure(UserNotFoundError(user_id=user_id))
            
            if user.is_active:
                return Failure(UserAlreadyActiveError(user_id=user_id))
            
            user.is_active = True
            await self.uow.users.update(user)
            
            self.uow.add_event(UserActivated(user_id=user.id))
            await self.uow.commit()
        
        return Success(user)
```

### Step 5: Зарегистрировать Action в Providers

**Файл:** `Providers.py`

```python
class UserRequestProvider(Provider):
    # ... existing
    activate_user_action = provide(ActivateUserAction)
```

### Step 6: Добавить endpoint в Controller

**Файл:** `UI/API/Controllers/UserController.py`

```python
@post("/{user_id:uuid}/activate")
@result_handler(UserResponse, success_status=HTTP_200_OK)
async def activate_user(
    self,
    user_id: UUID,
    data: ActivateUserRequest,
    action: FromDishka[ActivateUserAction],
) -> Result[AppUser, UserError]:
    return await action.run(user_id, data)
```

---

## 🚀 Для READ операции (GET)

### Step 1: Создать Query Input

**Файл:** `Queries/GetActiveUsersQuery.py`

```python
class GetActiveUsersQueryInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    limit: int = Field(default=20, ge=1, le=100)
    department: str | None = None
```

### Step 2: Создать Query

```python
class GetActiveUsersQuery(Query[GetActiveUsersQueryInput, list[AppUser]]):
    async def execute(self, params: GetActiveUsersQueryInput) -> list[AppUser]:
        query = AppUser.objects().where(AppUser.is_active == True)
        
        if params.department:
            query = query.where(AppUser.department == params.department)
        
        return await query.limit(params.limit)
```

### Step 3: Зарегистрировать Query в Providers

**Файл:** `Providers.py`

```python
class UserRequestProvider(Provider):
    # ... existing
    get_active_users_query = provide(GetActiveUsersQuery)
```

### Step 4: Добавить endpoint в Controller

```python
@get("/active")
async def get_active_users(
    self,
    query: FromDishka[GetActiveUsersQuery],
    limit: int = 20,
    department: str | None = None,
) -> list[UserResponse]:
    users = await query.execute(GetActiveUsersQueryInput(
        limit=limit,
        department=department,
    ))
    return [UserResponse.from_entity(u) for u in users]
```

---

## 📐 HTTP методы и статусы

| Операция | Method | Success Status | Response |
|----------|--------|----------------|----------|
| Create | POST | 201 Created | Entity |
| Read one | GET | 200 OK | Entity |
| Read list | GET | 200 OK | List |
| Update | PATCH | 200 OK | Entity |
| Delete | DELETE | 204 No Content | None |
| Action | POST | 200 OK | Entity/Result |

---

## ✅ Чеклист

- [ ] Request DTO создан (для write)
- [ ] Response DTO создан/выбран
- [ ] Error создан (если новый)
- [ ] Action/Query создан
- [ ] Зарегистрирован в Providers
- [ ] Endpoint добавлен в Controller
- [ ] OpenAPI документация проверена (`/api/docs`)
- [ ] Тест написан

---

## 🔗 Связанные

- **Templates:** `../templates/action.py.template`, `../templates/query.py.template`
- **Standards:** `../standards/backend/api.md`



