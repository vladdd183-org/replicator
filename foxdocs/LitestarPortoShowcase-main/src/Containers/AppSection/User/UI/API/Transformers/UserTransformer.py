"""User transformer."""

from src.Containers.AppSection.User.Data.Dto import UserDTO
from src.Containers.AppSection.User.Models import User
from src.Ship.Parents import Transformer


class UserTransformer(Transformer[User, UserDTO]):
    """Transform User model to UserDTO."""

    def transform(self, data: User) -> UserDTO:
        """Transform User model to DTO."""
        return UserDTO(
            id=data.id,
            email=data.email,
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            role=data.role,
            is_active=data.is_active,
            is_verified=data.is_verified,
            created_at=data.created_at,
            updated_at=data.updated_at,
            last_login=data.last_login,
        )
