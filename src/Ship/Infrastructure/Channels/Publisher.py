"""WebSocket channel publisher utility.

Provides a single source of truth for publishing events to WebSocket channels.
Used by event listeners across modules to send real-time updates to clients.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from litestar import Litestar


def publish_to_user_channel(
    app: "Litestar | None",
    user_id: str,
    event_type: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Publish event to user's WebSocket channel.
    
    This is the single source of truth for WebSocket publishing.
    Use this function instead of accessing ChannelsPlugin directly.
    
    Note: channels.publish() is non-blocking (synchronous).
    
    Args:
        app: Litestar application instance (may be None in CLI context)
        user_id: User ID for channel name (channel will be "user:{user_id}")
        event_type: Event type name for client to handle
        data: Additional event data to include in message
        
    Example:
        publish_to_user_channel(
            app,
            user_id="123",
            event_type="notification_created",
            data={"notification_id": "456", "title": "New message"},
        )
        
        # Client receives:
        # {"event": "notification_created", "user_id": "123", "notification_id": "456", "title": "New message"}
    """
    if app is None:
        return
    
    from litestar.channels import ChannelsPlugin
    
    channels = app.plugins.get(ChannelsPlugin)
    if channels:
        message = {"event": event_type, "user_id": user_id, **(data or {})}
        channels.publish(message, channels=[f"user:{user_id}"])


def publish_to_channel(
    app: "Litestar | None",
    channel_name: str,
    event_type: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Publish event to arbitrary WebSocket channel.
    
    Use this for non-user-specific channels (e.g., admin broadcasts, topics).
    
    Args:
        app: Litestar application instance
        channel_name: Full channel name (e.g., "admin", "topic:news")
        event_type: Event type name
        data: Additional event data
    """
    if app is None:
        return
    
    from litestar.channels import ChannelsPlugin
    
    channels = app.plugins.get(ChannelsPlugin)
    if channels:
        message = {"event": event_type, **(data or {})}
        channels.publish(message, channels=[channel_name])


__all__ = ["publish_to_user_channel", "publish_to_channel"]



