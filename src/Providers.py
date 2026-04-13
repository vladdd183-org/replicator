"""Агрегатор DI-провайдеров приложения.

Собирает все провайдеры из Ship и Containers.
Расположен на уровне App (не Ship) для соблюдения архитектурных слоев.
"""

from __future__ import annotations

from dishka import Provider

from src.Ship.Providers.AppProvider import AppProvider
from src.Ship.Providers.AdapterProvider import LocalAdapterProvider

from src.Containers.CoreSection.SpecModule.Providers import SpecModuleProvider
from src.Containers.CoreSection.CellRegistryModule.Providers import CellRegistryModuleProvider
from src.Containers.CoreSection.TemplateModule.Providers import TemplateModuleProvider
from src.Containers.CoreSection.EvolutionModule.Providers import EvolutionModuleProvider

from src.Containers.AgentSection.CompassModule.Providers import CompassModuleProvider
from src.Containers.AgentSection.MakerModule.Providers import MakerModuleProvider
from src.Containers.AgentSection.OrchestratorModule.Providers import OrchestratorModuleProvider

from src.Containers.ToolSection.MCPClientModule.Providers import MCPClientModuleProvider
from src.Containers.ToolSection.GitModule.Providers import GitModuleProvider
from src.Containers.ToolSection.NixModule.Providers import NixModuleProvider

from src.Containers.KnowledgeSection.MemoryModule.Providers import MemoryModuleProvider


def get_all_providers() -> list[Provider]:
    """Получить все провайдеры для HTTP-контекста."""
    return [
        AppProvider(),
        LocalAdapterProvider(),
        # CoreSection
        SpecModuleProvider(),
        CellRegistryModuleProvider(),
        TemplateModuleProvider(),
        EvolutionModuleProvider(),
        # AgentSection
        CompassModuleProvider(),
        MakerModuleProvider(),
        OrchestratorModuleProvider(),
        # ToolSection
        MCPClientModuleProvider(),
        GitModuleProvider(),
        NixModuleProvider(),
        # KnowledgeSection
        MemoryModuleProvider(),
    ]


def get_cli_providers() -> list[Provider]:
    """Получить провайдеры для CLI-контекста (без Request)."""
    return [
        AppProvider(),
        LocalAdapterProvider(),
        SpecModuleProvider(),
        CellRegistryModuleProvider(),
        TemplateModuleProvider(),
        EvolutionModuleProvider(),
        CompassModuleProvider(),
        MakerModuleProvider(),
        OrchestratorModuleProvider(),
        MCPClientModuleProvider(),
        GitModuleProvider(),
        NixModuleProvider(),
        MemoryModuleProvider(),
    ]
