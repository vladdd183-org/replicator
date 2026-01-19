"""ListSettingsQuery - list settings with optional category filter."""

from pydantic import BaseModel, ConfigDict

from src.Containers.AppSection.SettingsModule.Data.Repositories.SettingsRepository import (
    SettingsRepository,
)
from src.Containers.AppSection.SettingsModule.Models.Setting import Setting
from src.Ship.Parents.Query import Query


class ListSettingsQueryInput(BaseModel):
    """Input for list settings query."""

    model_config = ConfigDict(frozen=True)

    category: str | None = None


class SettingsListResult(BaseModel):
    """Result of settings list query."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    settings: list[Setting]
    total: int


class ListSettingsQuery(Query[ListSettingsQueryInput, SettingsListResult]):
    """CQRS Query: List settings with optional category filter."""

    def __init__(self, repository: SettingsRepository) -> None:
        self.repository = repository

    async def execute(self, input: ListSettingsQueryInput) -> SettingsListResult:
        if input.category:
            settings = await self.repository.get_by_category(input.category)
        else:
            settings = await self.repository.get_all()

        return SettingsListResult(settings=settings, total=len(settings))
