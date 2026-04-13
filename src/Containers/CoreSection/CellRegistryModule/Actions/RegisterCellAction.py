from __future__ import annotations

from returns.result import Failure, Result, Success

from src.Containers.CoreSection.CellRegistryModule.Errors import (
    CellAlreadyExistsError,
    RegistryError,
)
from src.Ship.Cell.CellSpec import CellSpec, compute_spec_hash
from src.Ship.Parents.Action import Action

_registry: dict[str, CellSpec] = {}


class RegisterCellAction(Action[CellSpec, CellSpec, RegistryError]):
    """Регистрирует новый CellSpec в реестре (in-memory для MVP)."""

    async def run(self, data: CellSpec) -> Result[CellSpec, RegistryError]:
        key = f"{data.name}:{data.version}"

        if key in _registry:
            return Failure(CellAlreadyExistsError(
                message=f"Cell '{data.name}' v{data.version} already registered",
                cell_name=data.name,
            ))

        spec_hash = compute_spec_hash(data)
        registered = CellSpec(
            name=data.name,
            version=data.version,
            description=data.description,
            section=data.section,
            spec_hash=spec_hash,
            actions=data.actions,
            tasks=data.tasks,
            queries=data.queries,
            events_emitted=data.events_emitted,
            events_consumed=data.events_consumed,
            capabilities_required=data.capabilities_required,
            dependencies=data.dependencies,
            adapters_required=data.adapters_required,
            resources=data.resources,
            health_check=data.health_check,
            status=data.status,
            parent_spec_hash=data.parent_spec_hash,
            tags=data.tags,
        )
        _registry[key] = registered
        return Success(registered)
