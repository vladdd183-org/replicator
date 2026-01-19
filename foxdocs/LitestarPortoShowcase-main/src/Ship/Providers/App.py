"""Application dependency injection provider."""

from dishka import Provider, Scope, provide
from piccolo.engine.sqlite import SQLiteEngine

from src.Containers.AppSection.Book.Providers import BookProvider
from src.Containers.AppSection.User.Providers import UserProvider
from src.Containers.VendorSection.Payment.Providers import PaymentProvider
from src.Containers.VendorSection.Notification.Providers import NotificationProvider
from src.Ship.Configs import AppSettings, get_settings
from src.Ship.Core.Database import DB


class AppProvider(Provider):
    """Main application provider."""

    @provide(scope=Scope.APP)
    def provide_settings(self) -> AppSettings:
        """Provide application settings."""
        return get_settings()

    @provide(scope=Scope.APP)
    def provide_database(self) -> SQLiteEngine:
        """Provide database engine."""
        return DB


# Combine all providers
def get_all_providers() -> list[Provider]:
    """Get all application providers."""
    return [
        AppProvider(),
        # AppSection
        BookProvider(),
        UserProvider(),
        # VendorSection
        PaymentProvider(),
        NotificationProvider(),
    ]