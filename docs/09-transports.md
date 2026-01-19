# 🚀 Transports (UI Layer)

> **Версия:** 4.3 | **Дата:** Январь 2026

В Hyper-Porto **один Action** может быть доступен через **несколько транспортов**:
HTTP REST, GraphQL, CLI, WebSocket, Background Workers.

---

## 📐 Структура UI Layer

```
Container/
└── UI/
    ├── API/              # HTTP REST (Litestar Controllers)
    │   ├── Controllers/
    │   │   ├── UserController.py
    │   │   └── AuthController.py
    │   └── Routes.py     # Router composition
    │
    ├── GraphQL/          # Strawberry GraphQL
    │   ├── Types.py      # Input/Output types
    │   └── Resolvers.py  # Queries + Mutations
    │
    ├── CLI/              # Click + Litestar CLIPlugin
    │   └── Commands.py
    │
    ├── WebSocket/        # Litestar Channels
    │   └── Handlers.py
    │
    └── Workers/          # TaskIQ Background Tasks
        └── Tasks.py
```

---

## 🌐 HTTP REST (Litestar Controllers)

### Принципы:

1. **Controller вызывает только Action (write) или Query (read)**
2. **DI через `FromDishka`** — инъекция зависимостей
3. **`@result_handler`** — автоматическая конвертация Result → Response
4. **Pydantic DTOs** — для Request/Response

### Реальный пример: UserController

```python
# src/Containers/AppSection/UserModule/UI/API/Controllers/UserController.py
"""User HTTP API endpoints."""

from uuid import UUID
from litestar import Controller, get, post, put, delete
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from dishka.integrations.litestar import FromDishka

from src.Ship.Decorators.result_handler import result_handler
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.UpdateUserAction import UpdateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import (
    ListUsersQuery,
    ListUsersQueryInput,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import (
    CreateUserRequest,
    UpdateUserRequest,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    UserResponse,
    UserListResponse,
)
from src.Containers.AppSection.UserModule.Errors import UserNotFoundError


class UserController(Controller):
    """User CRUD endpoints."""
    
    path = "/users"
    tags = ["Users"]

    @post("/")
    @result_handler(UserResponse, success_status=HTTP_201_CREATED)
    async def create_user(
        self,
        data: CreateUserRequest,
        action: FromDishka[CreateUserAction],
    ):
        """Create new user.
        
        @result_handler автоматически:
        - Success(user) → Response(UserResponse.from_entity(user), status=201)
        - Failure(error) → DomainException → Problem Details (RFC 9457)
        """
        return await action.run(data)

    @get("/{user_id:uuid}")
    async def get_user(
        self,
        user_id: UUID,
        query: FromDishka[GetUserQuery],
    ) -> UserResponse:
        """Get user by ID.
        
        CQRS: Uses Query for read operation.
        """
        user = await query.execute(GetUserQueryInput(user_id=user_id))
        if user is None:
            raise UserNotFoundError(user_id=user_id).to_exception()
        return UserResponse.from_entity(user)

    @get("/")
    async def list_users(
        self,
        query: FromDishka[ListUsersQuery],
        limit: int = 20,
        offset: int = 0,
        active_only: bool = False,
    ) -> UserListResponse:
        """List users with pagination."""
        result = await query.execute(
            ListUsersQueryInput(limit=limit, offset=offset, active_only=active_only)
        )
        return UserListResponse(
            users=[UserResponse.from_entity(u) for u in result.users],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    @put("/{user_id:uuid}")
    @result_handler(UserResponse)
    async def update_user(
        self,
        user_id: UUID,
        data: UpdateUserRequest,
        action: FromDishka[UpdateUserAction],
    ):
        """Update user profile."""
        return await action.run(user_id, data)

    @delete("/{user_id:uuid}")
    @result_handler(None, success_status=HTTP_204_NO_CONTENT)
    async def delete_user(
        self,
        user_id: UUID,
        action: FromDishka[DeleteUserAction],
    ):
        """Delete user (soft delete)."""
        return await action.run(user_id)
```

### Реальный пример: AuthController

```python
# src/Containers/AppSection/UserModule/UI/API/Controllers/AuthController.py
"""Authentication HTTP API endpoints."""

from uuid import UUID
from litestar import Controller, get, post
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT
from dishka.integrations.litestar import FromDishka

from src.Ship.Auth.Guards import auth_guard
from src.Ship.Auth.Middleware import AuthUser
from src.Ship.Decorators.result_handler import result_handler
from src.Containers.AppSection.UserModule.Actions.AuthenticateAction import AuthenticateAction
from src.Containers.AppSection.UserModule.Actions.ChangePasswordAction import ChangePasswordAction
from src.Containers.AppSection.UserModule.Actions.RefreshTokenAction import RefreshTokenAction
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import GetUserQuery, GetUserQueryInput
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import (
    LoginRequest,
    ChangePasswordRequest,
    RefreshTokenRequest,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    AuthResponse,
    TokenRefreshResponse,
    UserResponse,
)
from src.Containers.AppSection.UserModule.Errors import UserNotFoundError


class AuthController(Controller):
    """Authentication endpoints."""
    
    path = "/auth"
    tags = ["Authentication"]

    @post("/login")
    @result_handler(AuthResponse)
    async def login(
        self,
        data: LoginRequest,
        action: FromDishka[AuthenticateAction],
    ):
        """Authenticate user and return tokens."""
        return await action.run(data)

    @get("/me", dependencies={"auth_user": auth_guard})
    async def get_current_user(
        self,
        auth_user: AuthUser,
        query: FromDishka[GetUserQuery],
    ) -> UserResponse:
        """Get current authenticated user.
        
        Protected endpoint: requires valid JWT token.
        """
        user = await query.execute(GetUserQueryInput(user_id=auth_user.id))
        if user is None:
            raise UserNotFoundError(user_id=auth_user.id).to_exception()
        return UserResponse.from_entity(user)

    @post("/change-password", dependencies={"auth_user": auth_guard})
    @result_handler(None, success_status=HTTP_204_NO_CONTENT)
    async def change_password(
        self,
        data: ChangePasswordRequest,
        auth_user: AuthUser,
        action: FromDishka[ChangePasswordAction],
    ):
        """Change password for current user."""
        return await action.run(auth_user.id, data)

    @post("/refresh")
    @result_handler(TokenRefreshResponse)
    async def refresh_token(
        self,
        data: RefreshTokenRequest,
        action: FromDishka[RefreshTokenAction],
    ):
        """Refresh access token using refresh token."""
        return await action.run(data)

    @post("/logout", dependencies={"auth_user": auth_guard})
    async def logout(self, auth_user: AuthUser) -> dict:
        """Logout current user (client-side token removal).
        
        JWT stateless: server doesn't store tokens.
        Client should remove tokens from storage.
        """
        return {"message": "Successfully logged out", "user_id": str(auth_user.id)}
```

### Router composition

```python
# src/Containers/AppSection/UserModule/UI/API/Routes.py
"""Router composition for UserModule."""

from litestar import Router

from src.Containers.AppSection.UserModule.UI.API.Controllers.UserController import UserController
from src.Containers.AppSection.UserModule.UI.API.Controllers.AuthController import AuthController

user_router = Router(
    path="/api/v1",
    route_handlers=[UserController, AuthController],
)
```

---

## 🔮 GraphQL (Strawberry)

### Принципы:

1. **Queries используют Query классы** (CQRS read)
2. **Mutations используют Actions** (CQRS write)
3. **DI через `get_dependency` helper** (dishka-strawberry не поддерживает Litestar)
4. **Strawberry Types ↔ Pydantic DTOs** — конвертация через `from_pydantic/to_pydantic`

### Реальный пример: Resolvers

```python
# src/Containers/AppSection/UserModule/UI/GraphQL/Resolvers.py
"""GraphQL resolvers for UserModule."""

import strawberry
from uuid import UUID
from returns.result import Success, Failure

from src.Ship.GraphQL.Helpers import get_dependency
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import (
    ListUsersQuery,
    ListUsersQueryInput,
)
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    UserResponse,
    UserListResponse,
)
from src.Containers.AppSection.UserModule.UI.GraphQL.Types import (
    UserType,
    UserListType,
    CreateUserInput,
    CreateUserPayload,
    DeleteUserPayload,
    UserError as UserErrorType,
)


def _user_to_graphql(user) -> UserType:
    """Convert User entity to GraphQL UserType via Pydantic."""
    response = UserResponse.from_entity(user)
    return UserType.from_pydantic(response)


@strawberry.type
class UserQuery:
    """GraphQL queries for users."""

    @strawberry.field
    async def user(
        self,
        id: UUID,
        info: strawberry.Info,
    ) -> UserType | None:
        """Get user by ID.
        
        CQRS: Uses GetUserQuery for read operation.
        """
        query = await get_dependency(info, GetUserQuery)
        user = await query.execute(GetUserQueryInput(user_id=id))
        return _user_to_graphql(user) if user else None

    @strawberry.field
    async def users(
        self,
        info: strawberry.Info,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = False,
    ) -> UserListType:
        """List users with pagination.
        
        CQRS: Uses ListUsersQuery for read operation.
        """
        query = await get_dependency(info, ListUsersQuery)
        
        result = await query.execute(ListUsersQueryInput(
            limit=limit,
            offset=offset,
            active_only=active_only,
        ))
        
        response = UserListResponse(
            users=[UserResponse.from_entity(u) for u in result.users],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )
        return UserListType.from_pydantic(response)


@strawberry.type
class UserMutation:
    """GraphQL mutations for users."""

    @strawberry.mutation
    async def create_user(
        self,
        input: CreateUserInput,
        info: strawberry.Info,
    ) -> CreateUserPayload:
        """Create a new user.
        
        Uses Action for write operation.
        Returns payload with user or error.
        """
        action = await get_dependency(info, CreateUserAction)
        
        # Convert Strawberry input to Pydantic
        request = input.to_pydantic()
        result = await action.run(request)
        
        match result:
            case Success(user):
                return CreateUserPayload(user=_user_to_graphql(user))
            case Failure(error):
                return CreateUserPayload(
                    error=UserErrorType(message=error.message, code=error.code)
                )

    @strawberry.mutation
    async def delete_user(
        self,
        id: UUID,
        info: strawberry.Info,
    ) -> DeleteUserPayload:
        """Delete a user by ID."""
        action = await get_dependency(info, DeleteUserAction)
        result = await action.run(id)
        
        match result:
            case Success(_):
                return DeleteUserPayload(success=True)
            case Failure(error):
                return DeleteUserPayload(
                    success=False,
                    error=UserErrorType(message=error.message, code=error.code)
                )
```

### GraphQL Types

```python
# src/Containers/AppSection/UserModule/UI/GraphQL/Types.py
"""GraphQL types for UserModule."""

import strawberry
from uuid import UUID
from datetime import datetime

from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    UserResponse,
    UserListResponse,
)


@strawberry.experimental.pydantic.type(model=UserResponse, all_fields=True)
class UserType:
    """GraphQL User type - auto-generated from Pydantic model."""
    pass


@strawberry.experimental.pydantic.type(model=UserListResponse)
class UserListType:
    """GraphQL UserList type with pagination."""
    users: list[UserType]
    total: int
    limit: int
    offset: int


@strawberry.experimental.pydantic.input(model=CreateUserRequest, all_fields=True)
class CreateUserInput:
    """GraphQL input for creating user."""
    pass


@strawberry.type
class UserError:
    """GraphQL error type."""
    message: str
    code: str


@strawberry.type
class CreateUserPayload:
    """Payload for createUser mutation."""
    user: UserType | None = None
    error: UserError | None = None


@strawberry.type
class DeleteUserPayload:
    """Payload for deleteUser mutation."""
    success: bool
    error: UserError | None = None
```

### get_dependency helper

```python
# src/Ship/GraphQL/Helpers.py
"""GraphQL helpers for DI and error handling."""

from typing import TypeVar
import strawberry

T = TypeVar("T")


async def get_dependency(info: strawberry.Info, dependency_type: type[T]) -> T:
    """Get dependency from Dishka container via GraphQL info.
    
    Workaround for dishka-strawberry not supporting Litestar.
    
    Usage:
        action = await get_dependency(info, CreateUserAction)
    """
    request = info.context["request"]
    container = request.app.state.dishka_container
    
    async with container() as request_container:
        return await request_container.get(dependency_type)
```

### Schema Registration

```python
# src/Ship/GraphQL/Schema.py
"""GraphQL schema composition."""

import strawberry
from strawberry.litestar import make_graphql_controller

from src.Containers.AppSection.UserModule.UI.GraphQL.Resolvers import (
    UserQuery,
    UserMutation,
)


@strawberry.type
class Query(UserQuery):
    """Root GraphQL Query type.
    
    Inherit from all module Query classes.
    """
    pass


@strawberry.type
class Mutation(UserMutation):
    """Root GraphQL Mutation type.
    
    Inherit from all module Mutation classes.
    """
    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)

# Litestar GraphQL controller
GraphQLController = make_graphql_controller(
    schema=schema,
    path="/graphql",
)
```

---

## 💻 CLI (Click + Litestar CLIPlugin)

### Принципы:

1. **Click команды интегрируются с Litestar CLIPlugin**
2. **`@with_container` декоратор** для async DI
3. **Rich для красивого вывода** (tables, colors)
4. **Actions для write, Queries для read**

### Реальный пример: Commands

```python
# src/Containers/AppSection/UserModule/UI/CLI/Commands.py
"""CLI commands for UserModule."""

import click
from uuid import UUID
from rich.console import Console
from rich.table import Table
from returns.result import Success, Failure

from src.Ship.CLI.Decorators import with_container
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import (
    ListUsersQuery,
    ListUsersQueryInput,
)
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest

console = Console()


@click.group(name="users")
def users_group() -> None:
    """User management commands.
    
    Usage: litestar users <command>
    """
    pass


@users_group.command(name="create")
@click.option("--email", "-e", required=True, help="User email address")
@click.option("--password", "-p", required=True, help="User password (min 8 chars)")
@click.option("--name", "-n", required=True, help="User display name")
@with_container
async def create_user(container, email: str, password: str, name: str) -> None:
    """Create a new user.
    
    Example:
        litestar users create -e user@example.com -p password123 -n "John Doe"
    """
    action = await container.get(CreateUserAction)
    request = CreateUserRequest(email=email, password=password, name=name)
    result = await action.run(request)
    
    match result:
        case Success(user):
            console.print(f"[green]✓[/green] User created successfully!")
            console.print(f"  ID: {user.id}")
            console.print(f"  Email: {user.email}")
            console.print(f"  Name: {user.name}")
        case Failure(error):
            console.print(f"[red]✗[/red] Error: {error.message}")
            raise SystemExit(1)


@users_group.command(name="get")
@click.argument("user_id", type=click.UUID)
@with_container
async def get_user(container, user_id: UUID) -> None:
    """Get user by ID.
    
    Example:
        litestar users get 550e8400-e29b-41d4-a716-446655440000
    """
    query = await container.get(GetUserQuery)
    user = await query.execute(GetUserQueryInput(user_id=user_id))

    if user is None:
        console.print(f"[red]✗[/red] User not found")
        raise SystemExit(1)

    console.print(f"[bold]User Details[/bold]")
    console.print(f"  ID: {user.id}")
    console.print(f"  Email: {user.email}")
    console.print(f"  Name: {user.name}")
    console.print(f"  Active: {'Yes' if user.is_active else 'No'}")
    console.print(f"  Created: {user.created_at}")


@users_group.command(name="list")
@click.option("--limit", "-l", default=20, help="Maximum number of users")
@click.option("--offset", "-o", default=0, help="Number of users to skip")
@click.option("--active-only", "-a", is_flag=True, help="Show only active users")
@with_container
async def list_users(container, limit: int, offset: int, active_only: bool) -> None:
    """List all users with pagination.
    
    Example:
        litestar users list --limit 10 --active-only
    """
    query = await container.get(ListUsersQuery)
    output = await query.execute(
        ListUsersQueryInput(limit=limit, offset=offset, active_only=active_only)
    )

    table = Table(title="Users")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Email")
    table.add_column("Name")
    table.add_column("Active", justify="center")
    table.add_column("Created")

    for user in output.users:
        table.add_row(
            str(user.id)[:8] + "...",
            user.email,
            user.name,
            "✓" if user.is_active else "✗",
            str(user.created_at)[:19],
        )

    console.print(table)
    console.print(f"\nTotal: {output.total} | Showing: {len(output.users)}")


@users_group.command(name="delete")
@click.argument("user_id", type=click.UUID)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@with_container
async def delete_user(container, user_id: UUID, force: bool) -> None:
    """Delete a user by ID (soft delete).
    
    Example:
        litestar users delete 550e8400-e29b-41d4-a716-446655440000 --force
    """
    if not force:
        if not click.confirm(f"Are you sure you want to delete user {user_id}?"):
            console.print("Cancelled.")
            return

    action = await container.get(DeleteUserAction)
    result = await action.run(user_id)

    match result:
        case Success(_):
            console.print(f"[green]✓[/green] User {user_id} deleted successfully!")
        case Failure(error):
            console.print(f"[red]✗[/red] Error: {error.message}")
            raise SystemExit(1)
```

### @with_container decorator

```python
# src/Ship/CLI/Decorators.py
"""CLI decorators for DI and async support."""

import asyncio
import functools
from typing import Callable, Any

from src.Ship.Providers.AppProvider import get_all_providers
from dishka import make_async_container


def with_container(func: Callable) -> Callable:
    """Decorator for async CLI commands with DI container.
    
    Wraps async function with:
    1. asyncio.run() for async execution
    2. Dishka container initialization
    3. Automatic container cleanup
    
    Usage:
        @users_group.command()
        @with_container
        async def create_user(container, email: str, ...):
            action = await container.get(CreateUserAction)
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        async def _run() -> Any:
            container = make_async_container(*get_all_providers())
            try:
                async with container() as request_container:
                    return await func(request_container, *args, **kwargs)
            finally:
                await container.close()
        
        return asyncio.run(_run())
    
    return wrapper
```

### CLI Registration

```python
# src/Ship/CLI/Main.py
"""CLI entry point."""

from litestar.plugins.cli import CLIPlugin

from src.Containers.AppSection.UserModule.UI.CLI.Commands import users_group
from src.Ship.CLI.MigrationCommands import migration_group

# Litestar CLIPlugin автоматически добавит команды
cli_plugin = CLIPlugin()

# Регистрируем группы команд
cli_commands = [
    users_group,
    migration_group,
]
```

---

## 🔌 WebSocket (Litestar Channels)

### Принципы:

1. **Litestar ChannelsPlugin** для pub/sub
2. **JWT аутентификация** через query param или header
3. **Structured Concurrency** с anyio TaskGroup
4. **Domain Events → Channel publish** через Listeners

### Реальный пример: Handlers

```python
# src/Containers/AppSection/UserModule/UI/WebSocket/Handlers.py
"""WebSocket handlers for UserModule using Litestar Channels."""

import base64
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import UUID

import anyio
from litestar import WebSocket, websocket
from litestar.channels import ChannelsPlugin

from src.Ship.Auth.JWT import get_jwt_service
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import UserResponse


def _authenticate_websocket(socket: WebSocket) -> UUID | None:
    """Authenticate WebSocket connection via JWT token.
    
    Checks for token in:
    1. Query parameter: ?token=<jwt_token>
    2. Sec-WebSocket-Protocol header
    """
    jwt_service = get_jwt_service()
    
    # Check query parameter
    token = socket.query_params.get("token")
    
    # Check header if no query param
    if not token:
        protocol = socket.headers.get("sec-websocket-protocol")
        if protocol:
            parts = protocol.split(",")
            if len(parts) >= 2:
                token = parts[1].strip()
    
    if not token:
        return None
    
    payload = jwt_service.verify_token(token)
    return payload.sub if payload else None


def _decode_channel_message(message: bytes | str) -> dict:
    """Decode message from Litestar Channels.
    
    Handles different formats: JSON, Base64, raw bytes.
    """
    if isinstance(message, bytes):
        message = message.decode("utf-8")
    
    try:
        unwrapped = json.loads(message)
        if isinstance(unwrapped, str):
            decoded = base64.b64decode(unwrapped).decode("utf-8")
            return json.loads(decoded)
        return unwrapped
    except (json.JSONDecodeError, ValueError):
        return {"event": "error", "message": f"Failed to decode: {message}"}


@asynccontextmanager
async def _websocket_lifecycle(
    socket: WebSocket,
    accepted: bool = True,
) -> AsyncGenerator[None, None]:
    """Context manager for WebSocket lifecycle with error handling."""
    try:
        yield
    except Exception as e:
        try:
            if accepted:
                await socket.send_json({"event": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await socket.close()
        except Exception:
            pass


async def _handle_websocket_session(
    socket: WebSocket,
    user_id: UUID,
    channels: ChannelsPlugin,
    query: GetUserQuery,
    is_authenticated: bool = False,
) -> None:
    """Common WebSocket session handler.
    
    Uses anyio TaskGroup for Structured Concurrency:
    - handle_commands: process client commands
    - handle_channel_messages: forward channel updates
    """
    channel_name = f"user:{user_id}"
    
    # Send initial state
    user = await query.execute(GetUserQueryInput(user_id=user_id))
    if not user:
        await socket.send_json({
            "event": "error",
            "message": "User not found",
            "code": "USER_NOT_FOUND",
        })
        await socket.close()
        return
    
    response = UserResponse.from_entity(user)
    await socket.send_json({
        "event": "connected",
        "channel": channel_name,
        "user": response.model_dump(mode="json"),
        "authenticated": is_authenticated,
    })
    
    # Subscribe to channel and handle messages
    async with channels.start_subscription([channel_name]) as subscriber:
        
        async def handle_commands() -> None:
            """Handle incoming commands from client."""
            while True:
                try:
                    message = await socket.receive_json()
                except Exception:
                    return
                
                match message.get("command"):
                    case "refresh":
                        user = await query.execute(GetUserQueryInput(user_id=user_id))
                        if user:
                            response = UserResponse.from_entity(user)
                            await socket.send_json({
                                "event": "user_data",
                                "user": response.model_dump(mode="json"),
                            })
                        else:
                            await socket.send_json({
                                "event": "error",
                                "message": "User not found",
                            })
                    
                    case "ping":
                        await socket.send_json({"event": "pong"})
                    
                    case _:
                        await socket.send_json({
                            "event": "error",
                            "message": f"Unknown command: {message.get('command')}",
                        })
        
        async def handle_channel_messages() -> None:
            """Forward channel messages to WebSocket."""
            async for message in subscriber.iter_events():
                data = _decode_channel_message(message)
                await socket.send_json(data)
        
        # Run both handlers with Structured Concurrency
        async with anyio.create_task_group() as tg:
            tg.start_soon(handle_commands)
            tg.start_soon(handle_channel_messages)


@websocket("/ws/users/{user_id:uuid}")
async def user_updates_handler(
    socket: WebSocket,
    user_id: UUID,
    channels: ChannelsPlugin,
) -> None:
    """Public WebSocket handler for user updates.
    
    Protocol:
    - Connect: Receive current user state
    - Messages: Real-time updates via channel
    - Commands:
        - {"command": "refresh"} - Get latest user data
        - {"command": "ping"} - Keep-alive
    """
    await socket.accept()
    
    async with _websocket_lifecycle(socket):
        container = socket.app.state.dishka_container
        async with container() as request_container:
            query = await request_container.get(GetUserQuery)
            await _handle_websocket_session(
                socket=socket,
                user_id=user_id,
                channels=channels,
                query=query,
                is_authenticated=False,
            )


@websocket("/ws/me")
async def authenticated_user_updates_handler(
    socket: WebSocket,
    channels: ChannelsPlugin,
) -> None:
    """Authenticated WebSocket handler for current user.
    
    Requires JWT token via:
    - Query parameter: ?token=<jwt_token>
    - Sec-WebSocket-Protocol header
    """
    auth_user_id = _authenticate_websocket(socket)
    
    if auth_user_id is None:
        await socket.close(code=4001, reason="Authentication required")
        return
    
    await socket.accept()
    
    async with _websocket_lifecycle(socket):
        container = socket.app.state.dishka_container
        async with container() as request_container:
            query = await request_container.get(GetUserQuery)
            await _handle_websocket_session(
                socket=socket,
                user_id=auth_user_id,
                channels=channels,
                query=query,
                is_authenticated=True,
            )


async def publish_user_update(
    channels: ChannelsPlugin,
    user_id: str,
    event_type: str = "user_updated",
    data: dict | None = None,
) -> None:
    """Helper for publishing user updates from event listeners."""
    message = {
        "event": event_type,
        "user_id": user_id,
        **(data or {}),
    }
    await channels.publish(message, channels=[f"user:{user_id}"])
```

---

## ⚙️ Background Workers (TaskIQ)

### Принципы:

1. **`dishka.integrations.taskiq`** для DI
2. **`@inject` + `FromDishka`** — автоматическая инъекция
3. **`.kiq()` для отправки** задач в очередь
4. **Chaining tasks** — одна задача запускает другую

### Реальный пример: Background Tasks

```python
# src/Containers/AppSection/UserModule/UI/Workers/Tasks.py
"""Background tasks for UserModule."""

from uuid import UUID

from dishka.integrations.taskiq import FromDishka, inject
from returns.result import Success, Failure

from src.Ship.Infrastructure.Workers.Broker import broker
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Tasks.SendWelcomeEmailTask import (
    SendWelcomeEmailTask,
    WelcomeEmailData,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest


@broker.task
@inject
async def send_welcome_email_task(
    email: str,
    name: str,
    task: FromDishka[SendWelcomeEmailTask],
) -> dict:
    """Background task: Send welcome email to new user.
    
    DI: task injected via FromDishka[SendWelcomeEmailTask]
    
    Usage:
        await send_welcome_email_task.kiq(email="user@example.com", name="John")
    """
    result = await task.run(WelcomeEmailData(email=email, name=name))
    
    return {
        "status": "sent" if result else "failed",
        "email": email,
        "name": name,
        "template": "welcome",
    }


@broker.task
@inject
async def create_user_async_task(
    email: str,
    password: str,
    name: str,
    action: FromDishka[CreateUserAction],
) -> dict:
    """Background task: Create user asynchronously.
    
    Useful for bulk imports or delayed user creation.
    Chains to send_welcome_email_task on success.
    """
    request = CreateUserRequest(email=email, password=password, name=name)
    result = await action.run(request)

    match result:
        case Success(user):
            # Schedule welcome email (task chaining)
            await send_welcome_email_task.kiq(email=user.email, name=user.name)
            return {
                "status": "created",
                "user_id": str(user.id),
                "email": user.email,
            }
        case Failure(error):
            return {
                "status": "failed",
                "error": error.message,
                "code": error.code,
            }


@broker.task
async def bulk_create_users_task(users_data: list[dict]) -> dict:
    """Background task: Create multiple users in bulk.
    
    Schedules individual create tasks for each user.
    """
    results = {"created": [], "failed": []}

    for user_data in users_data:
        task = await create_user_async_task.kiq(
            email=user_data["email"],
            password=user_data["password"],
            name=user_data["name"],
        )
        results["created"].append({
            "email": user_data["email"],
            "task_id": str(task.task_id),
        })

    return {
        "status": "scheduled",
        "total": len(users_data),
        "tasks": results,
    }


@broker.task
async def cleanup_inactive_users_task(days_inactive: int = 30) -> dict:
    """Background task: Mark inactive users for cleanup."""
    import logfire
    logfire.info("🧹 Cleanup task running", days_inactive=days_inactive)

    return {
        "status": "completed",
        "days_inactive": days_inactive,
        "users_found": 0,
        "users_cleaned": 0,
    }
```

### Broker Setup

```python
# src/Ship/Infrastructure/Workers/Broker.py
"""TaskIQ broker configuration."""

from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend
from dishka.integrations.taskiq import setup_dishka

from src.Ship.Configs.Settings import get_settings
from src.Ship.Providers.AppProvider import get_all_providers
from dishka import make_async_container

settings = get_settings()

broker = ListQueueBroker(
    url=settings.redis_url,
).with_result_backend(
    RedisAsyncResultBackend(redis_url=settings.redis_url)
)

# Setup Dishka DI for TaskIQ
container = make_async_container(*get_all_providers())
setup_dishka(container, broker)
```

---

## 📊 Сравнение транспортов

| Transport | DI механизм | Error Handling | Streaming |
|-----------|-------------|----------------|-----------|
| **HTTP REST** | `FromDishka[T]` | `@result_handler` → Problem Details | ❌ |
| **GraphQL** | `get_dependency(info, T)` | Payload с `error` полем | ❌ |
| **CLI** | `@with_container` | `match-case` + `SystemExit(1)` | ❌ |
| **WebSocket** | Manual container | `send_json({"event": "error"})` | ✅ |
| **TaskIQ** | `FromDishka[T]` + `@inject` | Return dict с status | ❌ |

---

## 🔗 Один Action — много транспортов

```python
# CreateUserAction используется везде:

# HTTP REST
@post("/")
@result_handler(UserResponse)
async def create_user(action: FromDishka[CreateUserAction]):
    return await action.run(data)

# GraphQL
@strawberry.mutation
async def create_user(self, input: CreateUserInput, info):
    action = await get_dependency(info, CreateUserAction)
    return await action.run(input.to_pydantic())

# CLI
@users_group.command()
@with_container
async def create_user(container, email, password, name):
    action = await container.get(CreateUserAction)
    return await action.run(CreateUserRequest(...))

# TaskIQ
@broker.task
@inject
async def create_user_async(action: FromDishka[CreateUserAction]):
    return await action.run(CreateUserRequest(...))
```

---

<div align="center">

**Следующий раздел:** [10-registration.md](10-registration.md) — Явная регистрация компонентов

</div>
