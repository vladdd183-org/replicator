"""Base Repository class according to Porto architecture."""

from abc import ABC
from typing import Generic, TypeVar

from piccolo.table import Table

ModelT = TypeVar("ModelT", bound=Table)


class Repository(ABC, Generic[ModelT]):
    """Base Repository class.

    Repositories handle data persistence operations.
    They abstract the database layer from the business logic.
    """

    def __init__(self, model: type[ModelT]) -> None:
        """Initialize repository.

        Args:
            model: Piccolo model class
        """
        self.model = model
