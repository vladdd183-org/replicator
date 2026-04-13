from __future__ import annotations

from dishka import Provider, Scope, provide

from src.Containers.CoreSection.CellRegistryModule.Actions.ListCellsAction import (
    ListCellsAction,
)
from src.Containers.CoreSection.CellRegistryModule.Actions.RegisterCellAction import (
    RegisterCellAction,
)


class CellRegistryModuleProvider(Provider):
    scope = Scope.REQUEST

    register_cell = provide(RegisterCellAction)
    list_cells = provide(ListCellsAction)
