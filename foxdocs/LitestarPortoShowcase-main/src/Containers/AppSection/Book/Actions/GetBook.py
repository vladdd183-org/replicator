"""Get book action."""

from uuid import UUID

from src.Containers.AppSection.Book.Data.Dto import BookDTO
from src.Containers.AppSection.Book.Exceptions import BookNotFoundException
from src.Containers.AppSection.Book.UI.API.Transformers import BookTransformer
from src.Containers.AppSection.Book.Tasks import FindBookByIdTask
from src.Ship.Parents import Action


class GetBookAction(Action[UUID, BookDTO]):
    """Action for getting a book by ID."""

    def __init__(
        self,
        find_book_task: FindBookByIdTask,
        transformer: BookTransformer,
    ) -> None:
        """Initialize action.

        Args:
            find_book_task: Task for finding book
            transformer: Book transformer
        """
        self.find_book_task = find_book_task
        self.transformer = transformer

    async def run(self, data: UUID) -> BookDTO:
        """Get a book by ID.

        Args:
            data: Book ID

        Returns:
            Book DTO

        Raises:
            BookNotFoundException: If book not found
        """
        book = await self.find_book_task.run(data)
        if not book:
            raise BookNotFoundException(book_id=data)

        return self.transformer.transform(book)
