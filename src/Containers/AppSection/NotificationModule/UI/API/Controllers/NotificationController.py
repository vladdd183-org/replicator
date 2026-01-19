"""Notification HTTP API Controller.

Uses DishkaRouter - no need for @inject decorator.
"""

from uuid import UUID

from dishka.integrations.litestar import FromDishka
from litestar import Controller, get, patch, post
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from returns.result import Result

from src.Containers.AppSection.NotificationModule.Actions.CreateNotificationAction import (
    CreateNotificationAction,
)
from src.Containers.AppSection.NotificationModule.Actions.MarkAllAsReadAction import (
    MarkAllAsReadAction,
    MarkAllAsReadResult,
)
from src.Containers.AppSection.NotificationModule.Actions.MarkAsReadAction import (
    MarkAsReadAction,
    MarkAsReadInput,
)
from src.Containers.AppSection.NotificationModule.Data.Schemas.Requests import (
    CreateNotificationRequest,
)
from src.Containers.AppSection.NotificationModule.Data.Schemas.Responses import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from src.Containers.AppSection.NotificationModule.Errors import NotificationError
from src.Containers.AppSection.NotificationModule.Models.Notification import Notification
from src.Containers.AppSection.NotificationModule.Queries.CountUnreadQuery import (
    CountUnreadQuery,
)
from src.Containers.AppSection.NotificationModule.Queries.GetUserNotificationsQuery import (
    GetUserNotificationsInput,
    GetUserNotificationsQuery,
)
from src.Ship.Auth.Guards import CurrentUser, auth_guard
from src.Ship.Decorators.result_handler import result_handler


class NotificationController(Controller):
    """HTTP API controller for Notification operations.

    Most endpoints require authentication.
    """

    path = "/notifications"
    tags = ["Notifications"]

    @post("/")
    @result_handler(NotificationResponse, success_status=HTTP_201_CREATED)
    async def create_notification(
        self,
        data: CreateNotificationRequest,
        action: FromDishka[CreateNotificationAction],
    ) -> Result[Notification, NotificationError]:
        """Create a new notification (admin/system endpoint).

        Args:
            data: CreateNotificationRequest with notification data
            action: Injected CreateNotificationAction

        Returns:
            Created notification as NotificationResponse (201)
        """
        return await action.run(data)

    @get(
        "/",
        dependencies={"current_user": auth_guard},
    )
    async def list_notifications(
        self,
        current_user: CurrentUser,
        query: FromDishka[GetUserNotificationsQuery],
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
    ) -> NotificationListResponse:
        """List current user's notifications.

        Args:
            current_user: Authenticated user from JWT
            query: Injected GetUserNotificationsQuery
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            unread_only: If True, only return unread notifications

        Returns:
            NotificationListResponse with notifications and counts
        """
        result = await query.execute(
            GetUserNotificationsInput(
                user_id=current_user.id,
                limit=limit,
                offset=offset,
                unread_only=unread_only,
            )
        )

        return NotificationListResponse(
            notifications=[NotificationResponse.from_entity(n) for n in result.notifications],
            total=result.total,
            unread_count=result.unread_count,
            limit=result.limit,
            offset=result.offset,
        )

    @get(
        "/unread-count",
        dependencies={"current_user": auth_guard},
    )
    async def get_unread_count(
        self,
        current_user: CurrentUser,
        query: FromDishka[CountUnreadQuery],
    ) -> UnreadCountResponse:
        """Get count of unread notifications.

        Args:
            current_user: Authenticated user from JWT
            query: Injected CountUnreadQuery

        Returns:
            UnreadCountResponse with count
        """
        count = await query.execute(current_user.id)
        return UnreadCountResponse(count=count)

    @patch(
        "/{notification_id:uuid}/read",
        dependencies={"current_user": auth_guard},
    )
    @result_handler(NotificationResponse, success_status=HTTP_200_OK)
    async def mark_as_read(
        self,
        notification_id: UUID,
        current_user: CurrentUser,
        action: FromDishka[MarkAsReadAction],
    ) -> Result[Notification, NotificationError]:
        """Mark a notification as read.

        Args:
            notification_id: ID of notification to mark as read
            current_user: Authenticated user from JWT
            action: Injected MarkAsReadAction

        Returns:
            Updated notification as NotificationResponse
        """
        return await action.run(
            MarkAsReadInput(
                notification_id=notification_id,
                user_id=current_user.id,
            )
        )

    @post(
        "/read-all",
        dependencies={"current_user": auth_guard},
    )
    @result_handler(UnreadCountResponse, success_status=HTTP_200_OK)
    async def mark_all_as_read(
        self,
        current_user: CurrentUser,
        action: FromDishka[MarkAllAsReadAction],
    ) -> Result[MarkAllAsReadResult, NotificationError]:
        """Mark all notifications as read.

        Args:
            current_user: Authenticated user from JWT
            action: Injected MarkAllAsReadAction

        Returns:
            UnreadCountResponse with count of marked notifications
        """
        return await action.run(current_user.id)
