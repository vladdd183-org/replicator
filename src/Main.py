"""Application entry point.

This module provides the main entry point for running the application.
It handles database setup and server configuration.
"""

import asyncio
from pathlib import Path

import uvicorn

from src.App import create_app
from src.Ship.Configs import get_settings


async def setup_database() -> None:
    """Setup database and create tables.
    
    Creates data directory and initializes database tables.
    In production, use Piccolo migrations instead.
    """
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Import models and create tables
    from src.Containers.AppSection.UserModule.Models.User import AppUser
    
    # Create tables if they don't exist
    await AppUser.create_table(if_not_exists=True)


def run_server() -> None:
    """Run the application server.
    
    Configures and starts uvicorn server based on settings.
    """
    settings = get_settings()
    
    # Setup database
    asyncio.run(setup_database())
    
    if settings.is_development:
        # Development mode with hot reload
        uvicorn.run(
            "src.Main:create_app_instance",
            host=settings.app_host,
            port=settings.app_port,
            reload=True,
            log_level="debug" if settings.app_debug else "info",
            factory=True,
        )
    else:
        # Production mode
        app = create_app()
        uvicorn.run(
            app,
            host=settings.app_host,
            port=settings.app_port,
            reload=False,
            log_level="info",
        )


def create_app_instance():
    """Create app instance for uvicorn with string import.
    
    Used for hot reload in development mode.
    """
    return create_app()


if __name__ == "__main__":
    run_server()

