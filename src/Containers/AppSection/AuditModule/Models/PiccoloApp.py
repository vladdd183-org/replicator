"""Piccolo app configuration for AuditModule."""

import os

from piccolo.conf.apps import AppConfig

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


# Import table classes directly
from src.Containers.AppSection.AuditModule.Models.AuditLog import AuditLog

APP_CONFIG = AppConfig(
    app_name="audit",
    migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
    table_classes=[AuditLog],
    migration_dependencies=[],
    commands=[],
)
