"""Query for searching audit logs."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.Containers.AppSection.AuditModule.Data.Repositories.AuditRepository import AuditRepository
from src.Containers.AppSection.AuditModule.Models.AuditLog import AuditLog
from src.Ship.Parents.Query import Query


class SearchAuditLogsInput(BaseModel):
    """Input for audit logs search."""

    model_config = ConfigDict(frozen=True)

    actor_id: UUID | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    action: str | None = None
    ip_address: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class SearchAuditLogsOutput:
    """Output for audit logs search."""

    logs: list[AuditLog]
    total: int
    limit: int
    offset: int


class SearchAuditLogsQuery(Query[SearchAuditLogsInput, SearchAuditLogsOutput]):
    """Query for searching audit logs with filters."""

    def __init__(self, repository: AuditRepository) -> None:
        self.repository = repository

    async def execute(self, params: SearchAuditLogsInput) -> SearchAuditLogsOutput:
        """Execute search with given filters."""
        logs, total = await self.repository.search(
            actor_id=params.actor_id,
            entity_type=params.entity_type,
            entity_id=params.entity_id,
            action=params.action,
            ip_address=params.ip_address,
            start_date=params.start_date,
            end_date=params.end_date,
            limit=params.limit,
            offset=params.offset,
        )

        return SearchAuditLogsOutput(
            logs=logs,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )
