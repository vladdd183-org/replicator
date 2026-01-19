"""User model."""

from datetime import datetime
from enum import Enum

from piccolo.columns import UUID, Boolean, Text, Timestamptz, Varchar

from src.Ship.Parents import Model


class UserRole(Enum):
    """User roles."""
    
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class User(Model):
    """User model."""

    id = UUID(primary_key=True)
    email = Varchar(length=255, unique=True, required=True)
    username = Varchar(length=100, unique=True, required=True)
    first_name = Varchar(length=100, default="")
    last_name = Varchar(length=100, default="")
    password_hash = Text(required=True)
    role = Varchar(length=20, default=UserRole.USER.value)
    is_active = Boolean(default=True)
    is_verified = Boolean(default=False)
    created_at = Timestamptz()
    updated_at = Timestamptz()
    last_login = Timestamptz(null=True)

    @classmethod
    def get_readable(cls) -> Varchar:
        """Get readable representation."""
        return cls.username
