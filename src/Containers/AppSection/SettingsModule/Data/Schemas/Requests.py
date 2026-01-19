"""SettingsModule request DTOs."""

from uuid import UUID

from pydantic import BaseModel, Field


class SetSettingRequest(BaseModel):
    """Request for setting a configuration value."""
    
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., max_length=10000)
    value_type: str = Field("string", pattern="^(string|int|float|bool|json)$")
    description: str | None = Field(None, max_length=500)
    category: str = Field("general", max_length=50)


class CreateFeatureFlagRequest(BaseModel):
    """Request for creating a feature flag."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    enabled: bool = False
    rollout_percentage: int = Field(0, ge=0, le=100)


class UpdateFeatureFlagRequest(BaseModel):
    """Request for updating a feature flag."""
    
    enabled: bool | None = None
    rollout_percentage: int | None = Field(None, ge=0, le=100)
    description: str | None = None
    user_allowlist: list[str] | None = None
    user_denylist: list[str] | None = None


class CheckFeatureFlagRequest(BaseModel):
    """Request for checking if feature flag is enabled."""
    
    flag_name: str = Field(..., min_length=1, max_length=100)
    user_id: UUID | None = None



