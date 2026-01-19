# Queries & CQRS — Read Operations

> Стандарты для CQRS Queries (read операции) в Hyper-Porto.

---

## 🎯 CQRS Pattern

```
Write операции → Actions (через UnitOfWork)
Read операции  → Queries (напрямую к Repository)
```

---

## 📁 Расположение

```
Containers/{Section}/{Module}/Queries/
├── __init__.py
├── Get{Entity}Query.py
└── List{Entities}Query.py
```

---

## 🏗️ Базовый шаблон Query

```python
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Models.User import AppUser


class GetUserQueryInput(BaseModel):
    """Input for GetUserQuery.
    
    Uses Pydantic with frozen=True for immutability.
    """
    model_config = ConfigDict(frozen=True)
    
    user_id: UUID


class GetUserQuery(Query[GetUserQueryInput, AppUser | None]):
    """Query to get single user by ID.
    
    Direct ORM access — Query не использует Repository для простоты.
    Returns None if user not found.
    """
    
    async def execute(self, input: GetUserQueryInput) -> AppUser | None:
        return await AppUser.objects().where(AppUser.id == input.user_id).first()
```

---

## 📋 List Query с пагинацией

```python
from dataclasses import dataclass

from pydantic import BaseModel, Field, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Models.User import AppUser


class ListUsersQueryInput(BaseModel):
    """Input for ListUsersQuery.
    
    Uses Pydantic for validation + frozen for immutability.
    """
    model_config = ConfigDict(frozen=True)
    
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    active_only: bool = False


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
    """Query to list users with pagination.
    
    Direct ORM access — no Repository dependency for simplicity.
    """
    
    async def execute(self, params: ListUsersQueryInput) -> ListUsersQueryOutput:
        query = AppUser.objects()
        count_query = AppUser.count()
        
        if params.active_only:
            query = query.where(AppUser.is_active == True)
            count_query = count_query.where(AppUser.is_active == True)
        
        total = await count_query
        users = await (
            query
            .limit(params.limit)
            .offset(params.offset)
            .order_by(AppUser.created_at, ascending=False)
        )
        
        return ListUsersQueryOutput(
            users=users,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )
```

---

## 📏 Naming Conventions

| Элемент | Паттерн | Пример |
|---------|---------|--------|
| Query class | `{Verb}{Entity}Query` | `GetUserQuery`, `ListUsersQuery` |
| Input class | `{Query}Input` | `GetUserQueryInput`, `ListUsersQueryInput` |
| Output class | `{Query}Output` | `ListUsersQueryOutput` |
| Method | `execute` | `async def execute(...)` |
| Parameter | `input` или `params` | `async def execute(self, params: ...)` |

### Input — Pydantic (frozen)

```python
class GetUserQueryInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    user_id: UUID
```

### Output — dataclass(frozen=True) для ORM моделей

```python
@dataclass(frozen=True)
class ListUsersQueryOutput:
    users: list[AppUser]  # ORM models
    total: int
```

---

## 🔧 Base Query Class

```python
# src/Ship/Parents/Query.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Query(ABC, Generic[InputT, OutputT]):
    """CQRS Query — read-only операция.
    
    Rules:
    - Только чтение данных
    - Не изменяет состояние
    - Может обращаться к Repository напрямую
    - НЕ использует UnitOfWork
    """
    
    @abstractmethod
    async def execute(self, input: InputT) -> OutputT:
        ...
```

---

## 🎨 Использование в Controller

### Query напрямую (без @result_handler)

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

### List Query с пагинацией

```python
@get("/")
async def list_users(
    self,
    query: FromDishka[ListUsersQuery],
    limit: int = 20,
    offset: int = 0,
    active_only: bool = False,
) -> UserListResponse:
    result = await query.execute(ListUsersQueryInput(
        limit=limit,
        offset=offset,
        active_only=active_only,
    ))
    
    return UserListResponse(
        users=[UserResponse.from_entity(u) for u in result.users],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )
```

---

## 🔗 DI Registration

```python
# Providers.py
class UserRequestProvider(Provider):
    scope = Scope.REQUEST
    
    list_users_query = provide(ListUsersQuery)
    get_user_query = provide(GetUserQuery)
```

---

## ⚡ SyncQuery для in-memory операций

```python
from src.Ship.Parents.Query import SyncQuery


@dataclass
class GetCachedSettingQuery(SyncQuery[str, str | None]):
    """Sync query for cached settings."""
    
    cache: dict[str, str]
    
    def execute(self, input: str) -> str | None:
        return self.cache.get(input)
```

---

## 🆚 Query vs Action

| Аспект | Query | Action |
|--------|-------|--------|
| Операция | Read (SELECT) | Write (INSERT/UPDATE/DELETE) |
| Return type | `T` или `T \| None` | `Result[T, Error]` |
| UnitOfWork | Не использует | Использует |
| События | Не публикует | Публикует через UoW |
| Метод | `execute()` | `run()` |

---

## ⚠️ Чего НЕ делать

```python
# ❌ Query НЕ должен изменять данные
async def execute(self, input):
    await self.repo.update(...)  # Нет!

# ❌ Query НЕ должен возвращать Result
async def execute(self, input) -> Result[User, Error]:  # Нет!
    ...

# ❌ Query НЕ должен использовать UoW
async def execute(self, input):
    async with self.uow:  # Нет!
        ...
```

---

## 📚 Дополнительно

- `src/Ship/Parents/Query.py` — базовый класс Query
- `docs/03-components.md` — описание компонентов
- `docs/04-result-railway.md` — когда использовать Result
