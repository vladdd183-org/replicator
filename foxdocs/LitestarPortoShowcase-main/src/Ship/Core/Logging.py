"""Logging configuration with Logfire."""

import logfire

from src.Ship.Configs import get_settings


def setup_logging() -> None:
    """Configure logging with Logfire."""
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


def get_logger(name: str):
    """Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logfire logger instance
    """
    return logfire.with_tags([name])
