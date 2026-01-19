"""Book API controller."""

from uuid import UUID

from dishka import FromDishka
from dishka.integrations.litestar import inject
from litestar import Request, delete, get, patch, post
from litestar.params import Parameter
import httpx
from src.Ship.Parents.Controller import BaseController

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


class BookController(BaseController):
    """Book API controller."""

    path = "/api/books"

    @post("/")
    @inject
    async def create_book(
        self,
        request: Request,
        data: BookCreateDTO,
        action: FromDishka[CreateBookAction],
    ) -> BookDTO:
        """Create a new book.

        Args:
            request: HTTP request
            data: Book creation data
            action: Create book action

        Returns:
            Created book
        """
        self.log_request(request, book_title=data.title)
        self.log_action_call("CreateBookAction", book_title=data.title)
        
        result = await action.execute(data)
        
        self.log_response(request, status=201, book_id=str(result.id))
        return result

    @get("/")
    @inject
    async def list_books(
        self,
        request: Request,
        action: FromDishka[ListBooksAction],
        limit: int = Parameter(default=100, ge=1, le=1000),
        offset: int = Parameter(default=0, ge=0),
    ) -> list[BookDTO]:
        """List books with pagination.

        Args:
            request: HTTP request
            action: List books action
            limit: Maximum number of books to return
            offset: Number of books to skip

        Returns:
            List of books
        """
        url = "https://httpbin.org/get"

        with httpx.Client() as client:
            client.get(url)



        async with httpx.AsyncClient() as client:
            await client.get(url)
        self.log_request(request, limit=limit, offset=offset)
        self.log_action_call("ListBooksAction", limit=limit, offset=offset)
        
        result = await action.execute({"limit": limit, "offset": offset})
        
        self.log_response(request, books_count=len(result))
        return result

    @get("/{book_id:uuid}")
    @inject
    async def get_book(
        self,
        request: Request,
        book_id: UUID,
        action: FromDishka[GetBookAction],
    ) -> BookDTO:
        """Get a book by ID.

        Args:
            request: HTTP request
            book_id: Book ID
            action: Get book action

        Returns:
            Book details
        """
        self.log_request(request, book_id=str(book_id))
        self.log_action_call("GetBookAction", book_id=str(book_id))
        
        result = await action.execute(book_id)
        
        self.log_response(request, book_id=str(result.id), book_title=result.title)
        return result

    @patch("/{book_id:uuid}")
    @inject
    async def update_book(
        self,
        request: Request,
        book_id: UUID,
        data: BookUpdateDTO,
        action: FromDishka[UpdateBookAction],
    ) -> BookDTO:
        """Update a book.

        Args:
            request: HTTP request
            book_id: Book ID
            data: Update data
            action: Update book action

        Returns:
            Updated book
        """
        self.log_request(request, book_id=str(book_id), updates=data.model_dump(exclude_unset=True))
        self.log_action_call("UpdateBookAction", book_id=str(book_id))
        
        result = await action.execute((book_id, data))
        
        self.log_response(request, book_id=str(result.id), book_title=result.title)
        return result

    @delete("/{book_id:uuid}", status_code=204)
    @inject
    async def delete_book(
        self,
        request: Request,
        book_id: UUID,
        action: FromDishka[DeleteBookAction],
    ) -> None:
        """Delete a book.

        Args:
            request: HTTP request
            book_id: Book ID
            action: Delete book action
        """
        self.log_request(request, book_id=str(book_id))
        self.log_action_call("DeleteBookAction", book_id=str(book_id))
        
        await action.execute(book_id)
        
        self.log_response(request, status=204, book_id=str(book_id))
