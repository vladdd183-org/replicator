"""Notification task for order events.

Sends notifications for order-related events.
Uses the notification system or external services.
"""

from dataclasses import dataclass
from uuid import UUID

import logfire
from pydantic import BaseModel

from src.Ship.Parents.Task import Task


class OrderNotificationInput(BaseModel):
    """Input for order notifications.
    
    Attributes:
        user_id: User to notify
        order_id: Related order
        notification_type: Type of notification
        message: Notification message
    """
    
    user_id: UUID
    order_id: UUID
    notification_type: str  # "order_created", "order_shipped", etc.
    message: str
    email: str | None = None
    data: dict | None = None


@dataclass
class NotificationTask(Task[OrderNotificationInput, bool]):
    """Task for sending order notifications.
    
    Sends notifications via email, push, SMS, etc.
    In production, would integrate with notification service.
    """
    
    async def run(self, data: OrderNotificationInput) -> bool:
        """Send notification.
        
        Args:
            data: Notification details
            
        Returns:
            True if notification sent successfully
        """
        logfire.info(
            f"📧 Sending {data.notification_type} notification",
            user_id=str(data.user_id),
            order_id=str(data.order_id),
            notification_type=data.notification_type,
        )
        
        # In production, this would:
        # - Call notification service API
        # - Send email via SMTP/SendGrid/etc.
        # - Send push notification
        # - Record notification in database
        
        # Simulate successful send
        logfire.info(
            f"✅ Notification sent",
            user_id=str(data.user_id),
            notification_type=data.notification_type,
        )
        
        return True


def create_notification_task() -> NotificationTask:
    """Create NotificationTask instance."""
    return NotificationTask()


__all__ = [
    "NotificationTask",
    "OrderNotificationInput",
    "create_notification_task",
]
