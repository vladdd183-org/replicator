"""Main CLI entry point with Dishka integration.

This module provides the root CLI group that integrates with Litestar CLIPlugin.
Commands from containers are registered via entry points in pyproject.toml.

Usage:
    # Built-in Litestar commands
    litestar --help
    litestar run
    litestar routes
    litestar schema openapi
    
    # Custom commands (registered via entry points)
    litestar users --help
    litestar users create --email user@example.com --password secret123 --name "John"
    
    # Database commands
    litestar db migrate
    litestar db makemigrations --app user
    litestar db status
    
Note: For code generation, use the standalone Porto CLI:
    porto --help
    porto make:module Blog
"""

import click

from src.Ship.CLI.Decorators import setup_cli_container


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Hyper-Porto CLI.
    
    Main entry point for all CLI commands.
    """
    # Setup Dishka DI for CLI (enables FromDishka injection)
    setup_cli_container(ctx)


# Import and register container command groups
from src.Containers.AppSection.UserModule.UI.CLI.Commands import users_group
from src.Ship.CLI.MigrationCommands import db_group
from src.Ship.Infrastructure.Events.Outbox.CLI import outbox_cli

cli.add_command(users_group)
cli.add_command(db_group)
cli.add_command(outbox_cli)


if __name__ == "__main__":
    cli()
