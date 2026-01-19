"""NotificationModule schemas."""

from src.Containers.AppSection.NotificationModule.Data.Schemas.Requests import (
    CreateNotificationRequest,
    MarkAsReadRequest,
)
from src.Containers.AppSection.NotificationModule.Data.Schemas.Responses import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
)

__all__ = [
    "CreateNotificationRequest",
    "MarkAsReadRequest",
    "NotificationResponse",
    "NotificationListResponse",
    "UnreadCountResponse",
]



