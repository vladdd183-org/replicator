# 🎮 Command: /add-graphql

> Создание GraphQL Types и Resolvers (Strawberry).

---

## Синтаксис

```
/add-graphql <Entity> [в <Module>] [с mutations]
```

## Параметры

| Параметр | Обязательный | Пример |
|----------|--------------|--------|
| Entity | ✅ | `User`, `Order`, `Product` |
| Module | ❌ | `UserModule` |
| с mutations | ❌ | Создать также Mutations |

---

## Ключевые правила

| Правило | Описание |
|---------|----------|
| **Library** | Strawberry GraphQL |
| **Types** | В `UI/GraphQL/Types.py` |
| **Resolvers** | В `UI/GraphQL/Resolvers.py` |
| **DI** | Через `get_dependency()` helper |
| **Auth** | Через `Info` context |

---

## Примеры

### Query only
```
/add-graphql User в UserModule
```
→ Создаст Types + Query resolvers

### С mutations
```
/add-graphql User в UserModule с mutations
```
→ Создаст Types + Query + Mutation resolvers

---

## Что создаётся

### 1. GraphQL Types

`UI/GraphQL/Types.py`:

```python
"""GraphQL types for UserModule."""

from datetime import datetime
from uuid import UUID

import strawberry

from src.Containers.AppSection.UserModule.Models.User import AppUser


@strawberry.type
class UserType:
    """GraphQL representation of User."""
    
    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_entity(cls, user: AppUser) -> "UserType":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


@strawberry.type
class AuthTokensType:
    """JWT tokens response."""
    access_token: str
    refresh_token: str
    expires_at: datetime


@strawberry.input
class CreateUserInput:
    """Input for user registration."""
    email: str
    password: str
    name: str


@strawberry.input
class LoginInput:
    """Input for authentication."""
    email: str
    password: str


@strawberry.input
class UpdateUserInput:
    """Input for updating user profile."""
    name: str | None = None
    email: str | None = None


@strawberry.type
class PaginatedUsersType:
    """Paginated users response."""
    items: list[UserType]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
```

### 2. Query Resolvers

`UI/GraphQL/Resolvers.py`:

```python
"""GraphQL resolvers for UserModule."""

from uuid import UUID

import strawberry
from strawberry.types import Info

from src.Ship.GraphQL.Helpers import get_dependency, get_current_user
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import GetUserQuery, GetUserQueryInput
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import ListUsersQuery, ListUsersQueryInput
from src.Containers.AppSection.UserModule.UI.GraphQL.Types import (
    UserType,
    PaginatedUsersType,
)


@strawberry.type
class UserQuery:
    """Query resolvers for User."""
    
    @strawberry.field
    async def user(self, info: Info, id: UUID) -> UserType | None:
        """Get user by ID."""
        query = await get_dependency(info, GetUserQuery)
        user = await query.execute(GetUserQueryInput(user_id=id))
        return UserType.from_entity(user) if user else None
    
    @strawberry.field
    async def users(
        self,
        info: Info,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
    ) -> PaginatedUsersType:
        """Get paginated list of users."""
        query = await get_dependency(info, ListUsersQuery)
        result = await query.execute(ListUsersQueryInput(
            page=page,
            per_page=per_page,
            search=search,
        ))
        return PaginatedUsersType(
            items=[UserType.from_entity(u) for u in result.items],
            total=result.total,
            page=result.page,
            per_page=result.per_page,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )
    
    @strawberry.field
    async def me(self, info: Info) -> UserType:
        """Get current authenticated user."""
        current_user = get_current_user(info)
        query = await get_dependency(info, GetUserQuery)
        user = await query.execute(GetUserQueryInput(user_id=current_user.id))
        if not user:
            raise Exception("User not found")
        return UserType.from_entity(user)
```

### 3. Mutation Resolvers

```python
from returns.result import Success, Failure

from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.AuthenticateAction import AuthenticateAction
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import (
    CreateUserRequest,
    AuthenticateRequest,
)
from src.Containers.AppSection.UserModule.UI.GraphQL.Types import (
    UserType,
    AuthTokensType,
    CreateUserInput,
    LoginInput,
)


@strawberry.type
class UserMutation:
    """Mutation resolvers for User."""
    
    @strawberry.mutation
    async def register(self, info: Info, input: CreateUserInput) -> UserType:
        """Register new user."""
        action = await get_dependency(info, CreateUserAction)
        result = await action.run(CreateUserRequest(
            email=input.email,
            password=input.password,
            name=input.name,
        ))
        
        match result:
            case Success(user):
                return UserType.from_entity(user)
            case Failure(error):
                raise Exception(error.message)
    
    @strawberry.mutation
    async def login(self, info: Info, input: LoginInput) -> AuthTokensType:
        """Authenticate user and get tokens."""
        action = await get_dependency(info, AuthenticateAction)
        result = await action.run(AuthenticateRequest(
            email=input.email,
            password=input.password,
        ))
        
        match result:
            case Success(tokens):
                return AuthTokensType(
                    access_token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    expires_at=tokens.expires_at,
                )
            case Failure(error):
                raise Exception(error.message)
```

---

## DI Helper Functions

```python
# In Ship/GraphQL/Helpers.py
"""GraphQL helper functions."""

from typing import TypeVar
from strawberry.types import Info

from src.Ship.Auth.Middleware import AuthUser


T = TypeVar("T")


async def get_dependency(info: Info, dependency_type: type[T]) -> T:
    """Get dependency from Dishka container via GraphQL context."""
    container = info.context["container"]
    return await container.get(dependency_type)


def get_current_user(info: Info) -> AuthUser:
    """Get current authenticated user from context."""
    user = info.context.get("user")
    if not user:
        raise Exception("Authentication required")
    return user


def get_container_context(info: Info):
    """Get raw Dishka container from context."""
    return info.context["container"]
```

---

## Регистрация Schema в App.py

```python
# In Ship/GraphQL/Schema.py
"""GraphQL schema assembly."""

import strawberry

from src.Containers.AppSection.UserModule.UI.GraphQL.Resolvers import UserQuery, UserMutation


@strawberry.type
class Query(UserQuery):
    """Root Query - combines all module queries."""
    pass


@strawberry.type
class Mutation(UserMutation):
    """Root Mutation - combines all module mutations."""
    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)
```

```python
# In App.py
from litestar import Litestar
from litestar.contrib.strawberry import make_graphql_controller

from src.Ship.GraphQL.Schema import schema


GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    context_getter=get_graphql_context,  # Provides container + user
)

app = Litestar(
    route_handlers=[GraphQLController],
    ...
)
```

---

## Error Handling в Resolvers

```python
from returns.result import Success, Failure

@strawberry.mutation
async def create_user(self, info: Info, input: CreateUserInput) -> UserType:
    action = await get_dependency(info, CreateUserAction)
    result = await action.run(...)
    
    match result:
        case Success(user):
            return UserType.from_entity(user)
        case Failure(error):
            # Option 1: Raise exception
            raise Exception(error.message)
            
            # Option 2: Return error type (union)
            # return UserError(message=error.message, code=error.code)
```

---

## Структура файлов

```
src/Containers/[Section]/[Module]/
└── UI/
    └── GraphQL/
        ├── __init__.py
        ├── Types.py          # @strawberry.type, @strawberry.input
        └── Resolvers.py      # Query and Mutation classes

src/Ship/
└── GraphQL/
    ├── Schema.py             # Root schema assembly
    └── Helpers.py            # get_dependency, get_current_user
```

---

## Действия после создания

1. ✅ Создать `UI/GraphQL/Types.py`
2. ✅ Создать `@strawberry.type` для entity
3. ✅ Создать `@strawberry.input` для inputs
4. ✅ Добавить `from_entity()` class method
5. ✅ Создать `UI/GraphQL/Resolvers.py`
6. ✅ Создать Query resolver class
7. ✅ Создать Mutation resolver class
8. ✅ Использовать `get_dependency()` для DI
9. ✅ Обработать Result через pattern matching
10. ✅ Добавить в root Schema

---

## Связанные ресурсы

- **Template:** `../templates/graphql-resolver.py.template`
- **Docs:** `docs/09-transports.md` (GraphQL секция)
- **Library docs:** `foxdocs/strawberry-main/docs/`
