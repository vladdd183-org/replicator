"""Book Container - Porto Architecture.

This module provides a clean interface for the Book container,
exposing commonly used classes and functions.
"""

# Core Models
from src.Containers.AppSection.Book.Models import Book, BookLoan

# DTOs
from src.Containers.AppSection.Book.Data import BookCreateDTO, BookDTO, BookUpdateDTO, BookRepository

# Actions
from src.Containers.AppSection.Book.Actions import (
    CreateBookAction,
    DeleteBookAction,
    GetBookAction,
    ListBooksAction,
    UpdateBookAction,
)

# Tasks
from src.Containers.AppSection.Book.Tasks import (
    CreateBookTask,
    DeleteBookTask,
    FindBookByIdTask,
    FindBookByIsbnTask,
    FindBooksTask,
    UpdateBookTask,
)

# Exceptions
from src.Containers.AppSection.Book.Exceptions import BookAlreadyExistsException, BookNotFoundException

# Transformers are available via .UI.API.Transformers import

# Managers
from src.Containers.AppSection.Book.Managers import BookServerManager, UserClientManager

__all__ = [
    # Models
    "Book",
    "BookLoan",
    # DTOs & Repository
    "BookCreateDTO",
    "BookDTO", 
    "BookUpdateDTO",
    "BookRepository",
    # Actions
    "CreateBookAction",
    "DeleteBookAction",
    "GetBookAction",
    "ListBooksAction",
    "UpdateBookAction",
    # Tasks
    "CreateBookTask",
    "DeleteBookTask",
    "FindBookByIdTask",
    "FindBookByIsbnTask",
    "FindBooksTask",
    "UpdateBookTask",
    # Exceptions
    "BookAlreadyExistsException",
    "BookNotFoundException",
    # Transformers available via .UI.API.Transformers import
    # Managers
    "BookServerManager",
    "UserClientManager",
]
