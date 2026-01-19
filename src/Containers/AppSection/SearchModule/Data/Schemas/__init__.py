"""SearchModule Data Transfer Objects.

Request and Response DTOs for search operations.
"""

from src.Containers.AppSection.SearchModule.Data.Schemas.Requests import (
    IndexEntityRequest,
    ReindexRequest,
    SearchRequest,
)
from src.Containers.AppSection.SearchModule.Data.Schemas.Responses import (
    IndexStatsResponse,
    ReindexResponse,
    SearchResponse,
    SearchResultItem,
)

__all__ = [
    # Requests
    "SearchRequest",
    "IndexEntityRequest",
    "ReindexRequest",
    # Responses
    "SearchResultItem",
    "SearchResponse",
    "IndexStatsResponse",
    "ReindexResponse",
]
