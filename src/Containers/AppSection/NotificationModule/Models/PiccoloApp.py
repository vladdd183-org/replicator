"""Piccolo App configuration for NotificationModule.

This file registers the Notification model with Piccolo for migrations.
"""

import os

from piccolo.conf.apps import AppConfig

from src.Containers.AppSection.NotificationModule.Models.Notification import Notification

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


APP_CONFIG = AppConfig(
    app_name="notification",
    migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
    table_classes=[Notification],
)
