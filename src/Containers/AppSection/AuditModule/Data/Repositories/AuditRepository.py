"""Repository for AuditLog entity."""

from datetime import datetime
from uuid import UUID

from src.Containers.AppSection.AuditModule.Models.AuditLog import AuditLog
from src.Ship.Parents.Repository import Repository


class AuditRepository(Repository[AuditLog]):
    """Repository for AuditLog with specialized query methods."""

    def __init__(self) -> None:
        super().__init__(AuditLog)

    async def get_by_actor(
        self,
        actor_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs for a specific actor."""
        return await (
            self.model.objects()
            .where(self.model.actor_id == actor_id)
            .order_by(self.model.created_at, ascending=False)
            .limit(limit)
            .offset(offset)
        )

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs for a specific entity type/id."""
        query = self.model.objects().where(self.model.entity_type == entity_type)

        if entity_id:
            query = query.where(self.model.entity_id == entity_id)

        return await (
            query.order_by(self.model.created_at, ascending=False).limit(limit).offset(offset)
        )

    async def get_by_action(
        self,
        action: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs for a specific action."""
        return await (
            self.model.objects()
            .where(self.model.action == action)
            .order_by(self.model.created_at, ascending=False)
            .limit(limit)
            .offset(offset)
        )

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs within a date range."""
        return await (
            self.model.objects()
            .where(self.model.created_at >= start_date)
            .where(self.model.created_at <= end_date)
            .order_by(self.model.created_at, ascending=False)
            .limit(limit)
            .offset(offset)
        )

    async def count_by_action(self, action: str) -> int:
        """Count audit logs for a specific action."""
        return await self.model.count().where(self.model.action == action)

    async def get_recent_actions(
        self,
        limit: int = 20,
    ) -> list[AuditLog]:
        """Get most recent actions."""
        return await (
            self.model.objects().order_by(self.model.created_at, ascending=False).limit(limit)
        )

    async def search(
        self,
        actor_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        action: str | None = None,
        ip_address: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """Advanced search with multiple filters."""
        query = self.model.objects()
        count_query = self.model.count()

        if actor_id:
            query = query.where(self.model.actor_id == actor_id)
            count_query = count_query.where(self.model.actor_id == actor_id)

        if entity_type:
            query = query.where(self.model.entity_type == entity_type)
            count_query = count_query.where(self.model.entity_type == entity_type)

        if entity_id:
            query = query.where(self.model.entity_id == entity_id)
            count_query = count_query.where(self.model.entity_id == entity_id)

        if action:
            query = query.where(self.model.action.like(f"%{action}%"))
            count_query = count_query.where(self.model.action.like(f"%{action}%"))

        if ip_address:
            query = query.where(self.model.ip_address == ip_address)
            count_query = count_query.where(self.model.ip_address == ip_address)

        if start_date:
            query = query.where(self.model.created_at >= start_date)
            count_query = count_query.where(self.model.created_at >= start_date)

        if end_date:
            query = query.where(self.model.created_at <= end_date)
            count_query = count_query.where(self.model.created_at <= end_date)

        total = await count_query
        logs = await (
            query.order_by(self.model.created_at, ascending=False).limit(limit).offset(offset)
        )

        return logs, total

    async def count(self) -> int:
        """Get total count of audit logs."""
        return await self.model.count()

    async def count_since(self, start_date: datetime) -> int:
        """Count audit logs since a specific date."""
        return await self.model.count().where(self.model.created_at >= start_date)

    async def get_unique_actors_count(self, start_date: datetime) -> int:
        """Get count of unique actors since a specific date.

        Note: Piccolo doesn't have DISTINCT COUNT, so we fetch actor_ids and count unique.
        """
        logs = await (
            self.model.select(self.model.actor_id)
            .where(self.model.created_at >= start_date)
            .where(self.model.actor_id.is_not_null())
        )
        return len(set(log["actor_id"] for log in logs))

    async def get_top_actions(
        self,
        start_date: datetime,
        limit: int = 10,
    ) -> list[dict]:
        """Get top actions by count since a specific date.

        Returns list of dicts with 'action' and 'count' keys.
        Note: Uses in-memory aggregation since Piccolo doesn't have GROUP BY with COUNT.
        """
        logs = await (
            self.model.select(self.model.action)
            .where(self.model.created_at >= start_date)
            .limit(1000)
        )
        action_counts: dict[str, int] = {}
        for log in logs:
            action = log["action"]
            action_counts[action] = action_counts.get(action, 0) + 1

        return [
            {"action": action, "count": count}
            for action, count in sorted(
                action_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:limit]
        ]

    async def get_top_entities(
        self,
        start_date: datetime,
        limit: int = 10,
    ) -> list[dict]:
        """Get top entity types by count since a specific date.

        Returns list of dicts with 'entity_type' and 'count' keys.
        Note: Uses in-memory aggregation since Piccolo doesn't have GROUP BY with COUNT.
        """
        logs = await (
            self.model.select(self.model.entity_type)
            .where(self.model.created_at >= start_date)
            .where(self.model.entity_type.is_not_null())
            .limit(1000)
        )
        entity_counts: dict[str, int] = {}
        for log in logs:
            entity = log["entity_type"]
            entity_counts[entity] = entity_counts.get(entity, 0) + 1

        return [
            {"entity_type": entity, "count": count}
            for entity, count in sorted(
                entity_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:limit]
        ]
