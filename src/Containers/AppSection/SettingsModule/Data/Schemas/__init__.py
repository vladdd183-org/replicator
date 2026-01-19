"""SettingsModule Data Transfer Objects.

Request and Response DTOs for settings and feature flags.
"""

from src.Containers.AppSection.SettingsModule.Data.Schemas.Requests import (
    CheckFeatureFlagRequest,
    CreateFeatureFlagRequest,
    SetSettingRequest,
    UpdateFeatureFlagRequest,
)
from src.Containers.AppSection.SettingsModule.Data.Schemas.Responses import (
    FeatureFlagCheckResponse,
    FeatureFlagResponse,
    FeatureFlagsListResponse,
    SettingResponse,
    SettingsListResponse,
)

__all__ = [
    # Requests
    "SetSettingRequest",
    "CreateFeatureFlagRequest",
    "UpdateFeatureFlagRequest",
    "CheckFeatureFlagRequest",
    # Responses
    "SettingResponse",
    "SettingsListResponse",
    "FeatureFlagResponse",
    "FeatureFlagsListResponse",
    "FeatureFlagCheckResponse",
]
