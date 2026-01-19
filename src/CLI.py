"""Main CLI entry point with Container command registration.

This module is at the App level (not Ship) and can properly import from Containers.
It extends the base Ship CLI with Container-specific command groups.

ARCHITECTURE NOTE: This is the proper place for Container imports in CLI context.
Ship CLI only includes Ship-level commands (db, outbox).
Container commands are registered here.

Usage:
    # Run via uv
    uv run python -m src.CLI --help
    uv run python -m src.CLI users create --email user@example.com --password secret123 --name "John"
    uv run python -m src.CLI db migrate
    uv run python -m src.CLI outbox stats
"""

# Configure CLI providers BEFORE importing cli (providers are used during import)
from src.Ship.CLI.Decorators import configure_cli_providers
from src.Providers import get_cli_providers

configure_cli_providers(get_cli_providers)

# Import base CLI from Ship (no Container imports in Ship)
from src.Ship.CLI.Main import cli

# Import Container CLI command groups (allowed at App level)
from src.Containers.AppSection.UserModule.UI.CLI.Commands import users_group

# Register Container command groups
cli.add_command(users_group)


if __name__ == "__main__":
    cli()
