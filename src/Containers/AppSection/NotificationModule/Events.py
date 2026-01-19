"""NotificationModule domain events.

Events for tracking notification operations.
"""

from uuid import UUID

from src.Ship.Parents.Event import DomainEvent


class NotificationCreated(DomainEvent):
    """Event raised when a notification is created.

    Attributes:
        notification_id: Unique notification identifier
        user_id: User who received the notification
        notification_type: Type of notification
        title: Notification title
        message: Notification message content
    """

    notification_id: UUID
    user_id: UUID
    notification_type: str
    title: str
    message: str


class NotificationRead(DomainEvent):
    """Event raised when a notification is marked as read.

    Attributes:
        notification_id: Notification identifier
        user_id: User who read the notification
    """

    notification_id: UUID
    user_id: UUID


class NotificationDeleted(DomainEvent):
    """Event raised when a notification is deleted.

    Attributes:
        notification_id: Notification identifier
        user_id: User whose notification was deleted
    """

    notification_id: UUID
    user_id: UUID


class AllNotificationsRead(DomainEvent):
    """Event raised when all notifications are marked as read.

    Attributes:
        user_id: User who marked all as read
        count: Number of notifications marked as read
    """

    user_id: UUID
    count: int


__all__ = [
    "AllNotificationsRead",
    "NotificationCreated",
    "NotificationDeleted",
    "NotificationRead",
]
