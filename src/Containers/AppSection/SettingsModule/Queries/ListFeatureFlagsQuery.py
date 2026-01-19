"""ListFeatureFlagsQuery - list feature flags with optional enabled filter."""

from pydantic import BaseModel, ConfigDict

from src.Containers.AppSection.SettingsModule.Data.Repositories.FeatureFlagRepository import (
    FeatureFlagRepository,
)
from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag
from src.Ship.Parents.Query import Query


class ListFeatureFlagsQueryInput(BaseModel):
    """Input for list feature flags query."""

    model_config = ConfigDict(frozen=True)

    enabled_only: bool = False


class FeatureFlagsListResult(BaseModel):
    """Result of feature flags list query."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    flags: list[FeatureFlag]
    total: int


class ListFeatureFlagsQuery(Query[ListFeatureFlagsQueryInput, FeatureFlagsListResult]):
    """CQRS Query: List feature flags with optional enabled filter."""

    def __init__(self, repository: FeatureFlagRepository) -> None:
        self.repository = repository

    async def execute(self, input: ListFeatureFlagsQueryInput) -> FeatureFlagsListResult:
        if input.enabled_only:
            flags = await self.repository.get_enabled()
        else:
            flags = await self.repository.get_all()

        return FeatureFlagsListResult(flags=flags, total=len(flags))
