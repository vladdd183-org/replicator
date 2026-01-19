"""Repository for Outbox Events.

Provides data access methods for the outbox_events table,
following the Hyper-Porto Repository pattern.
"""

from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING
from uuid import UUID
import json

from src.Ship.Parents.Repository import Repository
from src.Ship.Infrastructure.Events.Outbox.Models import OutboxEvent

if TYPE_CHECKING:
    from src.Ship.Parents.Event import DomainEvent


def _utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class OutboxEventRepository(Repository[OutboxEvent]):
    """Repository for OutboxEvent CRUD operations.
    
    Provides specialized methods for the Transactional Outbox pattern:
    - Adding events from domain events
    - Fetching unpublished events for processing
    - Marking events as published or failed
    - Cleanup of old published events
    
    Example:
        repo = OutboxEventRepository()
        
        # Add event to outbox
        outbox_event = await repo.add_from_domain_event(
            UserCreated(user_id=user.id, email=user.email)
        )
        
        # Get unpublished events for processing
        events = await repo.get_unpublished(limit=100)
        
        # Mark as published
        await repo.mark_published(event.id)
    """
    
    def __init__(self) -> None:
        """Initialize repository with OutboxEvent model."""
        super().__init__(OutboxEvent)
    
    async def add_from_domain_event(
        self,
        event: "DomainEvent",
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
    ) -> OutboxEvent:
        """Create outbox event from domain event.
        
        Serializes the domain event to JSON and stores in outbox table.
        Should be called within the same transaction as business data.
        
        Args:
            event: Domain event to store
            aggregate_type: Optional type name of aggregate (e.g., 'User')
            aggregate_id: Optional ID of aggregate
            
        Returns:
            Created OutboxEvent entity
        """
        outbox_event = OutboxEvent(
            event_name=event.event_name,
            payload=json.dumps(event.model_dump(mode="json")),
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id) if aggregate_id else None,
        )
        return await self.add(outbox_event)
    
    async def get_unpublished(
        self,
        limit: int = 100,
        include_retry_ready: bool = True,
    ) -> list[OutboxEvent]:
        """Get unpublished events ready for processing.
        
        Fetches events that:
        - Have not been published yet
        - Have not exceeded max retry count
        - Are ready for retry (next_retry_at is in the past or null)
        
        Events are ordered by created_at to ensure FIFO processing.
        
        Args:
            limit: Maximum number of events to fetch
            include_retry_ready: Include events ready for retry
            
        Returns:
            List of OutboxEvent entities ready for publishing
        """
        now = _utc_now()
        
        query = (
            OutboxEvent.objects()
            .where(OutboxEvent.is_published == False)
            .where(OutboxEvent.retry_count < OutboxEvent.max_retries)
        )
        
        if include_retry_ready:
            # Include events where next_retry_at is null OR in the past
            query = query.where(
                (OutboxEvent.next_retry_at.is_null()) | 
                (OutboxEvent.next_retry_at <= now)
            )
        else:
            # Only fresh events (never failed)
            query = query.where(OutboxEvent.next_retry_at.is_null())
        
        return await query.order_by(OutboxEvent.created_at).limit(limit)
    
    async def get_by_aggregate(
        self,
        aggregate_type: str,
        aggregate_id: str,
        include_published: bool = False,
    ) -> list[OutboxEvent]:
        """Get events by aggregate reference.
        
        Useful for debugging and auditing events related to a specific entity.
        
        Args:
            aggregate_type: Type of aggregate (e.g., 'User')
            aggregate_id: ID of aggregate
            include_published: Whether to include already published events
            
        Returns:
            List of OutboxEvent entities for the aggregate
        """
        query = (
            OutboxEvent.objects()
            .where(OutboxEvent.aggregate_type == aggregate_type)
            .where(OutboxEvent.aggregate_id == aggregate_id)
        )
        
        if not include_published:
            query = query.where(OutboxEvent.is_published == False)
        
        return await query.order_by(OutboxEvent.created_at)
    
    async def mark_published(self, event_id: UUID) -> None:
        """Mark event as successfully published.
        
        Sets is_published=True and published_at to current time.
        Clears any error message from previous failed attempts.
        
        Args:
            event_id: ID of the event to mark as published
        """
        await (
            OutboxEvent.update({
                OutboxEvent.is_published: True,
                OutboxEvent.published_at: _utc_now(),
                OutboxEvent.error_message: None,
            })
            .where(OutboxEvent.id == event_id)
        )
    
    async def mark_failed(
        self,
        event_id: UUID,
        error: str,
        backoff_base_seconds: int = 30,
    ) -> None:
        """Mark event as failed with error message.
        
        Increments retry_count and sets next_retry_at using exponential backoff.
        Backoff formula: backoff_base_seconds * 2^retry_count
        
        Example backoff sequence (30s base):
        - Retry 1: 30s
        - Retry 2: 60s (1 min)
        - Retry 3: 120s (2 min)
        - Retry 4: 240s (4 min)
        - Retry 5: 480s (8 min)
        
        Args:
            event_id: ID of the event to mark as failed
            error: Error message describing the failure
            backoff_base_seconds: Base delay for exponential backoff
        """
        # First, get current retry count
        event = await self.get(event_id)
        if event is None:
            return
        
        new_retry_count = event.retry_count + 1
        backoff_seconds = backoff_base_seconds * (2 ** (new_retry_count - 1))
        next_retry = _utc_now() + timedelta(seconds=backoff_seconds)
        
        await (
            OutboxEvent.update({
                OutboxEvent.retry_count: new_retry_count,
                OutboxEvent.error_message: error[:4000],  # Truncate long errors
                OutboxEvent.next_retry_at: next_retry,
            })
            .where(OutboxEvent.id == event_id)
        )
    
    async def get_failed_events(
        self,
        limit: int = 100,
        include_exhausted: bool = False,
    ) -> list[OutboxEvent]:
        """Get failed events for monitoring/debugging.
        
        Args:
            limit: Maximum number of events to fetch
            include_exhausted: Include events that exceeded max retries
            
        Returns:
            List of failed OutboxEvent entities
        """
        query = (
            OutboxEvent.objects()
            .where(OutboxEvent.is_published == False)
            .where(OutboxEvent.retry_count > 0)
        )
        
        if not include_exhausted:
            query = query.where(OutboxEvent.retry_count < OutboxEvent.max_retries)
        
        return await query.order_by(OutboxEvent.created_at).limit(limit)
    
    async def get_exhausted_events(self, limit: int = 100) -> list[OutboxEvent]:
        """Get events that have exhausted all retry attempts.
        
        These events require manual intervention or investigation.
        
        Args:
            limit: Maximum number of events to fetch
            
        Returns:
            List of exhausted OutboxEvent entities
        """
        return await (
            OutboxEvent.objects()
            .where(OutboxEvent.is_published == False)
            .where(OutboxEvent.retry_count >= OutboxEvent.max_retries)
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
    
    async def reset_exhausted(self, event_id: UUID) -> None:
        """Reset an exhausted event for reprocessing.
        
        Resets retry_count to 0 and clears next_retry_at,
        allowing the event to be picked up again.
        
        Args:
            event_id: ID of the event to reset
        """
        await (
            OutboxEvent.update({
                OutboxEvent.retry_count: 0,
                OutboxEvent.next_retry_at: None,
                OutboxEvent.error_message: None,
            })
            .where(OutboxEvent.id == event_id)
        )
    
    async def cleanup_published(
        self,
        older_than_hours: int = 24,
        limit: int = 1000,
    ) -> int:
        """Delete old published events to prevent table bloat.
        
        Should be run periodically (e.g., daily) to clean up
        successfully processed events.
        
        Args:
            older_than_hours: Delete events published more than this many hours ago
            limit: Maximum number of events to delete in one call
            
        Returns:
            Number of deleted events
        """
        cutoff = _utc_now() - timedelta(hours=older_than_hours)
        
        # Get IDs to delete (Piccolo doesn't support DELETE ... LIMIT directly)
        events_to_delete = await (
            OutboxEvent.select(OutboxEvent.id)
            .where(OutboxEvent.is_published == True)
            .where(OutboxEvent.published_at < cutoff)
            .limit(limit)
        )
        
        if not events_to_delete:
            return 0
        
        ids_to_delete = [e["id"] for e in events_to_delete]
        
        await (
            OutboxEvent.delete()
            .where(OutboxEvent.id.is_in(ids_to_delete))
        )
        
        return len(ids_to_delete)
    
    async def count_by_status(self) -> dict[str, int]:
        """Get event counts by status for monitoring.
        
        Returns:
            Dictionary with counts: published, pending, failed, exhausted
        """
        total = await OutboxEvent.count()
        published = await OutboxEvent.count().where(OutboxEvent.is_published == True)
        exhausted = await (
            OutboxEvent.count()
            .where(OutboxEvent.is_published == False)
            .where(OutboxEvent.retry_count >= OutboxEvent.max_retries)
        )
        failed = await (
            OutboxEvent.count()
            .where(OutboxEvent.is_published == False)
            .where(OutboxEvent.retry_count > 0)
            .where(OutboxEvent.retry_count < OutboxEvent.max_retries)
        )
        pending = total - published - failed - exhausted
        
        return {
            "total": total,
            "published": published,
            "pending": pending,
            "failed": failed,
            "exhausted": exhausted,
        }
