"""SettingsModule event listeners.

Listeners for handling settings-related domain events.
"""

import logfire
from litestar import Litestar
from litestar.events import listener


@listener("SettingChanged")
async def on_setting_changed(
    key: str,
    old_value: str | None,
    new_value: str,
    changed_by: str | None = None,
    app: Litestar | None = None,
    **kwargs,
) -> None:
    """Handle SettingChanged event.

    Logs the setting change for audit purposes.
    Can be extended to notify other systems or invalidate caches.
    """
    logfire.info(
        "⚙️ Setting changed",
        key=key,
        old_value=old_value,
        new_value=new_value,
        changed_by=changed_by,
    )


@listener("FeatureFlagToggled")
async def on_feature_flag_toggled(
    flag_name: str,
    enabled: bool,
    changed_by: str | None = None,
    app: Litestar | None = None,
    **kwargs,
) -> None:
    """Handle FeatureFlagToggled event.

    Logs the feature flag toggle for audit purposes.
    Can be extended to notify other systems or invalidate caches.
    """
    status = "enabled" if enabled else "disabled"
    logfire.info(
        f"🚩 Feature flag {status}",
        flag_name=flag_name,
        enabled=enabled,
        changed_by=changed_by,
    )


@listener("UserSettingChanged")
async def on_user_setting_changed(
    user_id: str,
    key: str,
    old_value: str | None,
    new_value: str,
    app: Litestar | None = None,
    **kwargs,
) -> None:
    """Handle UserSettingChanged event.

    Logs user-specific setting changes for audit purposes.
    """
    logfire.info(
        "👤 User setting changed",
        user_id=user_id,
        key=key,
        old_value=old_value,
        new_value=new_value,
    )


__all__ = [
    "on_feature_flag_toggled",
    "on_setting_changed",
    "on_user_setting_changed",
]
