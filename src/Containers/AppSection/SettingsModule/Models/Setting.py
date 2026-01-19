"""Global Setting model."""

from piccolo.columns import UUID, Varchar, Text, Boolean, Timestamptz, JSONB
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.defaults.timestamptz import TimestamptzNow

from src.Ship.Parents.Model import Model


class Setting(Model):
    """Global application settings.
    
    Key-value store for application configuration.
    
    Attributes:
        id: Unique identifier
        key: Setting key (unique, e.g., "max_file_size", "maintenance_mode")
        value: Setting value (stored as string, parsed by type)
        value_type: Type of value ("string", "int", "float", "bool", "json")
        description: Human-readable description
        is_readonly: Whether setting can be modified via API
        category: Category for grouping ("general", "security", "limits")
        created_at: When created
        updated_at: When last modified
    """
    
    id = UUID(primary_key=True, default=UUID4())
    key = Varchar(length=100, required=True, unique=True, index=True)
    value = Text(required=True)
    value_type = Varchar(length=20, default="string")  # string, int, float, bool, json
    description = Text(null=True)
    is_readonly = Boolean(default=False)
    category = Varchar(length=50, default="general", index=True)
    
    created_at = Timestamptz(default=TimestamptzNow())
    updated_at = Timestamptz(default=TimestamptzNow())
    
    class Meta:
        tablename = "settings"



