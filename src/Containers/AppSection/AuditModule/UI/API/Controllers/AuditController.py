"""AuditModule API controller."""

from datetime import datetime
from uuid import UUID

from dishka.integrations.litestar import FromDishka
from litestar import Controller, get
from litestar.status_codes import HTTP_200_OK

from src.Containers.AppSection.AuditModule.Queries.SearchAuditLogsQuery import (
    SearchAuditLogsQuery,
    SearchAuditLogsInput,
)
from src.Containers.AppSection.AuditModule.Queries.GetAuditStatsQuery import (
    GetAuditStatsQuery,
    GetAuditStatsInput,
)
from src.Containers.AppSection.AuditModule.Data.Schemas.Responses import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditStatsResponse,
)


class AuditController(Controller):
    """Controller for audit log operations.
    
    Provides read-only access to audit logs.
    In production, these endpoints should be admin-only.
    """
    
    path = "/audit"
    tags = ["Audit"]
    
    @get("/")
    async def search_audit_logs(
        self,
        query: FromDishka[SearchAuditLogsQuery],
        actor_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        action: str | None = None,
        ip_address: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLogListResponse:
        """Search audit logs with filters.
        
        Query Parameters:
            actor_id: Filter by user who performed action
            entity_type: Filter by entity type (e.g., "User", "Payment")
            entity_id: Filter by specific entity ID
            action: Filter by action (supports partial match)
            ip_address: Filter by IP address
            start_date: Start of date range (ISO format)
            end_date: End of date range (ISO format)
            limit: Max results (1-100, default 50)
            offset: Pagination offset
            
        Returns:
            List of audit logs matching filters
        """
        result = await query.execute(SearchAuditLogsInput(
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            ip_address=ip_address,
            start_date=start_date,
            end_date=end_date,
            limit=min(limit, 100),
            offset=offset,
        ))
        
        return AuditLogListResponse(
            logs=[AuditLogResponse.from_entity(log) for log in result.logs],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )
    
    @get("/stats")
    async def get_audit_stats(
        self,
        query: FromDishka[GetAuditStatsQuery],
        days: int = 7,
    ) -> AuditStatsResponse:
        """Get audit statistics.
        
        Query Parameters:
            days: Number of days to include in stats (default 7)
            
        Returns:
            Aggregated audit statistics
        """
        result = await query.execute(GetAuditStatsInput(days=min(days, 30)))
        
        return AuditStatsResponse(
            total_logs=result.total_logs,
            logs_today=result.logs_today,
            unique_actors=result.unique_actors,
            top_actions=result.top_actions,
            top_entities=result.top_entities,
        )
    
    @get("/actor/{actor_id:uuid}")
    async def get_actor_logs(
        self,
        actor_id: UUID,
        query: FromDishka[SearchAuditLogsQuery],
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLogListResponse:
        """Get audit logs for a specific actor.
        
        Path Parameters:
            actor_id: UUID of the actor
            
        Query Parameters:
            limit: Max results (1-100, default 50)
            offset: Pagination offset
            
        Returns:
            List of audit logs for the actor
        """
        result = await query.execute(SearchAuditLogsInput(
            actor_id=actor_id,
            limit=min(limit, 100),
            offset=offset,
        ))
        
        return AuditLogListResponse(
            logs=[AuditLogResponse.from_entity(log) for log in result.logs],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )
    
    @get("/entity/{entity_type:str}")
    async def get_entity_logs(
        self,
        entity_type: str,
        query: FromDishka[SearchAuditLogsQuery],
        entity_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLogListResponse:
        """Get audit logs for a specific entity type.
        
        Path Parameters:
            entity_type: Type of entity (e.g., "User", "Payment")
            
        Query Parameters:
            entity_id: Optional specific entity ID
            limit: Max results (1-100, default 50)
            offset: Pagination offset
            
        Returns:
            List of audit logs for the entity type
        """
        result = await query.execute(SearchAuditLogsInput(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=min(limit, 100),
            offset=offset,
        ))
        
        return AuditLogListResponse(
            logs=[AuditLogResponse.from_entity(log) for log in result.logs],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

