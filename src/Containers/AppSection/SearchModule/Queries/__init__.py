"""SearchModule Queries.

CQRS Read operations for search.
"""

from src.Containers.AppSection.SearchModule.Queries.FullTextSearchQuery import (
    FullTextSearchInput,
    FullTextSearchOutput,
    FullTextSearchQuery,
    SearchResult,
)
from src.Containers.AppSection.SearchModule.Queries.GetIndexStatsQuery import (
    GetIndexStatsInput,
    GetIndexStatsQuery,
    IndexStats,
)

__all__ = [
    # FullTextSearchQuery
    "FullTextSearchQuery",
    "FullTextSearchInput",
    "FullTextSearchOutput",
    "SearchResult",
    # GetIndexStatsQuery
    "GetIndexStatsQuery",
    "GetIndexStatsInput",
    "IndexStats",
]
