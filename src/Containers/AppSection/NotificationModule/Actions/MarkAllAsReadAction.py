"""MarkAllAsReadAction - Use case for marking all notifications as read."""

from uuid import UUID

from pydantic import BaseModel
from returns.result import Result, Success

from src.Containers.AppSection.NotificationModule.Data.UnitOfWork import NotificationUnitOfWork
from src.Containers.AppSection.NotificationModule.Errors import NotificationError
from src.Containers.AppSection.NotificationModule.Events import AllNotificationsRead
from src.Ship.Parents.Action import Action


class MarkAllAsReadResult(BaseModel):
    """Result of marking all notifications as read."""

    model_config = {"frozen": True}

    count: int


class MarkAllAsReadAction(Action[UUID, MarkAllAsReadResult, NotificationError]):
    """Use Case: Mark all notifications as read for a user.

    Steps:
    1. Mark all unread notifications as read
    2. Publish AllNotificationsRead event

    Example:
        action = MarkAllAsReadAction(uow)
        result = await action.run(user_id)
    """

    def __init__(self, uow: NotificationUnitOfWork) -> None:
        self.uow = uow

    async def run(self, user_id: UUID) -> Result[MarkAllAsReadResult, NotificationError]:
        """Execute the mark all as read use case.

        Args:
            user_id: User ID to mark all notifications for

        Returns:
            Result[MarkAllAsReadResult, NotificationError]: Success with count
        """
        async with self.uow:
            count = await self.uow.notifications.mark_all_as_read(user_id)

            if count > 0:
                self.uow.add_event(
                    AllNotificationsRead(
                        user_id=user_id,
                        count=count,
                    )
                )

            await self.uow.commit()

        return Success(MarkAllAsReadResult(count=count))
