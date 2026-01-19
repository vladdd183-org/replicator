"""SearchModule request DTOs.

All Request DTOs are frozen (immutable) for safety.
"""

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    """Request for full-text search."""
    
    model_config = ConfigDict(frozen=True)
    
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    entity_types: list[str] | None = Field(
        None,
        description="Filter by entity types (e.g., ['User', 'Notification'])",
    )
    tags: list[str] | None = Field(
        None,
        description="Filter by tags",
    )
    limit: int = Field(20, ge=1, le=100, description="Maximum results")
    offset: int = Field(0, ge=0, description="Pagination offset")


class IndexEntityRequest(BaseModel):
    """Request for manually indexing an entity."""
    
    model_config = ConfigDict(frozen=True)
    
    entity_type: str = Field(..., min_length=1, max_length=100)
    entity_id: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    content: str | None = Field(None, max_length=10000)
    tags: list[str] | None = None
    metadata: dict | None = None
    boost: float = Field(1.0, ge=0.1, le=10.0)


class ReindexRequest(BaseModel):
    """Request for reindexing entities."""
    
    model_config = ConfigDict(frozen=True)
    
    entity_type: str | None = Field(
        None,
        description="Reindex specific entity type, or all if None",
    )



