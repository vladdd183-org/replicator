"""Outbox Event model for Piccolo ORM.

Implements the Transactional Outbox pattern table for reliable event delivery.
Events are stored in this table within the same transaction as business data,
then processed asynchronously by a background worker.
"""

from piccolo.table import Table
from piccolo.columns import UUID, Varchar, Text, Timestamptz, Boolean, Integer
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.defaults.timestamptz import TimestamptzNow


class OutboxEvent(Table, tablename="outbox_events"):
    """Outbox event entity for transactional event storage.
    
    This table stores domain events atomically with business data,
    ensuring reliable event delivery even if the application crashes
    after committing the transaction.
    
    Lifecycle:
    1. Event is created when UnitOfWork.add_event() is called
    2. Event is saved to this table during commit (same transaction)
    3. Background worker picks up unpublished events
    4. Worker publishes event via Litestar events system
    5. Event is marked as published (or failed with retry count)
    
    Attributes:
        id: Unique identifier (UUID)
        event_name: Name of the event class (e.g., 'UserCreated')
        payload: JSON-serialized event data
        aggregate_type: Optional type of aggregate that produced event
        aggregate_id: Optional ID of aggregate that produced event
        created_at: When the event was created
        published_at: When the event was successfully published
        is_published: Whether the event has been published
        retry_count: Number of failed publish attempts
        max_retries: Maximum retry attempts before giving up
        error_message: Last error message if publish failed
        next_retry_at: When to retry failed publish (exponential backoff)
    """
    
    # Primary key
    id = UUID(primary_key=True, default=UUID4())
    
    # Event metadata
    event_name = Varchar(length=255, required=True, index=True)
    payload = Text(required=True)  # JSON serialized event data
    
    # Aggregate reference (optional, for debugging/filtering)
    aggregate_type = Varchar(length=100, null=True, index=True)
    aggregate_id = Varchar(length=100, null=True, index=True)
    
    # Timestamps
    created_at = Timestamptz(default=TimestamptzNow(), index=True)
    published_at = Timestamptz(null=True)
    
    # Publication status
    is_published = Boolean(default=False, index=True)
    
    # Retry logic
    retry_count = Integer(default=0)
    max_retries = Integer(default=5)
    error_message = Text(null=True)
    next_retry_at = Timestamptz(null=True, index=True)
    
    class Meta:
        """Piccolo meta configuration."""
        
        # Composite indexes for efficient queries
        # Note: Piccolo handles these via column-level indexes
        pass
    
    def __str__(self) -> str:
        """String representation for logging."""
        status = "published" if self.is_published else f"pending (retries: {self.retry_count})"
        return f"OutboxEvent({self.event_name}, {status})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"OutboxEvent(id={self.id}, event_name={self.event_name!r}, "
            f"is_published={self.is_published}, retry_count={self.retry_count})"
        )
