"""WebSocket handlers for UserModule using Litestar Channels.

Provides real-time updates for user data with proper pub/sub.
Uses ChannelsPlugin for scalable WebSocket subscriptions.

Channel naming convention:
- user:{user_id} - Updates for specific user

Authentication:
- Pass JWT token as query parameter: ?token=<jwt_token>
- Or use Sec-WebSocket-Protocol header with token

To publish updates from event listeners:
    from litestar.channels import ChannelsPlugin
    
    async def on_user_updated(app, user_id: str, ...):
        channels = app.plugins.get(ChannelsPlugin)
        await channels.publish(
            {"event": "user_updated", "user_id": user_id},
            channels=[f"user:{user_id}"]
        )
"""

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
    
    Args:
        socket: WebSocket connection
        
    Returns:
        User UUID if authenticated, None otherwise
    """
    jwt_service = get_jwt_service()
    token = None
    
    # Check query parameter
    token = socket.query_params.get("token")
    
    # Check Sec-WebSocket-Protocol header if no query param
    if not token:
        protocol = socket.headers.get("sec-websocket-protocol")
        if protocol:
            # Protocol format: "bearer, <token>"
            parts = protocol.split(",")
            if len(parts) >= 2:
                token = parts[1].strip()
    
    if not token:
        return None
    
    # Verify token
    payload = jwt_service.verify_token(token)
    if payload is None:
        return None
    
    return payload.sub


def _decode_channel_message(message: bytes | str) -> dict:
    """Decode message from Litestar Channels.
    
    Litestar Channels may send messages in different formats:
    - JSON string
    - Base64 encoded JSON
    - Raw bytes
    
    Args:
        message: Raw message from channel
        
    Returns:
        Decoded message as dict
    """
    if isinstance(message, bytes):
        message = message.decode("utf-8")
    
    # Try to unwrap JSON string
    try:
        unwrapped = json.loads(message)
        
        if isinstance(unwrapped, str):
            # It's a base64 encoded string, decode it
            decoded = base64.b64decode(unwrapped).decode("utf-8")
            return json.loads(decoded)
        else:
            # Already a dict/object
            return unwrapped
    except (json.JSONDecodeError, ValueError):
        # Return as error message if can't decode
        return {"event": "error", "message": f"Failed to decode: {message}"}


@asynccontextmanager
async def _websocket_lifecycle(
    socket: WebSocket,
    accepted: bool = True,
) -> AsyncGenerator[None, None]:
    """Context manager for WebSocket lifecycle.
    
    Handles error sending and proper socket closing.
    
    Args:
        socket: WebSocket connection
        accepted: Whether socket is already accepted
        
    Yields:
        None - use socket directly in context
    """
    try:
        yield
    except Exception as e:
        try:
            if accepted:
                await socket.send_json({
                    "event": "error",
                    "message": str(e),
                })
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
    
    Handles user subscription, commands, and channel messages.
    Extracted to avoid code duplication between authenticated and public handlers.
    
    Args:
        socket: WebSocket connection
        user_id: User UUID to subscribe to
        channels: Litestar ChannelsPlugin
        query: GetUserQuery for fetching user data
        is_authenticated: Whether this is an authenticated session
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
    initial_message = {
        "event": "connected",
        "channel": channel_name,
        "user": response.model_dump(mode="json"),
    }
    if is_authenticated:
        initial_message["authenticated"] = True
    
    await socket.send_json(initial_message)
    
    # Subscribe to channel and handle messages
    async with channels.start_subscription([channel_name]) as subscriber:
        
        async def handle_commands() -> None:
            """Handle incoming commands from client."""
            while True:
                try:
                    message = await socket.receive_json()
                except Exception:
                    return
                
                command = message.get("command")
                
                match command:
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
                            "message": f"Unknown command: {command}",
                        })
        
        async def handle_channel_messages() -> None:
            """Forward channel messages to WebSocket."""
            async for message in subscriber.iter_events():
                data = _decode_channel_message(message)
                await socket.send_json(data)
        
        async with anyio.create_task_group() as tg:
            tg.start_soon(handle_commands)
            tg.start_soon(handle_channel_messages)


@websocket("/ws/users/{user_id:uuid}")
async def user_updates_handler(
    socket: WebSocket,
    user_id: UUID,
    channels: ChannelsPlugin,
) -> None:
    """WebSocket handler for user updates using Litestar Channels.
    
    Protocol:
    - Connect: Receive current user state, auto-subscribe to channel
    - Messages: Receive real-time updates via channel subscription
    - Commands:
        - {"command": "refresh"} - Get latest user data
        - {"command": "ping"} - Keep-alive ping
    
    Args:
        socket: WebSocket connection
        user_id: User UUID to subscribe to
        channels: Litestar ChannelsPlugin (auto-injected)
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
    """Authenticated WebSocket handler for current user updates.
    
    Requires JWT token via query parameter or Sec-WebSocket-Protocol header.
    Automatically subscribes to the authenticated user's channel.
    
    Protocol:
    - Connect with ?token=<jwt_token>
    - Receive current user state
    - Receive real-time updates via channel subscription
    
    Args:
        socket: WebSocket connection
        channels: Litestar ChannelsPlugin (auto-injected)
    """
    # Authenticate before accepting
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
    """Publish user update to channel.
    
    Helper function for event listeners to publish updates.
    
    Args:
        channels: ChannelsPlugin instance
        user_id: User ID to publish to
        event_type: Event type name
        data: Additional event data
    """
    message = {
        "event": event_type,
        "user_id": user_id,
        **(data or {}),
    }
    await channels.publish(message, channels=[f"user:{user_id}"])
