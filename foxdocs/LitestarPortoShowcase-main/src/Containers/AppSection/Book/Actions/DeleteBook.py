"""Delete book action."""

from uuid import UUID

from src.Containers.AppSection.Book.Exceptions import BookNotFoundException
from src.Containers.AppSection.Book.Tasks import DeleteBookTask
from src.Ship.Parents import Action


class DeleteBookAction(Action[UUID, None]):
    """Action for deleting a book."""

    def __init__(self, delete_book_task: DeleteBookTask) -> None:
        """Initialize action.

        Args:
            delete_book_task: Task for deleting book
        """
        self.delete_book_task = delete_book_task

    async def run(self, data: UUID) -> None:
        """Delete a book.

        Args:
            data: Book ID

        Raises:
            BookNotFoundException: If book not found
        """
        deleted = await self.delete_book_task.run(data)
        if not deleted:
            raise BookNotFoundException(book_id=data)
