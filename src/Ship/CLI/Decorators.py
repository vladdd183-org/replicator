"""CLI decorators and utilities for DI integration.

Uses dishka.integrations.click for automatic DI in Click commands.

ARCHITECTURE NOTE: Ship MUST NOT import from Containers.
CLI providers are configured via configure_cli_providers() called from App level.

Usage:
    from dishka.integrations.click import FromDishka, inject
    
    @click.command()
    @inject  # Required for FromDishka to work
    async def create_user(
        email: str,
        action: FromDishka[CreateUserAction],  # Auto-injected!
    ) -> None:
        result = await action.run(...)

Setup (call once in CLI entry point):
    from src.Ship.CLI.Decorators import setup_cli_container, configure_cli_providers
    from src.Providers import get_cli_providers
    
    configure_cli_providers(get_cli_providers)
    setup_cli_container(click_group)
"""

import asyncio
import functools
from typing import TypeVar, Callable, Any

import click
from rich.console import Console
from returns.result import Result, Success, Failure
from dishka import Provider, make_async_container

from src.Ship.Infrastructure.Telemetry import ensure_logfire_configured

T = TypeVar("T")

console = Console()

# Global container for CLI - initialized once
_cli_container = None
# Provider function - configured from App level
_provider_fn: Callable[[], list[Provider]] | None = None


def configure_cli_providers(provider_fn: Callable[[], list[Provider]]) -> None:
    """Configure CLI providers function.
    
    Must be called before using get_cli_container().
    Should be called from App level (not Ship) to maintain architecture.
    
    Args:
        provider_fn: Function that returns list of providers
        
    Example:
        from src.Ship.CLI.Decorators import configure_cli_providers
        from src.Providers import get_cli_providers
        
        configure_cli_providers(get_cli_providers)
    """
    global _provider_fn
    _provider_fn = provider_fn


def get_cli_container():
    """Get or create CLI DI container.
    
    Returns singleton container for CLI commands.
    
    Raises:
        RuntimeError: If configure_cli_providers() was not called
    """
    global _cli_container
    if _cli_container is None:
        if _provider_fn is None:
            # Fall back to ship-only providers if not configured
            from src.Ship.Providers import get_ship_cli_providers
            _cli_container = make_async_container(*get_ship_cli_providers())
        else:
            _cli_container = make_async_container(*_provider_fn())
    return _cli_container


def setup_cli_container(ctx: click.Context) -> None:
    """Setup CLI environment.
    
    Configures Logfire for CLI context.
    Note: DI is handled via @with_container decorator, not dishka-click integration,
    because click cannot properly close async containers.
    
    Call this in your CLI group with @click.pass_context.
    
    Args:
        ctx: Click context from @click.pass_context
        
    Example:
        @click.group()
        @click.pass_context
        def cli(ctx: click.Context):
            setup_cli_container(ctx)
    """
    # Ensure logfire is configured for CLI
    ensure_logfire_configured()


def with_container(func: Callable[..., Any]) -> Callable[..., None]:
    """Decorator for async CLI commands with DI container.
    
    Properly manages async container lifecycle.
    
    Example:
        @click.command()
        @with_container
        async def my_command(container, arg1: str) -> None:
            action = await container.get(MyAction)
            result = await action.run(...)
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        async def run() -> Any:
            container = get_cli_container()
            async with container() as request_container:
                return await func(request_container, *args, **kwargs)
        
        try:
            result = asyncio.run(run())
            if isinstance(result, Result):
                handle_cli_result(result)
        except SystemExit:
            raise
        except Exception as e:
            console.print(f"[red]✗[/red] Unexpected error: {str(e)}")
            raise SystemExit(1)
    
    return wrapper


def handle_cli_result(
    result: Result[Any, Any],
    success_message: str = "Success",
    show_fields: list[str] | None = None,
) -> None:
    """Handle Result object for CLI output.
    
    Args:
        result: Result from action/task
        success_message: Message to show on success
        show_fields: Specific fields to display (None = all)
    """
    match result:
        case Success(value):
            console.print(f"[green]✓[/green] {success_message}")
            if value is not None:
                if show_fields:
                    for field in show_fields:
                        if hasattr(value, field):
                            console.print(f"  {field}: {getattr(value, field)}")
                elif hasattr(value, "__dict__"):
                    for key, val in vars(value).items():
                        if not key.startswith("_"):
                            console.print(f"  {key}: {val}")
        case Failure(error):
            msg = error.message if hasattr(error, "message") else str(error)
            console.print(f"[red]✗[/red] Error: {msg}")
            raise SystemExit(1)
