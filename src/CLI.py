"""CLI Replicator -- точка входа.

Главная команда:
    uv run python -m src.CLI replicator run <REPO_URL> <INTENT>

Примеры:
    uv run python -m src.CLI replicator run https://github.com/owner/repo "Добавить фичу X"
    uv run python -m src.CLI replicator run . "Улучшить покрытие тестами" --dry-run
    uv run python -m src.CLI replicator spec:compile "Создать микросервис"
    uv run python -m src.CLI replicator beads
"""

from src.Ship.CLI.Decorators import configure_cli_providers
from src.Providers import get_cli_providers

configure_cli_providers(get_cli_providers)

from src.Ship.CLI.Main import cli
from src.Ship.CLI.Commands.ReplicatorCommands import replicator_group

cli.add_command(replicator_group)


if __name__ == "__main__":
    cli()
