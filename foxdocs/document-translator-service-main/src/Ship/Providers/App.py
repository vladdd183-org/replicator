"""Application dependency injection provider."""

from dishka import Provider, Scope, provide

from src.Containers.AppSection.OCR.Providers import OCRProvider
from src.Containers.AppSection.Translation.Providers import TranslationProvider
from src.Containers.AppSection.DocsTranslate.Providers import DocsTranslateProvider
from src.Ship.Configs import AppSettings, get_settings


class AppProvider(Provider):
    """Main application provider."""

    @provide(scope=Scope.APP)
    def provide_settings(self) -> AppSettings:
        """Provide application settings."""
        return get_settings()

    # Database is not used in this service anymore


# Combine all providers
def get_all_providers() -> list[Provider]:
    """Get all application providers."""
    return [
        AppProvider(),
        # AppSection
        OCRProvider(),
        TranslationProvider(),
        DocsTranslateProvider(),
    ]