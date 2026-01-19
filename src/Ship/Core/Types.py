"""Core types and protocols for the application."""

from typing import Protocol, TypeVar, runtime_checkable
from uuid import UUID

# Re-export DomainEvent from Ship/Parents/Event.py for backward compatibility
from src.Ship.Parents.Event import DomainEvent


T = TypeVar("T")


@runtime_checkable
class Entity(Protocol):
    """Protocol for entities with an ID.
    
    All domain entities should implement this protocol.
    """
    
    id: UUID


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for objects that have an identifier."""
    
    @property
    def id(self) -> UUID:
        """Get entity identifier."""
        ...
