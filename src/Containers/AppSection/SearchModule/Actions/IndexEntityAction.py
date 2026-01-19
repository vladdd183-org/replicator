"""Action for manually indexing an entity."""

from dataclasses import dataclass

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.SearchModule.Data.Schemas.Requests import IndexEntityRequest
from src.Containers.AppSection.SearchModule.Errors import SearchError, IndexingError
from src.Containers.AppSection.SearchModule.Tasks.IndexEntityTask import (
    IndexEntityTask,
    IndexableEntity,
)


@dataclass
class IndexEntityAction(Action[IndexEntityRequest, bool, SearchError]):
    """Action for manually indexing an entity."""
    
    index_task: IndexEntityTask
    
    async def run(self, data: IndexEntityRequest) -> Result[bool, SearchError]:
        """Index an entity manually.
        
        Args:
            data: Entity data to index
            
        Returns:
            Result with True on success, or error
        """
        success = await self.index_task.run(IndexableEntity(
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            title=data.title,
            content=data.content,
            tags=data.tags,
            metadata=data.metadata,
            boost=data.boost,
        ))
        
        if success:
            return Success(True)
        
        return Failure(IndexingError(
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            details="Failed to index entity",
        ))



