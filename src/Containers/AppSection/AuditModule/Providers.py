"""AuditModule DI providers."""

from dishka import Provider, Scope, provide

from src.Containers.AppSection.AuditModule.Data.Repositories.AuditRepository import (
    AuditRepository,
)
from src.Containers.AppSection.AuditModule.Queries.SearchAuditLogsQuery import (
    SearchAuditLogsQuery,
)
from src.Containers.AppSection.AuditModule.Queries.GetAuditStatsQuery import (
    GetAuditStatsQuery,
)


class AuditModuleProvider(Provider):
    """App-scoped provider for AuditModule."""
    
    scope = Scope.APP


class AuditRequestProvider(Provider):
    """Request-scoped provider for AuditModule."""
    
    scope = Scope.REQUEST
    
    audit_repository = provide(AuditRepository)
    search_audit_logs_query = provide(SearchAuditLogsQuery)
    get_audit_stats_query = provide(GetAuditStatsQuery)



