"""Notification model for Piccolo ORM."""

from piccolo.columns import UUID, Boolean, Text, Timestamptz, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.defaults.uuid import UUID4

from src.Ship.Parents.Model import Model


class Notification(Model):
    """Notification entity.

    Represents a user notification in the system.

    Attributes:
        id: Unique identifier (UUID)
        user_id: User who owns this notification
        notification_type: Type of notification (info, warning, success, error, payment, system)
        title: Notification title
        message: Notification message content
        is_read: Whether the notification has been read
        link: Optional link related to the notification
        created_at: Timestamp when notification was created
        read_at: Timestamp when notification was read (null if unread)
    """

    id = UUID(primary_key=True, default=UUID4())
    user_id = UUID(required=True, index=True)
    notification_type = Varchar(length=50, required=True, default="info")
    title = Varchar(length=255, required=True)
    message = Text(required=False, default="")
    is_read = Boolean(default=False)
    link = Varchar(length=500, required=False, default="")
    created_at = Timestamptz(default=TimestamptzNow())
    read_at = Timestamptz(required=False, null=True, default=None)

    class Meta:
        """Piccolo meta configuration."""

        tablename = "notifications"
