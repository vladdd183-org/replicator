# ⚡ Litestar Features Integration

> **Версия:** 4.1 | **Дата:** Январь 2026

Litestar предоставляет множество встроенных возможностей, которые отлично интегрируются с Hyper-Porto.

---

## 📋 Обзор используемых фич

| Фича | Назначение | Документ |
|------|------------|----------|
| **Events + Listeners** | Domain Events публикация | Этот раздел |
| **Channels** | WebSocket Pub/Sub | Этот раздел |
| **Problem Details** | RFC 9457 ошибки | Этот раздел |
| **Middleware** | Аутентификация, Logging | Этот раздел |
| **Rate Limiting** | Защита от злоупотреблений | Этот раздел |
| **OpenAPI** | Автодокументация | Встроенная |
| **CORS** | Cross-Origin настройки | Встроенная |
| **Guards** | Route protection | Этот раздел |

---

## 📢 Domain Events с litestar.events

### Архитектура Event Flow

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│      Action      │      │    UnitOfWork    │      │    Listeners     │
│                  │      │                  │      │                  │
│ uow.add_event(   │ ──▶  │ _events.append() │ ──▶  │ on_user_created  │
│   UserCreated()  │      │                  │      │ on_user_updated  │
│ )                │      │ commit():        │      │ on_user_deleted  │
│                  │      │   _emit(event)   │      │                  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                  │
                                  ▼
                          ┌──────────────────┐
                          │ litestar.events  │
                          │   EventEmitter   │
                          │                  │
                          │ app.emit(name,   │
                          │          data)   │
                          └──────────────────┘
```

### Domain Events

```python
# src/Containers/AppSection/UserModule/Events.py
"""UserModule domain events."""

from uuid import UUID
from pydantic import Field
from src.Ship.Parents.Event import DomainEvent


class UserCreated(DomainEvent):
    """Event raised when a new user is created."""
    user_id: UUID
    email: str


class UserUpdated(DomainEvent):
    """Event raised when a user is updated."""
    user_id: UUID
    updated_fields: list[str] = Field(default_factory=list)


class UserDeleted(DomainEvent):
    """Event raised when a user is deleted."""
    user_id: UUID
    email: str
```

### Base DomainEvent

```python
# src/Ship/Parents/Event.py
"""Base Domain Event class."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events.
    
    Events are immutable (frozen).
    Published via litestar.events after UoW.commit().
    """
    
    model_config = {"frozen": True}
    
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    @property
    def event_name(self) -> str:
        """Event name for routing (class name)."""
        return self.__class__.__name__
```

### Публикация событий через UoW

```python
# src/Ship/Parents/UnitOfWork.py
"""UnitOfWork with event publishing."""

from dataclasses import dataclass, field
from typing import Callable, Any
from piccolo.engine import engine_finder
from src.Ship.Parents.Event import DomainEvent

EventEmitter = Callable[[str, DomainEvent], None]


@dataclass
class BaseUnitOfWork:
    """Unit of Work with integrated event publishing."""
    
    _emit: EventEmitter | None = None  # Injected from request.app.emit
    _events: list[DomainEvent] = field(default_factory=list)
    _transaction: Any = field(default=None, repr=False)
    
    def add_event(self, event: DomainEvent) -> None:
        """Queue event for publishing after commit."""
        self._events.append(event)
    
    async def commit(self) -> None:
        """Commit transaction and publish events.
        
        Events are published AFTER successful commit.
        This ensures only committed changes trigger events.
        """
        if self._transaction:
            await self._transaction.__aexit__(None, None, None)
            self._transaction = None
        
        # Publish events after successful commit
        if self._emit:
            for event in self._events:
                # Event data is serialized via model_dump()
                self._emit(event.event_name, event.model_dump(mode="json"))
        
        self._events.clear()
```

### Event Listeners

```python
# src/Containers/AppSection/UserModule/Listeners.py
"""User module event listeners."""

import logfire
from litestar import Litestar
from litestar.events import listener
from litestar.channels import ChannelsPlugin


def _publish_to_channel(
    app: Litestar | None,
    user_id: str,
    event_type: str,
    data: dict | None = None,
) -> None:
    """Publish event to user's WebSocket channel.
    
    Note: channels.publish() is non-blocking (synchronous).
    """
    if app is None:
        return
    
    channels = app.plugins.get(ChannelsPlugin)
    if channels:
        message = {"event": event_type, "user_id": user_id, **(data or {})}
        channels.publish(message, channels=[f"user:{user_id}"])


@listener("UserCreated")
async def on_user_created(
    user_id: str,
    email: str,
    app: Litestar | None = None,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle UserCreated event.
    
    Triggered after a new user is successfully created.
    Publishes to WebSocket channel for real-time updates.
    """
    logfire.info(
        "🎉 User created event received",
        user_id=user_id,
        email=email,
        occurred_at=occurred_at,
    )
    
    # Publish to WebSocket channel
    _publish_to_channel(app, user_id, "user_created", {"email": email})
    
    # TODO: Send welcome email via SendWelcomeEmailTask
    # TODO: Create default user settings


@listener("UserDeleted")
async def on_user_deleted(
    user_id: str,
    email: str,
    app: Litestar | None = None,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle UserDeleted event."""
    logfire.info(
        "🗑️ User deleted event received",
        user_id=user_id,
        email=email,
    )
    
    _publish_to_channel(app, user_id, "user_deleted", {"email": email})


@listener("UserUpdated")
async def on_user_updated(
    user_id: str,
    app: Litestar | None = None,
    updated_fields: list[str] | None = None,
    **kwargs,
) -> None:
    """Handle UserUpdated event."""
    logfire.info(
        "✏️ User updated event received",
        user_id=user_id,
        updated_fields=updated_fields,
    )
    
    _publish_to_channel(app, user_id, "user_updated", {"updated_fields": updated_fields})


@listener("UserCreated", "UserDeleted", "UserUpdated")
async def on_user_changed(
    user_id: str,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle any user change event for audit logging.
    
    Multiple event types in one listener for cross-cutting concerns.
    """
    logfire.info(
        "📝 User change audit",
        user_id=user_id,
        occurred_at=occurred_at,
    )
```

### Регистрация Listeners в App

```python
# src/App.py (фрагмент)
from src.Containers.AppSection.UserModule.Listeners import (
    on_user_created,
    on_user_updated,
    on_user_deleted,
    on_user_changed,
)

app = Litestar(
    route_handlers=[...],
    listeners=[
        on_user_created,
        on_user_updated,
        on_user_deleted,
        on_user_changed,
    ],
    ...
)
```

### DI для UoW с EventEmitter

```python
# src/Containers/AppSection/UserModule/Providers.py (фрагмент)
from dishka import Provider, Scope, provide
from litestar import Request


class UserRequestProvider(Provider):
    """Request-scoped providers with event emitter."""
    scope = Scope.REQUEST
    
    @provide
    def user_uow(self, users: UserRepository, request: Request) -> UserUnitOfWork:
        """Create UoW with event emitter from request.app.emit."""
        return UserUnitOfWork(
            users=users,
            _emit=request.app.emit,  # Litestar's EventEmitter
        )
```

---

## 📡 Channels (WebSocket Pub/Sub)

### Настройка ChannelsPlugin

```python
# src/App.py (фрагмент)
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.memory import MemoryChannelsBackend


def _create_channels_plugin() -> ChannelsPlugin:
    """Create ChannelsPlugin with appropriate backend.
    
    Uses MemoryChannelsBackend for development.
    For production with multiple instances, use RedisChannelsBackend.
    """
    settings = get_settings()
    
    # For production with multiple instances:
    # from litestar.channels.backends.redis import RedisChannelsBackend
    # backend = RedisChannelsBackend(url=settings.redis_url)
    
    backend = MemoryChannelsBackend()
    
    return ChannelsPlugin(
        backend=backend,
        arbitrary_channels_allowed=True,  # Allow dynamic channel names like user:{id}
    )


app = Litestar(
    plugins=[
        _create_channels_plugin(),
    ],
    ...
)
```

### Channel Naming Convention

```
user:{user_id}     # Updates for specific user
users:all          # Broadcast to all users
room:{room_id}     # Chat room channel
```

### WebSocket Handler с Channels

```python
# src/Containers/AppSection/UserModule/UI/WebSocket/Handlers.py
from litestar import WebSocket, websocket
from litestar.channels import ChannelsPlugin
import anyio


@websocket("/ws/users/{user_id:uuid}")
async def user_updates_handler(
    socket: WebSocket,
    user_id: UUID,
    channels: ChannelsPlugin,  # Auto-injected!
) -> None:
    """WebSocket handler using Litestar Channels.
    
    Protocol:
    - Connect: Receive current user state
    - Subscribe: Auto-subscribe to user:{user_id} channel
    - Messages: Real-time updates via channel
    """
    await socket.accept()
    
    # Get initial user data
    container = socket.app.state.dishka_container
    async with container() as request_container:
        query = await request_container.get(GetUserQuery)
        user = await query.execute(GetUserQueryInput(user_id=user_id))
        
        if not user:
            await socket.send_json({"event": "error", "message": "User not found"})
            await socket.close()
            return
        
        # Send initial state
        response = UserResponse.from_entity(user)
        await socket.send_json({
            "event": "connected",
            "channel": f"user:{user_id}",
            "user": response.model_dump(mode="json"),
        })
        
        # Subscribe to channel
        async with channels.start_subscription([f"user:{user_id}"]) as subscriber:
            
            async def handle_commands():
                """Handle client commands."""
                while True:
                    try:
                        message = await socket.receive_json()
                    except Exception:
                        return
                    
                    match message.get("command"):
                        case "refresh":
                            # Fetch and send latest user data
                            user = await query.execute(GetUserQueryInput(user_id=user_id))
                            if user:
                                await socket.send_json({
                                    "event": "user_data",
                                    "user": UserResponse.from_entity(user).model_dump(mode="json"),
                                })
                        case "ping":
                            await socket.send_json({"event": "pong"})
            
            async def handle_channel_messages():
                """Forward channel messages to WebSocket."""
                async for message in subscriber.iter_events():
                    data = json.loads(message) if isinstance(message, str) else message
                    await socket.send_json(data)
            
            # Structured Concurrency with anyio
            async with anyio.create_task_group() as tg:
                tg.start_soon(handle_commands)
                tg.start_soon(handle_channel_messages)
```

### Publishing to Channels from Listeners

```python
# src/Containers/AppSection/UserModule/Listeners.py
from litestar.channels import ChannelsPlugin


def _publish_to_channel(
    app: Litestar | None,
    user_id: str,
    event_type: str,
    data: dict | None = None,
) -> None:
    """Publish event to user's WebSocket channel.
    
    Note: channels.publish() is non-blocking (synchronous).
    No await needed!
    """
    if app is None:
        return
    
    channels = app.plugins.get(ChannelsPlugin)
    if channels:
        message = {"event": event_type, "user_id": user_id, **(data or {})}
        channels.publish(message, channels=[f"user:{user_id}"])


@listener("UserCreated")
async def on_user_created(user_id: str, email: str, app: Litestar | None = None, **kwargs):
    # ... logging ...
    _publish_to_channel(app, user_id, "user_created", {"email": email})
```

---

## ⚠️ Problem Details (RFC 9457)

### Настройка Problem Details Plugin

```python
# src/Ship/Exceptions/ProblemDetails.py
"""RFC 9457 Problem Details error handling."""

from litestar.plugins.problem_details import ProblemDetailsPlugin, ProblemDetailsConfig

from src.Ship.Core.Errors import DomainException, BaseError


def _exception_to_status_code(exc: Exception) -> int:
    """Extract HTTP status code from exception."""
    if isinstance(exc, DomainException):
        return exc.error.http_status
    return 500


def _exception_handler(exc: Exception) -> dict:
    """Convert exception to Problem Details format."""
    if isinstance(exc, DomainException):
        return {
            "type": f"urn:error:{exc.error.code.lower()}",
            "title": exc.error.code.replace("_", " ").title(),
            "detail": exc.error.message,
            "status": exc.error.http_status,
        }
    
    return {
        "type": "urn:error:internal-server-error",
        "title": "Internal Server Error",
        "detail": str(exc),
        "status": 500,
    }


def create_problem_details_plugin() -> ProblemDetailsPlugin:
    """Create configured Problem Details plugin."""
    return ProblemDetailsPlugin(
        ProblemDetailsConfig(
            enable_for_all_http_exceptions=True,
            exception_handler=_exception_handler,
            exception_to_status_code=_exception_to_status_code,
        )
    )
```

### Использование в Controller через @result_handler

```python
# src/Ship/Decorators/result_handler.py
from functools import wraps
from returns.result import Success, Failure
from litestar import Response

from src.Ship.Core.Errors import DomainException


def result_handler(response_dto: type | None, *, success_status: int = 200):
    """Convert Result[T, E] to Response or raise DomainException.
    
    Success(value) → Response(dto.from_entity(value), status=success_status)
    Failure(error) → DomainException(error) → Problem Details (RFC 9457)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            match result:
                case Success(value):
                    if response_dto is None:
                        return Response(content=None, status_code=success_status)
                    if hasattr(response_dto, "from_entity"):
                        content = response_dto.from_entity(value)
                    else:
                        content = response_dto.model_validate(value)
                    return Response(content=content, status_code=success_status)
                
                case Failure(error):
                    # Raise DomainException → Problem Details Plugin handles it
                    raise DomainException(error)
        
        return wrapper
    return decorator
```

### Пример ошибки в Problem Details формате

```json
// HTTP 404 Response
{
  "type": "urn:error:user-not-found",
  "title": "User Not Found",
  "detail": "User with id 550e8400-e29b-41d4-a716-446655440000 not found",
  "status": 404
}
```

---

## 🔐 Middleware

### Authentication Middleware

```python
# src/Ship/Auth/Middleware.py
"""Authentication middleware."""

from dataclasses import dataclass
from uuid import UUID
from litestar.middleware import AbstractMiddleware
from litestar import Request, ASGIConnection
from litestar.types import ASGIApp, Scope, Receive, Send

from src.Ship.Auth.JWT import get_jwt_service


@dataclass(frozen=True)
class AuthUser:
    """Authenticated user info."""
    id: UUID
    email: str | None = None


def get_auth_user_from_request(request: Request) -> AuthUser | None:
    """Extract authenticated user from request.
    
    Checks Authorization header for Bearer token.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.removeprefix("Bearer ")
    jwt_service = get_jwt_service()
    
    payload = jwt_service.verify_token(token)
    if payload is None:
        return None
    
    return AuthUser(id=payload.sub)


class AuthenticationMiddleware(AbstractMiddleware):
    """Middleware that extracts auth user and attaches to request."""
    
    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] == "http":
            request = Request(scope)
            auth_user = get_auth_user_from_request(request)
            scope["auth_user"] = auth_user  # Attach to scope
        
        await self.app(scope, receive, send)
```

### Request Logging Middleware

```python
# src/Ship/Infrastructure/Telemetry/RequestLoggingMiddleware.py
"""Request logging middleware with Logfire."""

import time
import logfire
from litestar.middleware import AbstractMiddleware
from litestar import Request
from litestar.types import Scope, Receive, Send


class RequestLoggingMiddleware(AbstractMiddleware):
    """Log all HTTP requests with timing."""
    
    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope)
        start_time = time.perf_counter()
        
        # Capture response status
        response_status = 500
        
        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logfire.info(
                "{method} {path} → {status} ({duration:.0f}ms)",
                method=request.method,
                path=request.url.path,
                status=response_status,
                duration=duration_ms,
            )
```

### Middleware Registration

```python
# src/App.py (фрагмент)
from src.Ship.Auth.Middleware import AuthenticationMiddleware
from src.Ship.Infrastructure.Telemetry.RequestLoggingMiddleware import RequestLoggingMiddleware

app = Litestar(
    middleware=[RequestLoggingMiddleware, AuthenticationMiddleware],
    ...
)
```

---

## 🛡️ Guards (Route Protection)

### Auth Guards

```python
# src/Ship/Auth/Guards.py
"""Route protection guards."""

from litestar import Request
from litestar.exceptions import NotAuthorizedException
from litestar.connection import ASGIConnection

from src.Ship.Auth.Middleware import AuthUser, get_auth_user_from_request


async def auth_guard(request: Request) -> AuthUser:
    """Guard that requires authentication.
    
    Use as dependency for protected routes:
        @get("/protected", dependencies={"auth_user": auth_guard})
        async def protected(auth_user: AuthUser):
            ...
    
    Raises:
        NotAuthorizedException: If no valid token
    """
    auth_user = get_auth_user_from_request(request)
    if auth_user is None:
        raise NotAuthorizedException(detail="Authentication required")
    return auth_user


async def optional_auth_guard(request: Request) -> AuthUser | None:
    """Guard that optionally extracts auth user.
    
    Returns None if no valid token instead of raising.
    Use for routes that work with or without auth.
    """
    return get_auth_user_from_request(request)
```

### Использование Guards

```python
# src/Containers/AppSection/UserModule/UI/API/Controllers/AuthController.py
from src.Ship.Auth.Guards import auth_guard
from src.Ship.Auth.Middleware import AuthUser


class AuthController(Controller):
    path = "/auth"
    
    @get("/me", dependencies={"auth_user": auth_guard})
    async def get_current_user(
        self,
        auth_user: AuthUser,  # Injected by guard
        query: FromDishka[GetUserQuery],
    ) -> UserResponse:
        """Protected endpoint: requires valid JWT."""
        user = await query.execute(GetUserQueryInput(user_id=auth_user.id))
        if user is None:
            raise UserNotFoundError(user_id=auth_user.id).to_exception()
        return UserResponse.from_entity(user)
    
    @post("/change-password", dependencies={"auth_user": auth_guard})
    @result_handler(None, success_status=204)
    async def change_password(
        self,
        data: ChangePasswordRequest,
        auth_user: AuthUser,
        action: FromDishka[ChangePasswordAction],
    ):
        """Protected endpoint: change password for current user."""
        return await action.run(auth_user.id, data)
```

---

## 🚦 Rate Limiting

Litestar предоставляет встроенный Rate Limiting middleware на основе IETF RateLimit draft specification.

### Конфигурация

```python
# src/Ship/Infrastructure/RateLimiting.py
from litestar.middleware.rate_limit import RateLimitConfig


def get_client_ip(request: "Request") -> str:
    """Extract client IP for rate limiting."""
    # Check X-Forwarded-For header (from reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    client = request.client
    return client.host if client else "unknown"


# Pre-configured rate limits
default_rate_limit = RateLimitConfig(
    rate_limit=("minute", 100),  # 100 req/min
    exclude=["/health", "/api/docs"],
    check_throttle_handler=get_client_ip,
)

auth_rate_limit = RateLimitConfig(
    rate_limit=("minute", 10),  # 10 req/min - strict for auth
    check_throttle_handler=get_client_ip,
)

strict_rate_limit = RateLimitConfig(
    rate_limit=("minute", 3),  # 3 req/min - very strict
    check_throttle_handler=get_client_ip,
)
```

### Использование: Глобальный Rate Limit

```python
# src/App.py
from src.Ship.Infrastructure.RateLimiting import default_rate_limit

app = Litestar(
    middleware=[default_rate_limit.middleware],  # Global rate limit
    ...
)
```

### Использование: Rate Limit для конкретного роута

```python
# src/Containers/AppSection/UserModule/UI/API/Controllers/AuthController.py
from src.Ship.Infrastructure.RateLimiting import auth_rate_limit, strict_rate_limit


class AuthController(Controller):
    path = "/auth"
    tags = ["Authentication"]
    
    @post(
        "/login",
        middleware=[auth_rate_limit.middleware],  # 10 req/min
    )
    async def login(self, data: LoginRequest) -> AuthResponse:
        """Rate Limited: 10 requests per minute per IP."""
        ...
    
    @post(
        "/change-password",
        middleware=[strict_rate_limit.middleware],  # 3 req/min
        dependencies={"current_user": auth_guard},
    )
    async def change_password(self, data: ChangePasswordRequest) -> Response:
        """Rate Limited: 3 requests per minute per IP."""
        ...
```

### Custom Rate Limit (фабрика)

```python
from src.Ship.Infrastructure.RateLimiting import create_rate_limit_config


# 50 requests per hour for expensive reports
reports_rate_limit = create_rate_limit_config(
    rate_limit=("hour", 50),
    exclude=["/health"],
)

@get("/api/reports/export", middleware=[reports_rate_limit.middleware])
async def export_report() -> StreamingResponse:
    """Rate Limited: 50 requests per hour."""
    ...
```

### Per-User Rate Limiting

```python
from src.Ship.Infrastructure.RateLimiting import user_rate_limit


# 200 req/min per authenticated user (not IP)
@get("/api/data", middleware=[user_rate_limit.middleware])
async def get_data(current_user: AuthUser) -> dict:
    """Rate Limited: 200 req/min per user ID."""
    ...
```

### Response Headers (IETF spec)

При каждом запросе возвращаются заголовки:

```http
HTTP/1.1 200 OK
RateLimit-Limit: 100
RateLimit-Remaining: 95
RateLimit-Reset: 45

{"data": "..."}
```

При превышении лимита:

```http
HTTP/1.1 429 Too Many Requests
RateLimit-Limit: 100
RateLimit-Remaining: 0
RateLimit-Reset: 30
Retry-After: 30

{"status_code": 429, "detail": "Rate limit exceeded"}
```

### Доступные Time Units

| Unit | Описание | Пример |
|------|----------|--------|
| `"second"` | Запросов в секунду | `("second", 5)` — 5 req/sec |
| `"minute"` | Запросов в минуту | `("minute", 100)` — 100 req/min |
| `"hour"` | Запросов в час | `("hour", 1000)` — 1000 req/hour |
| `"day"` | Запросов в день | `("day", 10000)` — 10000 req/day |

### Pre-configured Limits (готовые)

| Конфиг | Лимит | Назначение |
|--------|-------|------------|
| `default_rate_limit` | 100/min | Общие API endpoints |
| `auth_rate_limit` | 10/min | Login, registration |
| `strict_rate_limit` | 3/min | Password reset, exports |
| `relaxed_rate_limit` | 1000/min | Search autocomplete |
| `burst_rate_limit` | 5/sec | Prevent burst attacks |
| `user_rate_limit` | 200/min | Per-user (authenticated) |
| `api_key_rate_limit` | 500/min | API key-based |

---

## 📚 OpenAPI Configuration

```python
# src/App.py (фрагмент)
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin

app = Litestar(
    openapi_config=OpenAPIConfig(
        title=settings.app_name,
        version=settings.app_version,
        path="/api/docs",
        render_plugins=[ScalarRenderPlugin()],  # Beautiful UI
    ),
    ...
)
```

### Controller Tags для группировки

```python
class UserController(Controller):
    path = "/users"
    tags = ["Users"]  # OpenAPI grouping


class AuthController(Controller):
    path = "/auth"
    tags = ["Authentication"]
```

---

## 🌐 CORS Configuration

```python
# src/App.py (фрагмент)
from litestar.config.cors import CORSConfig

app = Litestar(
    cors_config=CORSConfig(
        allow_origins=settings.cors_allow_origins,      # ["*"] or specific origins
        allow_credentials=settings.cors_allow_credentials,  # True for cookies
        allow_methods=settings.cors_allow_methods,      # ["GET", "POST", "PUT", "DELETE"]
        allow_headers=settings.cors_allow_headers,      # ["*"] or specific headers
    ),
    ...
)
```

---

## 🔄 Lifespan Management

```python
# src/App.py (фрагмент)
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from litestar import Litestar


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """Application lifespan handler.
    
    Manages startup and shutdown:
    - Startup: Initialize resources
    - Shutdown: Cleanup (close DI container, connections, etc.)
    """
    # Startup
    # ...
    
    yield  # Application runs here
    
    # Shutdown
    if hasattr(app.state, "dishka_container"):
        await app.state.dishka_container.close()


app = Litestar(
    lifespan=[lifespan],
    ...
)
```

---

## 📊 Полная App.py конфигурация

```python
# src/App.py
"""Main Litestar application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.memory import MemoryChannelsBackend
from strawberry.litestar import make_graphql_controller

from src.Ship.Configs import get_settings
from src.Ship.Exceptions.ProblemDetails import create_problem_details_plugin
from src.Ship.Providers import get_all_providers
from src.Ship.GraphQL.Schema import schema, get_graphql_context
from src.Ship.Auth.Middleware import AuthenticationMiddleware
from src.Ship.Infrastructure.Telemetry import setup_logfire
from src.Ship.Infrastructure.Telemetry.RequestLoggingMiddleware import RequestLoggingMiddleware
from src.Ship.Infrastructure.Cache import setup_cache

# Routers
from src.Containers.AppSection.UserModule import user_router
from src.Containers.AppSection.UserModule.UI.WebSocket.Handlers import (
    user_updates_handler,
    authenticated_user_updates_handler,
)
from src.Ship.Infrastructure.HealthCheck import health_controller

# Listeners
from src.Containers.AppSection.UserModule.Listeners import (
    on_user_created,
    on_user_updated,
    on_user_deleted,
    on_user_changed,
)


def _create_channels_plugin() -> ChannelsPlugin:
    backend = MemoryChannelsBackend()
    return ChannelsPlugin(
        backend=backend,
        arbitrary_channels_allowed=True,
    )


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    yield
    if hasattr(app.state, "dishka_container"):
        await app.state.dishka_container.close()


def create_app() -> Litestar:
    settings = get_settings()
    container = make_async_container(*get_all_providers())
    
    GraphQLController = make_graphql_controller(
        schema,
        path="/graphql",
        context_getter=get_graphql_context,
        graphql_ide="graphiql",
    )
    
    app = Litestar(
        route_handlers=[
            health_controller,
            user_router,
            GraphQLController,
            user_updates_handler,
            authenticated_user_updates_handler,
        ],
        listeners=[
            on_user_created,
            on_user_updated,
            on_user_deleted,
            on_user_changed,
        ],
        plugins=[
            _create_channels_plugin(),
            create_problem_details_plugin(),
        ],
        cors_config=CORSConfig(
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        ),
        openapi_config=OpenAPIConfig(
            title=settings.app_name,
            version=settings.app_version,
            path="/api/docs",
            render_plugins=[ScalarRenderPlugin()],
        ),
        middleware=[RequestLoggingMiddleware, AuthenticationMiddleware],
        lifespan=[lifespan],
        debug=settings.app_debug,
    )
    
    setup_dishka(container, app)
    setup_logfire(app)
    setup_cache()
    
    return app


app = create_app()
```

---

<div align="center">

**Следующий раздел:** [12-reducing-boilerplate.md](12-reducing-boilerplate.md) — Паттерны сокращения бойлерплейта

</div>
