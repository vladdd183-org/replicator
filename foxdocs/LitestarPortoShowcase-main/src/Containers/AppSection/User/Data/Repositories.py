"""User repository."""

from uuid import UUID

from src.Containers.AppSection.User.Models import User
from src.Ship.Parents import Repository


class UserRepository(Repository[User]):
    """User repository for data persistence."""

    def __init__(self) -> None:
        """Initialize user repository."""
        super().__init__(User)

    async def find_by_id(self, user_id: UUID) -> User | None:
        """Find user by ID."""
        return await self.model.objects().where(
            self.model.id == user_id
        ).first()

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email."""
        return await self.model.objects().where(
            self.model.email == email
        ).first()

    async def find_by_username(self, username: str) -> User | None:
        """Find user by username."""
        return await self.model.objects().where(
            self.model.username == username
        ).first()

    async def find_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """Find all users with pagination."""
        return await self.model.objects().limit(limit).offset(offset)

    async def create(self, data: dict) -> User:
        """Create a new user."""
        user = self.model(**data)
        await user.save()
        return user

    async def update(self, user_id: UUID, data: dict) -> User | None:
        """Update a user."""
        # Remove None values
        update_data = {k: v for k, v in data.items() if v is not None}
        
        if not update_data:
            return await self.find_by_id(user_id)
        
        await self.model.update(update_data).where(
            self.model.id == user_id
        )
        
        return await self.find_by_id(user_id)

    async def delete(self, user_id: UUID) -> bool:
        """Delete a user."""
        result = await self.model.delete().where(
            self.model.id == user_id
        )
        return result > 0
