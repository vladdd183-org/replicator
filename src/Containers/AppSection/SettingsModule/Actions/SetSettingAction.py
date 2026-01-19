"""Action for setting a configuration value."""

from dataclasses import dataclass

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.SettingsModule.Data.Schemas.Requests import SetSettingRequest
from src.Containers.AppSection.SettingsModule.Data.Repositories.SettingsRepository import SettingsRepository
from src.Containers.AppSection.SettingsModule.Errors import SettingsError, SettingReadOnlyError
from src.Containers.AppSection.SettingsModule.Models.Setting import Setting


@dataclass
class SetSettingAction(Action[SetSettingRequest, Setting, SettingsError]):
    """Action for setting a configuration value."""
    
    repository: SettingsRepository
    
    async def run(self, data: SetSettingRequest) -> Result[Setting, SettingsError]:
        """Set a setting value."""
        # Check if setting exists and is readonly
        existing = await self.repository.get_by_key(data.key)
        if existing and existing.is_readonly:
            return Failure(SettingReadOnlyError(key=data.key))
        
        # Set the value
        setting = await self.repository.set_value(
            key=data.key,
            value=data.value,
            value_type=data.value_type,
            description=data.description,
            category=data.category,
        )
        
        import logfire
        logfire.info(
            "⚙️ Setting updated",
            key=data.key,
            category=data.category,
        )
        
        return Success(setting)



