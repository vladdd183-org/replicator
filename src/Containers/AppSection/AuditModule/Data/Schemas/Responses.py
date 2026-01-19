"""AuditModule response DTOs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import field_validator

from src.Ship.Core.BaseSchema import EntitySchema


def _parse_jsonb(value: Any) -> dict[str, Any] | None:
    """Parse JSONB value from SQLite/Piccolo.
    
    SQLite may return empty strings for empty JSONB columns.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return value if value else None
    if isinstance(value, str):
        if value in ("", "{}", "[]", "null"):
            return None
        import json
        try:
            parsed = json.loads(value)
            return parsed if parsed else None
        except (json.JSONDecodeError, TypeError):
            return None
    return None


class AuditLogResponse(EntitySchema):
    """Response DTO for audit log entry."""
    
    id: UUID
    actor_id: UUID | None = None
    actor_email: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    endpoint: str | None = None
    http_method: str | None = None
    status_code: str | None = None
    duration_ms: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    
    @field_validator("old_values", "new_values", "metadata", mode="before")
    @classmethod
    def parse_jsonb_fields(cls, v: Any) -> dict[str, Any] | None:
        """Parse JSONB fields from SQLite/Piccolo."""
        return _parse_jsonb(v)


class AuditLogListResponse(EntitySchema):
    """Response DTO for audit log list."""
    
    logs: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class AuditStatsResponse(EntitySchema):
    """Response DTO for audit statistics."""
    
    total_logs: int
    logs_today: int
    unique_actors: int
    top_actions: list[dict]
    top_entities: list[dict]

