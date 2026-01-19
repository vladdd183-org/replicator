"""NotificationModule queries."""

from src.Containers.AppSection.NotificationModule.Queries.GetUserNotificationsQuery import (
    GetUserNotificationsQuery,
    GetUserNotificationsInput,
    GetUserNotificationsOutput,
)
from src.Containers.AppSection.NotificationModule.Queries.CountUnreadQuery import (
    CountUnreadQuery,
)

__all__ = [
    "GetUserNotificationsQuery",
    "GetUserNotificationsInput",
    "GetUserNotificationsOutput",
    "CountUnreadQuery",
]



