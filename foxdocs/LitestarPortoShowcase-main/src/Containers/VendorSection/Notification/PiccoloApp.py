"""Piccolo app configuration for Notification container."""

from piccolo.conf.apps import AppConfig

from src.Containers.VendorSection.Notification.Models import Notification

APP_CONFIG = AppConfig(
    app_name="notification",
    migrations_folder_path="Migrations",
    table_classes=[Notification],
)



