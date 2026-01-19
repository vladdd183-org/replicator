"""Event handler registry and utilities.

DEPRECATED: Use litestar.events @listener decorator instead.
This module is kept for backward compatibility and standalone usage.

For new code, use:
    from litestar.events import listener
    
    @listener("UserCreated")
    async def on_user_created(user_id: str, email: str, **kwargs):
        ...
"""

from typing import Callable, Awaitable, TypeVar
from functools import wraps

from src.Ship.Core.Types import DomainEvent

T = TypeVar("T", bound=DomainEvent)
EventHandler = Callable[[T], Awaitable[None]]


# Global handler registry
_handlers: dict[str, list[EventHandler]] = {}


def register_handler(event_name: str) -> Callable[[EventHandler[T]], EventHandler[T]]:
    """Decorator to register an event handler.
    
    Note: For litestar.events, use @listener decorator instead.
    This is for standalone EventBus usage.
    
    Args:
        event_name: Name of the event to handle
        
    Returns:
        Decorator function
        
    Example:
        @register_handler("UserCreated")
        async def handle_user_created(event: UserCreated) -> None:
            await send_welcome_email(event.email)
    """
    def decorator(func: EventHandler[T]) -> EventHandler[T]:
        if event_name not in _handlers:
            _handlers[event_name] = []
        _handlers[event_name].append(func)
        
        @wraps(func)
        async def wrapper(event: T) -> None:
            return await func(event)
        
        return wrapper
    
    return decorator


def get_handlers(event_name: str) -> list[EventHandler]:
    """Get all registered handlers for an event.
    
    Args:
        event_name: Name of the event
        
    Returns:
        List of handler functions
    """
    return _handlers.get(event_name, [])


def clear_handlers() -> None:
    """Clear all registered handlers."""
    _handlers.clear()

