"""NotificationModule - User notification system.

This module handles user notifications for the application.
Notifications can be created from various events (payments, system, etc.)
and delivered through different channels.

Components:
- Models: Notification (Piccolo Table)
- Actions: CreateNotificationAction, MarkAsReadAction, MarkAllAsReadAction
- Tasks: SendNotificationTask
- Events: NotificationCreated, NotificationRead
- Queries: GetUserNotificationsQuery, CountUnreadQuery
"""

from src.Containers.AppSection.NotificationModule.UI.API.Routes import notification_router

__all__ = ["notification_router"]



