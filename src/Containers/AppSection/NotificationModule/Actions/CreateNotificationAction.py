"""CreateNotificationAction - Use case for creating notifications."""

from returns.result import Result, Success

from src.Containers.AppSection.NotificationModule.Data.Schemas.Requests import (
    CreateNotificationRequest,
)
from src.Containers.AppSection.NotificationModule.Data.UnitOfWork import NotificationUnitOfWork
from src.Containers.AppSection.NotificationModule.Errors import NotificationError
from src.Containers.AppSection.NotificationModule.Events import NotificationCreated
from src.Containers.AppSection.NotificationModule.Models.Notification import Notification
from src.Ship.Parents.Action import Action


class CreateNotificationAction(Action[CreateNotificationRequest, Notification, NotificationError]):
    """Use Case: Create a new notification.

    Steps:
    1. Create notification entity
    2. Save to database
    3. Publish NotificationCreated event

    Example:
        action = CreateNotificationAction(uow)
        result = await action.run(CreateNotificationRequest(
            user_id=user_id,
            notification_type="info",
            title="Welcome!",
            message="Thanks for joining.",
        ))
    """

    def __init__(self, uow: NotificationUnitOfWork) -> None:
        self.uow = uow

    async def run(self, data: CreateNotificationRequest) -> Result[Notification, NotificationError]:
        """Execute the create notification use case.

        Args:
            data: CreateNotificationRequest with notification data

        Returns:
            Result[Notification, NotificationError]: Success with created notification or Failure
        """
        # Create notification entity
        notification = Notification(
            user_id=data.user_id,
            notification_type=data.notification_type,
            title=data.title,
            message=data.message,
            link=data.link,
        )

        # Save to database and publish event
        async with self.uow:
            await self.uow.notifications.add(notification)

            self.uow.add_event(
                NotificationCreated(
                    notification_id=notification.id,
                    user_id=notification.user_id,
                    notification_type=notification.notification_type,
                    title=notification.title,
                    message=notification.message,
                )
            )

            await self.uow.commit()

        return Success(notification)
