"""NotificationModule schemas."""

from src.Containers.AppSection.NotificationModule.Data.Schemas.Requests import (
    CreateNotificationRequest,
    MarkAsReadRequest,
)
from src.Containers.AppSection.NotificationModule.Data.Schemas.Responses import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)

__all__ = [
    "CreateNotificationRequest",
    "MarkAsReadRequest",
    "NotificationListResponse",
    "NotificationResponse",
    "UnreadCountResponse",
]
