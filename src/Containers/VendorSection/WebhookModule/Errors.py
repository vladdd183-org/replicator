"""WebhookModule errors."""

from typing import ClassVar
from uuid import UUID

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class WebhookError(BaseError):
    """Base error for WebhookModule."""
    
    code: str = "WEBHOOK_ERROR"


class WebhookNotFoundError(ErrorWithTemplate, WebhookError):
    """Raised when webhook is not found."""
    
    _message_template: ClassVar[str] = "Webhook with id {webhook_id} not found"
    code: str = "WEBHOOK_NOT_FOUND"
    http_status: int = 404
    webhook_id: UUID


class InvalidWebhookSignatureError(WebhookError):
    """Raised when webhook signature verification fails."""
    
    code: str = "INVALID_WEBHOOK_SIGNATURE"
    http_status: int = 401
    message: str = "Invalid webhook signature"


class WebhookDeliveryFailedError(ErrorWithTemplate, WebhookError):
    """Raised when webhook delivery fails."""
    
    _message_template: ClassVar[str] = "Failed to deliver webhook to {url}: {details}"
    code: str = "WEBHOOK_DELIVERY_FAILED"
    http_status: int = 500
    url: str
    details: str


class WebhookUrlInvalidError(ErrorWithTemplate, WebhookError):
    """Raised when webhook URL is invalid."""
    
    _message_template: ClassVar[str] = "Invalid webhook URL: {url}"
    code: str = "WEBHOOK_URL_INVALID"
    http_status: int = 400
    url: str


class WebhookDisabledError(ErrorWithTemplate, WebhookError):
    """Raised when trying to use a disabled webhook."""
    
    _message_template: ClassVar[str] = "Webhook {webhook_id} is disabled"
    code: str = "WEBHOOK_DISABLED"
    http_status: int = 400
    webhook_id: UUID



