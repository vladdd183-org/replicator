"""Application entry point."""

import sys
import uvicorn

from src.Ship.App import create_app
from src.Ship.Configs import get_settings


def is_frozen() -> bool:
    """Check if running in PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def run_server() -> None:
    """Run the application server."""
    settings = get_settings()
    
    # CRITICAL: Disable reload in PyInstaller bundle (not supported)
    frozen = is_frozen()
    
    # src/Ship/Parents/Action.py
    # В общем пока не получается сделать rich traceback для logfire -- нужно хакать
    # import litestar
    # from rich.traceback import install
    # install(suppress=[litestar], show_locals=True)
    
    # Run server with app factory
    if settings.is_development and not frozen:
        # Use string import for reload in development (only when NOT frozen)
        uvicorn.run(
            "src.Main:create_app_instance",
            host=settings.app_host,
            port=settings.app_port,
            reload=True,
            log_level="debug" if settings.app_debug else "info",
            factory=True,
        )
    else:
        # Use app object in production OR when running from PyInstaller
        app = create_app()
        uvicorn.run(
            app,
            host=settings.app_host,
            port=settings.app_port,
            reload=False,
            log_level="debug" if settings.app_debug else "info",
        )


def create_app_instance():
    """Create app instance for uvicorn with string import."""
    return create_app()


if __name__ == "__main__":
    run_server()
