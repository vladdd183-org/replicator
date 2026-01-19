"""Piccolo app configuration for UserModule."""

import os

from piccolo.conf.apps import AppConfig

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


# Import table classes directly
from src.Containers.AppSection.UserModule.Models.User import AppUser


APP_CONFIG = AppConfig(
    app_name="user",
    migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
    table_classes=[AppUser],
    migration_dependencies=[],
    commands=[],
)
