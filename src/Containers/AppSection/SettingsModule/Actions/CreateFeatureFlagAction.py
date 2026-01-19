"""Action for creating a new feature flag."""

from dataclasses import dataclass

import logfire
from returns.result import Failure, Result, Success

from src.Containers.AppSection.SettingsModule.Data.Schemas.Requests import CreateFeatureFlagRequest
from src.Containers.AppSection.SettingsModule.Data.UnitOfWork import SettingsUnitOfWork
from src.Containers.AppSection.SettingsModule.Errors import (
    FeatureFlagAlreadyExistsError,
    SettingsError,
)
from src.Containers.AppSection.SettingsModule.Events import FeatureFlagToggled
from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag
from src.Ship.Parents.Action import Action


@dataclass
class CreateFeatureFlagAction(Action[CreateFeatureFlagRequest, FeatureFlag, SettingsError]):
    """Action for creating a feature flag."""

    uow: SettingsUnitOfWork

    async def run(self, data: CreateFeatureFlagRequest) -> Result[FeatureFlag, SettingsError]:
        """Create a new feature flag."""
        existing = await self.uow.feature_flags.get_by_name(data.name)
        if existing:
            return Failure(FeatureFlagAlreadyExistsError(flag_name=data.name))

        async with self.uow:
            flag = await self.uow.feature_flags.create_flag(
                name=data.name,
                description=data.description,
                enabled=data.enabled,
                rollout_percentage=data.rollout_percentage,
            )

            # Add domain event if flag is created with enabled state
            if data.enabled:
                self.uow.add_event(
                    FeatureFlagToggled(
                        flag_name=data.name,
                        enabled=data.enabled,
                        changed_by=None,  # Can be extended to include user ID
                    )
                )

            await self.uow.commit()

        logfire.info(
            "🚩 Feature flag created",
            flag_name=data.name,
            enabled=data.enabled,
            rollout_percentage=data.rollout_percentage,
        )

        return Success(flag)
