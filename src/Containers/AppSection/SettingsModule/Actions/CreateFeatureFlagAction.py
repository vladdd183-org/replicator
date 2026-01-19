"""Action for creating a new feature flag."""

from dataclasses import dataclass

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.SettingsModule.Data.Schemas.Requests import CreateFeatureFlagRequest
from src.Containers.AppSection.SettingsModule.Data.Repositories.FeatureFlagRepository import (
    FeatureFlagRepository,
)
from src.Containers.AppSection.SettingsModule.Errors import (
    SettingsError,
    FeatureFlagAlreadyExistsError,
)
from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag


@dataclass
class CreateFeatureFlagAction(Action[CreateFeatureFlagRequest, FeatureFlag, SettingsError]):
    """Action for creating a feature flag."""
    
    repository: FeatureFlagRepository
    
    async def run(self, data: CreateFeatureFlagRequest) -> Result[FeatureFlag, SettingsError]:
        """Create a new feature flag."""
        existing = await self.repository.get_by_name(data.name)
        if existing:
            return Failure(FeatureFlagAlreadyExistsError(flag_name=data.name))
        
        flag = await self.repository.create_flag(
            name=data.name,
            description=data.description,
            enabled=data.enabled,
            rollout_percentage=data.rollout_percentage,
        )
        
        import logfire
        logfire.info(
            "🚩 Feature flag created",
            flag_name=data.name,
            enabled=data.enabled,
            rollout_percentage=data.rollout_percentage,
        )
        
        return Success(flag)
