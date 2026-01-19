"""NotificationActivity - Temporal Activity for order notifications.

This Activity sends notifications for order events.
Notifications typically don't need compensation (user gets cancellation notice).

Architecture:
- @activity.defn decorator makes this a Temporal Activity
- Simulates notification sending (replace with actual service)
- No compensation needed for most notifications
"""

from uuid import UUID

from pydantic import BaseModel
from temporalio import activity


# =============================================================================
# Input/Output DTOs
# =============================================================================

class NotificationInput(BaseModel):
    """Input for notification activities.
    
    Attributes:
        user_id: User to notify
        order_id: Related order
        notification_type: Type of notification
        message: Notification message
        email: Optional email address
    """
    
    user_id: UUID
    order_id: UUID
    notification_type: str  # "order_created", "order_cancelled", etc.
    message: str
    email: str | None = None
    
    # Additional data for templates
    data: dict | None = None


# =============================================================================
# Send Order Confirmation Activity
# =============================================================================

@activity.defn(name="send_order_confirmation")
async def send_order_confirmation(data: NotificationInput) -> bool:
    """Send order confirmation notification.
    
    This is a Temporal Activity that sends confirmation.
    In production, this would call notification service.
    
    Note: Notification activities typically don't fail the saga.
    Temporal will retry, and if it ultimately fails,
    we log the error but don't compensate.
    
    Args:
        data: Notification details
        
    Returns:
        True if sent successfully
    """
    activity.logger.info(
        f"📧 Sending order confirmation to user {data.user_id} "
        f"for order {data.order_id}"
    )
    
    # In production:
    # await notification_service.send_email(
    #     to=data.email,
    #     template="order_confirmation",
    #     data={
    #         "order_id": str(data.order_id),
    #         "message": data.message,
    #         **data.data or {},
    #     },
    # )
    # 
    # await notification_service.send_push(
    #     user_id=data.user_id,
    #     title="Order Confirmed",
    #     body=data.message,
    # )
    
    activity.logger.info(
        f"✅ Notification sent for order {data.order_id}"
    )
    
    return True


# =============================================================================
# Send Order Cancelled Notification
# =============================================================================

@activity.defn(name="send_order_cancelled")
async def send_order_cancelled(data: NotificationInput) -> bool:
    """Send order cancelled notification.
    
    This is used when saga fails and order is cancelled.
    User should be notified about the cancellation.
    
    Args:
        data: Notification details
        
    Returns:
        True if sent successfully
    """
    activity.logger.info(
        f"📧 Sending cancellation notice to user {data.user_id} "
        f"for order {data.order_id}"
    )
    
    # In production: send email and push notification
    
    activity.logger.info(
        f"✅ Cancellation notice sent for order {data.order_id}"
    )
    
    return True


__all__ = [
    "NotificationInput",
    "send_order_confirmation",
    "send_order_cancelled",
]
