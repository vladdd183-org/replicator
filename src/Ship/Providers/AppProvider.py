"""Ship-level dependency injection providers.

ARCHITECTURE NOTE: Ship MUST NOT import from Containers.
Container providers are collected at the App level (src/Providers.py).
This file only defines Ship-level providers.
"""

from dishka import Provider, Scope, provide

from src.Ship.Configs import Settings, get_settings
from src.Ship.Auth.JWT import JWTService, get_jwt_service


class AppProvider(Provider):
    """Main application provider.
    
    Provides application-level dependencies like settings and database.
    """
    
    @provide(scope=Scope.APP)
    def provide_settings(self) -> Settings:
        """Provide application settings."""
        return get_settings()
    
    @provide(scope=Scope.APP)
    def provide_jwt_service(self) -> JWTService:
        """Provide JWT service for token operations (singleton)."""
        return get_jwt_service()


def get_ship_providers() -> list[Provider]:
    """Get Ship-level providers (no Container imports).
    
    Returns Ship infrastructure providers only.
    Container providers are added at the App level.
    
    Returns:
        List of Ship-level providers
    """
    from dishka.integrations.litestar import LitestarProvider
    from src.Ship.Infrastructure.Events.Outbox.Providers import (
        OutboxModuleProvider,
        OutboxRequestProvider,
    )
    from src.Ship.Infrastructure.Temporal.Providers import (
        TemporalModuleProvider,
    )
    
    return [
        # Core providers
        AppProvider(),
        # Litestar integration - provides Request in REQUEST scope
        LitestarProvider(),
        # Ship Infrastructure - Outbox
        OutboxModuleProvider(),
        OutboxRequestProvider(),
        # Ship Infrastructure - Temporal (for Workflows)
        TemporalModuleProvider(),
    ]


def get_ship_cli_providers() -> list[Provider]:
    """Get Ship-level providers for CLI context (no Request dependency).
    
    Returns Ship infrastructure providers for CLI.
    Container providers are added at the App level.
    
    Returns:
        List of Ship-level providers for CLI
    """
    from src.Ship.Infrastructure.Events.Outbox.Providers import (
        OutboxModuleProvider,
        OutboxCLIProvider,
    )
    from src.Ship.Infrastructure.Temporal.Providers import (
        TemporalModuleProvider,
    )
    
    return [
        # Core providers
        AppProvider(),
        # Ship Infrastructure - Outbox (CLI version)
        OutboxModuleProvider(),
        OutboxCLIProvider(),
        # Ship Infrastructure - Temporal (for Workflows)
        TemporalModuleProvider(),
    ]
