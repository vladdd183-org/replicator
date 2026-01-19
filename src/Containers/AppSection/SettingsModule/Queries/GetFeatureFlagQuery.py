"""GetFeatureFlagQuery - fetch feature flag by name."""

from pydantic import BaseModel, ConfigDict

from src.Containers.AppSection.SettingsModule.Data.Repositories.FeatureFlagRepository import (
    FeatureFlagRepository,
)
from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag
from src.Ship.Parents.Query import Query


class GetFeatureFlagQueryInput(BaseModel):
    """Input for get feature flag query."""

    model_config = ConfigDict(frozen=True)

    name: str


class GetFeatureFlagQuery(Query[GetFeatureFlagQueryInput, FeatureFlag | None]):
    """CQRS Query: Get feature flag by name."""

    def __init__(self, repository: FeatureFlagRepository) -> None:
        self.repository = repository

    async def execute(self, input: GetFeatureFlagQueryInput) -> FeatureFlag | None:
        return await self.repository.get_by_name(input.name)
