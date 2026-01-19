"""AuditModule Queries.

CQRS Read operations for audit logs.
"""

from src.Containers.AppSection.AuditModule.Queries.GetAuditStatsQuery import (
    AuditStats,
    GetAuditStatsInput,
    GetAuditStatsQuery,
)
from src.Containers.AppSection.AuditModule.Queries.SearchAuditLogsQuery import (
    SearchAuditLogsInput,
    SearchAuditLogsOutput,
    SearchAuditLogsQuery,
)

__all__ = [
    # GetAuditStatsQuery
    "GetAuditStatsQuery",
    "GetAuditStatsInput",
    "AuditStats",
    # SearchAuditLogsQuery
    "SearchAuditLogsQuery",
    "SearchAuditLogsInput",
    "SearchAuditLogsOutput",
]
