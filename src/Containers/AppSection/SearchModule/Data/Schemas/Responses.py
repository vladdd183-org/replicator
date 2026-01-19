"""SearchModule response DTOs."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import field_validator

from src.Ship.Core.BaseSchema import EntitySchema


class SearchResultItem(EntitySchema):
    """Single search result item."""
    
    id: UUID
    entity_type: str
    entity_id: str
    title: str
    content: str | None
    tags: list[str] | None
    metadata: dict | None
    score: float  # Relevance score
    highlight: str | None  # Highlighted snippet
    
    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v: Any) -> list[str] | None:
        """Parse tags from JSON string if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v
    
    @field_validator("metadata", mode="before")
    @classmethod
    def parse_metadata(cls, v: Any) -> dict | None:
        """Parse metadata from JSON string if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class SearchResponse(EntitySchema):
    """Response for search query."""
    
    results: list[SearchResultItem]
    total: int
    query: str
    took_ms: float  # Search duration in milliseconds
    facets: dict | None  # Aggregated facets


class IndexStatsResponse(EntitySchema):
    """Response for index statistics."""
    
    total_documents: int
    entity_types: dict[str, int]  # Count by entity type
    last_indexed_at: datetime | None
    index_size_estimate: str


class ReindexResponse(EntitySchema):
    """Response for reindex operation."""
    
    status: str
    entity_type: str | None
    documents_processed: int
    duration_ms: float

