"""Event subscription decorators for Hyper-Porto Event Bus.

Provides @subscribe decorator with global registry for declarative event handling.
Handlers registered via decorators are auto-discovered and bound to the event bus.

This module follows litestar.events pattern but adds:
- Multi-event subscription support
- Handler metadata (group, priority)
- Global registry for auto-discovery
- Type-safe handler validation
"""

from dataclasses import dataclass, field
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar

from src.Ship.Infrastructure.Events.Models import EventEnvelope, EventPriority

# Type variables
P = ParamSpec("P")
R = TypeVar("R")

# Handler types
SimpleHandler = Callable[[str, dict[str, Any]], Awaitable[None]]
EnvelopeHandler = Callable[[EventEnvelope], Awaitable[None]]
AnyHandler = SimpleHandler | EnvelopeHandler


@dataclass(frozen=True)
class SubscriptionInfo:
    """Metadata about a subscription.
    
    Stores all information needed to register a handler with the event bus.
    """
    
    event_names: tuple[str, ...]
    handler: AnyHandler
    handler_name: str
    group: str | None = None
    priority: EventPriority = EventPriority.NORMAL
    use_envelope: bool = False
    
    def __repr__(self) -> str:
        events = ", ".join(self.event_names)
        return f"<Subscription {self.handler_name} -> [{events}]>"


@dataclass
class SubscriptionRegistry:
    """Global registry for event subscriptions.
    
    Collects all handlers decorated with @subscribe for auto-discovery.
    Thread-safe via immutable SubscriptionInfo objects.
    
    Usage:
        # Get all registered subscriptions
        for sub in get_subscriptions():
            await event_bus.subscribe(sub.event_names[0], sub.handler)
    """
    
    _subscriptions: list[SubscriptionInfo] = field(default_factory=list)
    _by_event: dict[str, list[SubscriptionInfo]] = field(default_factory=dict)
    
    def register(self, info: SubscriptionInfo) -> None:
        """Register a subscription.
        
        Args:
            info: Subscription metadata
        """
        self._subscriptions.append(info)
        for event_name in info.event_names:
            if event_name not in self._by_event:
                self._by_event[event_name] = []
            self._by_event[event_name].append(info)
    
    def get_all(self) -> list[SubscriptionInfo]:
        """Get all registered subscriptions.
        
        Returns:
            List of all subscription infos
        """
        return self._subscriptions.copy()
    
    def get_by_event(self, event_name: str) -> list[SubscriptionInfo]:
        """Get subscriptions for a specific event.
        
        Args:
            event_name: Event to get handlers for
            
        Returns:
            List of subscription infos for the event
        """
        return self._by_event.get(event_name, []).copy()
    
    def get_event_names(self) -> set[str]:
        """Get all registered event names.
        
        Returns:
            Set of event names with registered handlers
        """
        return set(self._by_event.keys())
    
    def clear(self) -> None:
        """Clear all subscriptions (for testing)."""
        self._subscriptions.clear()
        self._by_event.clear()
    
    def __len__(self) -> int:
        return len(self._subscriptions)
    
    def __iter__(self):
        return iter(self._subscriptions)


# Global subscription registry instance
_registry = SubscriptionRegistry()


def subscribe(
    *event_names: str,
    group: str | None = None,
    priority: EventPriority = EventPriority.NORMAL,
    use_envelope: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to subscribe a handler to one or more events.
    
    The decorated function will be registered in the global registry
    and automatically subscribed when the event bus starts.
    
    Args:
        event_names: One or more event names to subscribe to
        group: Optional consumer group for load balancing
        priority: Handler priority (for ordering when multiple handlers)
        use_envelope: If True, handler receives EventEnvelope instead of (name, payload)
        
    Returns:
        Decorator function
        
    Example - Simple handler:
        @subscribe("UserCreated")
        async def on_user_created(event_name: str, payload: dict[str, Any]) -> None:
            user_id = payload["user_id"]
            await send_welcome_email(user_id)
            
    Example - Multi-event handler:
        @subscribe("UserCreated", "UserUpdated", "UserDeleted")
        async def audit_user_changes(event_name: str, payload: dict[str, Any]) -> None:
            await log_audit(event_name, payload)
            
    Example - Envelope handler:
        @subscribe("OrderPlaced", use_envelope=True)
        async def process_order(envelope: EventEnvelope) -> None:
            correlation_id = envelope.metadata.correlation_id
            order_data = envelope.payload
            await process_with_tracing(correlation_id, order_data)
            
    Example - Consumer group:
        @subscribe("EmailSend", group="email-workers")
        async def send_email(event_name: str, payload: dict[str, Any]) -> None:
            # Only one worker in the group will process each event
            await email_service.send(payload)
    """
    if not event_names:
        raise ValueError("At least one event name is required for @subscribe")
    
    # Validate event names
    for name in event_names:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Invalid event name: {name!r}")
    
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # Validate handler is async
        if not iscoroutinefunction(func):
            raise TypeError(
                f"Event handler {func.__name__} must be async (use 'async def')"
            )
        
        # Create subscription info
        info = SubscriptionInfo(
            event_names=tuple(event_names),
            handler=func,  # type: ignore
            handler_name=func.__qualname__,
            group=group,
            priority=priority,
            use_envelope=use_envelope,
        )
        
        # Register in global registry
        _registry.register(info)
        
        # Mark function as subscribed (for introspection)
        func.__event_subscription__ = info  # type: ignore
        
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return await func(*args, **kwargs)  # type: ignore
        
        return wrapper  # type: ignore
    
    return decorator


def subscribe_all(
    *event_names: str,
    group: str | None = None,
    priority: EventPriority = EventPriority.NORMAL,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Alias for @subscribe with multiple events (semantic clarity).
    
    Example:
        @subscribe_all("UserCreated", "UserUpdated", "UserDeleted")
        async def audit_user(event_name: str, payload: dict) -> None:
            await audit_service.log(event_name, payload)
    """
    return subscribe(*event_names, group=group, priority=priority)


def subscribe_envelope(
    *event_names: str,
    group: str | None = None,
    priority: EventPriority = EventPriority.NORMAL,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Alias for @subscribe with use_envelope=True (semantic clarity).
    
    Example:
        @subscribe_envelope("OrderPlaced")
        async def process_order(envelope: EventEnvelope) -> None:
            correlation_id = envelope.metadata.correlation_id
            await process(envelope.payload, correlation_id)
    """
    return subscribe(*event_names, group=group, priority=priority, use_envelope=True)


# ============================================================
# Registry access functions
# ============================================================


def get_subscriptions() -> list[SubscriptionInfo]:
    """Get all registered subscriptions.
    
    Returns:
        List of all subscription infos
    """
    return _registry.get_all()


def get_subscriptions_for_event(event_name: str) -> list[SubscriptionInfo]:
    """Get subscriptions for a specific event.
    
    Args:
        event_name: Event name to get handlers for
        
    Returns:
        List of subscription infos for the event
    """
    return _registry.get_by_event(event_name)


def get_registered_events() -> set[str]:
    """Get all event names that have registered handlers.
    
    Returns:
        Set of event names
    """
    return _registry.get_event_names()


def clear_subscriptions() -> None:
    """Clear all registered subscriptions.
    
    Use only for testing!
    """
    _registry.clear()


def get_registry() -> SubscriptionRegistry:
    """Get the global subscription registry.
    
    For advanced use cases and testing.
    
    Returns:
        Global SubscriptionRegistry instance
    """
    return _registry


# ============================================================
# Auto-registration helper
# ============================================================


async def auto_register_subscriptions(
    event_bus: "EventBusProtocol",
    *,
    include_groups: set[str] | None = None,
    exclude_groups: set[str] | None = None,
) -> int:
    """Auto-register all decorated handlers with an event bus.
    
    Call this during application startup to connect handlers to the bus.
    
    Args:
        event_bus: Event bus instance to register handlers with
        include_groups: If set, only register handlers in these groups
        exclude_groups: If set, skip handlers in these groups
        
    Returns:
        Number of handlers registered
        
    Example:
        async def on_startup(app: Litestar) -> None:
            event_bus = app.state.event_bus
            await event_bus.start()
            
            # Import modules with @subscribe handlers to trigger registration
            import src.Containers.AppSection.UserModule.Listeners  # noqa
            import src.Containers.AppSection.NotificationModule.Listeners  # noqa
            
            count = await auto_register_subscriptions(event_bus)
            logfire.info(f"Registered {count} event handlers")
    """
    from src.Ship.Infrastructure.Events.Protocol import EventBusProtocol
    
    registered = 0
    
    for sub in _registry:
        # Filter by group if specified
        if include_groups and sub.group not in include_groups:
            continue
        if exclude_groups and sub.group in exclude_groups:
            continue
        
        # Register with event bus
        for event_name in sub.event_names:
            if sub.use_envelope:
                await event_bus.subscribe_envelope(
                    event_name,
                    sub.handler,  # type: ignore
                    group=sub.group,
                )
            else:
                await event_bus.subscribe(
                    event_name,
                    sub.handler,  # type: ignore
                    group=sub.group,
                )
            registered += 1
    
    return registered


# Type import for auto_register_subscriptions
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.Ship.Infrastructure.Events.Protocol import EventBusProtocol


__all__ = [
    # Main decorator
    "subscribe",
    "subscribe_all",
    "subscribe_envelope",
    # Registry access
    "get_subscriptions",
    "get_subscriptions_for_event",
    "get_registered_events",
    "clear_subscriptions",
    "get_registry",
    # Types
    "SubscriptionInfo",
    "SubscriptionRegistry",
    # Helpers
    "auto_register_subscriptions",
]
