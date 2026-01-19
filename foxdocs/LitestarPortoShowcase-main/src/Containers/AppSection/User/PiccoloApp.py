"""Piccolo app configuration for User container."""

from piccolo.conf.apps import AppConfig

from src.Containers.AppSection.User.Models import User

APP_CONFIG = AppConfig(
    app_name="user",
    migrations_folder_path="Migrations",
    table_classes=[User],
)
