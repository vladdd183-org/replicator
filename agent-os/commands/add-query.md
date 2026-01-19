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

from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository
from src.Containers.AppSection.UserModule.Models.User import AppUser


class GetUserQueryInput(BaseModel):
    """Input for GetUserQuery."""
    model_config = ConfigDict(frozen=True)
    user_id: UUID


class GetUserQuery(Query[GetUserQueryInput, AppUser | None]):
    """Get single user by ID.
    
    Returns None if user not found.
    """
    
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository
    
    async def execute(self, input: GetUserQueryInput) -> AppUser | None:
        return await self.user_repository.get(input.user_id)
```

### 2. Query с пагинацией

`Queries/ListUsersQuery.py`:

```python
"""ListUsersQuery - Retrieves paginated list of users."""

from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository
from src.Containers.AppSection.UserModule.Models.User import AppUser


T = TypeVar("T")


@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    """Paginated query result."""
    items: list[T]
    total: int
    page: int
    per_page: int
    
    @property
    def total_pages(self) -> int:
        return (self.total + self.per_page - 1) // self.per_page
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1


class ListUsersQueryInput(BaseModel):
    """Input for ListUsersQuery."""
    model_config = ConfigDict(frozen=True)
    page: int = 1
    per_page: int = 20
    search: str | None = None
    is_active: bool | None = None


class ListUsersQuery(Query[ListUsersQueryInput, PaginatedResult[AppUser]]):
    """Get paginated list of users with optional filters."""
    
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository
    
    async def execute(self, input: ListUsersQueryInput) -> PaginatedResult[AppUser]:
        # Get total count
        total = await self.user_repository.count(
            search=input.search,
            is_active=input.is_active,
        )
        
        # Get paginated items
        offset = (input.page - 1) * input.per_page
        items = await self.user_repository.list(
            offset=offset,
            limit=input.per_page,
            search=input.search,
            is_active=input.is_active,
        )
        
        return PaginatedResult(
            items=items,
            total=total,
            page=input.page,
            per_page=input.per_page,
        )
```

### 3. Query для агрегаций

`Queries/GetUserStatsQuery.py`:

```python
"""GetUserStatsQuery - Retrieves user statistics."""

from dataclasses import dataclass

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository


@dataclass(frozen=True)
class UserStats:
    """User statistics."""
    total_users: int
    active_users: int
    inactive_users: int
    new_users_today: int
    new_users_this_week: int


class GetUserStatsQuery(Query[None, UserStats]):
    """Get aggregated user statistics."""
    
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository
    
    async def execute(self, input: None = None) -> UserStats:
        return UserStats(
            total_users=await self.user_repository.count(),
            active_users=await self.user_repository.count(is_active=True),
            inactive_users=await self.user_repository.count(is_active=False),
            new_users_today=await self.user_repository.count_created_since_days(1),
            new_users_this_week=await self.user_repository.count_created_since_days(7),
        )
```

---

## Использование в Controller

Queries возвращают напрямую (без `@result_handler`):

```python
from litestar import Controller, get
from dishka.integrations.litestar import FromDishka
from litestar.exceptions import NotFoundException

from src.Containers.AppSection.UserModule.Queries.GetUserQuery import GetUserQuery, GetUserQueryInput
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import UserResponse


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
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        query: FromDishka[ListUsersQuery],
    ) -> PaginatedUsersResponse:
        result = await query.execute(ListUsersQueryInput(
            page=page,
            per_page=per_page,
            search=search,
        ))
        return PaginatedUsersResponse.from_paginated(result, UserResponse)
```

---

## Регистрация в Providers

Queries регистрируются в **REQUEST scope**:

```python
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
2. ✅ Создать `@dataclass(frozen=True)` для Input
3. ✅ Метод `execute()` возвращает прямое значение
4. ✅ Зарегистрировать в `Providers.py` (REQUEST scope)
5. ✅ Добавить в `Queries/__init__.py` exports

---

## Типичные ошибки

| ❌ Неправильно | ✅ Правильно |
|----------------|-------------|
| Возвращать `Result[T, E]` | Возвращать `T` или `None` |
| Модифицировать данные | Queries только для чтения |
| Использовать UoW | Напрямую Repository |
| Эмитить события | Queries не эмитят events |
| APP scope | REQUEST scope |

---

## Связанные ресурсы

- **Template:** `../templates/query.py.template`
- **Standard:** `../standards/backend/queries.md`
- **Docs:** `docs/03-components.md`
