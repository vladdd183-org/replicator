"""Action for toggling a feature flag."""

from dataclasses import dataclass

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.SettingsModule.Data.Repositories.FeatureFlagRepository import FeatureFlagRepository
from src.Containers.AppSection.SettingsModule.Errors import SettingsError, FeatureFlagNotFoundError
from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag


@dataclass
class ToggleFeatureFlagInput:
    """Input for toggling feature flag."""
    
    name: str
    enabled: bool


@dataclass
class ToggleFeatureFlagAction(Action[ToggleFeatureFlagInput, FeatureFlag, SettingsError]):
    """Action for toggling a feature flag on/off."""
    
    repository: FeatureFlagRepository
    
    async def run(self, data: ToggleFeatureFlagInput) -> Result[FeatureFlag, SettingsError]:
        """Toggle feature flag."""
        flag = await self.repository.toggle(data.name, data.enabled)
        
        if not flag:
            return Failure(FeatureFlagNotFoundError(flag_name=data.name))
        
        import logfire
        logfire.info(
            "🚩 Feature flag toggled",
            flag_name=data.name,
            enabled=data.enabled,
        )
        
        return Success(flag)



