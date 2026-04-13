"""Ship providers module.

Exports Ship-level providers only.
Container providers are collected at the App level (src/Providers.py).

ARCHITECTURE NOTE: Ship MUST NOT import from Containers.
"""

from src.Ship.Providers.AppProvider import (
    AppProvider,
    get_ship_providers,
    get_ship_cli_providers,
)


def get_worker_providers():
    """Провайдеры для TaskIQ workers (без HTTP Request)."""
    return get_ship_cli_providers()


__all__ = [
    "AppProvider",
    "get_ship_providers",
    "get_ship_cli_providers",
    "get_worker_providers",
]
