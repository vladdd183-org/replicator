"""Idempotency middleware domain errors.

Pydantic frozen models for all idempotency-related errors.
Follows Hyper-Porto error conventions with http_status mapping.
"""

from typing import ClassVar

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class IdempotencyError(BaseError):
    """Base error for idempotency middleware.
    
    All idempotency errors inherit from this class.
    """
    
    code: str = "IDEMPOTENCY_ERROR"


class IdempotencyKeyRequiredError(IdempotencyError):
    """Error when idempotency key is required but not provided.
    
    Raised when enforce_on_endpoints is configured and
    a matching endpoint is called without X-Idempotency-Key header.
    """
    
    code: str = "IDEMPOTENCY_KEY_REQUIRED"
    http_status: int = 400
    message: str = "X-Idempotency-Key header is required for this endpoint"
    method: str
    path: str


class IdempotencyKeyTooLongError(ErrorWithTemplate, IdempotencyError):
    """Error when idempotency key exceeds maximum length.
    
    Keys are limited to 256 characters for performance.
    """
    
    _message_template: ClassVar[str] = (
        "Idempotency key exceeds maximum length of {max_length} characters"
    )
    code: str = "IDEMPOTENCY_KEY_TOO_LONG"
    http_status: int = 400
    max_length: int = 256
    actual_length: int


class IdempotencyKeyInvalidError(ErrorWithTemplate, IdempotencyError):
    """Error when idempotency key has invalid format.
    
    Keys must contain only alphanumeric characters, dashes, underscores.
    """
    
    _message_template: ClassVar[str] = (
        "Idempotency key contains invalid characters. "
        "Only alphanumeric, dash (-), and underscore (_) are allowed"
    )
    code: str = "IDEMPOTENCY_KEY_INVALID"
    http_status: int = 400
    key: str


class IdempotencyConflictError(ErrorWithTemplate, IdempotencyError):
    """Error when request body doesn't match cached request.
    
    This happens when:
    1. Same idempotency key is used with different request body
    2. Possible replay attack or client error
    
    Returns 409 Conflict per Stripe/PayPal conventions.
    """
    
    _message_template: ClassVar[str] = (
        "Idempotency key '{key}' was already used with different request body. "
        "Use a new key for different requests"
    )
    code: str = "IDEMPOTENCY_CONFLICT"
    http_status: int = 409
    key: str


class IdempotencyProcessingError(ErrorWithTemplate, IdempotencyError):
    """Error when same key is already being processed.
    
    This happens when:
    1. Concurrent requests with same idempotency key
    2. Previous request timed out but is still processing
    
    Returns 409 Conflict with Retry-After suggestion.
    """
    
    _message_template: ClassVar[str] = (
        "Request with idempotency key '{key}' is currently being processed. "
        "Please retry after {retry_after_seconds} seconds"
    )
    code: str = "IDEMPOTENCY_PROCESSING"
    http_status: int = 409
    key: str
    retry_after_seconds: int = 5


class IdempotencyCacheError(IdempotencyError):
    """Error when cache operations fail.
    
    Internal error - should be logged but not exposed to clients.
    Falls back to processing request without idempotency.
    """
    
    code: str = "IDEMPOTENCY_CACHE_ERROR"
    http_status: int = 500
    message: str = "Idempotency cache operation failed"
    original_error: str | None = None
