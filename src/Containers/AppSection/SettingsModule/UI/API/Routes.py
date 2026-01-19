"""SettingsModule API routes."""

from dishka.integrations.litestar import DishkaRouter

from src.Containers.AppSection.SettingsModule.UI.API.Controllers.SettingsController import (
    FeatureFlagsController,
    SettingsController,
)

settings_router = DishkaRouter(
    path="/api/v1",
    route_handlers=[
        SettingsController,
        FeatureFlagsController,
    ],
)
