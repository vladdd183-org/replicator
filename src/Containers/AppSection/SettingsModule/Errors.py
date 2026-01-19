"""SettingsModule errors."""

from typing import ClassVar

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class SettingsError(BaseError):
    """Base error for SettingsModule."""
    
    code: str = "SETTINGS_ERROR"


class SettingNotFoundError(ErrorWithTemplate, SettingsError):
    """Raised when setting is not found."""
    
    _message_template: ClassVar[str] = "Setting '{key}' not found"
    code: str = "SETTING_NOT_FOUND"
    http_status: int = 404
    key: str


class InvalidSettingValueError(ErrorWithTemplate, SettingsError):
    """Raised when setting value is invalid."""
    
    _message_template: ClassVar[str] = "Invalid value for setting '{key}': {details}"
    code: str = "INVALID_SETTING_VALUE"
    http_status: int = 400
    key: str
    details: str


class FeatureFlagNotFoundError(ErrorWithTemplate, SettingsError):
    """Raised when feature flag is not found."""
    
    _message_template: ClassVar[str] = "Feature flag '{flag_name}' not found"
    code: str = "FEATURE_FLAG_NOT_FOUND"
    http_status: int = 404
    flag_name: str


class SettingReadOnlyError(ErrorWithTemplate, SettingsError):
    """Raised when trying to modify a read-only setting."""
    
    _message_template: ClassVar[str] = "Setting '{key}' is read-only"
    code: str = "SETTING_READ_ONLY"
    http_status: int = 403
    key: str



