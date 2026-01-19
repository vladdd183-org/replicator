"""Base Event class according to Hyper-Porto architecture.

Domain Events represent something that happened in the domain.
They are immutable and used for decoupling between modules.
"""

from datetime import datetime, timezone
from typing import TypeVar

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Get current UTC time (timezone-aware).
    
    Replacement for deprecated datetime.utcnow().
    """
    return datetime.now(timezone.utc)


class DomainEvent(BaseModel):
    """Base class for domain events.
    
    Domain events represent something that happened in the domain.
    They are immutable (frozen) Pydantic models.
    
    Events are published after successful UnitOfWork commit
    via litestar.events integration.
    
    Rules:
    - Immutable (frozen=True)
    - Named as past tense verb (e.g., UserCreated, OrderPlaced)
    - Contains only data needed by listeners
    - Published AFTER successful transaction commit
    
    Example:
        class UserCreated(DomainEvent):
            user_id: UUID
            email: str
            
        class OrderPlaced(DomainEvent):
            order_id: UUID
            user_id: UUID
            total: Decimal
            
    Usage in Action:
        async with self.uow:
            await self.uow.users.add(user)
            self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
            await self.uow.commit()  # Event published here
    """
    
    model_config = {"frozen": True}
    
    # Timestamp when event occurred (auto-generated, timezone-aware UTC)
    occurred_at: datetime = Field(default_factory=_utc_now)
    
    @property
    def event_name(self) -> str:
        """Get event name from class name.
        
        Returns:
            Event name (e.g., 'UserCreated', 'OrderPlaced')
        """
        return self.__class__.__name__
    
    def __str__(self) -> str:
        """String representation of event."""
        return f"{self.event_name}(occurred_at={self.occurred_at})"


# Re-export for backward compatibility
__all__ = ["DomainEvent"]

