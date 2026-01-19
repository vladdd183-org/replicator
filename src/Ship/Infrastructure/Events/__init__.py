"""Unified Event Bus Infrastructure for Hyper-Porto.

Provides a pluggable event bus abstraction with multiple backends:
- InMemory: For development and testing
- Redis Streams: For production (scalable, persistent)
- RabbitMQ: For enterprise (reliable, feature-rich)

Quick Start:
    from src.Ship.Infrastructure.Events import (
        create_event_bus,
        subscribe,
        EventBusProtocol,
    )
    from src.Ship.Configs import get_settings
    
    # Create event bus based on environment
    settings = get_settings()
    event_bus = create_event_bus(settings)
    await event_bus.start()
    
    # Subscribe to events
    @subscribe("UserCreated")
    async def on_user_created(event_name: str, payload: dict) -> None:
        user_id = payload["user_id"]
        await send_welcome_email(user_id)
    
    # Publish events
    await event_bus.publish(
        "UserCreated",
        {"user_id": "123", "email": "user@example.com"},
    )

Architecture:
    Protocol (Interface)
    └── BaseEventBus (Abstract base with common logic)
        ├── InMemoryEventBus (Development/Test)
        ├── RedisEventBus (Production)
        └── RabbitMQEventBus (Enterprise)
    
    Factory → Creates appropriate backend based on config

Features:
    - @subscribe decorator for declarative handlers
    - Event envelope with metadata (correlation_id, priority, etc.)
    - Retry logic with exponential backoff
    - Dead letter queue for failed events
    - Statistics and health checks
    - Structured concurrency with anyio

Integration with Hyper-Porto:
    - Events can be published from UnitOfWork after commit
    - DI integration via Dishka provider
    - Litestar lifecycle hooks for startup/shutdown

Example Integration:
    # In App.py
    async def on_startup(app: Litestar) -> None:
        event_bus = await create_and_start_event_bus(get_settings())
        app.state.event_bus = event_bus
        
        # Auto-register decorated handlers
        from src.Ship.Infrastructure.Events import auto_register_subscriptions
        await auto_register_subscriptions(event_bus)
    
    async def on_shutdown(app: Litestar) -> None:
        await app.state.event_bus.stop()
"""

# Protocol (interface)
from src.Ship.Infrastructure.Events.Protocol import (
    EventBusProtocol,
    EventBusWithRetryProtocol,
    EventHandler,
    EnvelopeHandler,
)

# Models
from src.Ship.Infrastructure.Events.Models import (
    EventEnvelope,
    EventMetadata,
    EventPriority,
    EventStatus,
    DeadLetterEvent,
    EventBusStats,
)

# Errors
from src.Ship.Infrastructure.Events.Errors import (
    EventBusError,
    EventBusNotInitializedError,
    EventBusConnectionError,
    EventPublishError,
    EventSubscriptionError,
    EventHandlerError,
    EventTimeoutError,
    MaxRetriesExceededError,
)

# Decorators
from src.Ship.Infrastructure.Events.Decorators import (
    subscribe,
    subscribe_all,
    subscribe_envelope,
    get_subscriptions,
    get_subscriptions_for_event,
    get_registered_events,
    clear_subscriptions,
    auto_register_subscriptions,
    SubscriptionInfo,
)

# Factory
from src.Ship.Infrastructure.Events.Factory import (
    create_event_bus,
    create_and_start_event_bus,
    EventBusFactory,
    BackendType,
    AVAILABLE_BACKENDS,
)

# Backends (for direct usage if needed)
from src.Ship.Infrastructure.Events.Backends import (
    BaseEventBus,
    InMemoryEventBus,
    RedisEventBus,
    RabbitMQEventBus,
)

# DI Provider
from src.Ship.Infrastructure.Events.Provider import (
    EventBusProvider,
    startup_event_bus,
    shutdown_event_bus,
)


__all__ = [
    # Protocol
    "EventBusProtocol",
    "EventBusWithRetryProtocol",
    "EventHandler",
    "EnvelopeHandler",
    # Models
    "EventEnvelope",
    "EventMetadata",
    "EventPriority",
    "EventStatus",
    "DeadLetterEvent",
    "EventBusStats",
    # Errors
    "EventBusError",
    "EventBusNotInitializedError",
    "EventBusConnectionError",
    "EventPublishError",
    "EventSubscriptionError",
    "EventHandlerError",
    "EventTimeoutError",
    "MaxRetriesExceededError",
    # Decorators
    "subscribe",
    "subscribe_all",
    "subscribe_envelope",
    "get_subscriptions",
    "get_subscriptions_for_event",
    "get_registered_events",
    "clear_subscriptions",
    "auto_register_subscriptions",
    "SubscriptionInfo",
    # Factory
    "create_event_bus",
    "create_and_start_event_bus",
    "EventBusFactory",
    "BackendType",
    "AVAILABLE_BACKENDS",
    # Backends
    "BaseEventBus",
    "InMemoryEventBus",
    "RedisEventBus",
    "RabbitMQEventBus",
    # DI Provider
    "EventBusProvider",
    "startup_event_bus",
    "shutdown_event_bus",
]
