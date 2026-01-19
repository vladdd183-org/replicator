"""Dishka DI Provider for Event Bus.

Provides EventBusProtocol instance for dependency injection.
Handles lifecycle management (start/stop) via Litestar hooks.

Usage in Controller:
    @post("/users")
    async def create_user(
        data: CreateUserRequest,
        event_bus: FromDishka[EventBusProtocol],
    ) -> Response:
        # ... create user ...
        await event_bus.publish("UserCreated", {"user_id": str(user.id)})

Usage in Providers.py:
    from src.Ship.Infrastructure.Events.Provider import EventBusProvider
    
    def get_all_providers() -> list[Provider]:
        return [
            AppProvider(),
            EventBusProvider(),
            # ... other providers
        ]
"""


from dishka import Provider, Scope, provide

from src.Ship.Configs.Settings import Settings
from src.Ship.Infrastructure.Events.Factory import (
    BackendType,
    create_event_bus,
)
from src.Ship.Infrastructure.Events.Protocol import EventBusProtocol


class EventBusProvider(Provider):
    """Dishka provider for Event Bus.
    
    Provides EventBusProtocol as APP-scoped singleton.
    The event bus is created once and shared across all requests.
    
    Note: Start/stop is handled via Litestar lifecycle hooks,
    not by this provider. See integrate_with_litestar().
    """
    
    scope = Scope.APP
    
    @provide
    def provide_event_bus(self, settings: Settings) -> EventBusProtocol:
        """Provide Event Bus instance.
        
        Creates the appropriate backend based on settings.
        The event bus is NOT started here - use lifecycle hooks.
        
        Args:
            settings: Application settings
            
        Returns:
            EventBusProtocol implementation (not started)
        """
        backend: BackendType = settings.event_bus_backend  # type: ignore
        return create_event_bus(settings, backend=backend)


class EventBusRequestProvider(Provider):
    """Provider for request-scoped event bus access.
    
    For scenarios where you need request-specific event bus wrapper
    (e.g., with correlation_id from request context).
    
    Most use cases should use EventBusProvider instead.
    """
    
    scope = Scope.REQUEST
    
    # The APP-scoped event bus is automatically available
    # No need to re-provide it


def integrate_with_litestar(app: "Litestar") -> None:
    """Integrate Event Bus with Litestar lifecycle.
    
    Call this in your App.py to setup lifecycle hooks.
    
    Args:
        app: Litestar application instance
        
    Example in App.py:
        from src.Ship.Infrastructure.Events.Provider import (
            integrate_with_litestar,
            get_event_bus_from_state,
        )
        
        app = Litestar(
            on_startup=[on_startup],
            on_shutdown=[on_shutdown],
        )
        
        async def on_startup(app: Litestar) -> None:
            # Get event bus from DI container
            async with app.state.dishka_container() as container:
                event_bus = await container.get(EventBusProtocol)
                await event_bus.start()
                app.state.event_bus = event_bus
                
                # Auto-register decorated handlers
                from src.Ship.Infrastructure.Events import auto_register_subscriptions
                await auto_register_subscriptions(event_bus)
        
        async def on_shutdown(app: Litestar) -> None:
            if hasattr(app.state, "event_bus"):
                await app.state.event_bus.stop()
    """
    pass  # Documentation-only function


async def startup_event_bus(
    event_bus: EventBusProtocol,
    *,
    auto_register: bool = True,
    listener_modules: list[str] | None = None,
) -> None:
    """Start event bus and register handlers.
    
    Helper function for Litestar on_startup hook.
    
    Args:
        event_bus: Event bus instance from DI
        auto_register: Whether to auto-register @subscribe handlers
        listener_modules: Module paths to import for handler discovery
        
    Example:
        async def on_startup(app: Litestar) -> None:
            container = app.state.dishka_container
            event_bus = await container.get(EventBusProtocol)
            
            await startup_event_bus(
                event_bus,
                listener_modules=[
                    "src.Containers.AppSection.UserModule.Listeners",
                    "src.Containers.AppSection.NotificationModule.Listeners",
                ],
            )
            
            app.state.event_bus = event_bus
    """
    import importlib
    import logfire
    
    # Import listener modules to trigger @subscribe registration
    if listener_modules:
        for module_path in listener_modules:
            try:
                importlib.import_module(module_path)
                logfire.debug(f"Imported listener module: {module_path}")
            except ImportError as e:
                logfire.warning(f"Failed to import listener module {module_path}: {e}")
    
    # Start the event bus
    await event_bus.start()
    
    # Auto-register decorated handlers
    if auto_register:
        from src.Ship.Infrastructure.Events import auto_register_subscriptions
        count = await auto_register_subscriptions(event_bus)
        logfire.info(f"Registered {count} event handlers")


async def shutdown_event_bus(
    event_bus: EventBusProtocol,
    *,
    wait_timeout: float = 30.0,
) -> None:
    """Stop event bus gracefully.
    
    Helper function for Litestar on_shutdown hook.
    
    Args:
        event_bus: Event bus instance
        wait_timeout: Timeout for pending events
        
    Example:
        async def on_shutdown(app: Litestar) -> None:
            if hasattr(app.state, "event_bus"):
                await shutdown_event_bus(app.state.event_bus)
    """
    import logfire
    
    # Wait for pending events
    if event_bus.is_running:
        await event_bus.wait_for_pending(timeout=wait_timeout)
    
    # Stop the event bus
    await event_bus.stop()
    logfire.info("Event bus stopped")


# Type import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar import Litestar


__all__ = [
    "EventBusProvider",
    "EventBusRequestProvider",
    "integrate_with_litestar",
    "startup_event_bus",
    "shutdown_event_bus",
]
