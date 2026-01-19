"""Event Bus errors according to Hyper-Porto architecture.

All errors are Pydantic frozen models with http_status for API responses.
Uses ErrorWithTemplate for automatic message generation.
"""

from typing import Any, ClassVar
from uuid import UUID

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class EventBusError(BaseError):
    """Base error for all Event Bus operations.
    
    All Event Bus errors inherit from this class.
    """
    
    code: str = "EVENT_BUS_ERROR"
    http_status: int = 500


class EventBusNotInitializedError(ErrorWithTemplate, EventBusError):
    """Error raised when event bus is used before initialization."""
    
    _message_template: ClassVar[str] = "Event bus not initialized. Call start() first."
    code: str = "EVENT_BUS_NOT_INITIALIZED"
    http_status: int = 503  # Service Unavailable


class EventBusConnectionError(ErrorWithTemplate, EventBusError):
    """Error raised when connection to event bus backend fails."""
    
    _message_template: ClassVar[str] = "Failed to connect to event bus backend: {backend_type}"
    code: str = "EVENT_BUS_CONNECTION_ERROR"
    http_status: int = 503
    
    backend_type: str
    original_error: str | None = None


class EventBusDisconnectedError(ErrorWithTemplate, EventBusError):
    """Error raised when event bus loses connection during operation."""
    
    _message_template: ClassVar[str] = "Event bus disconnected from {backend_type}"
    code: str = "EVENT_BUS_DISCONNECTED"
    http_status: int = 503
    
    backend_type: str
    reconnect_attempts: int = 0


class EventPublishError(ErrorWithTemplate, EventBusError):
    """Error raised when publishing an event fails."""
    
    _message_template: ClassVar[str] = "Failed to publish event '{event_name}': {reason}"
    code: str = "EVENT_PUBLISH_ERROR"
    http_status: int = 500
    
    event_name: str
    reason: str
    event_id: UUID | None = None


class EventSubscriptionError(ErrorWithTemplate, EventBusError):
    """Error raised when subscribing to events fails."""
    
    _message_template: ClassVar[str] = "Failed to subscribe to '{event_name}': {reason}"
    code: str = "EVENT_SUBSCRIPTION_ERROR"
    http_status: int = 500
    
    event_name: str
    reason: str
    handler_name: str | None = None


class EventHandlerError(ErrorWithTemplate, EventBusError):
    """Error raised when an event handler fails to process an event."""
    
    _message_template: ClassVar[str] = (
        "Handler '{handler_name}' failed for event '{event_name}': {reason}"
    )
    code: str = "EVENT_HANDLER_ERROR"
    http_status: int = 500
    
    event_name: str
    handler_name: str
    reason: str
    event_id: UUID | None = None
    retry_count: int = 0


class EventTimeoutError(ErrorWithTemplate, EventBusError):
    """Error raised when event processing times out."""
    
    _message_template: ClassVar[str] = (
        "Event '{event_name}' processing timed out after {timeout_seconds}s"
    )
    code: str = "EVENT_TIMEOUT_ERROR"
    http_status: int = 504  # Gateway Timeout
    
    event_name: str
    timeout_seconds: float
    event_id: UUID | None = None


class EventSerializationError(ErrorWithTemplate, EventBusError):
    """Error raised when event serialization/deserialization fails."""
    
    _message_template: ClassVar[str] = "Failed to {operation} event '{event_name}': {reason}"
    code: str = "EVENT_SERIALIZATION_ERROR"
    http_status: int = 400
    
    event_name: str
    operation: str  # "serialize" or "deserialize"
    reason: str


class EventValidationError(ErrorWithTemplate, EventBusError):
    """Error raised when event validation fails."""
    
    _message_template: ClassVar[str] = "Event validation failed for '{event_name}': {reason}"
    code: str = "EVENT_VALIDATION_ERROR"
    http_status: int = 422
    
    event_name: str
    reason: str
    validation_errors: list[dict[str, Any]] | None = None


class DeadLetterQueueFullError(ErrorWithTemplate, EventBusError):
    """Error raised when dead letter queue reaches capacity."""
    
    _message_template: ClassVar[str] = (
        "Dead letter queue is full (max: {max_size}). "
        "Event '{event_name}' discarded."
    )
    code: str = "DLQ_FULL_ERROR"
    http_status: int = 507  # Insufficient Storage
    
    event_name: str
    max_size: int
    event_id: UUID | None = None


class EventExpiredError(ErrorWithTemplate, EventBusError):
    """Error raised when processing an expired event."""
    
    _message_template: ClassVar[str] = "Event '{event_name}' has expired (expired_at: {expired_at})"
    code: str = "EVENT_EXPIRED"
    http_status: int = 410  # Gone
    
    event_name: str
    expired_at: str
    event_id: UUID | None = None


class MaxRetriesExceededError(ErrorWithTemplate, EventBusError):
    """Error raised when event exceeds maximum retry attempts."""
    
    _message_template: ClassVar[str] = (
        "Event '{event_name}' exceeded max retries ({max_retries}). "
        "Moving to dead letter queue."
    )
    code: str = "MAX_RETRIES_EXCEEDED"
    http_status: int = 500
    
    event_name: str
    max_retries: int
    event_id: UUID | None = None
    last_error: str | None = None


class BackendNotSupportedError(ErrorWithTemplate, EventBusError):
    """Error raised when requested backend is not supported."""
    
    _message_template: ClassVar[str] = (
        "Backend '{backend_name}' is not supported. "
        "Available: {available_backends}"
    )
    code: str = "BACKEND_NOT_SUPPORTED"
    http_status: int = 400
    
    backend_name: str
    available_backends: str


class InvalidEventNameError(ErrorWithTemplate, EventBusError):
    """Error raised when event name is invalid."""
    
    _message_template: ClassVar[str] = (
        "Invalid event name '{event_name}'. {reason}"
    )
    code: str = "INVALID_EVENT_NAME"
    http_status: int = 400
    
    event_name: str
    reason: str


class HandlerAlreadyRegisteredError(ErrorWithTemplate, EventBusError):
    """Error raised when trying to register duplicate handler."""
    
    _message_template: ClassVar[str] = (
        "Handler '{handler_name}' already registered for event '{event_name}'"
    )
    code: str = "HANDLER_ALREADY_REGISTERED"
    http_status: int = 409
    
    event_name: str
    handler_name: str


__all__ = [
    "EventBusError",
    "EventBusNotInitializedError",
    "EventBusConnectionError",
    "EventBusDisconnectedError",
    "EventPublishError",
    "EventSubscriptionError",
    "EventHandlerError",
    "EventTimeoutError",
    "EventSerializationError",
    "EventValidationError",
    "DeadLetterQueueFullError",
    "EventExpiredError",
    "MaxRetriesExceededError",
    "BackendNotSupportedError",
    "InvalidEventNameError",
    "HandlerAlreadyRegisteredError",
]
