"""Ship Piccolo App configuration for migrations.

This module provides the APP_CONFIG for Piccolo migrations at the Ship level.
Containers should define their own PiccoloApp.py for module-specific tables.

Usage in piccolo_conf.py:
    from src.Ship.Core.PiccoloApp import APP_CONFIG as ship_app

    APP_REGISTRY = AppRegistry(apps=[
        ship_app.app_name,
        # ... other container apps
    ])
"""

import os

from piccolo.conf.apps import AppConfig, table_finder

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


APP_CONFIG = AppConfig(
    app_name="ship",
    migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
    table_classes=table_finder(
        modules=["src.Ship.Parents.Model"],
        include_tags=True,
    ),
    migration_dependencies=[],
    commands=[],
)
