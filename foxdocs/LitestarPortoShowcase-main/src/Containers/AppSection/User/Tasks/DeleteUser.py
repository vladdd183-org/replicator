"""Delete user task."""

from uuid import UUID

from src.Containers.AppSection.User.Data.Repositories import UserRepository
from src.Ship.Parents import Task


class DeleteUserTask(Task[UUID, bool]):
    """Task for deleting a user."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize task."""
        self.repository = repository

    async def run(self, data: UUID) -> bool:
        """Delete a user."""
        return await self.repository.delete(data)
