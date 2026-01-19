"""Repository for Feature Flags."""

from datetime import UTC, datetime

from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag
from src.Ship.Parents.Repository import Repository


class FeatureFlagRepository(Repository[FeatureFlag]):
    """Repository for feature flags."""

    def __init__(self) -> None:
        super().__init__(FeatureFlag)

    async def get_by_name(self, name: str) -> FeatureFlag | None:
        """Get feature flag by name."""
        return await self.model.objects().where(self.model.name == name).first()

    async def get_all(self) -> list[FeatureFlag]:
        """Get all feature flags."""
        return await self.model.objects().order_by(self.model.name)

    async def get_enabled(self) -> list[FeatureFlag]:
        """Get all enabled feature flags."""
        return await (
            self.model.objects().where(self.model.enabled == True).order_by(self.model.name)
        )

    async def toggle(self, name: str, enabled: bool) -> FeatureFlag | None:
        """Toggle feature flag."""
        flag = await self.get_by_name(name)
        if flag:
            flag.enabled = enabled
            flag.updated_at = datetime.now(UTC)
            await flag.save()
        return flag

    async def set_rollout(self, name: str, percentage: int) -> FeatureFlag | None:
        """Set rollout percentage for a feature flag."""
        flag = await self.get_by_name(name)
        if flag:
            flag.rollout_percentage = max(0, min(100, percentage))
            flag.updated_at = datetime.now(UTC)
            await flag.save()
        return flag

    async def create_flag(
        self,
        name: str,
        description: str | None = None,
        enabled: bool = False,
        rollout_percentage: int = 0,
    ) -> FeatureFlag:
        """Create a new feature flag."""
        flag = FeatureFlag(
            name=name,
            description=description,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
        )
        await flag.save()
        return flag
