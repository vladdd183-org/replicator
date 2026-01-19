# API Standards — Litestar Controllers

> Стандарты для HTTP REST API на базе Litestar с Result pattern.

---

## 🏗️ Структура Controller

### Расположение
```
Containers/{Section}/{Module}/UI/API/Controllers/{Entity}Controller.py
```

### Базовый шаблон

```python
from uuid import UUID
from dishka.integrations.litestar import FromDishka
from litestar import Controller, get, post, patch, delete
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from returns.result import Result

from src.Ship.Decorators.result_handler import result_handler
from src.Containers.{Section}.{Module}.Actions.{Action} import {Action}
from src.Containers.{Section}.{Module}.Queries.{Query} import {Query}
from src.Containers.{Section}.{Module}.Data.Schemas.Requests import {Request}
from src.Containers.{Section}.{Module}.Data.Schemas.Responses import {Response}
from src.Containers.{Section}.{Module}.Errors import {ModuleError}


class {Entity}Controller(Controller):
    path = "/{entities}"
    tags = ["{Entities}"]
    
    @post("/")
    @result_handler({Entity}Response, success_status=HTTP_201_CREATED)
    async def create_{entity}(
        self,
        data: Create{Entity}Request,
        action: FromDishka[Create{Entity}Action],
    ) -> Result[{Entity}, {ModuleError}]:
        return await action.run(data)
```

---

## 📋 CQRS в Controllers

### Write операции → Action

```python
@post("/")
@result_handler(UserResponse, success_status=HTTP_201_CREATED)
async def create_user(
    self,
    data: CreateUserRequest,
    action: FromDishka[CreateUserAction],
) -> Result[AppUser, UserError]:
    return await action.run(data)
```

### Read операции → Query (напрямую)

```python
@get("/{user_id:uuid}")
async def get_user(
    self,
    user_id: UUID,
    query: FromDishka[GetUserQuery],
) -> UserResponse:
    user = await query.execute(GetUserQueryInput(user_id=user_id))
    if user is None:
        raise DomainException(UserNotFoundError(user_id=user_id))
    return UserResponse.from_entity(user)
```

---

## 🎯 HTTP методы и статусы

| Операция | Method | Success Status | Pattern |
|----------|--------|----------------|---------|
| Create | `POST` | `201 Created` | `@result_handler(..., success_status=HTTP_201_CREATED)` |
| Read One | `GET` | `200 OK` | Прямой return DTO |
| Read List | `GET` | `200 OK` | Прямой return DTO |
| Update | `PATCH` | `200 OK` | `@result_handler(..., success_status=HTTP_200_OK)` |
| Delete | `DELETE` | `204 No Content` | `@result_handler(None, success_status=HTTP_204_NO_CONTENT)` |

---

## 🔧 Dependency Injection

### FromDishka для инъекции

```python
from dishka.integrations.litestar import FromDishka

async def create_user(
    self,
    data: CreateUserRequest,
    action: FromDishka[CreateUserAction],  # DI инъекция
) -> Result[AppUser, UserError]:
    return await action.run(data)
```

### @inject НЕ нужен с DishkaRouter

```python
# ❌ НЕ нужно
@inject
async def create_user(action: CreateUserAction): ...

# ✅ Правильно
async def create_user(action: FromDishka[CreateUserAction]): ...
```

---

## 📄 Request/Response DTOs

### Request — с валидацией

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2, max_length=100)
```

### Response — EntitySchema

```python
from src.Ship.Core.BaseSchema import EntitySchema

class UserResponse(EntitySchema):
    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    # from_entity() уже есть!
```

---

## 🔗 Роутинг

### Router composition

```python
# Containers/{Section}/{Module}/UI/API/Routes.py
from litestar import Router
from src.Containers.AppSection.UserModule.UI.API.Controllers.UserController import UserController
from src.Containers.AppSection.UserModule.UI.API.Controllers.AuthController import AuthController

user_api_router = Router(
    path="/api/v1",
    route_handlers=[UserController, AuthController],
)
```

### Регистрация в App.py

```python
from src.Containers.AppSection.UserModule import user_router

app = Litestar(
    route_handlers=[
        user_router,
        # ...
    ],
)
```

---

## 📐 Naming Conventions

| Элемент | Паттерн | Пример |
|---------|---------|--------|
| Controller class | `{Entity}Controller` | `UserController` |
| Controller path | `/{entities}` (plural) | `/users` |
| Controller tags | `["{Entities}"]` | `["Users"]` |
| Create method | `create_{entity}` | `create_user` |
| Get method | `get_{entity}` | `get_user` |
| List method | `list_{entities}` | `list_users` |
| Update method | `update_{entity}` | `update_user` |
| Delete method | `delete_{entity}` | `delete_user` |

---

## 🌐 OpenAPI

### Автоматическая генерация

```python
app = Litestar(
    openapi_config=OpenAPIConfig(
        title=settings.app_name,
        version=settings.app_version,
        path="/api/docs",
        render_plugins=[ScalarRenderPlugin()],  # Scalar UI
    ),
)
```

### Доступные endpoints
- `/api/docs` — Scalar UI
- `/api/docs/openapi.json` — OpenAPI schema

---

## ⚠️ Чего НЕ делать

```python
# ❌ Controller напрямую к Repository
async def create_user(repo: FromDishka[UserRepository]): ...

# ❌ Бизнес-логика в Controller
async def create_user(self, data):
    if await repo.exists(data.email):  # Нет!
        return Response(...)

# ❌ Ручное преобразование Result
async def create_user(self, action):
    result = await action.run(data)
    match result:
        case Success(user): return Response(...)  # Используй @result_handler
```

---

## 📚 Дополнительно

- `src/Ship/Decorators/result_handler.py` — декоратор @result_handler
- `docs/09-transports.md` — HTTP, GraphQL, CLI, WebSocket
- <https://docs.litestar.dev/> — документация Litestar
