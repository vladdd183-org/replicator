"""Piccolo app configuration for Outbox module.

Registers the OutboxEvent model for Piccolo migrations.
Add this app to piccolo_conf.py APP_REGISTRY to enable migrations.
"""

import os

from piccolo.conf.apps import AppConfig

from src.Ship.Infrastructure.Events.Outbox.Models import OutboxEvent


CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


APP_CONFIG = AppConfig(
    app_name="outbox",
    migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
    table_classes=[OutboxEvent],
    migration_dependencies=[],
    commands=[],
)
