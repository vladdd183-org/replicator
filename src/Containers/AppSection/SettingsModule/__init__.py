"""SettingsModule - Настройки приложения и Feature Flags.

Демонстрирует:
- Key-value хранилище
- Кэширование с инвалидацией
- Feature Flags (A/B testing)
- Per-user settings vs global settings
"""

from src.Containers.AppSection.SettingsModule.UI.API.Routes import settings_router

__all__ = ["settings_router"]
