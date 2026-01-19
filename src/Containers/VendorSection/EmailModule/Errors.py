"""Email module errors.

All errors are Pydantic frozen models with explicit http_status.
"""

from typing import ClassVar

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class EmailError(BaseError):
    """Base error for EmailModule."""

    code: str = "EMAIL_ERROR"


class EmailSendFailedError(ErrorWithTemplate, EmailError):
    """Error raised when email sending fails."""

    _message_template: ClassVar[str] = "Failed to send email to {recipient}: {reason}"
    code: str = "EMAIL_SEND_FAILED"
    http_status: int = 500
    recipient: str
    reason: str = "Unknown error"


class InvalidEmailAddressError(ErrorWithTemplate, EmailError):
    """Error raised when email address is invalid."""

    _message_template: ClassVar[str] = "Invalid email address: {email}"
    code: str = "INVALID_EMAIL_ADDRESS"
    http_status: int = 400
    email: str


class EmailTemplateNotFoundError(ErrorWithTemplate, EmailError):
    """Error raised when email template is not found."""

    _message_template: ClassVar[str] = "Email template '{template_name}' not found"
    code: str = "EMAIL_TEMPLATE_NOT_FOUND"
    http_status: int = 404
    template_name: str


class EmailRateLimitError(ErrorWithTemplate, EmailError):
    """Error raised when email rate limit is exceeded."""

    _message_template: ClassVar[str] = "Email rate limit exceeded for {recipient}"
    code: str = "EMAIL_RATE_LIMIT"
    http_status: int = 429
    recipient: str


__all__ = [
    "EmailError",
    "EmailRateLimitError",
    "EmailSendFailedError",
    "EmailTemplateNotFoundError",
    "InvalidEmailAddressError",
]
