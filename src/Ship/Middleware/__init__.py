"""Ship-level middleware components.

Provides cross-cutting middleware for the application:
- IdempotencyMiddleware: Prevents duplicate request processing
- IdempotencyRecord: Cached response data model

Usage:
    from src.Ship.Middleware import IdempotencyMiddleware
    
    app = Litestar(
        middleware=[IdempotencyMiddleware],
        ...
    )
"""

from src.Ship.Middleware.Idempotency import IdempotencyMiddleware
from src.Ship.Middleware.Models import (
    IdempotencyRecord,
    IdempotencyStatus,
    CapturedResponse,
)
from src.Ship.Middleware.Errors import (
    IdempotencyError,
    IdempotencyKeyRequiredError,
    IdempotencyKeyTooLongError,
    IdempotencyConflictError,
    IdempotencyProcessingError,
)

__all__ = [
    # Middleware
    "IdempotencyMiddleware",
    # Models
    "IdempotencyRecord",
    "IdempotencyStatus",
    "CapturedResponse",
    # Errors
    "IdempotencyError",
    "IdempotencyKeyRequiredError",
    "IdempotencyKeyTooLongError",
    "IdempotencyConflictError",
    "IdempotencyProcessingError",
]
