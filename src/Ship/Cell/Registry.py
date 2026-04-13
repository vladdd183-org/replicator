"""Протокол порта реестра ячеек (``CellRegistryPort``) для L2 Cell Engine.

Async-интерфейс: регистрация, получение по имени/версии, списки по секции
и статусу, история версий и обновление статуса.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.Ship.Cell.CellSpec import CellSpec, CellStatus


@runtime_checkable
class CellRegistryPort(Protocol):
    """Protocol for the Cell registry."""

    async def register(self, spec: CellSpec) -> CellSpec: ...

    async def get(self, name: str, version: str | None = None) -> CellSpec | None: ...

    async def list_all(self) -> list[CellSpec]: ...

    async def list_by_section(self, section: str) -> list[CellSpec]: ...

    async def list_by_status(self, status: CellStatus) -> list[CellSpec]: ...

    async def get_history(self, name: str) -> list[CellSpec]: ...

    async def update_status(self, name: str, version: str, status: CellStatus) -> CellSpec: ...
