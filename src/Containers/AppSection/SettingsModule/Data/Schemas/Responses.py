"""SettingsModule response DTOs."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import field_validator

from src.Ship.Core.BaseSchema import EntitySchema


class SettingResponse(EntitySchema):
    """Response DTO for a setting."""
    
    id: UUID
    key: str
    value: str
    parsed_value: Any  # Parsed based on value_type
    value_type: str
    description: str | None
    category: str
    is_readonly: bool
    created_at: datetime
    updated_at: datetime


class SettingsListResponse(EntitySchema):
    """Response DTO for settings list."""
    
    settings: list[SettingResponse]
    total: int


class FeatureFlagResponse(EntitySchema):
    """Response DTO for a feature flag."""
    
    id: UUID
    name: str
    description: str | None
    enabled: bool
    rollout_percentage: int
    user_allowlist: list[str] | None
    user_denylist: list[str] | None
    metadata: dict | None
    created_at: datetime
    updated_at: datetime
    
    @field_validator("user_allowlist", "user_denylist", mode="before")
    @classmethod
    def parse_list(cls, v: Any) -> list[str] | None:
        """Parse list from JSON string if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            if v in ("", "{}", "null"):
                return None
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return None
            except json.JSONDecodeError:
                return None
        return v
    
    @field_validator("metadata", mode="before")
    @classmethod
    def parse_dict(cls, v: Any) -> dict | None:
        """Parse dict from JSON string if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            if v in ("", "{}", "null"):
                return None
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict) and parsed:  # Non-empty dict
                    return parsed
                return None
            except json.JSONDecodeError:
                return None
        return v


class FeatureFlagsListResponse(EntitySchema):
    """Response DTO for feature flags list."""
    
    flags: list[FeatureFlagResponse]
    total: int


class FeatureFlagCheckResponse(EntitySchema):
    """Response for feature flag check."""
    
    flag_name: str
    enabled: bool
    user_id: UUID | None

