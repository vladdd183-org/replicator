"""AuditModule DI providers."""

from dishka import Provider, Scope, provide

from src.Containers.AppSection.AuditModule.Data.Repositories.AuditRepository import (
    AuditRepository,
)
from src.Containers.AppSection.AuditModule.Queries.GetAuditStatsQuery import (
    GetAuditStatsQuery,
)
from src.Containers.AppSection.AuditModule.Queries.SearchAuditLogsQuery import (
    SearchAuditLogsQuery,
)


class AuditModuleProvider(Provider):
    """App-scoped provider for AuditModule."""

    scope = Scope.APP


class AuditRequestProvider(Provider):
    """Request-scoped provider for AuditModule."""

    scope = Scope.REQUEST

    audit_repository = provide(AuditRepository)
    search_audit_logs_query = provide(SearchAuditLogsQuery)

    @provide
    def get_audit_stats_query(
        self,
        audit_repository: AuditRepository,
    ) -> GetAuditStatsQuery:
        """Provide GetAuditStatsQuery with repository dependency."""
        return GetAuditStatsQuery(audit_repository=audit_repository)
