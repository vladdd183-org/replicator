"""Notification module errors.

All errors are Pydantic frozen models with explicit http_status.
"""

from typing import ClassVar
from uuid import UUID

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class NotificationError(BaseError):
    """Base error for NotificationModule."""
    
    code: str = "NOTIFICATION_ERROR"


class NotificationNotFoundError(ErrorWithTemplate, NotificationError):
    """Error raised when notification is not found."""
    
    _message_template: ClassVar[str] = "Notification with id {notification_id} not found"
    code: str = "NOTIFICATION_NOT_FOUND"
    http_status: int = 404
    notification_id: UUID


class NotificationAccessDeniedError(ErrorWithTemplate, NotificationError):
    """Error raised when user doesn't have access to notification."""
    
    _message_template: ClassVar[str] = "Access denied to notification {notification_id}"
    code: str = "NOTIFICATION_ACCESS_DENIED"
    http_status: int = 403
    notification_id: UUID


class InvalidNotificationTypeError(ErrorWithTemplate, NotificationError):
    """Error raised when notification type is invalid."""
    
    _message_template: ClassVar[str] = "Invalid notification type: {notification_type}"
    code: str = "INVALID_NOTIFICATION_TYPE"
    http_status: int = 400
    notification_type: str


__all__ = [
    "NotificationError",
    "NotificationNotFoundError",
    "NotificationAccessDeniedError",
    "InvalidNotificationTypeError",
]



