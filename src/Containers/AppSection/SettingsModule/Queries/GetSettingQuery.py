"""GetSettingQuery - fetch setting by key."""

from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.SettingsModule.Data.Repositories.SettingsRepository import (
    SettingsRepository,
)
from src.Containers.AppSection.SettingsModule.Models.Setting import Setting


class GetSettingQueryInput(BaseModel):
    """Input for get setting query."""
    
    model_config = ConfigDict(frozen=True)
    
    key: str


class GetSettingQuery(Query[GetSettingQueryInput, Setting | None]):
    """CQRS Query: Get setting by key."""
    
    def __init__(self, repository: SettingsRepository) -> None:
        self.repository = repository
    
    async def execute(self, input: GetSettingQueryInput) -> Setting | None:
        return await self.repository.get_by_key(input.key)
