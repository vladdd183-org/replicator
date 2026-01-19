"""SettingsModule DI providers."""

from dishka import Provider, Scope, provide

from src.Containers.AppSection.SettingsModule.Data.Repositories.SettingsRepository import SettingsRepository
from src.Containers.AppSection.SettingsModule.Data.Repositories.FeatureFlagRepository import FeatureFlagRepository
from src.Containers.AppSection.SettingsModule.Actions.SetSettingAction import SetSettingAction
from src.Containers.AppSection.SettingsModule.Actions.ToggleFeatureFlagAction import ToggleFeatureFlagAction
from src.Containers.AppSection.SettingsModule.Tasks.FeatureFlagTask import CheckFeatureFlagTask


class SettingsModuleProvider(Provider):
    """App-scoped provider for SettingsModule."""
    
    scope = Scope.APP
    
    check_feature_flag_task = provide(CheckFeatureFlagTask)


class SettingsRequestProvider(Provider):
    """Request-scoped provider for SettingsModule."""
    
    scope = Scope.REQUEST
    
    settings_repository = provide(SettingsRepository)
    feature_flag_repository = provide(FeatureFlagRepository)
    set_setting_action = provide(SetSettingAction)
    toggle_feature_flag_action = provide(ToggleFeatureFlagAction)



