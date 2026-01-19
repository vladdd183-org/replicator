"""Base Manager class for inter-container communication."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from dishka import FromDishka
from litestar.datastructures import State

T = TypeVar("T")


class Manager(ABC, Generic[T]):
    """Base Manager for inter-container operations."""
    
    def __init__(self, state: State | None = None):
        """Initialize the manager with application state."""
        self.state = state
    
    @abstractmethod
    async def get(self, id: Any) -> T | None:
        """Get an entity by ID."""
        pass
    
    @abstractmethod
    async def list(self, **filters) -> list[T]:
        """List entities with optional filters."""
        pass


class ClientManager(Manager[T]):
    """Client Manager for consuming services from other containers."""
    
    def __init__(self, endpoint: str, state: State | None = None):
        """Initialize with endpoint URL."""
        super().__init__(state)
        self.endpoint = endpoint
    
    async def get(self, id: Any) -> T | None:
        """Get entity from remote service."""
        # This would make HTTP calls to other services
        raise NotImplementedError("Client implementation needed")
    
    async def list(self, **filters) -> list[T]:
        """List entities from remote service."""
        # This would make HTTP calls to other services
        raise NotImplementedError("Client implementation needed")


class ServerManager(Manager[T]):
    """Server Manager for exposing container functionality."""
    
    def __init__(self, action_provider: Any, state: State | None = None):
        """Initialize with action provider."""
        super().__init__(state)
        self.action_provider = action_provider
    
    async def get(self, id: Any) -> T | None:
        """Get entity using local action."""
        # This would call local actions
        raise NotImplementedError("Server implementation needed")
    
    async def list(self, **filters) -> list[T]:
        """List entities using local action."""
        # This would call local actions
        raise NotImplementedError("Server implementation needed")
