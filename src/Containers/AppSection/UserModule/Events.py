"""UserModule domain events.

All domain events for the User module in one place.
Events are immutable (frozen) Pydantic models published after UoW commit.
"""

from uuid import UUID

from pydantic import Field

from src.Ship.Parents.Event import DomainEvent


class UserCreated(DomainEvent):
    """Event raised when a new user is created.

    Attributes:
        user_id: UUID of the created user
        email: Email of the created user
        name: Name of the created user
    """

    user_id: UUID
    email: str
    name: str


class UserUpdated(DomainEvent):
    """Event raised when a user is updated.

    Attributes:
        user_id: UUID of the updated user
        updated_fields: List of field names that were updated
    """

    user_id: UUID
    updated_fields: list[str] = Field(default_factory=list)


class UserDeleted(DomainEvent):
    """Event raised when a user is deleted.

    Attributes:
        user_id: UUID of the deleted user
        email: Email of the deleted user
    """

    user_id: UUID
    email: str


# Export all events
__all__ = ["UserCreated", "UserDeleted", "UserUpdated"]
