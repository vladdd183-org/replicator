"""Delete book task."""

from uuid import UUID

from src.Containers.AppSection.Book.Data.Repositories import BookRepository
from src.Ship.Parents import Task


class DeleteBookTask(Task[UUID, bool]):
    """Task for deleting a book."""

    def __init__(self, repository: BookRepository) -> None:
        """Initialize task.

        Args:
            repository: Book repository
        """
        self.repository = repository

    async def run(self, data: UUID) -> bool:
        """Delete a book.

        Args:
            data: Book ID

        Returns:
            True if deleted, False otherwise
        """
        return await self.repository.delete(data)
