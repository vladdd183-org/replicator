"""Outbox Event Publisher - TaskIQ Background Worker.

Processes unpublished events from the outbox table and publishes them
via the configured event system (Litestar events by default).

This worker runs periodically to ensure reliable event delivery,
implementing the "polling publisher" variant of the Outbox pattern.
"""

import json
from typing import TYPE_CHECKING, Any
from uuid import UUID

import logfire

from src.Ship.Configs import get_settings
from src.Ship.Infrastructure.Events.Outbox.Models import OutboxEvent
from src.Ship.Infrastructure.Events.Outbox.Repository import OutboxEventRepository
from src.Ship.Infrastructure.Workers.Broker import broker

if TYPE_CHECKING:
    from litestar import Litestar


# Module-level logger
logger = logfire


class OutboxPublisherService:
    """Service for publishing outbox events.
    
    Encapsulates the logic for:
    - Fetching unpublished events
    - Publishing events via configured mechanism
    - Handling success/failure and retries
    - Cleanup of old events
    
    Can be used both via TaskIQ worker and programmatically.
    
    Example:
        # Via TaskIQ (scheduled)
        @broker.task(schedule=[cron("* * * * *")])
        async def publish_outbox_events():
            service = OutboxPublisherService()
            result = await service.process_batch()
            
        # Programmatically
        service = OutboxPublisherService(app=litestar_app)
        await service.process_batch(limit=50)
    """
    
    def __init__(
        self,
        repository: OutboxEventRepository | None = None,
        app: "Litestar | None" = None,
        emit_func: Any | None = None,
    ) -> None:
        """Initialize publisher service.
        
        Args:
            repository: OutboxEventRepository instance (created if not provided)
            app: Litestar app for event emission (optional)
            emit_func: Custom emit function for testing (optional)
        """
        self.repository = repository or OutboxEventRepository()
        self.app = app
        self._emit = emit_func or (app.emit if app else None)
        self.settings = get_settings()
    
    async def process_batch(
        self,
        limit: int = 100,
    ) -> dict[str, int]:
        """Process a batch of unpublished events.
        
        Fetches unpublished events, attempts to publish each one,
        and updates their status accordingly.
        
        Args:
            limit: Maximum number of events to process
            
        Returns:
            Statistics dict: {processed, published, failed}
        """
        stats = {"processed": 0, "published": 0, "failed": 0}
        
        events = await self.repository.get_unpublished(limit=limit)
        
        if not events:
            logger.debug("No unpublished outbox events found")
            return stats
        
        logger.info(
            f"Processing {len(events)} outbox events",
            event_count=len(events),
        )
        
        for event in events:
            stats["processed"] += 1
            success = await self._publish_single_event(event)
            
            if success:
                stats["published"] += 1
            else:
                stats["failed"] += 1
        
        logger.info(
            "Outbox batch processed",
            processed=stats["processed"],
            published=stats["published"],
            failed=stats["failed"],
        )
        
        return stats
    
    async def _publish_single_event(self, event: OutboxEvent) -> bool:
        """Publish a single outbox event.
        
        Attempts to publish the event and updates its status.
        On failure, increments retry count with exponential backoff.
        
        Args:
            event: OutboxEvent to publish
            
        Returns:
            True if published successfully, False otherwise
        """
        event_id = event.id
        event_name = event.event_name
        
        try:
            # Parse the payload
            payload = json.loads(event.payload)
            
            # Publish via configured mechanism
            await self._emit_event(event_name, payload)
            
            # Mark as published
            await self.repository.mark_published(event_id)
            
            logger.info(
                f"Published outbox event: {event_name}",
                event_id=str(event_id),
                event_name=event_name,
                retry_count=event.retry_count,
            )
            
            return True
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON payload: {e}"
            logger.error(
                error_msg,
                event_id=str(event_id),
                event_name=event_name,
            )
            # Mark as failed but don't retry - payload is corrupted
            await self.repository.mark_failed(event_id, error_msg)
            # Set max retries to prevent further attempts
            await OutboxEvent.update({
                OutboxEvent.retry_count: OutboxEvent.max_retries
            }).where(OutboxEvent.id == event_id)
            return False
            
        except Exception as e:
            error_msg = f"Failed to publish: {type(e).__name__}: {e}"
            logger.error(
                f"Failed to publish outbox event: {event_name}",
                event_id=str(event_id),
                event_name=event_name,
                error=str(e),
                retry_count=event.retry_count,
            )
            await self.repository.mark_failed(event_id, error_msg)
            return False
    
    async def _emit_event(self, event_name: str, payload: dict) -> None:
        """Emit event via configured mechanism.
        
        Priority:
        1. Custom emit function (for testing)
        2. Litestar app.emit (for HTTP context)
        3. Fallback to logging (when no emitter available)
        
        Args:
            event_name: Name of the event
            payload: Event payload dict
        """
        if self._emit is not None:
            # Emit via Litestar events system
            # Pass app instance for listeners that need it
            self._emit(event_name, app=self.app, **payload)
            return
        
        # Fallback: log the event (useful for development/debugging)
        logger.info(
            f"📤 Outbox event (no emitter): {event_name}",
            event_name=event_name,
            payload=payload,
        )
    
    async def cleanup_old_events(
        self,
        older_than_hours: int = 24,
        limit: int = 1000,
    ) -> int:
        """Clean up old published events.
        
        Removes events that have been successfully published
        and are older than the specified threshold.
        
        Args:
            older_than_hours: Delete events older than this
            limit: Maximum events to delete per call
            
        Returns:
            Number of deleted events
        """
        deleted = await self.repository.cleanup_published(
            older_than_hours=older_than_hours,
            limit=limit,
        )
        
        if deleted > 0:
            logger.info(
                f"Cleaned up {deleted} old outbox events",
                deleted_count=deleted,
                older_than_hours=older_than_hours,
            )
        
        return deleted
    
    async def get_stats(self) -> dict[str, int]:
        """Get outbox statistics for monitoring.
        
        Returns:
            Dict with counts by status
        """
        return await self.repository.count_by_status()


# =============================================================================
# TaskIQ Worker Tasks
# =============================================================================

@broker.task
async def publish_outbox_events(limit: int = 100) -> dict[str, int]:
    """TaskIQ task: Process unpublished outbox events.
    
    This task is scheduled to run periodically (e.g., every minute)
    to process any events waiting in the outbox.
    
    Args:
        limit: Maximum events to process per run
        
    Returns:
        Processing statistics
    """
    service = OutboxPublisherService()
    return await service.process_batch(limit=limit)


@broker.task
async def cleanup_outbox_events(
    older_than_hours: int = 24,
    limit: int = 1000,
) -> int:
    """TaskIQ task: Clean up old published outbox events.
    
    Should be scheduled less frequently (e.g., daily) to prevent
    the outbox table from growing indefinitely.
    
    Args:
        older_than_hours: Delete events older than this
        limit: Maximum events to delete per run
        
    Returns:
        Number of deleted events
    """
    service = OutboxPublisherService()
    return await service.cleanup_old_events(
        older_than_hours=older_than_hours,
        limit=limit,
    )


@broker.task
async def get_outbox_stats() -> dict[str, int]:
    """TaskIQ task: Get outbox statistics.
    
    Useful for monitoring and alerting on outbox health.
    
    Returns:
        Dict with event counts by status
    """
    service = OutboxPublisherService()
    return await service.get_stats()


@broker.task
async def reset_exhausted_event(event_id: str) -> bool:
    """TaskIQ task: Reset an exhausted event for reprocessing.
    
    Use this to manually retry events that have exceeded max retries.
    
    Args:
        event_id: UUID of the event to reset (as string)
        
    Returns:
        True if reset successful
    """
    try:
        repository = OutboxEventRepository()
        await repository.reset_exhausted(UUID(event_id))
        logger.info(f"Reset exhausted outbox event: {event_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to reset outbox event: {event_id}", error=str(e))
        return False


@broker.task
async def publish_single_event(event_id: str) -> bool:
    """TaskIQ task: Force publish a single event.
    
    Bypasses the normal batch processing to immediately
    attempt publishing a specific event.
    
    Args:
        event_id: UUID of the event to publish (as string)
        
    Returns:
        True if published successfully
    """
    try:
        repository = OutboxEventRepository()
        event = await repository.get(UUID(event_id))
        
        if event is None:
            logger.error(f"Outbox event not found: {event_id}")
            return False
        
        if event.is_published:
            logger.info(f"Outbox event already published: {event_id}")
            return True
        
        service = OutboxPublisherService(repository=repository)
        return await service._publish_single_event(event)
        
    except Exception as e:
        logger.error(f"Failed to publish single event: {event_id}", error=str(e))
        return False
