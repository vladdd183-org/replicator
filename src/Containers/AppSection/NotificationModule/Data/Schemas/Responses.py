"""NotificationModule response DTOs.

Response DTOs inherit from EntitySchema for automatic conversion.
"""

from datetime import datetime
from uuid import UUID

from src.Ship.Core.BaseSchema import EntitySchema


class NotificationResponse(EntitySchema):
    """Response DTO for Notification entity.

    Attributes:
        id: Notification UUID
        user_id: User who owns the notification
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        is_read: Whether notification has been read
        link: Optional link
        created_at: When notification was created
        read_at: When notification was read (null if unread)
    """

    id: UUID
    user_id: UUID
    notification_type: str
    title: str
    message: str
    is_read: bool
    link: str
    created_at: datetime
    read_at: datetime | None = None


class NotificationListResponse(EntitySchema):
    """Response DTO for list of notifications.

    Attributes:
        notifications: List of notification responses
        total: Total count of notifications
        unread_count: Count of unread notifications
        limit: Page size
        offset: Page offset
    """

    notifications: list[NotificationResponse]
    total: int
    unread_count: int
    limit: int
    offset: int


class UnreadCountResponse(EntitySchema):
    """Response DTO for unread notification count.

    Attributes:
        count: Number of unread notifications
    """

    count: int
