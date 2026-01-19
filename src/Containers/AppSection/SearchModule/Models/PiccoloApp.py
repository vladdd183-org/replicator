"""Piccolo app configuration for SearchModule."""

import os

from piccolo.conf.apps import AppConfig

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


# Import table classes directly
from src.Containers.AppSection.SearchModule.Models.SearchIndex import SearchIndex


APP_CONFIG = AppConfig(
    app_name="search",
    migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
    table_classes=[SearchIndex],
    migration_dependencies=[],
    commands=[],
)
