"""MarkAsReadAction - Use case for marking notification as read."""

from uuid import UUID

from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.NotificationModule.Data.UnitOfWork import NotificationUnitOfWork
from src.Containers.AppSection.NotificationModule.Errors import (
    NotificationError,
    NotificationNotFoundError,
    NotificationAccessDeniedError,
)
from src.Containers.AppSection.NotificationModule.Events import NotificationRead
from src.Containers.AppSection.NotificationModule.Models.Notification import Notification


class MarkAsReadInput(BaseModel):
    """Input for marking notification as read."""
    
    model_config = {"frozen": True}
    
    notification_id: UUID
    user_id: UUID  # Current user ID for access check


class MarkAsReadAction(Action[MarkAsReadInput, Notification, NotificationError]):
    """Use Case: Mark a notification as read.
    
    Steps:
    1. Find notification by ID
    2. Check user has access
    3. Mark as read
    4. Publish NotificationRead event
    
    Example:
        action = MarkAsReadAction(uow)
        result = await action.run(MarkAsReadInput(
            notification_id=notification_id,
            user_id=current_user_id,
        ))
    """
    
    def __init__(self, uow: NotificationUnitOfWork) -> None:
        """Initialize action with dependencies.
        
        Args:
            uow: Unit of Work for data operations
        """
        self.uow = uow
    
    async def run(self, data: MarkAsReadInput) -> Result[Notification, NotificationError]:
        """Execute the mark as read use case.
        
        Args:
            data: MarkAsReadInput with notification_id and user_id
            
        Returns:
            Result[Notification, NotificationError]: Success with updated notification or Failure
        """
        # Find notification
        notification = await self.uow.notifications.get(data.notification_id)
        
        if notification is None:
            return Failure(NotificationNotFoundError(notification_id=data.notification_id))
        
        # Check access
        if notification.user_id != data.user_id:
            return Failure(NotificationAccessDeniedError(notification_id=data.notification_id))
        
        # Mark as read (if not already read)
        if not notification.is_read:
            async with self.uow:
                await self.uow.notifications.mark_as_read(notification)
                
                self.uow.add_event(NotificationRead(
                    notification_id=notification.id,
                    user_id=notification.user_id,
                ))
                
                await self.uow.commit()
        
        return Success(notification)



