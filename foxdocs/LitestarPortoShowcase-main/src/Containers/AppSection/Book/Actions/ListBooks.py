"""List books action."""

from src.Containers.AppSection.Book.Data.Dto import BookDTO
from src.Containers.AppSection.Book.UI.API.Transformers import BookTransformer
from src.Containers.AppSection.Book.Tasks import FindBooksTask
from src.Ship.Parents import Action


class ListBooksAction(Action[dict[str, int], list[BookDTO]]):
    """Action for listing books."""

    def __init__(
        self,
        find_books_task: FindBooksTask,
        transformer: BookTransformer,
    ) -> None:
        """Initialize action.

        Args:
            find_books_task: Task for finding books
            transformer: Book transformer
        """
        self.find_books_task = find_books_task
        self.transformer = transformer

    async def run(self, data: dict[str, int]) -> list[BookDTO]:
        """List books with pagination.

        Args:
            data: Pagination parameters (limit, offset)

        Returns:
            List of book DTOs
        """
        books = await self.find_books_task.run(data)
        return self.transformer.transform_collection(books)
