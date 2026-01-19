"""Piccolo app configuration for Payment container."""

from piccolo.conf.apps import AppConfig

from src.Containers.VendorSection.Payment.Models import Payment, PaymentMethod

APP_CONFIG = AppConfig(
    app_name="payment",
    migrations_folder_path="Migrations",
    table_classes=[Payment, PaymentMethod],
)



