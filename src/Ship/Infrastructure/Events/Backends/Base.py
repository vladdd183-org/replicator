"""Abstract Base Event Bus with common logic for all backends.

Provides shared implementation for:
- Handler registration and dispatch
- Event envelope creation and validation
- Statistics tracking
- Dead letter queue management
- Retry logic with exponential backoff
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import anyio
import logfire

from src.Ship.Infrastructure.Events.Errors import (
    EventBusNotInitializedError,
    EventPublishError,
    EventSerializationError,
    MaxRetriesExceededError,
)
from src.Ship.Infrastructure.Events.Models import (
    DeadLetterEvent,
    EventBusStats,
    EventEnvelope,
    EventMetadata,
    EventPriority,
)
from src.Ship.Infrastructure.Events.Protocol import (
    EnvelopeHandler,
    EventHandler,
)


@dataclass
class HandlerInfo:
    """Metadata about a registered handler."""
    
    handler: EventHandler | EnvelopeHandler
    handler_name: str
    is_envelope_handler: bool
    group: str | None = None


@dataclass
class BaseEventBus(ABC):
    """Abstract base class for Event Bus implementations.
    
    Provides common functionality shared by all backends:
    - Handler registration and dispatch
    - Statistics tracking
    - Dead letter queue (in-memory by default)
    - Retry logic
    
    Subclasses must implement:
    - _do_publish(): Backend-specific publish logic
    - _do_start(): Backend-specific initialization
    - _do_stop(): Backend-specific cleanup
    - _do_health_check(): Backend-specific health check
    
    Example subclass:
        @dataclass
        class InMemoryEventBus(BaseEventBus):
            async def _do_publish(self, envelope: EventEnvelope) -> None:
                await self._queue.put(envelope)
                
            async def _do_start(self) -> None:
                self._queue = asyncio.Queue()
                
            async def _do_stop(self) -> None:
                pass
    """
    
    # Configuration
    max_dead_letters: int = field(default=10000)
    default_timeout: float = field(default=30.0)
    retry_base_delay: float = field(default=1.0)
    retry_max_delay: float = field(default=60.0)
    
    # Internal state
    _handlers: dict[str, list[HandlerInfo]] = field(default_factory=dict, init=False)
    _dead_letters: list[DeadLetterEvent] = field(default_factory=list, init=False)
    _running: bool = field(default=False, init=False)
    
    # Statistics
    _stats_total_published: int = field(default=0, init=False)
    _stats_total_delivered: int = field(default=0, init=False)
    _stats_total_failed: int = field(default=0, init=False)
    _stats_total_retried: int = field(default=0, init=False)
    _stats_last_publish: datetime | None = field(default=None, init=False)
    _stats_last_delivery: datetime | None = field(default=None, init=False)
    _stats_processing_times: list[float] = field(default_factory=list, init=False)
    
    # ============================================================
    # Abstract methods - must be implemented by subclasses
    # ============================================================
    
    @abstractmethod
    async def _do_publish(self, envelope: EventEnvelope) -> None:
        """Backend-specific publish implementation.
        
        Args:
            envelope: Event envelope to publish
        """
        ...
    
    @abstractmethod
    async def _do_start(self) -> None:
        """Backend-specific startup logic."""
        ...
    
    @abstractmethod
    async def _do_stop(self) -> None:
        """Backend-specific shutdown logic."""
        ...
    
    @abstractmethod
    async def _do_health_check(self) -> bool:
        """Backend-specific health check.
        
        Returns:
            True if backend is healthy
        """
        ...
    
    @property
    @abstractmethod
    def backend_type(self) -> str:
        """Get backend type identifier.
        
        Returns:
            Backend type string (e.g., 'inmemory', 'redis', 'rabbitmq')
        """
        ...
    
    # ============================================================
    # Publishing - EventBusProtocol implementation
    # ============================================================
    
    async def publish(
        self,
        event_name: str,
        payload: dict[str, Any],
        *,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: EventMetadata | None = None,
    ) -> None:
        """Publish an event to all subscribers.
        
        Args:
            event_name: Name of the event
            payload: Event payload (must be JSON-serializable)
            priority: Event priority
            metadata: Optional metadata for tracing
            
        Raises:
            EventBusNotInitializedError: If not started
            EventPublishError: If publishing fails
            EventSerializationError: If payload invalid
        """
        self._ensure_running()
        
        # Validate payload is serializable
        try:
            import json
            json.dumps(payload)
        except (TypeError, ValueError) as e:
            raise EventSerializationError(
                event_name=event_name,
                operation="serialize",
                reason=str(e),
            )
        
        # Create envelope
        envelope = EventEnvelope(
            event_name=event_name,
            payload=payload,
            metadata=metadata or EventMetadata(priority=priority),
        )
        
        await self.publish_envelope(envelope)
    
    async def publish_envelope(self, envelope: EventEnvelope) -> None:
        """Publish a pre-built event envelope.
        
        Args:
            envelope: Complete event envelope
            
        Raises:
            EventBusNotInitializedError: If not started
            EventPublishError: If publishing fails
        """
        self._ensure_running()
        
        try:
            await self._do_publish(envelope)
            
            # Update stats
            self._stats_total_published += 1
            self._stats_last_publish = datetime.now(timezone.utc)
            
            logfire.debug(
                f"📤 Published event: {envelope.event_name}",
                event_name=envelope.event_name,
                event_id=str(envelope.metadata.event_id),
                priority=envelope.metadata.priority.value,
            )
            
        except Exception as e:
            logfire.error(
                f"❌ Failed to publish event: {envelope.event_name}",
                event_name=envelope.event_name,
                error=str(e),
            )
            raise EventPublishError(
                event_name=envelope.event_name,
                reason=str(e),
                event_id=envelope.metadata.event_id,
            )
    
    async def publish_many(
        self,
        events: list[tuple[str, dict[str, Any]]],
        *,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """Publish multiple events in a batch.
        
        Args:
            events: List of (event_name, payload) tuples
            priority: Priority for all events
        """
        for event_name, payload in events:
            await self.publish(event_name, payload, priority=priority)
    
    # ============================================================
    # Subscribing - EventBusProtocol implementation
    # ============================================================
    
    async def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
        *,
        group: str | None = None,
    ) -> None:
        """Subscribe a handler to an event.
        
        Args:
            event_name: Event to subscribe to
            handler: Async handler function
            group: Optional consumer group
        """
        info = HandlerInfo(
            handler=handler,
            handler_name=handler.__qualname__ if hasattr(handler, "__qualname__") else str(handler),
            is_envelope_handler=False,
            group=group,
        )
        
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        
        self._handlers[event_name].append(info)
        
        logfire.debug(
            f"📥 Subscribed handler: {info.handler_name} -> {event_name}",
            event_name=event_name,
            handler=info.handler_name,
            group=group,
        )
    
    async def subscribe_envelope(
        self,
        event_name: str,
        handler: EnvelopeHandler,
        *,
        group: str | None = None,
    ) -> None:
        """Subscribe a handler that receives the full envelope.
        
        Args:
            event_name: Event to subscribe to
            handler: Async handler that receives EventEnvelope
            group: Optional consumer group
        """
        info = HandlerInfo(
            handler=handler,
            handler_name=handler.__qualname__ if hasattr(handler, "__qualname__") else str(handler),
            is_envelope_handler=True,
            group=group,
        )
        
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        
        self._handlers[event_name].append(info)
        
        logfire.debug(
            f"📥 Subscribed envelope handler: {info.handler_name} -> {event_name}",
            event_name=event_name,
            handler=info.handler_name,
            group=group,
        )
    
    async def subscribe_many(
        self,
        event_names: list[str],
        handler: EventHandler,
        *,
        group: str | None = None,
    ) -> None:
        """Subscribe to multiple events with the same handler.
        
        Args:
            event_names: Events to subscribe to
            handler: Handler for all events
            group: Optional consumer group
        """
        for event_name in event_names:
            await self.subscribe(event_name, handler, group=group)
    
    async def unsubscribe(
        self,
        event_name: str,
        handler: EventHandler | EnvelopeHandler | None = None,
    ) -> None:
        """Unsubscribe handler(s) from an event.
        
        Args:
            event_name: Event to unsubscribe from
            handler: Specific handler, or None to remove all
        """
        if event_name not in self._handlers:
            return
        
        if handler is None:
            del self._handlers[event_name]
        else:
            self._handlers[event_name] = [
                h for h in self._handlers[event_name]
                if h.handler != handler
            ]
    
    # ============================================================
    # Handler dispatch - used by backends
    # ============================================================
    
    async def dispatch(self, envelope: EventEnvelope) -> None:
        """Dispatch an event to all registered handlers.
        
        Called by backends when an event is received.
        Handles errors, retries, and dead letter queue.
        
        Args:
            envelope: Event envelope to dispatch
        """
        handlers = self._handlers.get(envelope.event_name, [])
        
        if not handlers:
            logfire.debug(
                f"📭 No handlers for event: {envelope.event_name}",
                event_name=envelope.event_name,
            )
            return
        
        start_time = anyio.current_time()
        
        for handler_info in handlers:
            await self._dispatch_to_handler(envelope, handler_info)
        
        # Update stats
        elapsed = anyio.current_time() - start_time
        self._stats_processing_times.append(elapsed * 1000)  # ms
        if len(self._stats_processing_times) > 1000:
            self._stats_processing_times = self._stats_processing_times[-1000:]
        
        self._stats_total_delivered += 1
        self._stats_last_delivery = datetime.now(timezone.utc)
    
    async def _dispatch_to_handler(
        self,
        envelope: EventEnvelope,
        handler_info: HandlerInfo,
    ) -> None:
        """Dispatch event to a single handler with error handling.
        
        Args:
            envelope: Event envelope
            handler_info: Handler metadata
        """
        try:
            if handler_info.is_envelope_handler:
                await handler_info.handler(envelope)  # type: ignore
            else:
                await handler_info.handler(envelope.event_name, envelope.payload)  # type: ignore
            
            logfire.debug(
                f"✅ Handler completed: {handler_info.handler_name}",
                event_name=envelope.event_name,
                handler=handler_info.handler_name,
            )
            
        except Exception as e:
            self._stats_total_failed += 1
            
            logfire.error(
                f"❌ Handler failed: {handler_info.handler_name}",
                event_name=envelope.event_name,
                handler=handler_info.handler_name,
                error=str(e),
                exc_info=True,
            )
            
            # Handle retry or dead letter
            if envelope.metadata.should_retry():
                await self._handle_retry(envelope, handler_info, e)
            else:
                await self._handle_dead_letter(envelope, handler_info, e)
    
    async def _handle_retry(
        self,
        envelope: EventEnvelope,
        handler_info: HandlerInfo,
        error: Exception,
    ) -> None:
        """Handle event retry with exponential backoff.
        
        Args:
            envelope: Failed event envelope
            handler_info: Handler that failed
            error: Exception that occurred
        """
        self._stats_total_retried += 1
        
        # Calculate delay with exponential backoff
        retry_count = envelope.metadata.retry_count + 1
        delay = min(
            self.retry_base_delay * (2 ** (retry_count - 1)),
            self.retry_max_delay,
        )
        
        logfire.warning(
            f"🔄 Retrying event: {envelope.event_name} (attempt {retry_count})",
            event_name=envelope.event_name,
            retry_count=retry_count,
            delay_seconds=delay,
        )
        
        # Create new envelope with incremented retry count
        new_metadata = envelope.metadata.with_retry()
        new_envelope = envelope.model_copy(update={"metadata": new_metadata})
        
        # Wait and republish
        await anyio.sleep(delay)
        await self.publish_envelope(new_envelope)
    
    async def _handle_dead_letter(
        self,
        envelope: EventEnvelope,
        handler_info: HandlerInfo,
        error: Exception,
    ) -> None:
        """Move failed event to dead letter queue.
        
        Args:
            envelope: Failed event envelope
            handler_info: Handler that failed
            error: Exception that occurred
        """
        import traceback
        
        dead_letter = DeadLetterEvent(
            envelope=envelope,
            failure_reason=str(error),
            error_type=type(error).__name__,
            error_traceback=traceback.format_exc(),
            handler_name=handler_info.handler_name,
        )
        
        # Respect max dead letters
        if len(self._dead_letters) >= self.max_dead_letters:
            self._dead_letters.pop(0)
        
        self._dead_letters.append(dead_letter)
        
        logfire.error(
            f"💀 Event moved to dead letter queue: {envelope.event_name}",
            event_name=envelope.event_name,
            event_id=str(envelope.metadata.event_id),
            handler=handler_info.handler_name,
            reason=str(error),
        )
    
    # ============================================================
    # Retry protocol - EventBusWithRetryProtocol implementation
    # ============================================================
    
    async def retry(self, envelope: EventEnvelope) -> None:
        """Retry a failed event.
        
        Args:
            envelope: Event to retry
            
        Raises:
            MaxRetriesExceededError: If max retries reached
        """
        if not envelope.metadata.should_retry():
            raise MaxRetriesExceededError(
                event_name=envelope.event_name,
                max_retries=envelope.metadata.max_retries,
                event_id=envelope.metadata.event_id,
            )
        
        new_metadata = envelope.metadata.with_retry()
        new_envelope = envelope.model_copy(update={"metadata": new_metadata})
        
        await self.publish_envelope(new_envelope)
    
    async def dead_letter(
        self,
        envelope: EventEnvelope,
        reason: str,
        error_type: str | None = None,
        traceback: str | None = None,
    ) -> None:
        """Move event to dead letter queue.
        
        Args:
            envelope: Event that failed
            reason: Failure reason
            error_type: Exception class name
            traceback: Stack trace if available
        """
        dead_letter = DeadLetterEvent(
            envelope=envelope,
            failure_reason=reason,
            error_type=error_type or "",
            error_traceback=traceback,
        )
        
        if len(self._dead_letters) >= self.max_dead_letters:
            self._dead_letters.pop(0)
        
        self._dead_letters.append(dead_letter)
    
    async def get_dead_letters(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DeadLetterEvent]:
        """Get events from dead letter queue.
        
        Args:
            limit: Maximum events to return
            offset: Offset for pagination
            
        Returns:
            List of dead letter events
        """
        return self._dead_letters[offset:offset + limit]
    
    async def replay_dead_letter(self, event_id: str) -> bool:
        """Replay a dead letter event.
        
        Args:
            event_id: ID of the dead letter event
            
        Returns:
            True if replayed successfully
        """
        from uuid import UUID
        
        target_id = UUID(event_id)
        
        for i, dl in enumerate(self._dead_letters):
            if dl.envelope.metadata.event_id == target_id:
                # Reset retry count and republish
                new_metadata = dl.envelope.metadata.model_copy(update={"retry_count": 0})
                new_envelope = dl.envelope.model_copy(update={"metadata": new_metadata})
                
                await self.publish_envelope(new_envelope)
                self._dead_letters.pop(i)
                
                logfire.info(
                    f"🔄 Replayed dead letter: {dl.envelope.event_name}",
                    event_name=dl.envelope.event_name,
                    event_id=event_id,
                )
                
                return True
        
        return False
    
    # ============================================================
    # Lifecycle
    # ============================================================
    
    async def start(self) -> None:
        """Initialize and start the event bus."""
        if self._running:
            return
        
        logfire.info(
            f"🚀 Starting {self.backend_type} event bus",
            backend=self.backend_type,
        )
        
        await self._do_start()
        self._running = True
        
        logfire.info(
            f"✅ {self.backend_type} event bus started",
            backend=self.backend_type,
        )
    
    async def stop(self) -> None:
        """Gracefully stop the event bus."""
        if not self._running:
            return
        
        logfire.info(
            f"🛑 Stopping {self.backend_type} event bus",
            backend=self.backend_type,
        )
        
        await self._do_stop()
        self._running = False
        
        logfire.info(
            f"✅ {self.backend_type} event bus stopped",
            backend=self.backend_type,
            total_published=self._stats_total_published,
            total_delivered=self._stats_total_delivered,
            total_failed=self._stats_total_failed,
        )
    
    async def wait_for_pending(self, timeout: float = 30.0) -> bool:
        """Wait for all pending events to be processed.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if all processed, False if timeout
        """
        # Default implementation - subclasses may override
        return True
    
    # ============================================================
    # Health & Stats
    # ============================================================
    
    async def health_check(self) -> bool:
        """Check if event bus is healthy.
        
        Returns:
            True if healthy
        """
        if not self._running:
            return False
        
        return await self._do_health_check()
    
    async def stats(self) -> EventBusStats:
        """Get event bus statistics.
        
        Returns:
            EventBusStats with current metrics
        """
        avg_time = (
            sum(self._stats_processing_times) / len(self._stats_processing_times)
            if self._stats_processing_times else 0.0
        )
        
        return EventBusStats(
            total_published=self._stats_total_published,
            total_delivered=self._stats_total_delivered,
            total_failed=self._stats_total_failed,
            total_retried=self._stats_total_retried,
            dead_letter_count=len(self._dead_letters),
            active_subscriptions=sum(len(h) for h in self._handlers.values()),
            avg_processing_time_ms=avg_time,
            last_publish_at=self._stats_last_publish,
            last_delivery_at=self._stats_last_delivery,
            is_healthy=self._running,
            backend_type=self.backend_type,
        )
    
    @property
    def is_running(self) -> bool:
        """Check if event bus is running.
        
        Returns:
            True if started and not stopped
        """
        return self._running
    
    # ============================================================
    # Helpers
    # ============================================================
    
    def _ensure_running(self) -> None:
        """Ensure event bus is running.
        
        Raises:
            EventBusNotInitializedError: If not running
        """
        if not self._running:
            raise EventBusNotInitializedError(message="Event bus not initialized. Call start() first.")
    
    def get_handlers(self, event_name: str) -> list[HandlerInfo]:
        """Get handlers for an event.
        
        Args:
            event_name: Event name
            
        Returns:
            List of handler infos
        """
        return self._handlers.get(event_name, [])
    
    def get_all_event_names(self) -> list[str]:
        """Get all registered event names.
        
        Returns:
            List of event names
        """
        return list(self._handlers.keys())


__all__ = ["BaseEventBus", "HandlerInfo"]
