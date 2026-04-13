"""Protocol definitions for dependency injection."""

from typing import Protocol, TypeVar, runtime_checkable
from uuid import UUID

from returns.result import Result

T = TypeVar("T")
E = TypeVar("E")


@runtime_checkable
class RepositoryProtocol(Protocol[T]):
    """Protocol for repositories.

    Defines the interface that all repositories should implement.
    """

    async def get(self, id: UUID) -> T | None:
        """Get entity by ID."""
        ...

    async def add(self, entity: T) -> T:
        """Add entity to repository."""
        ...

    async def update(self, entity: T) -> T:
        """Update entity in repository."""
        ...

    async def delete(self, entity: T) -> None:
        """Delete entity from repository."""
        ...

    async def list(self, limit: int = 20, offset: int = 0) -> list[T]:
        """List entities with pagination."""
        ...


@runtime_checkable
class UnitOfWorkProtocol(Protocol):
    """Protocol for Unit of Work.

    Defines the interface for transaction management.
    """

    async def __aenter__(self) -> "UnitOfWorkProtocol":
        """Enter transaction context."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit transaction context."""
        ...

    async def commit(self) -> None:
        """Commit transaction."""
        ...

    async def rollback(self) -> None:
        """Rollback transaction."""
        ...


@runtime_checkable
class ActionProtocol(Protocol[T, E]):
    """Protocol for actions.

    Defines the interface that all actions should implement.
    """

    async def run(self, data: object) -> Result[T, E]:
        """Execute the action."""
        ...


@runtime_checkable
class TaskProtocol(Protocol[T]):
    """Protocol for tasks.

    Defines the interface that all tasks should implement.
    """

    def run(self, data: object) -> T:
        """Execute the task."""
        ...
