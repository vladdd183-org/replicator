"""NotificationModule event listeners.

Listeners for handling notification-related domain events.
"""

import logfire
from litestar import Litestar
from litestar.events import listener

from src.Ship.Infrastructure.Channels import publish_to_user_channel


@listener("NotificationCreated")
async def on_notification_created(
    notification_id: str,
    user_id: str,
    notification_type: str,
    title: str,
    app: Litestar | None = None,
    **kwargs,
) -> None:
    """Handle NotificationCreated event.

    Publishes to WebSocket channel for real-time updates.
    """
    logfire.info(
        "🔔 Notification created",
        notification_id=notification_id,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
    )

    publish_to_user_channel(
        app,
        user_id,
        "notification_created",
        {
            "notification_id": notification_id,
            "notification_type": notification_type,
            "title": title,
        },
    )


@listener("NotificationRead")
async def on_notification_read(
    notification_id: str,
    user_id: str,
    app: Litestar | None = None,
    **kwargs,
) -> None:
    """Handle NotificationRead event."""
    logfire.info(
        "✓ Notification read",
        notification_id=notification_id,
        user_id=user_id,
    )

    publish_to_user_channel(
        app,
        user_id,
        "notification_read",
        {"notification_id": notification_id},
    )


@listener("AllNotificationsRead")
async def on_all_notifications_read(
    user_id: str,
    count: int,
    app: Litestar | None = None,
    **kwargs,
) -> None:
    """Handle AllNotificationsRead event."""
    logfire.info(
        "✓ All notifications marked as read",
        user_id=user_id,
        count=count,
    )

    publish_to_user_channel(
        app,
        user_id,
        "all_notifications_read",
        {"count": count},
    )


__all__ = [
    "on_all_notifications_read",
    "on_notification_created",
    "on_notification_read",
]
