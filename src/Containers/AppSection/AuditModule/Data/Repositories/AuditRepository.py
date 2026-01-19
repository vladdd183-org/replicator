"""Repository for AuditLog entity."""

from datetime import datetime
from uuid import UUID

from src.Ship.Parents.Repository import Repository
from src.Containers.AppSection.AuditModule.Models.AuditLog import AuditLog


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
            query
            .order_by(self.model.created_at, ascending=False)
            .limit(limit)
            .offset(offset)
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
        return await (
            self.model.count()
            .where(self.model.action == action)
        )
    
    async def get_recent_actions(
        self,
        limit: int = 20,
    ) -> list[AuditLog]:
        """Get most recent actions."""
        return await (
            self.model.objects()
            .order_by(self.model.created_at, ascending=False)
            .limit(limit)
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
            query
            .order_by(self.model.created_at, ascending=False)
            .limit(limit)
            .offset(offset)
        )
        
        return logs, total



