"""Query for audit statistics."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict

from src.Containers.AppSection.AuditModule.Data.Repositories.AuditRepository import (
    AuditRepository,
)
from src.Ship.Parents.Query import Query


class GetAuditStatsInput(BaseModel):
    """Input for audit stats query."""

    model_config = ConfigDict(frozen=True)

    days: int = 7  # Stats for last N days


@dataclass(frozen=True)
class AuditStats:
    """Audit statistics data."""

    total_logs: int
    logs_today: int
    unique_actors: int
    top_actions: list[dict]
    top_entities: list[dict]


@dataclass
class GetAuditStatsQuery(Query[GetAuditStatsInput, AuditStats]):
    """Query for aggregated audit statistics."""

    audit_repository: AuditRepository

    async def execute(self, params: GetAuditStatsInput) -> AuditStats:
        """Calculate audit statistics."""
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = now - timedelta(days=params.days)

        # Total logs
        total_logs = await self.audit_repository.count()

        # Logs today
        logs_today = await self.audit_repository.count_since(today_start)

        # Unique actors (last N days)
        unique_actors = await self.audit_repository.get_unique_actors_count(period_start)

        # Top actions
        top_actions = await self.audit_repository.get_top_actions(period_start, limit=10)

        # Top entities
        top_entities = await self.audit_repository.get_top_entities(period_start, limit=10)

        return AuditStats(
            total_logs=total_logs,
            logs_today=logs_today,
            unique_actors=unique_actors,
            top_actions=top_actions,
            top_entities=top_entities,
        )
