from __future__ import annotations

from returns.result import Result, Success

from src.Containers.CoreSection.CellRegistryModule.Actions.RegisterCellAction import (
    _registry,
)
from src.Containers.CoreSection.CellRegistryModule.Errors import RegistryError
from src.Ship.Cell.CellSpec import CellSpec
from src.Ship.Parents.Action import Action


class ListCellsAction(Action[None, list[CellSpec], RegistryError]):
    """Возвращает список всех зарегистрированных CellSpec."""

    async def run(self, data: None = None) -> Result[list[CellSpec], RegistryError]:
        return Success(list(_registry.values()))
