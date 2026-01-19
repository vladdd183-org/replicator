"""Book container dependency injection providers."""

from dishka import Provider, Scope, provide

from src.Containers.AppSection.Book.Actions import (
    CreateBookAction,
    DeleteBookAction,
    GetBookAction,
    ListBooksAction,
    UpdateBookAction,
)
from src.Containers.AppSection.Book.Data.Repositories import BookRepository
from src.Containers.AppSection.Book.UI.API.Transformers import BookTransformer
from src.Containers.AppSection.Book.Tasks import (
    CreateBookTask,
    DeleteBookTask,
    FindBookByIdTask,
    FindBookByIsbnTask,
    FindBooksTask,
    UpdateBookTask,
)


class BookProvider(Provider):
    """Book container provider."""

    # Repositories
    @provide(scope=Scope.REQUEST)
    def provide_book_repository(self) -> BookRepository:
        """Provide book repository."""
        return BookRepository()

    # Transformers
    @provide(scope=Scope.APP)
    def provide_book_transformer(self) -> BookTransformer:
        """Provide book transformer."""
        return BookTransformer()

    # Tasks
    @provide(scope=Scope.REQUEST)
    def provide_create_book_task(
        self, repository: BookRepository
    ) -> CreateBookTask:
        """Provide create book task."""
        return CreateBookTask(repository)

    @provide(scope=Scope.REQUEST)
    def provide_find_book_by_id_task(
        self, repository: BookRepository
    ) -> FindBookByIdTask:
        """Provide find book by ID task."""
        return FindBookByIdTask(repository)

    @provide(scope=Scope.REQUEST)
    def provide_find_book_by_isbn_task(
        self, repository: BookRepository
    ) -> FindBookByIsbnTask:
        """Provide find book by ISBN task."""
        return FindBookByIsbnTask(repository)

    @provide(scope=Scope.REQUEST)
    def provide_find_books_task(
        self, repository: BookRepository
    ) -> FindBooksTask:
        """Provide find books task."""
        return FindBooksTask(repository)

    @provide(scope=Scope.REQUEST)
    def provide_update_book_task(
        self, repository: BookRepository
    ) -> UpdateBookTask:
        """Provide update book task."""
        return UpdateBookTask(repository)

    @provide(scope=Scope.REQUEST)
    def provide_delete_book_task(
        self, repository: BookRepository
    ) -> DeleteBookTask:
        """Provide delete book task."""
        return DeleteBookTask(repository)

    # Actions
    @provide(scope=Scope.REQUEST)
    def provide_create_book_action(
        self,
        find_by_isbn_task: FindBookByIsbnTask,
        create_task: CreateBookTask,
        transformer: BookTransformer,
    ) -> CreateBookAction:
        """Provide create book action."""
        return CreateBookAction(find_by_isbn_task, create_task, transformer)

    @provide(scope=Scope.REQUEST)
    def provide_get_book_action(
        self,
        find_task: FindBookByIdTask,
        transformer: BookTransformer,
    ) -> GetBookAction:
        """Provide get book action."""
        return GetBookAction(find_task, transformer)

    @provide(scope=Scope.REQUEST)
    def provide_list_books_action(
        self,
        find_task: FindBooksTask,
        transformer: BookTransformer,
    ) -> ListBooksAction:
        """Provide list books action."""
        return ListBooksAction(find_task, transformer)

    @provide(scope=Scope.REQUEST)
    def provide_update_book_action(
        self,
        update_task: UpdateBookTask,
        transformer: BookTransformer,
    ) -> UpdateBookAction:
        """Provide update book action."""
        return UpdateBookAction(update_task, transformer)

    @provide(scope=Scope.REQUEST)
    def provide_delete_book_action(
        self,
        delete_task: DeleteBookTask,
    ) -> DeleteBookAction:
        """Provide delete book action."""
        return DeleteBookAction(delete_task)
