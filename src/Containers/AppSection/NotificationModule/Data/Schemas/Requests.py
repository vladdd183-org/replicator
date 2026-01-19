"""NotificationModule request DTOs.

Request DTOs use Pydantic for validation.
"""

from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field


NotificationType = Literal["info", "warning", "success", "error", "payment", "system"]


class CreateNotificationRequest(BaseModel):
    """Request DTO for creating a notification.
    
    Attributes:
        user_id: User who will receive the notification
        notification_type: Type of notification
        title: Notification title
        message: Notification message content
        link: Optional link related to the notification
    """
    
    user_id: UUID
    notification_type: NotificationType = Field(default="info")
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    message: str = Field(default="", max_length=2000, description="Notification message")
    link: str = Field(default="", max_length=500, description="Optional link")


class MarkAsReadRequest(BaseModel):
    """Request DTO for marking notification as read.
    
    Attributes:
        notification_id: ID of notification to mark as read
    """
    
    notification_id: UUID



