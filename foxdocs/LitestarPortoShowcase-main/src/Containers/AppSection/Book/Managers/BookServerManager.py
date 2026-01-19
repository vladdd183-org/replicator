"""Book Server Manager for exposing book functionality."""

from uuid import UUID

from dishka import FromDishka

from src.Containers.AppSection.Book.Actions import (
    CreateBookAction,
    DeleteBookAction,
    GetBookAction,
    ListBooksAction,
    UpdateBookAction,
)
from src.Containers.AppSection.Book.Data.Dto import BookCreateDTO
from src.Containers.AppSection.Book.Data.Dto import BookDTO
from src.Containers.AppSection.Book.Data.Dto import BookUpdateDTO
from src.Ship.Parents import ServerManager


class BookServerManager(ServerManager[BookDTO]):
    """Server Manager for Book container."""
    
    def __init__(
        self,
        create_action: FromDishka[CreateBookAction],
        get_action: FromDishka[GetBookAction],
        list_action: FromDishka[ListBooksAction],
        update_action: FromDishka[UpdateBookAction],
        delete_action: FromDishka[DeleteBookAction],
    ):
        """Initialize with Book actions."""
        self.create_action = create_action
        self.get_action = get_action
        self.list_action = list_action
        self.update_action = update_action
        self.delete_action = delete_action
    
    async def get(self, id: UUID) -> BookDTO | None:
        """Get a book by ID."""
        try:
            return await self.get_action.run(book_id=id)
        except Exception:
            return None
    
    async def list(self, **filters) -> list[BookDTO]:
        """List all books."""
        return await self.list_action.run()
    
    async def create(self, data: BookCreateDTO) -> BookDTO:
        """Create a new book."""
        return await self.create_action.run(data=data)
    
    async def update(self, id: UUID, data: BookUpdateDTO) -> BookDTO | None:
        """Update a book."""
        try:
            return await self.update_action.run(book_id=id, data=data)
        except Exception:
            return None
    
    async def delete(self, id: UUID) -> bool:
        """Delete a book."""
        try:
            await self.delete_action.run(book_id=id)
            return True
        except Exception:
            return False
