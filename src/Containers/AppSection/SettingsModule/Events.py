"""SettingsModule domain events."""

from uuid import UUID

from src.Ship.Parents.Event import DomainEvent


class SettingChanged(DomainEvent):
    """Emitted when a setting is changed."""

    key: str
    old_value: str | None
    new_value: str
    changed_by: UUID | None


class FeatureFlagToggled(DomainEvent):
    """Emitted when a feature flag is toggled."""

    flag_name: str
    enabled: bool
    changed_by: UUID | None


class UserSettingChanged(DomainEvent):
    """Emitted when a user-specific setting is changed."""

    user_id: UUID
    key: str
    old_value: str | None
    new_value: str


__all__ = ["FeatureFlagToggled", "SettingChanged", "UserSettingChanged"]
