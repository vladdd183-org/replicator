"""Piccolo ORM configuration."""

from piccolo.conf.apps import AppRegistry
from piccolo.engine.sqlite import SQLiteEngine

from src.Ship.Configs import get_settings

settings = get_settings()

# Database connection
DB = SQLiteEngine(path=settings.db_url.replace("sqlite:///", ""))

# App registry - явная регистрация всех Piccolo приложений
APP_REGISTRY = AppRegistry(
    apps=[
        # Ship Infrastructure
        "src.Ship.Infrastructure.Events.Outbox.PiccoloApp",
        # AppSection
        "src.Containers.AppSection.UserModule.Models.PiccoloApp",
        "src.Containers.AppSection.NotificationModule.Models.PiccoloApp",
        "src.Containers.AppSection.AuditModule.Models.PiccoloApp",
        "src.Containers.AppSection.SearchModule.Models.PiccoloApp",
        "src.Containers.AppSection.SettingsModule.Models.PiccoloApp",
        "src.Containers.AppSection.OrderModule.Models.PiccoloApp",
        # VendorSection
        "src.Containers.VendorSection.WebhookModule.Models.PiccoloApp",
    ]
)

