from __future__ import annotations

from returns.result import Failure, Result, Success

from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import MissionSpec
from src.Containers.CoreSection.SpecModule.Errors import SpecValidationError
from src.Ship.Parents.Action import Action


class ValidateSpecAction(Action[MissionSpec, MissionSpec, SpecValidationError]):
    """Валидирует MissionSpec на полноту и корректность."""

    async def run(
        self, data: MissionSpec,
    ) -> Result[MissionSpec, SpecValidationError]:
        if not data.title:
            return Failure(SpecValidationError(
                message="Title is required",
                field="title",
                reason="empty",
            ))
        if not data.description:
            return Failure(SpecValidationError(
                message="Description is required",
                field="description",
                reason="empty",
            ))
        if not data.acceptance_criteria:
            return Failure(SpecValidationError(
                message="At least one acceptance criterion required",
                field="acceptance_criteria",
                reason="empty",
            ))
        return Success(data)
