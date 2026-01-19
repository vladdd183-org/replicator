"""Book Transformer for converting models to DTOs."""

from src.Containers.AppSection.Book.Data.Dto import BookDTO
from src.Containers.AppSection.Book.Models import Book
from src.Ship.Parents import Transformer


class BookTransformer(Transformer[Book, BookDTO]):
    """Transforms Book models to DTOs."""
    
    def transform(self, book: Book) -> BookDTO:
        """Transform a Book model to a DTO."""
        return BookDTO(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            description=book.description,
            is_available=book.is_available,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )
    
    def transform_list(self, books: list[Book]) -> list[BookDTO]:
        """Transform a list of Book models to DTOs."""
        return [self.transform(book) for book in books]
