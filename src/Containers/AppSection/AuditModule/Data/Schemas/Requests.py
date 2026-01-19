"""AuditModule request DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AuditSearchRequest(BaseModel):
    """Request for searching audit logs."""
    
    actor_id: UUID | None = Field(None, description="Filter by actor ID")
    entity_type: str | None = Field(None, description="Filter by entity type")
    entity_id: str | None = Field(None, description="Filter by entity ID")
    action: str | None = Field(None, description="Filter by action (supports partial match)")
    ip_address: str | None = Field(None, description="Filter by IP address")
    start_date: datetime | None = Field(None, description="Start of date range")
    end_date: datetime | None = Field(None, description="End of date range")
    limit: int = Field(50, ge=1, le=100, description="Maximum results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class CreateAuditLogRequest(BaseModel):
    """Request for manually creating audit log entry."""
    
    action: str = Field(..., min_length=1, max_length=50)
    entity_type: str | None = Field(None, max_length=100)
    entity_id: str | None = Field(None, max_length=255)
    old_values: dict | None = None
    new_values: dict | None = None
    metadata: dict | None = None



