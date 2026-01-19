"""Book-specific exceptions."""

from uuid import UUID

from src.Ship.Parents import PortoException


class BookNotFoundException(PortoException):
    """Exception raised when book is not found."""

    def __init__(self, book_id: UUID | None = None, isbn: str | None = None) -> None:
        """Initialize exception.

        Args:
            book_id: Book ID
            isbn: Book ISBN
        """
        if book_id:
            message = f"Book with ID {book_id} not found"
            details = {"book_id": str(book_id)}
        else:
            message = f"Book with ISBN {isbn} not found"
            details = {"isbn": isbn}

        super().__init__(
            message=message,
            code="BOOK_NOT_FOUND",
            status_code=404,
            details=details,
        )


class BookAlreadyExistsException(PortoException):
    """Exception raised when book already exists."""

    def __init__(self, isbn: str) -> None:
        """Initialize exception.

        Args:
            isbn: Book ISBN
        """
        super().__init__(
            message=f"Book with ISBN {isbn} already exists",
            code="BOOK_ALREADY_EXISTS",
            status_code=409,
            details={"isbn": isbn},
        )
