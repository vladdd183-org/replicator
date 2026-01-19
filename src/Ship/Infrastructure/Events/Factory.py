"""Event Bus Factory for Hyper-Porto.

Creates the appropriate event bus backend based on environment and configuration.
Follows Factory pattern for easy backend switching.

Usage:
    from src.Ship.Infrastructure.Events import create_event_bus
    from src.Ship.Configs import get_settings
    
    settings = get_settings()
    event_bus = create_event_bus(settings)
    await event_bus.start()
"""

from typing import Literal

import logfire

from src.Ship.Configs.Settings import Settings
from src.Ship.Infrastructure.Events.Backends.Base import BaseEventBus
from src.Ship.Infrastructure.Events.Errors import BackendNotSupportedError
from src.Ship.Infrastructure.Events.Protocol import EventBusProtocol


# Available backend types
BackendType = Literal["inmemory", "redis", "rabbitmq", "auto"]

# Environment to backend mapping
ENV_BACKEND_MAP: dict[str, BackendType] = {
    "development": "inmemory",
    "staging": "redis",
    "production": "redis",
    "testing": "inmemory",
}

AVAILABLE_BACKENDS = frozenset(["inmemory", "redis", "rabbitmq"])


def create_event_bus(
    settings: Settings,
    *,
    backend: BackendType = "auto",
    **backend_kwargs,
) -> EventBusProtocol:
    """Create an event bus instance based on configuration.
    
    Factory function that instantiates the appropriate backend
    based on environment or explicit backend parameter.
    
    Args:
        settings: Application settings
        backend: Backend type ("inmemory", "redis", "rabbitmq", "auto")
                 If "auto", selects based on app_env
        **backend_kwargs: Additional arguments passed to backend constructor
        
    Returns:
        EventBusProtocol implementation
        
    Raises:
        BackendNotSupportedError: If backend type is invalid
        
    Example - Auto selection:
        settings = get_settings()
        event_bus = create_event_bus(settings)  # Based on app_env
        
    Example - Explicit backend:
        event_bus = create_event_bus(
            settings,
            backend="redis",
            consumer_group="my-service",
        )
        
    Example - Custom configuration:
        event_bus = create_event_bus(
            settings,
            backend="rabbitmq",
            prefetch_count=20,
            confirm_delivery=True,
        )
    """
    # Determine backend type
    if backend == "auto":
        backend = ENV_BACKEND_MAP.get(settings.app_env, "inmemory")
    
    # Validate backend
    if backend not in AVAILABLE_BACKENDS:
        raise BackendNotSupportedError(
            backend_name=backend,
            available_backends=", ".join(sorted(AVAILABLE_BACKENDS)),
        )
    
    logfire.info(
        f"Creating {backend} event bus",
        backend=backend,
        app_env=settings.app_env,
    )
    
    # Create backend instance
    match backend:
        case "inmemory":
            return _create_inmemory_bus(**backend_kwargs)
        
        case "redis":
            return _create_redis_bus(settings, **backend_kwargs)
        
        case "rabbitmq":
            return _create_rabbitmq_bus(settings, **backend_kwargs)
        
        case _:
            raise BackendNotSupportedError(
                backend_name=backend,
                available_backends=", ".join(sorted(AVAILABLE_BACKENDS)),
            )


def _create_inmemory_bus(**kwargs) -> EventBusProtocol:
    """Create InMemory event bus.
    
    Args:
        **kwargs: InMemoryEventBus configuration
        
    Returns:
        InMemoryEventBus instance
    """
    from src.Ship.Infrastructure.Events.Backends.InMemory import InMemoryEventBus
    
    return InMemoryEventBus(**kwargs)


def _create_redis_bus(settings: Settings, **kwargs) -> EventBusProtocol:
    """Create Redis event bus.
    
    Args:
        settings: Application settings (for redis_url)
        **kwargs: RedisEventBus configuration overrides
        
    Returns:
        RedisEventBus instance
    """
    from src.Ship.Infrastructure.Events.Backends.Redis import RedisEventBus
    
    # Default configuration from settings
    config = {
        "redis_url": settings.redis_url,
        "consumer_group": f"{settings.app_name.lower().replace(' ', '-')}-events",
    }
    
    # Override with explicit kwargs
    config.update(kwargs)
    
    return RedisEventBus(**config)


def _create_rabbitmq_bus(settings: Settings, **kwargs) -> EventBusProtocol:
    """Create RabbitMQ event bus.
    
    Args:
        settings: Application settings (for rabbitmq_url)
        **kwargs: RabbitMQEventBus configuration overrides
        
    Returns:
        RabbitMQEventBus instance
    """
    from src.Ship.Infrastructure.Events.Backends.RabbitMQ import RabbitMQEventBus
    
    # Default configuration from settings
    config = {
        "rabbitmq_url": getattr(settings, "rabbitmq_url", "amqp://guest:guest@localhost:5672/"),
        "exchange_name": f"{settings.app_name.lower().replace(' ', '-')}-events",
    }
    
    # Override with explicit kwargs
    config.update(kwargs)
    
    return RabbitMQEventBus(**config)


async def create_and_start_event_bus(
    settings: Settings,
    *,
    backend: BackendType = "auto",
    **backend_kwargs,
) -> EventBusProtocol:
    """Create and start an event bus in one call.
    
    Convenience function that creates and initializes the event bus.
    
    Args:
        settings: Application settings
        backend: Backend type
        **backend_kwargs: Backend configuration
        
    Returns:
        Started EventBusProtocol implementation
        
    Example:
        event_bus = await create_and_start_event_bus(settings)
        
        # Use event bus
        await event_bus.publish("Test", {"data": "value"})
        
        # Cleanup
        await event_bus.stop()
    """
    event_bus = create_event_bus(settings, backend=backend, **backend_kwargs)
    await event_bus.start()
    return event_bus


class EventBusFactory:
    """Factory class for creating event bus instances.
    
    Alternative object-oriented interface for event bus creation.
    Useful for DI registration and testing.
    
    Example:
        factory = EventBusFactory(settings)
        event_bus = factory.create()
        
        # Or with specific backend
        event_bus = factory.create_redis(consumer_group="workers")
    """
    
    def __init__(self, settings: Settings) -> None:
        """Initialize factory with settings.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
    
    def create(
        self,
        backend: BackendType = "auto",
        **kwargs,
    ) -> EventBusProtocol:
        """Create event bus with auto or specified backend.
        
        Args:
            backend: Backend type
            **kwargs: Backend configuration
            
        Returns:
            EventBusProtocol implementation
        """
        return create_event_bus(self.settings, backend=backend, **kwargs)
    
    def create_inmemory(self, **kwargs) -> EventBusProtocol:
        """Create InMemory event bus.
        
        Args:
            **kwargs: InMemoryEventBus configuration
            
        Returns:
            InMemoryEventBus instance
        """
        return create_event_bus(self.settings, backend="inmemory", **kwargs)
    
    def create_redis(self, **kwargs) -> EventBusProtocol:
        """Create Redis event bus.
        
        Args:
            **kwargs: RedisEventBus configuration
            
        Returns:
            RedisEventBus instance
        """
        return create_event_bus(self.settings, backend="redis", **kwargs)
    
    def create_rabbitmq(self, **kwargs) -> EventBusProtocol:
        """Create RabbitMQ event bus.
        
        Args:
            **kwargs: RabbitMQEventBus configuration
            
        Returns:
            RabbitMQEventBus instance
        """
        return create_event_bus(self.settings, backend="rabbitmq", **kwargs)
    
    async def create_and_start(
        self,
        backend: BackendType = "auto",
        **kwargs,
    ) -> EventBusProtocol:
        """Create and start event bus.
        
        Args:
            backend: Backend type
            **kwargs: Backend configuration
            
        Returns:
            Started EventBusProtocol implementation
        """
        return await create_and_start_event_bus(
            self.settings,
            backend=backend,
            **kwargs,
        )


__all__ = [
    "create_event_bus",
    "create_and_start_event_bus",
    "EventBusFactory",
    "BackendType",
    "AVAILABLE_BACKENDS",
]
