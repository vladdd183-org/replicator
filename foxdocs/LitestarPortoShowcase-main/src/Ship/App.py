"""Main Litestar application factory."""

from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin

from src.Containers.AppSection.Book.UI.API.Controllers import BookController
from src.Containers.AppSection.User.UI.API.Controllers import UserController
from src.Ship.Configs import get_settings
from src.Ship.Exceptions import exception_handler
from src.Ship.Parents import PortoException
from src.Ship.Plugins import LogfirePlugin
from src.Ship.Providers import get_all_providers

def create_app() -> Litestar:
    """Create and configure Litestar application."""

    # Get settings
    settings = get_settings()

    # Create DI container
    container = make_async_container(*get_all_providers())

    # Create app
    app = Litestar(
        route_handlers=[
            # AppSection controllers
            BookController,
            UserController,
        ],
        exception_handlers={
            PortoException: exception_handler,
        },
        cors_config=CORSConfig(
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        ),
        openapi_config=OpenAPIConfig(
            title=settings.app_name,
            version="0.1.0",
            path="/api/docs",
            render_plugins=[ScalarRenderPlugin()],
        ),
        plugins=[
            LogfirePlugin(
                auto_trace_modules=["src.Containers"],
                min_duration=0.01,
            ),
        ],
        debug=settings.app_debug,
        # Отключаем встроенное логирование Litestar - используем только logfire
        logging_config=None,
    )
    # Setup Dishka
    setup_dishka(container, app)

    return app
