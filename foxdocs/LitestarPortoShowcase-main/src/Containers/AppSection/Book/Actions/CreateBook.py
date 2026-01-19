"""Create book action."""

from src.Containers.AppSection.Book.Data.Dto import (
    BookCreateDTO,
    BookDTO,
)
from src.Containers.AppSection.Book.Exceptions import BookAlreadyExistsException
from src.Containers.AppSection.Book.UI.API.Transformers import BookTransformer
from src.Containers.AppSection.Book.Tasks import CreateBookTask, FindBookByIsbnTask
from src.Ship.Parents import Action


class CreateBookAction(Action[BookCreateDTO, BookDTO]):
    """Action for creating a book."""

    def __init__(
        self,
        find_by_isbn_task: FindBookByIsbnTask,
        create_book_task: CreateBookTask,
        transformer: BookTransformer,
    ) -> None:
        """Initialize action.

        Args:
            find_by_isbn_task: Task for finding book by ISBN
            create_book_task: Task for creating book
            transformer: Book transformer
        """
        self.find_by_isbn_task = find_by_isbn_task
        self.create_book_task = create_book_task
        self.transformer = transformer

    async def run(self, data: BookCreateDTO) -> BookDTO:
        """Create a new book.

        Args:
            data: Book creation data

        Returns:
            Created book DTO

        Raises:
            BookAlreadyExistsException: If book with ISBN already exists
        """
        # Check if book with ISBN already exists
        existing_book = await self.find_by_isbn_task.run(data.isbn)
        if existing_book:
            raise BookAlreadyExistsException(isbn=data.isbn)

        # Create the book
        book = await self.create_book_task.run(data)

        # Transform to DTO
        return self.transformer.transform(book)
