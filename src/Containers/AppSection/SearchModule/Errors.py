"""SearchModule errors."""

from typing import ClassVar

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class SearchError(BaseError):
    """Base error for SearchModule."""

    code: str = "SEARCH_ERROR"


class InvalidSearchQueryError(ErrorWithTemplate, SearchError):
    """Raised when search query is invalid."""

    _message_template: ClassVar[str] = "Invalid search query: {details}"
    code: str = "INVALID_SEARCH_QUERY"
    http_status: int = 400
    details: str


class IndexingError(ErrorWithTemplate, SearchError):
    """Raised when indexing fails."""

    _message_template: ClassVar[str] = (
        "Failed to index {entity_type} with id {entity_id}: {details}"
    )
    code: str = "INDEXING_ERROR"
    http_status: int = 500
    entity_type: str
    entity_id: str
    details: str


class SearchServiceUnavailableError(SearchError):
    """Raised when search service is unavailable."""

    code: str = "SEARCH_SERVICE_UNAVAILABLE"
    http_status: int = 503
    message: str = "Search service is temporarily unavailable"
