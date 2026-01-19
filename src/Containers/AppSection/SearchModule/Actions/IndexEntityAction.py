"""Action for manually indexing an entity."""

from dataclasses import dataclass

from returns.result import Failure, Result, Success

from src.Containers.AppSection.SearchModule.Data.Schemas.Requests import IndexEntityRequest
from src.Containers.AppSection.SearchModule.Data.UnitOfWork import SearchUnitOfWork
from src.Containers.AppSection.SearchModule.Errors import IndexingError, SearchError
from src.Containers.AppSection.SearchModule.Events import EntityIndexed
from src.Containers.AppSection.SearchModule.Tasks.IndexEntityTask import (
    IndexableEntity,
    IndexEntityTask,
)
from src.Ship.Parents.Action import Action


@dataclass
class IndexEntityAction(Action[IndexEntityRequest, bool, SearchError]):
    """Action for manually indexing an entity."""

    index_task: IndexEntityTask
    uow: SearchUnitOfWork

    async def run(self, data: IndexEntityRequest) -> Result[bool, SearchError]:
        """Index an entity manually.

        Args:
            data: Entity data to index

        Returns:
            Result with True on success, or error
        """
        async with self.uow:
            success = await self.index_task.run(
                IndexableEntity(
                    entity_type=data.entity_type,
                    entity_id=data.entity_id,
                    title=data.title,
                    content=data.content,
                    tags=data.tags,
                    metadata=data.metadata,
                    boost=data.boost,
                )
            )

            if not success:
                return Failure(
                    IndexingError(
                        entity_type=data.entity_type,
                        entity_id=data.entity_id,
                        details="Failed to index entity",
                    )
                )

            # Publish EntityIndexed event after successful indexing
            self.uow.add_event(
                EntityIndexed(
                    entity_type=data.entity_type,
                    entity_id=data.entity_id,
                    index_name="search_index",
                )
            )
            await self.uow.commit()

        return Success(True)
