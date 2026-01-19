"""Update book action."""

from uuid import UUID

from src.Containers.AppSection.Book.Data.Dto import (
    BookDTO,
    BookUpdateDTO,
)
from src.Containers.AppSection.Book.Exceptions import BookNotFoundException
from src.Containers.AppSection.Book.UI.API.Transformers import BookTransformer
from src.Containers.AppSection.Book.Tasks import UpdateBookTask
from src.Ship.Parents import Action


class UpdateBookAction(Action[tuple[UUID, BookUpdateDTO], BookDTO]):
    """Action for updating a book."""

    def __init__(
        self,
        update_book_task: UpdateBookTask,
        transformer: BookTransformer,
    ) -> None:
        """Initialize action.

        Args:
            update_book_task: Task for updating book
            transformer: Book transformer
        """
        self.update_book_task = update_book_task
        self.transformer = transformer

    async def run(self, data: tuple[UUID, BookUpdateDTO]) -> BookDTO:
        """Update a book.

        Args:
            data: Tuple of book ID and update data

        Returns:
            Updated book DTO

        Raises:
            BookNotFoundException: If book not found
        """
        book = await self.update_book_task.run(data)
        if not book:
            raise BookNotFoundException(book_id=data[0])

        return self.transformer.transform(book)
