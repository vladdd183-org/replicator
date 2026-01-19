"""Create book task."""

from datetime import datetime
from uuid import uuid4

from src.Containers.AppSection.Book.Data.Dto import BookCreateDTO
from src.Containers.AppSection.Book.Data.Repositories import BookRepository
from src.Containers.AppSection.Book.Models import Book
from src.Ship.Parents import Task


class CreateBookTask(Task[BookCreateDTO, Book]):
    """Task for creating a book."""

    def __init__(self, repository: BookRepository) -> None:
        """Initialize task.

        Args:
            repository: Book repository
        """
        self.repository = repository

    async def run(self, data: BookCreateDTO) -> Book:
        """Create a new book.

        Args:
            data: Book creation data

        Returns:
            Created book
        """
        book_data = data.model_dump()
        book_data["id"] = uuid4()
        book_data["created_at"] = datetime.utcnow()
        book_data["updated_at"] = datetime.utcnow()

        return await self.repository.create(book_data)
