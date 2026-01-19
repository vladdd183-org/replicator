"""Event Bus Protocol (interface) according to Hyper-Porto architecture.

Defines the abstract interface that all event bus backends must implement.
Uses Python Protocol for structural subtyping (duck typing with type hints).
"""

from abc import abstractmethod
from typing import Any, Awaitable, Callable, Protocol, TypeVar, runtime_checkable

from src.Ship.Infrastructure.Events.Models import (
    EventBusStats,
    EventEnvelope,
    EventMetadata,
    EventPriority,
)

# Type variable for event payload
T = TypeVar("T")

# Handler type: async function that receives event_name and payload
EventHandler = Callable[[str, dict[str, Any]], Awaitable[None]]

# Handler with envelope: receives full envelope for advanced use cases
EnvelopeHandler = Callable[[EventEnvelope], Awaitable[None]]


@runtime_checkable
class EventBusProtocol(Protocol):
    """Protocol defining the Event Bus interface.
    
    All event bus backends (InMemory, Redis, RabbitMQ) must implement this interface.
    This enables dependency injection and easy backend switching via configuration.
    
    The protocol follows these principles:
    - Async-first: All operations are async for non-blocking I/O
    - Envelope pattern: Events are wrapped in EventEnvelope for metadata
    - Graceful lifecycle: start()/stop() for proper resource management
    - Health monitoring: stats() for observability
    
    Example implementation:
        class InMemoryEventBus:
            async def publish(
                self,
                event_name: str,
                payload: dict[str, Any],
                *,
                priority: EventPriority = EventPriority.NORMAL,
                metadata: EventMetadata | None = None,
            ) -> None:
                envelope = EventEnvelope(
                    event_name=event_name,
                    payload=payload,
                    metadata=metadata or EventMetadata(priority=priority),
                )
                await self._queue.put(envelope)
                
    Example usage:
        # Via DI (recommended)
        @post("/users")
        async def create_user(
            action: FromDishka[CreateUserAction],
            event_bus: FromDishka[EventBusProtocol],
        ) -> Response:
            result = await action.run(data)
            if isinstance(result, Success):
                await event_bus.publish(
                    "UserCreated",
                    {"user_id": str(result.unwrap().id)},
                )
            return result
    """
    
    # ============================================================
    # Publishing
    # ============================================================
    
    @abstractmethod
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
            event_name: Name of the event (e.g., 'UserCreated')
            payload: Event payload data (must be JSON-serializable)
            priority: Event priority for processing order
            metadata: Optional metadata for tracing and control
            
        Raises:
            EventPublishError: If publishing fails
            EventSerializationError: If payload is not serializable
            EventBusNotInitializedError: If event bus not started
        """
        ...
    
    @abstractmethod
    async def publish_envelope(self, envelope: EventEnvelope) -> None:
        """Publish a pre-built event envelope.
        
        Use this when you need full control over metadata and envelope fields.
        
        Args:
            envelope: Complete event envelope
            
        Raises:
            EventPublishError: If publishing fails
            EventBusNotInitializedError: If event bus not started
        """
        ...
    
    async def publish_many(
        self,
        events: list[tuple[str, dict[str, Any]]],
        *,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """Publish multiple events in a batch.
        
        Default implementation publishes sequentially.
        Backends may override for batch optimization.
        
        Args:
            events: List of (event_name, payload) tuples
            priority: Priority for all events in batch
            
        Raises:
            EventPublishError: If any publish fails (partial delivery possible)
        """
        for event_name, payload in events:
            await self.publish(event_name, payload, priority=priority)
    
    # ============================================================
    # Subscribing
    # ============================================================
    
    @abstractmethod
    async def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
        *,
        group: str | None = None,
    ) -> None:
        """Subscribe a handler to an event.
        
        Args:
            event_name: Name of the event to subscribe to
            handler: Async function to handle the event
            group: Optional consumer group for load balancing (backend-specific)
            
        Raises:
            EventSubscriptionError: If subscription fails
            EventBusNotInitializedError: If event bus not started
            
        Example:
            async def on_user_created(event_name: str, payload: dict) -> None:
                user_id = payload["user_id"]
                await send_welcome_email(user_id)
                
            await event_bus.subscribe("UserCreated", on_user_created)
        """
        ...
    
    @abstractmethod
    async def subscribe_envelope(
        self,
        event_name: str,
        handler: EnvelopeHandler,
        *,
        group: str | None = None,
    ) -> None:
        """Subscribe a handler that receives the full envelope.
        
        Use this when you need access to metadata (correlation_id, etc.).
        
        Args:
            event_name: Name of the event to subscribe to
            handler: Async function that receives EventEnvelope
            group: Optional consumer group
            
        Example:
            async def on_user_created(envelope: EventEnvelope) -> None:
                correlation_id = envelope.metadata.correlation_id
                payload = envelope.payload
                await process_with_tracing(correlation_id, payload)
                
            await event_bus.subscribe_envelope("UserCreated", on_user_created)
        """
        ...
    
    async def subscribe_many(
        self,
        event_names: list[str],
        handler: EventHandler,
        *,
        group: str | None = None,
    ) -> None:
        """Subscribe to multiple events with the same handler.
        
        Default implementation subscribes sequentially.
        
        Args:
            event_names: List of event names to subscribe to
            handler: Handler for all events
            group: Optional consumer group
        """
        for event_name in event_names:
            await self.subscribe(event_name, handler, group=group)
    
    @abstractmethod
    async def unsubscribe(
        self,
        event_name: str,
        handler: EventHandler | EnvelopeHandler | None = None,
    ) -> None:
        """Unsubscribe handler(s) from an event.
        
        Args:
            event_name: Name of the event to unsubscribe from
            handler: Specific handler to remove, or None to remove all
            
        Raises:
            EventSubscriptionError: If unsubscription fails
        """
        ...
    
    # ============================================================
    # Lifecycle
    # ============================================================
    
    @abstractmethod
    async def start(self) -> None:
        """Initialize and start the event bus.
        
        Must be called before publishing or subscribing.
        Establishes connections, creates queues/streams, etc.
        
        Raises:
            EventBusConnectionError: If connection fails
        """
        ...
    
    @abstractmethod
    async def stop(self) -> None:
        """Gracefully stop the event bus.
        
        Waits for pending events to be processed (with timeout).
        Closes connections and releases resources.
        Safe to call multiple times.
        """
        ...
    
    @abstractmethod
    async def wait_for_pending(self, timeout: float = 30.0) -> bool:
        """Wait for all pending events to be processed.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all events processed, False if timeout reached
        """
        ...
    
    # ============================================================
    # Health & Stats
    # ============================================================
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if event bus is healthy.
        
        Returns:
            True if event bus is operational
        """
        ...
    
    @abstractmethod
    async def stats(self) -> EventBusStats:
        """Get event bus statistics.
        
        Returns:
            EventBusStats with current metrics
        """
        ...
    
    # ============================================================
    # Properties
    # ============================================================
    
    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Check if event bus is currently running.
        
        Returns:
            True if started and not stopped
        """
        ...
    
    @property
    @abstractmethod
    def backend_type(self) -> str:
        """Get the backend type identifier.
        
        Returns:
            Backend type (e.g., 'inmemory', 'redis', 'rabbitmq')
        """
        ...


class EventBusWithRetryProtocol(EventBusProtocol, Protocol):
    """Extended protocol for event buses with retry support.
    
    Backends that support automatic retry and dead letter queues
    should implement this extended protocol.
    """
    
    @abstractmethod
    async def retry(self, envelope: EventEnvelope) -> None:
        """Retry a failed event.
        
        Args:
            envelope: Event to retry (with updated metadata)
            
        Raises:
            MaxRetriesExceededError: If max retries reached
        """
        ...
    
    @abstractmethod
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
        ...
    
    @abstractmethod
    async def get_dead_letters(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list["DeadLetterEvent"]:
        """Get events from dead letter queue.
        
        Args:
            limit: Maximum events to return
            offset: Offset for pagination
            
        Returns:
            List of dead letter events
        """
        ...
    
    @abstractmethod
    async def replay_dead_letter(self, event_id: str) -> bool:
        """Replay a dead letter event.
        
        Args:
            event_id: ID of the dead letter event to replay
            
        Returns:
            True if replayed successfully
        """
        ...


# Import for type hints
from src.Ship.Infrastructure.Events.Models import DeadLetterEvent


__all__ = [
    "EventHandler",
    "EnvelopeHandler",
    "EventBusProtocol",
    "EventBusWithRetryProtocol",
]
