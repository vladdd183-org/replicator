"""Find user tasks."""

from uuid import UUID

from src.Containers.AppSection.User.Data.Repositories import UserRepository
from src.Containers.AppSection.User.Models import User
from src.Ship.Parents import Task


class FindUserByIdTask(Task[UUID, User | None]):
    """Task for finding a user by ID."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize task."""
        self.repository = repository

    async def run(self, data: UUID) -> User | None:
        """Find user by ID."""
        return await self.repository.find_by_id(data)


class FindUserByEmailTask(Task[str, User | None]):
    """Task for finding a user by email."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize task."""
        self.repository = repository

    async def run(self, data: str) -> User | None:
        """Find user by email."""
        return await self.repository.find_by_email(data)


class FindUsersTask(Task[dict[str, int], list[User]]):
    """Task for finding multiple users."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize task."""
        self.repository = repository

    async def run(self, data: dict[str, int]) -> list[User]:
        """Find users with pagination."""
        limit = data.get("limit", 100)
        offset = data.get("offset", 0)
        return await self.repository.find_all(limit=limit, offset=offset)
