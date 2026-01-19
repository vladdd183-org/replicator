"""Piccolo app configuration for WebhookModule."""

import os

from piccolo.conf.apps import AppConfig

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


# Import table classes directly
from src.Containers.VendorSection.WebhookModule.Models.Webhook import Webhook
from src.Containers.VendorSection.WebhookModule.Models.WebhookDelivery import WebhookDelivery


APP_CONFIG = AppConfig(
    app_name="webhook",
    migrations_folder_path=os.path.join(CURRENT_DIRECTORY, "migrations"),
    table_classes=[Webhook, WebhookDelivery],
    migration_dependencies=[],
    commands=[],
)
