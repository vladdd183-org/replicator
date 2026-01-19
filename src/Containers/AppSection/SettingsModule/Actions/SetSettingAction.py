"""Action for setting a configuration value."""

from dataclasses import dataclass

import logfire
from returns.result import Failure, Result, Success

from src.Containers.AppSection.SettingsModule.Data.Schemas.Requests import SetSettingRequest
from src.Containers.AppSection.SettingsModule.Data.UnitOfWork import SettingsUnitOfWork
from src.Containers.AppSection.SettingsModule.Errors import SettingReadOnlyError, SettingsError
from src.Containers.AppSection.SettingsModule.Events import SettingChanged
from src.Containers.AppSection.SettingsModule.Models.Setting import Setting
from src.Ship.Parents.Action import Action


@dataclass
class SetSettingAction(Action[SetSettingRequest, Setting, SettingsError]):
    """Action for setting a configuration value."""

    uow: SettingsUnitOfWork

    async def run(self, data: SetSettingRequest) -> Result[Setting, SettingsError]:
        """Set a setting value."""
        # Check if setting exists and is readonly
        existing = await self.uow.settings.get_by_key(data.key)
        if existing and existing.is_readonly:
            return Failure(SettingReadOnlyError(key=data.key))

        # Store old value for event
        old_value = existing.value if existing else None

        # Set the value within transaction
        async with self.uow:
            setting = await self.uow.settings.set_value(
                key=data.key,
                value=data.value,
                value_type=data.value_type,
                description=data.description,
                category=data.category,
            )

            # Add domain event
            self.uow.add_event(
                SettingChanged(
                    key=data.key,
                    old_value=old_value,
                    new_value=data.value,
                    changed_by=None,  # Can be extended to include user ID
                )
            )

            await self.uow.commit()

        logfire.info(
            "⚙️ Setting updated",
            key=data.key,
            category=data.category,
        )

        return Success(setting)
