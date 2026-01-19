"""Notification model."""

from enum import Enum

from piccolo.columns import UUID, Boolean, ForeignKey, Text, Timestamptz, Varchar, JSON

from src.Ship.Parents import Model


class NotificationType(Enum):
    """Notification types."""
    
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(Enum):
    """Notification statuses."""
    
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class Notification(Model):
    """Notification model."""

    id = UUID(primary_key=True)
    user_id = ForeignKey("User", required=True)
    type = Varchar(length=20, required=True)
    status = Varchar(length=20, default=NotificationStatus.PENDING.value)
    subject = Varchar(length=255, required=True)
    body = Text(required=True)
    metadata = JSON(default={})  # Дополнительные данные (например, для push уведомлений)
    scheduled_at = Timestamptz(null=True)  # Для отложенных уведомлений
    sent_at = Timestamptz(null=True)
    delivered_at = Timestamptz(null=True)
    read_at = Timestamptz(null=True)
    created_at = Timestamptz()
    updated_at = Timestamptz()
