"""Piccolo app configuration for OrderModule.

Registers tables for migration management.
"""

import os

from piccolo.conf.apps import AppConfig, table_finder

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


APP_CONFIG = AppConfig(
    app_name="order",
    migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
    table_classes=table_finder(
        modules=[
            "src.Containers.AppSection.OrderModule.Models.Order",
            "src.Containers.AppSection.OrderModule.Models.OrderItem",
        ],
        exclude_imported=True,
    ),
)
