"""Book repository."""

from uuid import UUID

from src.Containers.AppSection.Book.Models import Book
from src.Ship.Parents import Repository


class BookRepository(Repository[Book]):
    """Book repository for data persistence."""

    def __init__(self) -> None:
        """Initialize book repository."""
        super().__init__(Book)

    async def find_by_id(self, book_id: UUID) -> Book | None:
        """Find book by ID.

        Args:
            book_id: Book ID

        Returns:
            Book instance or None
        """
        return await self.model.objects().where(
            self.model.id == book_id
        ).first()

    async def find_by_isbn(self, isbn: str) -> Book | None:
        """Find book by ISBN.

        Args:
            isbn: Book ISBN

        Returns:
            Book instance or None
        """
        return await self.model.objects().where(
            self.model.isbn == isbn
        ).first()

    async def find_all(self, limit: int = 100, offset: int = 0) -> list[Book]:
        """Find all books with pagination.

        Args:
            limit: Maximum number of books to return
            offset: Number of books to skip

        Returns:
            List of books
        """
        return await self.model.objects().limit(limit).offset(offset)

    async def create(self, data: dict) -> Book:
        """Create a new book.

        Args:
            data: Book data

        Returns:
            Created book instance
        """
        book = self.model(**data)
        await book.save()
        return book

    async def update(self, book_id: UUID, data: dict) -> Book | None:
        """Update a book.

        Args:
            book_id: Book ID
            data: Update data

        Returns:
            Updated book instance or None
        """
        # Remove None values
        update_data = {k: v for k, v in data.items() if v is not None}
        
        if not update_data:
            return await self.find_by_id(book_id)
        
        await self.model.update(update_data).where(
            self.model.id == book_id
        )
        
        return await self.find_by_id(book_id)

    async def delete(self, book_id: UUID) -> bool:
        """Delete a book.

        Args:
            book_id: Book ID

        Returns:
            True if deleted, False otherwise
        """
        result = await self.model.delete().where(
            self.model.id == book_id
        )
        return result > 0
