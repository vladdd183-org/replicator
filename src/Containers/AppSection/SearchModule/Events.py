"""SearchModule domain events."""

from uuid import UUID

from src.Ship.Parents.Event import DomainEvent


class EntityIndexed(DomainEvent):
    """Emitted when an entity is indexed."""
    
    entity_type: str
    entity_id: str
    index_name: str


class EntityRemovedFromIndex(DomainEvent):
    """Emitted when an entity is removed from index."""
    
    entity_type: str
    entity_id: str
    index_name: str


class IndexRebuilt(DomainEvent):
    """Emitted when an index is rebuilt."""
    
    index_name: str
    total_documents: int
    duration_ms: float


__all__ = ["EntityIndexed", "EntityRemovedFromIndex", "IndexRebuilt"]



