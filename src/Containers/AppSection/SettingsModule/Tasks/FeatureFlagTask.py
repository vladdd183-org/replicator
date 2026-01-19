"""Task for checking feature flags."""

import hashlib
from uuid import UUID

from pydantic import BaseModel

from src.Ship.Parents.Task import Task
from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag


class FeatureFlagCheckInput(BaseModel):
    """Input for feature flag check."""
    
    model_config = {"frozen": True}
    
    flag_name: str
    user_id: UUID | None = None


class CheckFeatureFlagTask(Task[FeatureFlagCheckInput, bool]):
    """Task for checking if a feature flag is enabled for a user.
    
    Logic:
    1. If flag doesn't exist -> False
    2. If user in denylist -> False
    3. If user in allowlist -> True
    4. If flag disabled globally -> False
    5. If rollout_percentage == 100 -> True
    6. If rollout_percentage == 0 -> False
    7. Otherwise: hash(user_id + flag_name) % 100 < rollout_percentage
    """
    
    _flags_cache: dict[str, FeatureFlag] = {}
    
    async def run(self, data: FeatureFlagCheckInput) -> bool:
        """Check if feature flag is enabled.
        
        Note: This task is async because it hits the database.
        In production, flags would be cached in Redis.
        """
        return await self._check_flag_async(data)
    
    async def _check_flag_async(self, data: FeatureFlagCheckInput) -> bool:
        """Async implementation of flag check."""
        flag = await (
            FeatureFlag.objects()
            .where(FeatureFlag.name == data.flag_name)
            .first()
        )
        
        if not flag:
            return False
        
        return self._evaluate_flag(flag, data.user_id)
    
    def _evaluate_flag(self, flag: FeatureFlag, user_id: UUID | None) -> bool:
        """Evaluate flag for a user."""
        # Check denylist
        if user_id and flag.user_denylist:
            if str(user_id) in flag.user_denylist:
                return False
        
        # Check allowlist
        if user_id and flag.user_allowlist:
            if str(user_id) in flag.user_allowlist:
                return True
        
        # Check global enable
        if not flag.enabled:
            return False
        
        # Check rollout percentage
        if flag.rollout_percentage >= 100:
            return True
        
        if flag.rollout_percentage <= 0:
            return False
        
        # Percentage-based rollout
        if user_id:
            # Consistent hashing: same user always gets same result
            hash_input = f"{user_id}:{flag.name}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            return (hash_value % 100) < flag.rollout_percentage
        
        # No user, no percentage-based check
        return False


async def is_feature_enabled(flag_name: str, user_id: UUID | None = None) -> bool:
    """Convenience async function to check feature flag.
    
    Example:
        if await is_feature_enabled("new_dashboard", current_user.id):
            return render_new_dashboard()
        else:
            return render_old_dashboard()
    """
    task = CheckFeatureFlagTask()
    return await task.run(FeatureFlagCheckInput(flag_name=flag_name, user_id=user_id))



