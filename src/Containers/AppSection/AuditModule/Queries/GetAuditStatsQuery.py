"""Query for audit statistics."""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.AuditModule.Models.AuditLog import AuditLog


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


class GetAuditStatsQuery(Query[GetAuditStatsInput, AuditStats]):
    """Query for aggregated audit statistics."""
    
    async def execute(self, params: GetAuditStatsInput) -> AuditStats:
        """Calculate audit statistics."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_start = now - timedelta(days=params.days)
        
        # Total logs
        total_logs = await AuditLog.count()
        
        # Logs today
        logs_today = await (
            AuditLog.count()
            .where(AuditLog.created_at >= today_start)
        )
        
        # Unique actors (last N days)
        # Note: Piccolo doesn't have DISTINCT COUNT, so we fetch and count
        recent_logs = await (
            AuditLog.select(AuditLog.actor_id)
            .where(AuditLog.created_at >= period_start)
            .where(AuditLog.actor_id.is_not_null())
        )
        unique_actors = len(set(log["actor_id"] for log in recent_logs))
        
        # Top actions (simplified - in production would use GROUP BY)
        action_logs = await (
            AuditLog.select(AuditLog.action)
            .where(AuditLog.created_at >= period_start)
            .limit(1000)
        )
        action_counts: dict[str, int] = {}
        for log in action_logs:
            action = log["action"]
            action_counts[action] = action_counts.get(action, 0) + 1
        
        top_actions = [
            {"action": action, "count": count}
            for action, count in sorted(
                action_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]
        ]
        
        # Top entities
        entity_logs = await (
            AuditLog.select(AuditLog.entity_type)
            .where(AuditLog.created_at >= period_start)
            .where(AuditLog.entity_type.is_not_null())
            .limit(1000)
        )
        entity_counts: dict[str, int] = {}
        for log in entity_logs:
            entity = log["entity_type"]
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
        
        top_entities = [
            {"entity_type": entity, "count": count}
            for entity, count in sorted(
                entity_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]
        ]
        
        return AuditStats(
            total_logs=total_logs,
            logs_today=logs_today,
            unique_actors=unique_actors,
            top_actions=top_actions,
            top_entities=top_entities,
        )



