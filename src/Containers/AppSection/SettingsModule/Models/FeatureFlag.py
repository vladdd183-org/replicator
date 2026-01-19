"""Feature Flag model."""

from piccolo.columns import UUID, Varchar, Text, Boolean, Timestamptz, JSONB, Integer
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.defaults.timestamptz import TimestamptzNow

from src.Ship.Parents.Model import Model


class FeatureFlag(Model):
    """Feature flags for progressive rollouts and A/B testing.
    
    Attributes:
        id: Unique identifier
        name: Flag name (unique, e.g., "new_dashboard", "dark_mode")
        description: Human-readable description
        enabled: Global enable/disable
        rollout_percentage: Percentage of users to enable for (0-100)
        user_allowlist: JSON array of user IDs to always enable for
        user_denylist: JSON array of user IDs to always disable for
        metadata: Additional configuration
        created_at: When created
        updated_at: When last modified
    """
    
    id = UUID(primary_key=True, default=UUID4())
    name = Varchar(length=100, required=True, unique=True, index=True)
    description = Text(null=True)
    enabled = Boolean(default=False)
    rollout_percentage = Integer(default=0)  # 0-100
    user_allowlist = JSONB(null=True)  # ["user_id_1", "user_id_2"]
    user_denylist = JSONB(null=True)  # ["user_id_1"]
    metadata = JSONB(null=True)
    
    created_at = Timestamptz(default=TimestamptzNow())
    updated_at = Timestamptz(default=TimestamptzNow())
    
    class Meta:
        tablename = "feature_flags"



