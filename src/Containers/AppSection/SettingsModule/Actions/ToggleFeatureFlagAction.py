"""Action for toggling a feature flag."""

from dataclasses import dataclass

import logfire
from pydantic import BaseModel
from returns.result import Failure, Result, Success

from src.Containers.AppSection.SettingsModule.Data.UnitOfWork import SettingsUnitOfWork
from src.Containers.AppSection.SettingsModule.Errors import FeatureFlagNotFoundError, SettingsError
from src.Containers.AppSection.SettingsModule.Events import FeatureFlagToggled
from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag
from src.Ship.Parents.Action import Action


class ToggleFeatureFlagInput(BaseModel):
    """Input for toggling feature flag."""

    model_config = {"frozen": True}

    name: str
    enabled: bool


@dataclass
class ToggleFeatureFlagAction(Action[ToggleFeatureFlagInput, FeatureFlag, SettingsError]):
    """Action for toggling a feature flag on/off."""

    uow: SettingsUnitOfWork

    async def run(self, data: ToggleFeatureFlagInput) -> Result[FeatureFlag, SettingsError]:
        """Toggle feature flag."""
        # Check if flag exists first
        existing = await self.uow.feature_flags.get_by_name(data.name)
        if not existing:
            return Failure(FeatureFlagNotFoundError(flag_name=data.name))

        async with self.uow:
            flag = await self.uow.feature_flags.toggle(data.name, data.enabled)

            # Add domain event
            self.uow.add_event(
                FeatureFlagToggled(
                    flag_name=data.name,
                    enabled=data.enabled,
                    changed_by=None,  # Can be extended to include user ID
                )
            )

            await self.uow.commit()

        logfire.info(
            "🚩 Feature flag toggled",
            flag_name=data.name,
            enabled=data.enabled,
        )

        return Success(flag)
