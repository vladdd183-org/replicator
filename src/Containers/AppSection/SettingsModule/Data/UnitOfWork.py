"""SettingsModule Unit of Work.

Provides transactional access to settings-related repositories.
Inherits event management from BaseUnitOfWork.
"""

from dataclasses import dataclass

from src.Containers.AppSection.SettingsModule.Data.Repositories.FeatureFlagRepository import (
    FeatureFlagRepository,
)
from src.Containers.AppSection.SettingsModule.Data.Repositories.SettingsRepository import (
    SettingsRepository,
)
from src.Ship.Parents.UnitOfWork import BaseUnitOfWork


@dataclass
class SettingsUnitOfWork(BaseUnitOfWork):
    """Unit of Work for SettingsModule.

    Provides transactional access to settings and feature flags repositories.
    Inherits event management from BaseUnitOfWork.

    Example:
        async with uow:
            setting = await uow.settings.set_value(key="app.name", value="MyApp")
            uow.add_event(SettingChanged(key=key, old_value=old, new_value=value))
            await uow.commit()
    """

    # Repositories - injected via DI
    settings: SettingsRepository
    feature_flags: FeatureFlagRepository
