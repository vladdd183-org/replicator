"""Notification module routes configuration.

Uses DishkaRouter for automatic dependency injection.
"""

from dishka.integrations.litestar import DishkaRouter

from src.Containers.AppSection.NotificationModule.UI.API.Controllers.NotificationController import (
    NotificationController,
)


# Notification router - groups all notification-related endpoints under /api/v1
notification_router = DishkaRouter(
    path="/api/v1",
    route_handlers=[
        NotificationController,
    ],
)



