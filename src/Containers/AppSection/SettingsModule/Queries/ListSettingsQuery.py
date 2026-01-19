"""ListSettingsQuery - list settings with optional category filter."""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.SettingsModule.Data.Repositories.SettingsRepository import (
    SettingsRepository,
)
from src.Containers.AppSection.SettingsModule.Models.Setting import Setting


class ListSettingsQueryInput(BaseModel):
    """Input for list settings query."""
    
    model_config = ConfigDict(frozen=True)
    
    category: str | None = None


@dataclass(frozen=True)
class SettingsListResult:
    """Result of settings list query."""
    
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
