"""Base Query class according to Hyper-Porto architecture.

Queries are CQRS read operations for fetching data.
They do not modify state and bypass UnitOfWork for better performance.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

__all__ = ["Query", "SyncQuery"]

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Query(ABC, Generic[InputT, OutputT]):
    """Base Query class for CQRS read operations.
    
    Queries are read-only operations optimized for data retrieval.
    They should NOT modify any state.
    
    Rules:
    - One Query = one read operation (Single Responsibility)
    - Read-only — does NOT modify state
    - Bypasses UnitOfWork for better performance
    - Can be called from Controller directly
    - Returns plain value T (not Result)
    
    Example:
        class GetUserQuery(Query[UUID, AppUser | None]):
            async def execute(self, user_id: UUID) -> AppUser | None:
                return await AppUser.objects().where(
                    AppUser.id == user_id
                ).first()
                
        class ListUsersQuery(Query[ListUsersInput, list[AppUser]]):
            async def execute(self, input: ListUsersInput) -> list[AppUser]:
                return await AppUser.objects().limit(input.limit).offset(input.offset)
    """
    
    @abstractmethod
    async def execute(self, data: InputT) -> OutputT:
        """Execute the query.
        
        Args:
            data: Input parameters for the query
            
        Returns:
            Query result
        """
        ...


class SyncQuery(ABC, Generic[InputT, OutputT]):
    """Synchronous Query class.
    
    For read operations that don't require I/O:
    - In-memory lookups
    - Cached data retrieval
    - Configuration reads
    
    Example:
        class GetConfigQuery(SyncQuery[str, str | None]):
            def execute(self, key: str) -> str | None:
                return self.config.get(key)
    """
    
    @abstractmethod
    def execute(self, data: InputT) -> OutputT:
        """Execute the synchronous query.
        
        Args:
            data: Input parameters for the query
            
        Returns:
            Query result
        """
        ...



