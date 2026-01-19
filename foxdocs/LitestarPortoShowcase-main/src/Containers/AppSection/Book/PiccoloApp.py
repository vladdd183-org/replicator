"""Piccolo app configuration for Book container."""

from piccolo.conf.apps import AppConfig

from src.Containers.AppSection.Book.Models import Book

APP_CONFIG = AppConfig(
    app_name="book",
    migrations_folder_path="migrations",
    table_classes=[Book],
)
