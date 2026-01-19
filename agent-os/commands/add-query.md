# 🎮 Command: /add-query

> Создание нового Query (CQRS Read операция).

---

## Синтаксис

```
/add-query <QueryName> [в <Module>]
```

## Параметры

| Параметр | Обязательный | Пример |
|----------|--------------|--------|
| QueryName | ✅ | `GetUser`, `ListUsers`, `SearchProducts` |
| Module | ❌ | `UserModule` |

---

## CQRS: Query vs Action

| Аспект | Query (Read) | Action (Write) |
|--------|--------------|----------------|
| **Purpose** | Чтение данных | Изменение данных |
| **Side effects** | Никаких | Creates/Updates/Deletes |
| **Returns** | Прямое значение или `None` | `Result[T, E]` |
| **Transactions** | Не нужны | Через UnitOfWork |
| **Events** | Никогда не эмитит | Эмитит domain events |
| **Controller** | Без декоратора | `@result_handler` |
| **DI Scope** | REQUEST | REQUEST |

---

## Примеры

### Базовый
```
/add-query GetUser в UserModule
```
→ Создаст `GetUserQuery` для получения одного пользователя

### List с пагинацией
```
/add-query ListUsers в UserModule
```
→ Создаст `ListUsersQuery` с пагинацией

---

## Что создаётся

### 1. Query для одной сущности

`Queries/GetUserQuery.py`:

```python
"""GetUserQuery - Retrieves user by ID."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Models.User import AppUser


class GetUserQueryInput(BaseModel):
    """Input for GetUserQuery."""
    model_config = ConfigDict(frozen=True)
    user_id: UUID


class GetUserQuery(Query[GetUserQueryInput, AppUser | None]):
    """Get single user by ID.
    
    Returns None if user not found.
    Direct ORM access for optimal read performance.
    """
    
    async def execute(self, input: GetUserQueryInput) -> AppUser | None:
        return await AppUser.objects().where(
            AppUser.id == input.user_id
        ).first()
```

### 2. Query с пагинацией

`Queries/ListUsersQuery.py`:

```python
"""ListUsersQuery - Retrieves paginated list of users."""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Models.User import AppUser


class ListUsersQueryInput(BaseModel):
    """Input for ListUsersQuery."""
    model_config = ConfigDict(frozen=True)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    search: str | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class ListUsersQueryOutput:
    """Output of ListUsersQuery.
    
    Uses dataclass(frozen=True) instead of Pydantic to avoid
    arbitrary_types_allowed issues with ORM models.
    """
    users: list[AppUser]
    total: int
    limit: int
    offset: int


class ListUsersQuery(Query[ListUsersQueryInput, ListUsersQueryOutput]):
    """Get paginated list of users with optional filters.
    
    Direct ORM access for optimal read performance.
    """
    
    async def execute(self, input: ListUsersQueryInput) -> ListUsersQueryOutput:
        query = AppUser.objects()
        count_query = AppUser.count()
        
        # Apply filters
        if input.is_active is not None:
            query = query.where(AppUser.is_active == input.is_active)
            count_query = count_query.where(AppUser.is_active == input.is_active)
        
        if input.search:
            query = query.where(AppUser.name.ilike(f"%{input.search}%"))
            count_query = count_query.where(AppUser.name.ilike(f"%{input.search}%"))
        
        total = await count_query
        users = await (
            query
            .limit(input.limit)
            .offset(input.offset)
            .order_by(AppUser.created_at, ascending=False)
        )
        
        return ListUsersQueryOutput(
            users=users,
            total=total,
            limit=input.limit,
            offset=input.offset,
        )
```

### 3. Query для агрегаций

`Queries/GetUserStatsQuery.py`:

```python
"""GetUserStatsQuery - Retrieves user statistics."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Models.User import AppUser


@dataclass(frozen=True)
class UserStats:
    """User statistics output."""
    total_users: int
    active_users: int
    inactive_users: int
    new_users_today: int
    new_users_this_week: int


class GetUserStatsQuery(Query[None, UserStats]):
    """Get aggregated user statistics.
    
    Direct ORM access for optimal read performance.
    """
    
    async def execute(self, input: None = None) -> UserStats:
        now = datetime.utcnow()
        today = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        return UserStats(
            total_users=await AppUser.count(),
            active_users=await AppUser.count().where(AppUser.is_active == True),
            inactive_users=await AppUser.count().where(AppUser.is_active == False),
            new_users_today=await AppUser.count().where(AppUser.created_at >= today),
            new_users_this_week=await AppUser.count().where(AppUser.created_at >= week_ago),
        )
```

### 4. Query с Repository (альтернативный паттерн)

Если нужна абстракция через Repository:

`Queries/GetUserByEmailQuery.py`:

```python
"""GetUserByEmailQuery - Retrieves user by email via Repository."""

from pydantic import BaseModel, ConfigDict, EmailStr

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository
from src.Containers.AppSection.UserModule.Models.User import AppUser


class GetUserByEmailQueryInput(BaseModel):
    """Input for GetUserByEmailQuery."""
    model_config = ConfigDict(frozen=True)
    email: EmailStr


class GetUserByEmailQuery(Query[GetUserByEmailQueryInput, AppUser | None]):
    """Get user by email using Repository.
    
    Uses Repository for complex query logic or when
    you want to reuse query logic across the codebase.
    """
    
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository
    
    async def execute(self, input: GetUserByEmailQueryInput) -> AppUser | None:
        return await self.user_repository.find_by_email(input.email)
```

---

## Использование в Controller

Queries возвращают напрямую (без `@result_handler`):

```python
from litestar import Controller, get
from litestar.exceptions import NotFoundException
from dishka.integrations.litestar import FromDishka
from uuid import UUID

from src.Containers.AppSection.UserModule.Queries.GetUserQuery import GetUserQuery, GetUserQueryInput
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import ListUsersQuery, ListUsersQueryInput
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import UserResponse, UserListResponse


class UserController(Controller):
    path = "/users"
    
    @get("/{user_id:uuid}")
    async def get_user(
        self,
        user_id: UUID,
        query: FromDishka[GetUserQuery],
    ) -> UserResponse:
        user = await query.execute(GetUserQueryInput(user_id=user_id))
        if not user:
            raise NotFoundException(detail="User not found")
        return UserResponse.from_entity(user)
    
    @get("/")
    async def list_users(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        query: FromDishka[ListUsersQuery],
    ) -> UserListResponse:
        result = await query.execute(ListUsersQueryInput(
            limit=limit,
            offset=offset,
            search=search,
        ))
        return UserListResponse(
            users=[UserResponse.from_entity(u) for u in result.users],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )
```

---

## Регистрация в Providers

Queries регистрируются в **REQUEST scope**:

```python
from dishka import Provider, Scope, provide

from src.Containers.AppSection.UserModule.Queries.GetUserQuery import GetUserQuery
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import ListUsersQuery
from src.Containers.AppSection.UserModule.Queries.GetUserStatsQuery import GetUserStatsQuery


class ModuleRequestProvider(Provider):
    scope = Scope.REQUEST
    
    get_user_query = provide(GetUserQuery)
    list_users_query = provide(ListUsersQuery)
    get_user_stats_query = provide(GetUserStatsQuery)
```

---

## Именование

| Операция | Паттерн | Пример |
|----------|---------|--------|
| Get single | `Get{Entity}Query` | `GetUserQuery` |
| List/paginated | `List{Entity}sQuery` | `ListUsersQuery` |
| Search | `Search{Entity}sQuery` | `SearchUsersQuery` |
| Stats/aggregation | `Get{Entity}StatsQuery` | `GetUserStatsQuery` |
| Exists check | `Check{Entity}ExistsQuery` | `CheckEmailExistsQuery` |
| By field | `Get{Entity}By{Field}Query` | `GetUserByEmailQuery` |

---

## Действия после создания

1. ✅ Создать `Queries/[QueryName].py`
2. ✅ Input — `pydantic.BaseModel` с `ConfigDict(frozen=True)`
3. ✅ Output — можно `@dataclass(frozen=True)` для сложных результатов
4. ✅ Метод `execute()` возвращает прямое значение
5. ✅ Зарегистрировать в `Providers.py` (REQUEST scope)
6. ✅ Добавить в `Queries/__init__.py` exports

---

## Типичные ошибки

| ❌ Неправильно | ✅ Правильно |
|----------------|-------------|
| Возвращать `Result[T, E]` | Возвращать `T` или `None` |
| Модифицировать данные | Queries только для чтения |
| Использовать UoW | Напрямую ORM или Repository |
| Эмитить события | Queries не эмитят events |
| APP scope | REQUEST scope |
| `@dataclass` на Query классе | `@dataclass` только на Output |

---

## Связанные ресурсы

- **Template:** `../templates/query.py.template`
- **Standard:** `../standards/backend/queries.md`
- **Docs:** `docs/03-components.md`
