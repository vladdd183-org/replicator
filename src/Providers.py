"""Application-level provider collection.

This module collects all providers from Ship and Containers.
Located at App level (not Ship) to maintain proper architecture layering.

ARCHITECTURE NOTE: Ship MUST NOT import from Containers.
All Container provider imports happen here at the App level.
"""

from dishka import Provider

from src.Ship.Providers import get_ship_providers, get_ship_cli_providers


def get_all_providers() -> list[Provider]:
    """Get all application providers for HTTP context.
    
    Collects providers from Ship and all Containers.
    
    Returns:
        List of all providers for HTTP/WebSocket context
    """
    # Import container providers here (App level can import from Containers)
    from src.Containers.AppSection.UserModule.Providers import (
        UserGatewayProvider,
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
        # Ship-level providers
        *get_ship_providers(),
        # AppSection - UserModule
        UserModuleProvider(),
        UserGatewayProvider(),
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
    # Import container providers here (App level can import from Containers)
    from src.Containers.AppSection.UserModule.Providers import (
        UserGatewayProvider,
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
        SearchCLIProvider,
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
        # Ship-level providers (CLI version)
        *get_ship_cli_providers(),
        # AppSection - UserModule (CLI version without Request)
        UserModuleProvider(),
        UserGatewayProvider(),
        UserCLIProvider(),
        # AppSection - NotificationModule (CLI version)
        NotificationCLIProvider(),
        # AppSection - AuditModule
        AuditModuleProvider(),
        AuditRequestProvider(),
        # AppSection - SearchModule (CLI version without Request)
        SearchModuleProvider(),
        SearchCLIProvider(),
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


__all__ = ["get_all_providers", "get_cli_providers", "get_worker_providers"]
