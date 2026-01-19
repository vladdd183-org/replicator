"""AuditModule domain events."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.Ship.Parents.Event import DomainEvent


class AuditLogCreated(DomainEvent):
    """Emitted when a new audit log entry is created."""
    
    audit_id: UUID
    actor_id: UUID | None
    action: str
    entity_type: str
    entity_id: str | None


class SuspiciousActivityDetected(DomainEvent):
    """Emitted when suspicious activity is detected."""
    
    actor_id: UUID | None
    action: str
    reason: str
    ip_address: str | None = None
    details: dict | None = None


__all__ = ["AuditLogCreated", "SuspiciousActivityDetected"]



