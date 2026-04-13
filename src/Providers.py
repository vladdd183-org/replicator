"""Агрегатор DI-провайдеров приложения.

Собирает все провайдеры из Ship и Containers.
Расположен на уровне App (не Ship) для соблюдения архитектурных слоев.
"""

from dishka import Provider

from src.Ship.Providers.AppProvider import AppProvider


def get_all_providers() -> list[Provider]:
    """Получить все провайдеры для HTTP-контекста."""
    return [
        AppProvider(),
        # TODO: добавить AdapterProvider() после реализации Ship/Adapters
        # TODO: добавить провайдеры CoreSection, AgentSection, ToolSection, KnowledgeSection
    ]


def get_cli_providers() -> list[Provider]:
    """Получить провайдеры для CLI-контекста (без Request)."""
    return [
        AppProvider(),
        # TODO: добавить провайдеры без Request-зависимостей
    ]
