"""Application entry point."""

import asyncio
from pathlib import Path

import uvicorn

from src.Ship.App import create_app
from src.Ship.Configs import get_settings
from src.Ship.Core.Database import APP_REGISTRY, DB



async def setup_database() -> None:
    """Setup database and run migrations."""
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # For now, we'll create tables directly
    # In production, use Piccolo migrations
    from src.Containers.AppSection.Book.Models import Book
    from src.Containers.AppSection.User.Models import User
    
    # Create tables
    await Book.create_table(if_not_exists=True)
    await User.create_table(if_not_exists=True)


def run_server() -> None:
    """Run the application server."""
    settings = get_settings()
    
    # Setup database
    asyncio.run(setup_database())
    # src/Ship/Parents/Action.py
    # В общем пока не получается сделать rich traceback для logfire -- нужно хакать
    # import litestar
    # from rich.traceback import install
    # install(suppress=[litestar], show_locals=True)
    # Run server with app factory
    if settings.is_development:
        # Use string import for reload in development
        uvicorn.run(
            "src.Main:create_app_instance",
            host=settings.app_host,
            port=settings.app_port,
            reload=True,
            log_level="debug" if settings.app_debug else "info",
            factory=True,
        )
    else:
        # Use app object in production
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
