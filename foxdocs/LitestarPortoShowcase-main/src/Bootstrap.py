"""Bootstrap file for auto-tracing.

This file should be run instead of Main.py to enable auto-tracing.
It configures Logfire BEFORE importing any application modules.
"""

import asyncio
from pathlib import Path

import logfire
import uvicorn


# Configure Logfire BEFORE importing application modules
from src.Ship.Configs import get_settings

settings = get_settings()

# Configure Logfire
if settings.logfire_token:
    logfire.configure(
        token=settings.logfire_token,
        project_name=settings.logfire_project_name,
        environment=settings.app_env,
    )
else:
    # Use local mode if no token provided
    logfire.configure(
        send_to_logfire=False,
        console=logfire.ConsoleOptions(
            verbose=settings.app_debug,
            include_timestamps=True,
        ),
    )

# Install auto-tracing BEFORE importing application modules
logfire.install_auto_tracing(
    modules=["src.Containers", "src.Ship"],
    min_duration=0.01,  # Only trace functions that take > 10ms
)

# NOW import application modules
from src.Ship.App import create_app


async def setup_database() -> None:
    """Setup database and run migrations."""
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # For now, we'll create tables directly
    # In production, use Piccolo migrations
    from src.Containers.AppSection.Book.Models import Book
    from src.Containers.AppSection.User.Models import User
    from src.Containers.AppSection.Book.Models.BookLoan import BookLoan
    from src.Containers.VendorSection.Payment.Models import Payment, PaymentMethod
    from src.Containers.VendorSection.Notification.Models import Notification
    
    # Create tables
    await Book.create_table(if_not_exists=True)
    await User.create_table(if_not_exists=True)
    await BookLoan.create_table(if_not_exists=True)
    await Payment.create_table(if_not_exists=True)
    await PaymentMethod.create_table(if_not_exists=True)
    await Notification.create_table(if_not_exists=True)


def run_server() -> None:
    """Run the application server."""
    # Setup database
    asyncio.run(setup_database())
    
    # Create app
    app = create_app()

    # Run server 
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        reload=False,  # Отключаем reload при использовании auto-tracing
        log_level="debug" if settings.app_debug else "info",
    )


if __name__ == "__main__":
    run_server()



