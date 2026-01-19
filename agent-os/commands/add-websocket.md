# 🎮 Command: /add-websocket

> Создание WebSocket handler (Litestar).

---

## Синтаксис

```
/add-websocket <HandlerName> [в <Module>] [с channels]
```

## Параметры

| Параметр | Обязательный | Пример |
|----------|--------------|--------|
| HandlerName | ✅ | `Chat`, `Notifications`, `LiveFeed` |
| Module | ❌ | `UserModule` |
| с channels | ❌ | Использовать Litestar Channels для pub/sub |

---

## Ключевые правила

| Правило | Описание |
|---------|----------|
| **Framework** | Litestar WebSocket |
| **Location** | `UI/WebSocket/Handlers.py` |
| **Channels** | Litestar Channels для pub/sub |
| **Auth** | Через middleware или on_connect |
| **DI** | Через `FromDishka[T]` |

---

## Примеры

### Базовый
```
/add-websocket Chat в UserModule
```
→ Создаст chat WebSocket handler

### С pub/sub
```
/add-websocket Notifications в NotificationModule с channels
```
→ Создаст handler с Litestar Channels

---

## Что создаётся

### 1. Basic WebSocket Handler

`UI/WebSocket/Handlers.py`:

```python
"""WebSocket handlers for [Module]."""

from litestar import WebSocket
from litestar.handlers import websocket


@websocket("/ws/[path]")
async def handler_name(socket: WebSocket) -> None:
    """WebSocket handler for [description]."""
    await socket.accept()
    
    try:
        while True:
            data = await socket.receive_json()
            # Process message
            await socket.send_json({"status": "received"})
    except Exception:
        pass
    finally:
        await socket.close()
```

### 2. Chat Handler с Channels

```python
"""WebSocket handlers for UserModule."""

from uuid import UUID

from litestar import WebSocket
from litestar.handlers import websocket
from litestar.channels import ChannelsPlugin


@websocket("/ws/chat/{room_id:uuid}")
async def chat_handler(
    socket: WebSocket,
    room_id: UUID,
    channels: ChannelsPlugin,
) -> None:
    """Real-time chat WebSocket handler.
    
    Protocol:
    - Connect: Join room channel
    - Send: {"type": "message", "content": "..."}
    - Receive: {"type": "message", "from": "user_id", "content": "..."}
    """
    await socket.accept()
    
    # Subscribe to room channel
    room_channel = f"chat:{room_id}"
    
    async with channels.start_subscription([room_channel]) as subscriber:
        try:
            # Handle incoming messages
            async for message in subscriber.iter_events():
                if message.get("type") == "message":
                    await socket.send_json(message)
        except Exception:
            pass
        finally:
            await socket.close()


@websocket("/ws/chat/{room_id:uuid}/send")
async def chat_send_handler(
    socket: WebSocket,
    room_id: UUID,
    channels: ChannelsPlugin,
) -> None:
    """WebSocket for sending chat messages."""
    await socket.accept()
    
    room_channel = f"chat:{room_id}"
    user_id = socket.scope.get("user", {}).get("id", "anonymous")
    
    try:
        while True:
            data = await socket.receive_json()
            
            if data.get("type") == "message":
                # Broadcast to room
                await channels.publish(
                    {
                        "type": "message",
                        "from": str(user_id),
                        "content": data.get("content", ""),
                        "room_id": str(room_id),
                    },
                    channels=[room_channel],
                )
                await socket.send_json({"status": "sent"})
    except Exception:
        pass
    finally:
        await socket.close()
```

### 3. Notifications Handler

```python
"""WebSocket handlers for NotificationModule."""

from uuid import UUID

from litestar import WebSocket
from litestar.handlers import websocket
from litestar.channels import ChannelsPlugin
from dishka.integrations.litestar import FromDishka

from src.Containers.AppSection.NotificationModule.Queries.GetUnreadQuery import (
    GetUnreadQuery,
    GetUnreadQueryInput,
)


@websocket("/ws/notifications")
async def notifications_handler(
    socket: WebSocket,
    channels: ChannelsPlugin,
) -> None:
    """Real-time notifications WebSocket.
    
    Features:
    - Receives new notifications in real-time
    - User-specific channel based on auth
    """
    await socket.accept()
    
    # Get user from auth
    user = socket.scope.get("user")
    if not user:
        await socket.send_json({"error": "Unauthorized"})
        await socket.close(code=4001)
        return
    
    user_channel = f"notifications:{user['id']}"
    
    async with channels.start_subscription([user_channel]) as subscriber:
        try:
            async for notification in subscriber.iter_events():
                await socket.send_json(notification)
        except Exception:
            pass
        finally:
            await socket.close()


@websocket("/ws/notifications/subscribe")
async def notifications_subscribe_handler(
    socket: WebSocket,
    channels: ChannelsPlugin,
    get_unread: FromDishka[GetUnreadQuery],
) -> None:
    """Subscribe to notifications with initial unread count."""
    await socket.accept()
    
    user = socket.scope.get("user")
    if not user:
        await socket.send_json({"error": "Unauthorized"})
        await socket.close(code=4001)
        return
    
    user_id = UUID(user["id"])
    user_channel = f"notifications:{user_id}"
    
    # Send initial unread count
    unread = await get_unread.execute(GetUnreadQueryInput(user_id=user_id))
    await socket.send_json({
        "type": "init",
        "unread_count": unread.count,
    })
    
    # Subscribe to real-time updates
    async with channels.start_subscription([user_channel]) as subscriber:
        try:
            async for notification in subscriber.iter_events():
                await socket.send_json({
                    "type": "notification",
                    "data": notification,
                })
        except Exception:
            pass
        finally:
            await socket.close()
```

---

## Публикация в Channels из Action

```python
# In Action
from litestar.channels import ChannelsPlugin


class CreateOrderAction(Action[CreateOrderRequest, Order, OrderError]):
    def __init__(
        self,
        uow: OrderUnitOfWork,
        channels: ChannelsPlugin,
    ) -> None:
        self.uow = uow
        self.channels = channels
    
    async def run(self, data: CreateOrderRequest) -> Result[Order, OrderError]:
        async with self.uow:
            order = Order(...)
            await self.uow.orders.add(order)
            await self.uow.commit()
        
        # Publish to WebSocket channels
        await self.channels.publish(
            {
                "type": "order_created",
                "order_id": str(order.id),
                "total": str(order.total),
            },
            channels=["stats:orders", "activity:feed"],
        )
        
        # Notify specific user
        await self.channels.publish(
            {
                "type": "order_confirmation",
                "order_id": str(order.id),
            },
            channels=[f"notifications:{data.user_id}"],
        )
        
        return Success(order)
```

---

## WebSocket с Authentication

```python
# Middleware approach
from litestar import WebSocket
from litestar.middleware import AbstractMiddleware


class WebSocketAuthMiddleware(AbstractMiddleware):
    """Authenticate WebSocket connections."""
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            # Extract token from query params or headers
            token = scope.get("query_string", b"").decode()
            
            if token:
                try:
                    user = decode_jwt(token)
                    scope["user"] = user
                except Exception:
                    pass
        
        await self.app(scope, receive, send)
```

```python
# Or in handler
@websocket("/ws/protected")
async def protected_handler(socket: WebSocket) -> None:
    """Protected WebSocket requiring auth."""
    # Check auth before accepting
    token = socket.query_params.get("token")
    
    if not token:
        await socket.close(code=4001, reason="Unauthorized")
        return
    
    try:
        user = decode_jwt(token)
    except Exception:
        await socket.close(code=4001, reason="Invalid token")
        return
    
    await socket.accept()
    # ... handle authenticated connection
```

---

## Конфигурация Channels в App.py

```python
# In App.py
from litestar import Litestar
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.memory import MemoryChannelsBackend
# Or for production:
# from litestar.channels.backends.redis import RedisChannelsBackend

from src.Containers.AppSection.UserModule.UI.WebSocket.Handlers import (
    chat_handler,
    notifications_handler,
)


channels_plugin = ChannelsPlugin(
    backend=MemoryChannelsBackend(),
    # For production:
    # backend=RedisChannelsBackend(url="redis://localhost:6379"),
    arbitrary_channels_allowed=True,
)

app = Litestar(
    route_handlers=[
        chat_handler,
        notifications_handler,
    ],
    plugins=[channels_plugin],
)
```

---

## Message Protocol

```python
from enum import Enum
from pydantic import BaseModel


class MessageType(str, Enum):
    MESSAGE = "message"
    NOTIFICATION = "notification"
    STATUS = "status"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class WSMessage(BaseModel):
    type: MessageType
    data: dict | None = None


class WSError(BaseModel):
    type: MessageType = MessageType.ERROR
    code: str
    message: str
```

---

## Структура файлов

```
src/Containers/[Section]/[Module]/
└── UI/
    └── WebSocket/
        ├── __init__.py
        └── Handlers.py       # WebSocket handlers

src/
└── App.py                    # Channels plugin + handler registration
```

---

## Действия после создания

1. ✅ Создать `UI/WebSocket/Handlers.py`
2. ✅ Использовать `@websocket` декоратор
3. ✅ Обработать `socket.accept()` / `socket.close()`
4. ✅ Реализовать error handling с try/finally
5. ✅ Добавить authentication если нужно
6. ✅ Настроить Channels plugin в App.py
7. ✅ Зарегистрировать handlers в route_handlers
8. ✅ Документировать message protocol

---

## Типичные ошибки

| ❌ Неправильно | ✅ Правильно |
|----------------|-------------|
| Забыть `socket.accept()` | Всегда accept перед отправкой |
| Нет `finally: socket.close()` | Всегда close в finally блоке |
| Блокирующий sync код | Только async операции |
| Нет auth проверки | Валидировать auth перед accepting |
| Нет error handling | Wrap в try/except |

---

## Связанные ресурсы

- **Template:** `../templates/websocket-handler.py.template`
- **Docs:** `docs/09-transports.md` (WebSocket секция)
- **Docs:** `docs/11-litestar-features.md` (Channels)
