"""SearchIndex model for storing searchable content."""

from piccolo.columns import JSONB, UUID, Float, Text, Timestamptz, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.defaults.uuid import UUID4

from src.Ship.Parents.Model import Model


class SearchIndex(Model):
    """Stores indexed content for full-text search.

    This is a virtual search index stored in SQLite.
    In production, this would typically be Elasticsearch/Meilisearch.

    Attributes:
        id: Unique identifier for the index entry
        entity_type: Type of the indexed entity (e.g., "User", "Notification")
        entity_id: ID of the source entity
        title: Primary searchable title
        content: Full searchable content
        tags: Array of tags for faceted search
        metadata: Additional data for filtering
        boost: Relevance boost factor
        created_at: When the entity was indexed
        updated_at: When the index entry was last updated
    """

    id = UUID(primary_key=True, default=UUID4())

    # Entity reference
    entity_type = Varchar(length=100, required=True, index=True)
    entity_id = Varchar(length=255, required=True, index=True)

    # Searchable content
    title = Varchar(length=500, required=True)
    content = Text(null=True)

    # Facets and filtering
    tags = JSONB(null=True)  # ["tag1", "tag2"]
    metadata = JSONB(null=True)  # {"category": "...", "author": "..."}

    # Relevance tuning
    boost = Float(default=1.0)

    # Timestamps
    created_at = Timestamptz(default=TimestamptzNow())
    updated_at = Timestamptz(default=TimestamptzNow())

    class Meta:
        tablename = "search_index"
        # Unique constraint on entity_type + entity_id
        unique_together = [("entity_type", "entity_id")]
