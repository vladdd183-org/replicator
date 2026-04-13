"""CLI Replicator -- точка входа для всех команд.

Регистрирует команды из Ship и Containers.

Usage:
    uv run python -m src.CLI --help
    uv run python -m src.CLI replicator evolve "Добавить поддержку gRPC"
    uv run python -m src.CLI replicator evolve --dry-run "Улучшить покрытие тестами"
    uv run python -m src.CLI replicator spec:compile "Создать микросервис платежей"
    uv run python -m src.CLI replicator cell:list
    uv run python -m src.CLI replicator generate "REST API для блога"
    uv run python -m src.CLI db migrate
"""

from src.Ship.CLI.Decorators import configure_cli_providers
from src.Providers import get_cli_providers

configure_cli_providers(get_cli_providers)

from src.Ship.CLI.Main import cli
from src.Ship.CLI.Commands.ReplicatorCommands import replicator_group

cli.add_command(replicator_group)


if __name__ == "__main__":
    cli()
