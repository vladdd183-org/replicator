"""User-specific Setting model."""

from piccolo.columns import UUID, Varchar, Text, Timestamptz
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.defaults.timestamptz import TimestamptzNow

from src.Ship.Parents.Model import Model


class UserSetting(Model):
    """User-specific settings.
    
    Allows users to override global settings or store preferences.
    
    Attributes:
        id: Unique identifier
        user_id: User this setting belongs to
        key: Setting key
        value: Setting value
        created_at: When created
        updated_at: When last modified
    """
    
    id = UUID(primary_key=True, default=UUID4())
    user_id = UUID(required=True, index=True)
    key = Varchar(length=100, required=True, index=True)
    value = Text(required=True)
    
    created_at = Timestamptz(default=TimestamptzNow())
    updated_at = Timestamptz(default=TimestamptzNow())
    
    class Meta:
        tablename = "user_settings"
        # Unique constraint on user_id + key
        unique_together = [("user_id", "key")]



