"""Main Litestar application factory.

This is the main entry point for the application.
It creates and configures the Litestar app with all providers and routes.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.memory import MemoryChannelsBackend
from strawberry.litestar import make_graphql_controller
from rich.traceback import install as install_rich_traceback

from src.Ship.Configs import get_settings
from src.Ship.Exceptions.ProblemDetails import create_problem_details_plugin
from src.Ship.Providers import get_all_providers
from src.Ship.GraphQL.Schema import schema, get_graphql_context
from src.Ship.Auth.Middleware import AuthenticationMiddleware
from src.Ship.Infrastructure.Telemetry import setup_logfire
from src.Ship.Infrastructure.Telemetry.RequestLoggingMiddleware import RequestLoggingMiddleware
from src.Ship.Infrastructure.Cache import setup_cache

# Import routers from containers
from src.Containers.AppSection.UserModule import user_router
from src.Containers.AppSection.UserModule.UI.WebSocket.Handlers import (
    user_updates_handler,
    authenticated_user_updates_handler,
)
from src.Containers.AppSection.NotificationModule import notification_router
from src.Containers.AppSection.AuditModule import audit_router
from src.Containers.AppSection.SearchModule import search_router
from src.Containers.AppSection.SettingsModule import settings_router
from src.Containers.VendorSection.EmailModule import email_router
from src.Containers.VendorSection.PaymentModule import payment_router
from src.Containers.VendorSection.WebhookModule import webhook_router

# Import health check controller
from src.Ship.Infrastructure.HealthCheck import health_controller

# Import listeners for domain events
from src.Containers.AppSection.UserModule.Listeners import (
    on_user_created,
    on_user_updated,
    on_user_deleted,
    on_user_changed,
)
from src.Containers.AppSection.NotificationModule.Listeners import (
    on_notification_created,
    on_notification_read,
    on_all_notifications_read,
)
from src.Containers.AppSection.SearchModule.Listeners import (
    on_user_created_index,
    on_user_updated_index,
    on_user_deleted_index,
    on_notification_created_index,
    on_payment_created_index,
)
from src.Containers.VendorSection.WebhookModule.Listeners import (
    on_user_created_webhook,
    on_user_updated_webhook,
    on_user_deleted_webhook,
    on_payment_created_webhook,
    on_notification_created_webhook,
)
from src.Containers.AppSection.AuditModule.Listeners import (
    on_action_executed,
)

# Install Rich traceback globally for beautiful exception output
# show_locals=True displays local variables in tracebacks
install_rich_traceback(
    show_locals=True,
    locals_max_length=80,
    locals_max_string=200,
    suppress=[],
    max_frames=50,
)


def _create_channels_plugin() -> ChannelsPlugin:
    """Create ChannelsPlugin with appropriate backend.
    
    Uses MemoryChannelsBackend for development.
    For production with multiple instances, use RedisChannelsBackend.
    """
    settings = get_settings()
    
    # TODO: Add Redis backend for production
    # if settings.is_production:
    #     from litestar.channels.backends.redis import RedisChannelsBackend
    #     backend = RedisChannelsBackend(url=settings.redis_url)
    # else:
    backend = MemoryChannelsBackend()
    
    return ChannelsPlugin(
        backend=backend,
        arbitrary_channels_allowed=True,  # Allow dynamic channel names like user:{id}
    )


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """Application lifespan handler.
    
    Manages startup and shutdown of the application.
    Closes Dishka container on shutdown.
    """
    yield
    # Close Dishka container on shutdown
    if hasattr(app.state, "dishka_container"):
        await app.state.dishka_container.close()


def create_app() -> Litestar:
    """Create and configure Litestar application.
    
    Returns:
        Configured Litestar application instance
    """
    settings = get_settings()
    
    # Create DI container with all providers
    container = make_async_container(*get_all_providers())
    
    # Create GraphQL controller
    GraphQLController = make_graphql_controller(
        schema,
        path="/graphql",
        context_getter=get_graphql_context,
        graphql_ide="graphiql",
    )
    
    # Create Litestar app
    app = Litestar(
        route_handlers=[
            # Infrastructure
            health_controller,
            # AppSection routers
            user_router,
            notification_router,
            audit_router,
            search_router,
            settings_router,
            # VendorSection routers
            email_router,
            payment_router,
            webhook_router,
            # GraphQL endpoint
            GraphQLController,
            # WebSocket handlers
            user_updates_handler,
            authenticated_user_updates_handler,
        ],
        # Event listeners for domain events
        listeners=[
            # UserModule listeners
            on_user_created,
            on_user_updated,
            on_user_deleted,
            on_user_changed,
            # NotificationModule listeners
            on_notification_created,
            on_notification_read,
            on_all_notifications_read,
            # SearchModule listeners (auto-indexing)
            on_user_created_index,
            on_user_updated_index,
            on_user_deleted_index,
            on_notification_created_index,
            on_payment_created_index,
            # WebhookModule listeners (webhook dispatch)
            on_user_created_webhook,
            on_user_updated_webhook,
            on_user_deleted_webhook,
            on_payment_created_webhook,
            on_notification_created_webhook,
            # AuditModule listener (Ship-level ActionExecuted events)
            on_action_executed,
        ],
        # Plugins
        plugins=[
            _create_channels_plugin(),  # WebSocket pub/sub channels
            create_problem_details_plugin(),  # RFC 9457 Problem Details
        ],
        cors_config=CORSConfig(
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        ),
        openapi_config=OpenAPIConfig(
            title=settings.app_name,
            version=settings.app_version,
            path="/api/docs",
            render_plugins=[ScalarRenderPlugin()],
        ),
        middleware=[RequestLoggingMiddleware, AuthenticationMiddleware],
        lifespan=[lifespan],
        debug=settings.app_debug,
    )
    
    # Setup Dishka integration
    setup_dishka(container, app)
    
    # Setup Logfire telemetry
    setup_logfire(app)
    
    # Setup cache (lazy init, but explicit call ensures it's ready)
    setup_cache()
    
    return app


# Application instance for ASGI servers
app = create_app()
