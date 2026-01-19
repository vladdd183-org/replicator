"""Base error classes for the application.

All errors are Pydantic frozen models for immutability and serialization.
Each error has an explicit http_status for direct HTTP response mapping.
Used with Problem Details (RFC 9457) for standardized error responses.
"""

from typing import Any, ClassVar
from uuid import UUID

from pydantic import BaseModel, model_validator


class BaseError(BaseModel):
    """Base error class for all domain errors.
    
    All errors should inherit from this class.
    Errors are frozen (immutable) Pydantic models.
    
    For raising as exceptions, use DomainException wrapper or raise directly
    (ProblemDetailsPlugin handles BaseError subclasses).
    
    Attributes:
        message: Human-readable error message
        code: Machine-readable error code (used in Problem Details type URI)
        http_status: HTTP status code for API responses
    
    Example:
        class UserError(BaseError):
            code: str = "USER_ERROR"
            
        class UserNotFoundError(UserError):
            code: str = "USER_NOT_FOUND"
            http_status: int = 404
            user_id: UUID
    """
    
    model_config = {"frozen": True}
    
    message: str
    code: str = "ERROR"
    http_status: int = 400  # Default to Bad Request
    
    def __str__(self) -> str:
        """Return error message."""
        return self.message


class ErrorWithTemplate(BaseError):
    """Base error with automatic message generation from template.
    
    Reduces boilerplate for errors that need dynamic messages.
    Subclasses define _message_template as class variable.
    
    Attributes:
        _message_template: Format string for generating message.
                          Uses field names as format keys.
    
    Example:
        class UserNotFoundError(ErrorWithTemplate):
            _message_template: ClassVar[str] = "User with id {user_id} not found"
            code: str = "USER_NOT_FOUND"
            http_status: int = 404
            user_id: UUID
            
        # Usage:
        error = UserNotFoundError(user_id=some_uuid)
        # error.message == "User with id <uuid> not found"
    """
    
    _message_template: ClassVar[str] = ""
    
    @model_validator(mode="before")
    @classmethod
    def auto_generate_message(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Auto-generate message from template if not provided."""
        if isinstance(data, dict) and "message" not in data and cls._message_template:
            try:
                data["message"] = cls._message_template.format(**data)
            except KeyError:
                # Fallback to template as-is if formatting fails
                data["message"] = cls._message_template
        return data


class DomainException(Exception):
    """Exception wrapper for domain errors.
    
    Wraps BaseError so it can be raised as exception.
    ProblemDetailsPlugin catches this and converts to RFC 9457 response.
    
    Example:
        error = UserNotFoundError(user_id=uuid)
        raise DomainException(error)
    """
    
    def __init__(self, error: BaseError) -> None:
        self.error = error
        super().__init__(error.message)


class NotFoundError(BaseError):
    """Error raised when entity is not found."""
    
    code: str = "NOT_FOUND"
    http_status: int = 404
    entity_type: str
    entity_id: UUID | str | int


class ValidationError(BaseError):
    """Error raised when validation fails."""
    
    code: str = "VALIDATION_ERROR"
    http_status: int = 422
    field: str | None = None
    details: dict[str, Any] | None = None


class AlreadyExistsError(BaseError):
    """Error raised when entity already exists."""
    
    code: str = "ALREADY_EXISTS"
    http_status: int = 409
    entity_type: str
    conflicting_field: str
    conflicting_value: str


class UnauthorizedError(BaseError):
    """Error raised when user is not authenticated."""
    
    code: str = "UNAUTHORIZED"
    http_status: int = 401
    message: str = "Authentication required"


class ForbiddenError(BaseError):
    """Error raised when user doesn't have permission."""
    
    code: str = "FORBIDDEN"
    http_status: int = 403
    message: str = "Permission denied"


class ConflictError(BaseError):
    """Error raised when there's a conflict."""
    
    code: str = "CONFLICT"
    http_status: int = 409


class UnexpectedError(BaseError):
    """Error for unexpected/unknown errors.
    
    Used to wrap non-Porto errors for consistent handling.
    """
    
    code: str = "UNEXPECTED_ERROR"
    http_status: int = 500
    message: str = "An unexpected error occurred"
    details: dict[str, Any] | None = None

