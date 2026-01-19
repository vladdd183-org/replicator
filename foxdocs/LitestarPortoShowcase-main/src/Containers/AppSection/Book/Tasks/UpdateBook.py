"""Update book task."""

from datetime import datetime
from uuid import UUID

from src.Containers.AppSection.Book.Data.Dto import BookUpdateDTO
from src.Containers.AppSection.Book.Data.Repositories import BookRepository
from src.Containers.AppSection.Book.Models import Book
from src.Ship.Parents import Task


class UpdateBookTask(Task[tuple[UUID, BookUpdateDTO], Book | None]):
    """Task for updating a book."""

    def __init__(self, repository: BookRepository) -> None:
        """Initialize task.

        Args:
            repository: Book repository
        """
        self.repository = repository

    async def run(self, data: tuple[UUID, BookUpdateDTO]) -> Book | None:
        """Update a book.

        Args:
            data: Tuple of book ID and update data

        Returns:
            Updated book or None
        """
        book_id, update_dto = data
        update_data = update_dto.model_dump(exclude_unset=True)
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()

        return await self.repository.update(book_id, update_data)
