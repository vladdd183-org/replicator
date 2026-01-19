"""Find book tasks."""

from uuid import UUID

from src.Containers.AppSection.Book.Data.Repositories import BookRepository
from src.Containers.AppSection.Book.Models import Book
from src.Ship.Parents import Task


class FindBookByIdTask(Task[UUID, Book | None]):
    """Task for finding a book by ID."""

    def __init__(self, repository: BookRepository) -> None:
        """Initialize task.

        Args:
            repository: Book repository
        """
        self.repository = repository

    async def run(self, data: UUID) -> Book | None:
        """Find book by ID.

        Args:
            data: Book ID

        Returns:
            Book or None
        """
        return await self.repository.find_by_id(data)


class FindBookByIsbnTask(Task[str, Book | None]):
    """Task for finding a book by ISBN."""

    def __init__(self, repository: BookRepository) -> None:
        """Initialize task.

        Args:
            repository: Book repository
        """
        self.repository = repository

    async def run(self, data: str) -> Book | None:
        """Find book by ISBN.

        Args:
            data: Book ISBN

        Returns:
            Book or None
        """
        return await self.repository.find_by_isbn(data)


class FindBooksTask(Task[dict[str, int], list[Book]]):
    """Task for finding multiple books."""

    def __init__(self, repository: BookRepository) -> None:
        """Initialize task.

        Args:
            repository: Book repository
        """
        self.repository = repository

    async def run(self, data: dict[str, int]) -> list[Book]:
        """Find books with pagination.

        Args:
            data: Pagination parameters (limit, offset)

        Returns:
            List of books
        """
        limit = data.get("limit", 100)
        offset = data.get("offset", 0)
        return await self.repository.find_all(limit=limit, offset=offset)
