"""Task for indexing entities into search index."""

from datetime import UTC, datetime

from pydantic import BaseModel

from src.Containers.AppSection.SearchModule.Models.SearchIndex import SearchIndex
from src.Ship.Parents.Task import Task


class IndexableEntity(BaseModel):
    """Data for indexing an entity."""

    model_config = {"frozen": True}

    entity_type: str
    entity_id: str
    title: str
    content: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None
    boost: float = 1.0


class IndexEntityTask(Task[IndexableEntity, bool]):
    """Task for indexing a single entity.

    Creates or updates an entry in the search index.
    This is a virtual implementation; in production would use Elasticsearch/Meilisearch.
    """

    async def run(self, data: IndexableEntity) -> bool:
        """Index an entity.

        Args:
            data: Entity data to index

        Returns:
            True if indexing was successful
        """
        try:
            # Check if entry exists
            existing = await (
                SearchIndex.objects()
                .where(SearchIndex.entity_type == data.entity_type)
                .where(SearchIndex.entity_id == data.entity_id)
                .first()
            )

            if existing:
                # Update existing entry
                existing.title = data.title
                existing.content = data.content
                existing.tags = data.tags
                existing.metadata = data.metadata
                existing.boost = data.boost
                existing.updated_at = datetime.now(UTC)
                await existing.save()
            else:
                # Create new entry
                entry = SearchIndex(
                    entity_type=data.entity_type,
                    entity_id=data.entity_id,
                    title=data.title,
                    content=data.content,
                    tags=data.tags,
                    metadata=data.metadata,
                    boost=data.boost,
                )
                await entry.save()

            import logfire

            logfire.info(
                "📝 Entity indexed",
                entity_type=data.entity_type,
                entity_id=data.entity_id,
            )

            return True

        except Exception as e:
            import logfire

            logfire.error(
                "❌ Failed to index entity",
                entity_type=data.entity_type,
                entity_id=data.entity_id,
                error=str(e),
            )
            return False


class RemoveFromIndexTask(Task[tuple[str, str], bool]):
    """Task for removing an entity from search index.

    Args:
        data: Tuple of (entity_type, entity_id)

    Returns:
        True if removal was successful
    """

    async def run(self, data: tuple[str, str]) -> bool:
        """Remove entity from index."""
        entity_type, entity_id = data

        try:
            await (
                SearchIndex.delete()
                .where(SearchIndex.entity_type == entity_type)
                .where(SearchIndex.entity_id == entity_id)
            )

            import logfire

            logfire.info(
                "🗑️ Entity removed from index",
                entity_type=entity_type,
                entity_id=entity_id,
            )

            return True

        except Exception as e:
            import logfire

            logfire.error(
                "❌ Failed to remove entity from index",
                entity_type=entity_type,
                entity_id=entity_id,
                error=str(e),
            )
            return False
