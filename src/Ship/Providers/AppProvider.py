"""Application-level dependency injection providers."""

from dishka import Provider, Scope, provide
from dishka.integrations.litestar import LitestarProvider

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


def get_all_providers() -> list[Provider]:
    """Get all application providers for HTTP context.
    
    This function collects all providers from Ship and Containers.
    Import and add Container providers here.
    
    Returns:
        List of all providers for HTTP/WebSocket context
    """
    # Import container providers here to avoid circular imports
    from src.Ship.Infrastructure.Events.Outbox.Providers import (
        OutboxModuleProvider,
        OutboxRequestProvider,
    )
    from src.Ship.Infrastructure.Temporal.Providers import (
        TemporalModuleProvider,
    )
    from src.Containers.AppSection.UserModule.Providers import (
        UserModuleProvider,
        UserRequestProvider,
    )
    from src.Containers.AppSection.NotificationModule.Providers import (
        NotificationRequestProvider,
    )
    from src.Containers.AppSection.AuditModule.Providers import (
        AuditModuleProvider,
        AuditRequestProvider,
    )
    from src.Containers.AppSection.SearchModule.Providers import (
        SearchModuleProvider,
        SearchRequestProvider,
    )
    from src.Containers.AppSection.SettingsModule.Providers import (
        SettingsModuleProvider,
        SettingsRequestProvider,
    )
    from src.Containers.AppSection.OrderModule.Providers import (
        OrderModuleProvider,
        OrderRequestProvider,
    )
    from src.Containers.VendorSection.EmailModule.Providers import (
        EmailModuleProvider,
        EmailRequestProvider,
    )
    from src.Containers.VendorSection.PaymentModule.Providers import (
        PaymentModuleProvider,
        PaymentRequestProvider,
    )
    from src.Containers.VendorSection.WebhookModule.Providers import (
        WebhookModuleProvider,
        WebhookRequestProvider,
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
        # AppSection - UserModule
        UserModuleProvider(),
        UserRequestProvider(),
        # AppSection - NotificationModule
        NotificationRequestProvider(),
        # AppSection - AuditModule
        AuditModuleProvider(),
        AuditRequestProvider(),
        # AppSection - SearchModule
        SearchModuleProvider(),
        SearchRequestProvider(),
        # AppSection - SettingsModule
        SettingsModuleProvider(),
        SettingsRequestProvider(),
        # AppSection - OrderModule
        OrderModuleProvider(),
        OrderRequestProvider(),
        # VendorSection - EmailModule
        EmailModuleProvider(),
        EmailRequestProvider(),
        # VendorSection - PaymentModule
        PaymentModuleProvider(),
        PaymentRequestProvider(),
        # VendorSection - WebhookModule
        WebhookModuleProvider(),
        WebhookRequestProvider(),
    ]


def get_cli_providers() -> list[Provider]:
    """Get providers for CLI context (without Request dependency).
    
    Returns:
        List of providers for CLI context
    """
    # Import container providers here to avoid circular imports
    from src.Ship.Infrastructure.Events.Outbox.Providers import (
        OutboxModuleProvider,
        OutboxCLIProvider,
    )
    from src.Ship.Infrastructure.Temporal.Providers import (
        TemporalModuleProvider,
    )
    from src.Containers.AppSection.UserModule.Providers import (
        UserModuleProvider,
        UserCLIProvider,
    )
    from src.Containers.AppSection.NotificationModule.Providers import (
        NotificationCLIProvider,
    )
    from src.Containers.AppSection.AuditModule.Providers import (
        AuditModuleProvider,
        AuditRequestProvider,
    )
    from src.Containers.AppSection.SearchModule.Providers import (
        SearchModuleProvider,
        SearchRequestProvider,
    )
    from src.Containers.AppSection.SettingsModule.Providers import (
        SettingsModuleProvider,
        SettingsRequestProvider,
    )
    from src.Containers.AppSection.OrderModule.Providers import (
        OrderModuleProvider,
        OrderCLIProvider,
    )
    from src.Containers.VendorSection.EmailModule.Providers import (
        EmailModuleProvider,
        EmailRequestProvider,
    )
    from src.Containers.VendorSection.PaymentModule.Providers import (
        PaymentModuleProvider,
        PaymentRequestProvider,
    )
    from src.Containers.VendorSection.WebhookModule.Providers import (
        WebhookModuleProvider,
        WebhookRequestProvider,
    )
    
    return [
        # Core providers
        AppProvider(),
        # Ship Infrastructure - Outbox (CLI version)
        OutboxModuleProvider(),
        OutboxCLIProvider(),
        # Ship Infrastructure - Temporal (for Workflows)
        TemporalModuleProvider(),
        # AppSection - UserModule (CLI version without Request)
        UserModuleProvider(),
        UserCLIProvider(),
        # AppSection - NotificationModule (CLI version)
        NotificationCLIProvider(),
        # AppSection - AuditModule
        AuditModuleProvider(),
        AuditRequestProvider(),
        # AppSection - SearchModule
        SearchModuleProvider(),
        SearchRequestProvider(),
        # AppSection - SettingsModule
        SettingsModuleProvider(),
        SettingsRequestProvider(),
        # AppSection - OrderModule (CLI version)
        OrderModuleProvider(),
        OrderCLIProvider(),
        # VendorSection - EmailModule
        EmailModuleProvider(),
        EmailRequestProvider(),
        # VendorSection - PaymentModule
        PaymentModuleProvider(),
        PaymentRequestProvider(),
        # VendorSection - WebhookModule
        WebhookModuleProvider(),
        WebhookRequestProvider(),
    ]


def get_worker_providers() -> list[Provider]:
    """Get providers for TaskIQ worker context (without HTTP Request).
    
    Workers run in separate processes without Litestar context,
    so they use CLI-style providers without Request dependency.
    
    Returns:
        List of providers for worker context
    """
    # Workers use same providers as CLI - no HTTP Request context
    return get_cli_providers()
