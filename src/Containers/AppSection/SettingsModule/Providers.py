"""SettingsModule DI providers."""

from dishka import Provider, Scope, provide

from src.Containers.AppSection.SettingsModule.Actions.CreateFeatureFlagAction import (
    CreateFeatureFlagAction,
)
from src.Containers.AppSection.SettingsModule.Actions.SetSettingAction import SetSettingAction
from src.Containers.AppSection.SettingsModule.Actions.ToggleFeatureFlagAction import (
    ToggleFeatureFlagAction,
)
from src.Containers.AppSection.SettingsModule.Data.Repositories.FeatureFlagRepository import (
    FeatureFlagRepository,
)
from src.Containers.AppSection.SettingsModule.Data.Repositories.SettingsRepository import (
    SettingsRepository,
)
from src.Containers.AppSection.SettingsModule.Data.UnitOfWork import SettingsUnitOfWork
from src.Containers.AppSection.SettingsModule.Queries.CheckFeatureFlagQuery import (
    CheckFeatureFlagQuery,
)
from src.Containers.AppSection.SettingsModule.Queries.GetFeatureFlagQuery import GetFeatureFlagQuery
from src.Containers.AppSection.SettingsModule.Queries.GetSettingQuery import GetSettingQuery
from src.Containers.AppSection.SettingsModule.Queries.ListFeatureFlagsQuery import (
    ListFeatureFlagsQuery,
)
from src.Containers.AppSection.SettingsModule.Queries.ListSettingsQuery import ListSettingsQuery
from src.Containers.AppSection.SettingsModule.Tasks.FeatureFlagTask import CheckFeatureFlagTask


class SettingsModuleProvider(Provider):
    """App-scoped provider for SettingsModule."""

    scope = Scope.APP

    check_feature_flag_task = provide(CheckFeatureFlagTask)


class SettingsRequestProvider(Provider):
    """Request-scoped provider for SettingsModule."""

    scope = Scope.REQUEST

    # Repositories
    settings_repository = provide(SettingsRepository)
    feature_flag_repository = provide(FeatureFlagRepository)

    # Unit of Work
    settings_uow = provide(SettingsUnitOfWork)

    # Queries
    list_settings_query = provide(ListSettingsQuery)
    get_setting_query = provide(GetSettingQuery)
    list_feature_flags_query = provide(ListFeatureFlagsQuery)
    get_feature_flag_query = provide(GetFeatureFlagQuery)
    check_feature_flag_query = provide(CheckFeatureFlagQuery)

    # Actions
    set_setting_action = provide(SetSettingAction)
    create_feature_flag_action = provide(CreateFeatureFlagAction)
    toggle_feature_flag_action = provide(ToggleFeatureFlagAction)
