"""User model for Piccolo ORM."""

from piccolo.columns import UUID, Varchar, Boolean, Timestamptz
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.defaults.timestamptz import TimestamptzNow

from src.Ship.Parents.Model import Model


class AppUser(Model):
    """User entity.
    
    Represents a user in the system with authentication data.
    Named AppUser to avoid SQL reserved word 'user'.
    
    Attributes:
        id: Unique identifier (UUID)
        email: User's email address (unique)
        password_hash: Hashed password
        name: User's display name
        is_active: Whether the user account is active
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    
    id = UUID(primary_key=True, default=UUID4())
    email = Varchar(length=255, unique=True, required=True, index=True)
    password_hash = Varchar(length=255, required=True)
    name = Varchar(length=100, required=True)
    is_active = Boolean(default=True)
    created_at = Timestamptz(default=TimestamptzNow())
    # Note: auto_update removed due to SQLite incompatibility with TimestamptzNow
    # updated_at is set manually in repository.update()
    updated_at = Timestamptz(default=TimestamptzNow())
    
    class Meta:
        """Piccolo meta configuration."""
        
        tablename = "app_users"
