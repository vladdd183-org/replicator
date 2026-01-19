"""CheckFeatureFlagQuery - evaluate feature flag state."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.Containers.AppSection.SettingsModule.Tasks.FeatureFlagTask import (
    CheckFeatureFlagTask,
    FeatureFlagCheckInput,
)
from src.Ship.Parents.Query import Query


class CheckFeatureFlagQueryInput(BaseModel):
    """Input for feature flag check query."""

    model_config = ConfigDict(frozen=True)

    flag_name: str
    user_id: UUID | None = None


class CheckFeatureFlagQuery(Query[CheckFeatureFlagQueryInput, bool]):
    """CQRS Query: Check if feature flag is enabled for a user."""

    def __init__(self, task: CheckFeatureFlagTask) -> None:
        self.task = task

    async def execute(self, input: CheckFeatureFlagQueryInput) -> bool:
        return await self.task.run(
            FeatureFlagCheckInput(
                flag_name=input.flag_name,
                user_id=input.user_id,
            )
        )
