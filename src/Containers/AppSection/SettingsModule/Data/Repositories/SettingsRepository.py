"""Repository for Settings."""

import json
from datetime import UTC, datetime
from typing import Any

from src.Containers.AppSection.SettingsModule.Models.Setting import Setting
from src.Ship.Parents.Repository import Repository


class SettingsRepository(Repository[Setting]):
    """Repository for global settings."""

    def __init__(self) -> None:
        super().__init__(Setting)

    async def get_by_key(self, key: str) -> Setting | None:
        """Get setting by key."""
        return await self.model.objects().where(self.model.key == key).first()

    async def get_by_category(self, category: str) -> list[Setting]:
        """Get all settings in a category."""
        return await (
            self.model.objects().where(self.model.category == category).order_by(self.model.key)
        )

    async def get_all(self) -> list[Setting]:
        """Get all settings."""
        return await self.model.objects().order_by(self.model.category).order_by(self.model.key)

    async def set_value(
        self,
        key: str,
        value: str,
        value_type: str = "string",
        description: str | None = None,
        category: str = "general",
        is_readonly: bool = False,
    ) -> Setting:
        """Set a setting value (create or update)."""
        existing = await self.get_by_key(key)

        if existing:
            existing.value = value
            existing.updated_at = datetime.now(UTC)
            if description:
                existing.description = description
            await existing.save()
            return existing

        setting = Setting(
            key=key,
            value=value,
            value_type=value_type,
            description=description,
            category=category,
            is_readonly=is_readonly,
        )
        await setting.save()
        return setting

    def parse_value(self, setting: Setting) -> Any:
        """Parse setting value based on its type."""
        value = setting.value
        value_type = setting.value_type

        if value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "bool":
            return value.lower() in ("true", "1", "yes", "on")
        elif value_type == "json":
            return json.loads(value)
        else:
            return value
