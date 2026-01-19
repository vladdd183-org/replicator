"""Piccolo app configuration for SettingsModule."""

import os

from piccolo.conf.apps import AppConfig

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


# Import table classes directly
from src.Containers.AppSection.SettingsModule.Models.Setting import Setting
from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag
from src.Containers.AppSection.SettingsModule.Models.UserSetting import UserSetting


APP_CONFIG = AppConfig(
    app_name="settings",
    migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
    table_classes=[Setting, FeatureFlag, UserSetting],
    migration_dependencies=[],
    commands=[],
)
