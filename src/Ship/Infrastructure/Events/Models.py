"""Event Bus data models according to Hyper-Porto architecture.

Defines EventEnvelope, EventMetadata, and related DTOs for event bus infrastructure.
All models are Pydantic for serialization, validation, and immutability.
"""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


def _utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class EventPriority(StrEnum):
    """Event priority levels for processing order.
    
    Higher priority events are processed first when backend supports it.
    """
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventStatus(StrEnum):
    """Event processing status for tracking."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class EventMetadata(BaseModel):
    """Metadata for event tracing, debugging and processing control.
    
    Contains all non-business information about an event:
    - Unique identifiers for tracing (event_id, correlation_id, causation_id)
    - Timing information (timestamp, expires_at)
    - Processing control (priority, retry_count, max_retries)
    - Source information (source_service, source_module)
    
    Example:
        metadata = EventMetadata(
            source_service="user-service",
            source_module="UserModule",
            correlation_id=request_id,
        )
    """
    
    model_config = {"frozen": True}
    
    # Unique event identifier
    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    
    # Distributed tracing identifiers
    correlation_id: UUID | None = Field(
        default=None,
        description="Correlation ID for request tracing across services"
    )
    causation_id: UUID | None = Field(
        default=None,
        description="ID of the event that caused this event (event chain)"
    )
    
    # Timing
    timestamp: datetime = Field(
        default_factory=_utc_now,
        description="When the event was created (UTC)"
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Optional expiration time for TTL (UTC)"
    )
    
    # Processing control
    priority: EventPriority = Field(
        default=EventPriority.NORMAL,
        description="Event priority for processing order"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts before dead letter"
    )
    
    # Source information
    source_service: str = Field(
        default="hyper-porto",
        description="Service that produced the event"
    )
    source_module: str | None = Field(
        default=None,
        description="Module within service that produced the event"
    )
    
    # Custom headers for extensibility
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Custom headers for routing, filtering, etc."
    )
    
    def with_retry(self) -> "EventMetadata":
        """Create new metadata with incremented retry count.
        
        Returns:
            New EventMetadata with retry_count + 1
        """
        return self.model_copy(update={"retry_count": self.retry_count + 1})
    
    def is_expired(self) -> bool:
        """Check if event has expired.
        
        Returns:
            True if event has expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def should_retry(self) -> bool:
        """Check if event should be retried.
        
        Returns:
            True if retry_count < max_retries and not expired
        """
        return self.retry_count < self.max_retries and not self.is_expired()


class EventEnvelope(BaseModel):
    """Wrapper for event data with metadata for transport.
    
    EventEnvelope is the unit of transmission in the event bus.
    It wraps the actual event payload with metadata for:
    - Event identification and routing (event_name, event_type)
    - Distributed tracing (metadata.correlation_id, causation_id)
    - Processing control (metadata.priority, retry logic)
    - Serialization (payload as dict)
    
    The envelope pattern separates infrastructure concerns from business logic,
    allowing handlers to focus on the payload while the bus handles delivery.
    
    Example:
        envelope = EventEnvelope(
            event_name="UserCreated",
            event_type="domain.user.created",
            payload={"user_id": str(user.id), "email": user.email},
            metadata=EventMetadata(
                source_module="UserModule",
                correlation_id=request_id,
            ),
        )
        
        await event_bus.publish(envelope)
    """
    
    model_config = {"frozen": True}
    
    # Event identification
    event_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Event class name (e.g., 'UserCreated')"
    )
    event_type: str = Field(
        default="",
        max_length=255,
        description="Qualified event type for routing (e.g., 'domain.user.created')"
    )
    
    # Event data
    payload: dict[str, Any] = Field(
        ...,
        description="Event payload data (JSON-serializable)"
    )
    
    # Metadata
    metadata: EventMetadata = Field(
        default_factory=EventMetadata,
        description="Event metadata for tracing and processing"
    )
    
    @model_validator(mode="after")
    def auto_set_event_type(self) -> Self:
        """Auto-generate event_type from event_name if not provided."""
        if not self.event_type:
            # Convert PascalCase to dot.notation
            # UserCreated -> domain.user.created
            name = self.event_name
            parts = []
            current = ""
            for char in name:
                if char.isupper() and current:
                    parts.append(current.lower())
                    current = char
                else:
                    current += char
            if current:
                parts.append(current.lower())
            
            # Use object.__setattr__ since model is frozen
            object.__setattr__(self, "event_type", f"domain.{'.'.join(parts)}")
        return self
    
    @classmethod
    def from_domain_event(
        cls,
        event: "DomainEvent",
        *,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        source_module: str | None = None,
        priority: EventPriority = EventPriority.NORMAL,
        headers: dict[str, str] | None = None,
    ) -> "EventEnvelope":
        """Create envelope from a DomainEvent.
        
        Convenience factory for wrapping DomainEvent instances.
        
        Args:
            event: DomainEvent instance
            correlation_id: Optional correlation ID for tracing
            causation_id: Optional ID of causing event
            source_module: Optional source module name
            priority: Event priority level
            headers: Optional custom headers
            
        Returns:
            EventEnvelope wrapping the event
        """
        
        return cls(
            event_name=event.event_name,
            payload=event.model_dump(mode="json"),
            metadata=EventMetadata(
                correlation_id=correlation_id,
                causation_id=causation_id,
                source_module=source_module,
                priority=priority,
                headers=headers or {},
            ),
        )
    
    def to_json(self) -> dict[str, Any]:
        """Serialize envelope to JSON-compatible dict.
        
        Returns:
            Dict suitable for JSON serialization
        """
        return self.model_dump(mode="json")
    
    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "EventEnvelope":
        """Deserialize envelope from JSON dict.
        
        Args:
            data: JSON dict from to_json()
            
        Returns:
            EventEnvelope instance
        """
        return cls.model_validate(data)


class DeadLetterEvent(BaseModel):
    """Event that failed processing and was moved to dead letter queue.
    
    Contains the original envelope plus failure information for debugging.
    
    Example:
        dead_letter = DeadLetterEvent(
            envelope=failed_envelope,
            failure_reason="Handler raised ValueError",
            failed_at=datetime.now(timezone.utc),
            handler_name="on_user_created",
        )
    """
    
    model_config = {"frozen": True}
    
    # Original event
    envelope: EventEnvelope = Field(..., description="Original event envelope")
    
    # Failure information
    failure_reason: str = Field(..., description="Reason for failure")
    error_type: str = Field(default="", description="Exception class name")
    error_traceback: str | None = Field(default=None, description="Stack trace if available")
    
    # Timing
    failed_at: datetime = Field(
        default_factory=_utc_now,
        description="When the event failed"
    )
    first_failed_at: datetime | None = Field(
        default=None,
        description="When the event first failed (for retried events)"
    )
    
    # Handler information
    handler_name: str | None = Field(
        default=None,
        description="Handler that failed"
    )


class EventBusStats(BaseModel):
    """Statistics for monitoring event bus health.
    
    Used by health checks and observability.
    """
    
    model_config = {"frozen": True}
    
    # Counts
    total_published: int = Field(default=0, ge=0)
    total_delivered: int = Field(default=0, ge=0)
    total_failed: int = Field(default=0, ge=0)
    total_retried: int = Field(default=0, ge=0)
    dead_letter_count: int = Field(default=0, ge=0)
    
    # Queue info
    pending_count: int = Field(default=0, ge=0)
    active_subscriptions: int = Field(default=0, ge=0)
    
    # Performance
    avg_processing_time_ms: float = Field(default=0.0, ge=0)
    last_publish_at: datetime | None = Field(default=None)
    last_delivery_at: datetime | None = Field(default=None)
    
    # Status
    is_healthy: bool = Field(default=True)
    backend_type: str = Field(default="unknown")


# Type alias for handler functions
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.Ship.Parents.Event import DomainEvent


__all__ = [
    "EventPriority",
    "EventStatus",
    "EventMetadata",
    "EventEnvelope",
    "DeadLetterEvent",
    "EventBusStats",
]
