"""Base Repository class according to Hyper-Porto architecture.

Repositories handle data persistence operations.
They abstract the database layer from the business logic.
"""

from abc import ABC
from typing import Generic, TypeVar
from uuid import UUID

from piccolo.table import Table
from piccolo.columns import Column

ModelT = TypeVar("ModelT", bound=Table)


class Repository(ABC, Generic[ModelT]):
    """Base Repository class.
    
    Repositories handle data persistence operations.
    They abstract the database layer from the business logic.
    
    This is a lightweight wrapper over Piccolo Table API.
    Subclasses should add domain-specific query methods.
    
    Lifecycle hooks:
    - _on_add(entity): Called after entity is added
    - _on_update(entity): Called after entity is updated
    - _on_delete(entity): Called after entity is deleted
    
    Override hooks in subclasses for cache invalidation, events, etc.
    
    Advantages:
    - Uniform interface — Action doesn't know ORM details
    - Testability — easy to mock repositories
    - Query encapsulation — complex queries in one place
    - Extensible via hooks — no need to override CRUD methods
    
    Example:
        class UserRepository(Repository[User]):
            def __init__(self):
                super().__init__(User)
            
            async def _on_add(self, entity: User) -> None:
                await invalidate_cache("users:list:*")
            
            async def find_by_email(self, email: str) -> User | None:
                return await self.model.objects().where(
                    self.model.email == email
                ).first()
    """
    
    def __init__(self, model: type[ModelT]) -> None:
        """Initialize repository with model class."""
        self.model = model
    
    # --- Lifecycle hooks (override in subclasses) ---
    
    async def _on_add(self, entity: ModelT) -> None:
        """Hook called after entity is added.
        
        Override in subclasses for cache invalidation, events, etc.
        """
        pass
    
    async def _on_update(self, entity: ModelT) -> None:
        """Hook called after entity is updated.
        
        Override in subclasses for cache invalidation, events, etc.
        """
        pass
    
    async def _on_delete(self, entity: ModelT) -> None:
        """Hook called after entity is deleted.
        
        Override in subclasses for cache invalidation, events, etc.
        """
        pass
    
    # --- Basic CRUD operations ---
    
    async def get(self, id: UUID) -> ModelT | None:
        """Get entity by ID."""
        return await self.model.objects().where(self.model.id == id).first()
    
    async def get_one_or_none(self, **filters: object) -> ModelT | None:
        """Get entity by arbitrary filters."""
        query = self.model.objects()
        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)
        return await query.first()
    
    async def add(self, entity: ModelT) -> ModelT:
        """Add entity and return with generated fields."""
        await entity.save()
        await entity.refresh()
        await self._on_add(entity)
        return entity
    
    async def update(self, entity: ModelT) -> ModelT:
        """Update entity."""
        await entity.save()
        await self._on_update(entity)
        return entity
    
    async def delete(self, entity: ModelT) -> None:
        """Delete entity."""
        await entity.remove()
        await self._on_delete(entity)
    
    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        order_by: Column | None = None,
        ascending: bool = False,
    ) -> list[ModelT]:
        """List entities with pagination and optional ordering.
        
        Args:
            limit: Maximum number of entities
            offset: Number to skip
            order_by: Column to order by (default: created_at if exists)
            ascending: Sort direction
        """
        query = self.model.objects().limit(limit).offset(offset)
        
        if order_by is not None:
            query = query.order_by(order_by, ascending=ascending)
        elif hasattr(self.model, 'created_at'):
            query = query.order_by(self.model.created_at, ascending=ascending)
        
        return await query
    
    async def count(self) -> int:
        """Count total entities."""
        return await self.model.count()
    
    async def exists(self, **filters: object) -> bool:
        """Check if entity exists with given filters."""
        query = self.model.exists()
        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)
        return await query

