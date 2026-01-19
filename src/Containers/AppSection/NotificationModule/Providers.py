"""Notification module dependency injection providers.

Consolidated providers with clear scope separation.
"""

from dishka import Provider, Scope, provide
from litestar import Request

from src.Containers.AppSection.NotificationModule.Actions.CreateNotificationAction import (
    CreateNotificationAction,
)
from src.Containers.AppSection.NotificationModule.Actions.MarkAllAsReadAction import (
    MarkAllAsReadAction,
)
from src.Containers.AppSection.NotificationModule.Actions.MarkAsReadAction import (
    MarkAsReadAction,
)
from src.Containers.AppSection.NotificationModule.Data.Repositories.NotificationRepository import (
    NotificationRepository,
)
from src.Containers.AppSection.NotificationModule.Data.UnitOfWork import NotificationUnitOfWork
from src.Containers.AppSection.NotificationModule.Queries.CountUnreadQuery import (
    CountUnreadQuery,
)
from src.Containers.AppSection.NotificationModule.Queries.GetUserNotificationsQuery import (
    GetUserNotificationsQuery,
)


class _BaseNotificationRequestProvider(Provider):
    """Base provider with common REQUEST scope dependencies.

    Contains all dependencies shared between HTTP and CLI contexts.
    """

    scope = Scope.REQUEST

    # Data Layer
    notification_repository = provide(NotificationRepository)

    # Queries - CQRS read side
    get_user_notifications_query = provide(GetUserNotificationsQuery)
    count_unread_query = provide(CountUnreadQuery)

    # Actions - CQRS write side
    create_notification_action = provide(CreateNotificationAction)
    mark_as_read_action = provide(MarkAsReadAction)
    mark_all_as_read_action = provide(MarkAllAsReadAction)


class NotificationRequestProvider(_BaseNotificationRequestProvider):
    """HTTP request-scoped provider for NotificationModule.

    Extends base provider with UnitOfWork that has event emitter.
    """

    @provide
    def provide_notification_uow(self, request: Request) -> NotificationUnitOfWork:
        """Provide NotificationUnitOfWork with event emitter from request."""
        return NotificationUnitOfWork(_emit=request.app.emit, _app=request.app)


class NotificationCLIProvider(_BaseNotificationRequestProvider):
    """CLI-specific provider for NotificationModule.

    Extends base provider with UnitOfWork without event emitter.
    """

    @provide
    def provide_notification_uow(self) -> NotificationUnitOfWork:
        """Provide NotificationUnitOfWork without event emitter for CLI."""
        return NotificationUnitOfWork(_emit=None, _app=None)
