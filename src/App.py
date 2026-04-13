"""Точка входа Replicator.

Litestar приложение с полной Ship-инфраструктурой
и подключёнными Sections: Core, Agent, Tool, Knowledge.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin

from src.Ship.Configs import get_settings
from src.Ship.Exceptions.ProblemDetails import create_problem_details_plugin
from src.Ship.Infrastructure.Telemetry import setup_logfire
from src.Ship.Infrastructure.Telemetry.RequestLoggingMiddleware import RequestLoggingMiddleware
from src.Ship.Infrastructure.HealthCheck import health_controller
from src.Providers import get_all_providers


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """Управление жизненным циклом приложения."""
    yield
    if hasattr(app.state, "dishka_container"):
        await app.state.dishka_container.close()


def create_app() -> Litestar:
    """Создать и сконфигурировать Litestar приложение."""
    settings = get_settings()

    container = make_async_container(*get_all_providers())

    app = Litestar(
        route_handlers=[
            health_controller,
        ],
        plugins=[
            create_problem_details_plugin(),
        ],
        cors_config=CORSConfig(
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        ),
        openapi_config=OpenAPIConfig(
            title="Replicator",
            version="0.1.0",
            path="/api/docs",
            render_plugins=[ScalarRenderPlugin()],
        ),
        middleware=[
            RequestLoggingMiddleware,
        ],
        lifespan=[lifespan],
        debug=settings.app_debug,
    )

    setup_dishka(container, app)
    setup_logfire(app)

    return app


app = create_app()
