"""SearchModule API controller."""

from dishka.integrations.litestar import FromDishka
from litestar import Controller, get, post
from litestar.status_codes import HTTP_201_CREATED
from returns.result import Result

from src.Containers.AppSection.SearchModule.Actions.IndexEntityAction import (
    IndexEntityAction,
)
from src.Containers.AppSection.SearchModule.Data.Schemas.Requests import (
    IndexEntityRequest,
)
from src.Containers.AppSection.SearchModule.Data.Schemas.Responses import (
    IndexStatsResponse,
    SearchResponse,
    SearchResultItem,
)
from src.Containers.AppSection.SearchModule.Errors import SearchError
from src.Containers.AppSection.SearchModule.Queries.FullTextSearchQuery import (
    FullTextSearchInput,
    FullTextSearchQuery,
)
from src.Containers.AppSection.SearchModule.Queries.GetIndexStatsQuery import (
    GetIndexStatsInput,
    GetIndexStatsQuery,
)
from src.Ship.Decorators.result_handler import result_handler


class SearchController(Controller):
    """Controller for search operations."""

    path = "/search"
    tags = ["Search"]

    @get("/")
    async def search(
        self,
        query: FromDishka[FullTextSearchQuery],
        q: str,
        entity_types: str | None = None,
        tags: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResponse:
        """Full-text search across all indexed entities.

        Query Parameters:
            q: Search query (required)
            entity_types: Comma-separated entity types (e.g., "User,Notification")
            tags: Comma-separated tags to filter by
            limit: Max results (1-100, default 20)
            offset: Pagination offset

        Returns:
            Search results with relevance scores and highlights
        """
        # Parse comma-separated filters
        entity_types_list = (
            [t.strip() for t in entity_types.split(",") if t.strip()] if entity_types else None
        )
        tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

        result = await query.execute(
            FullTextSearchInput(
                query=q,
                entity_types=entity_types_list,
                tags=tags_list,
                limit=min(limit, 100),
                offset=offset,
            )
        )

        return SearchResponse(
            results=[
                SearchResultItem(
                    id=r.index_entry.id,
                    entity_type=r.index_entry.entity_type,
                    entity_id=r.index_entry.entity_id,
                    title=r.index_entry.title,
                    content=r.index_entry.content,
                    tags=r.index_entry.tags,
                    metadata=r.index_entry.metadata,
                    score=r.score,
                    highlight=r.highlight,
                )
                for r in result.results
            ],
            total=result.total,
            query=result.query,
            took_ms=result.took_ms,
            facets=result.facets,
        )

    @get("/stats")
    async def get_stats(
        self,
        query: FromDishka[GetIndexStatsQuery],
    ) -> IndexStatsResponse:
        """Get search index statistics.

        Returns:
            Index statistics including document counts and size
        """
        result = await query.execute(GetIndexStatsInput())

        return IndexStatsResponse(
            total_documents=result.total_documents,
            entity_types=result.entity_types,
            last_indexed_at=result.last_indexed_at,
            index_size_estimate=result.index_size_estimate,
        )

    @post("/index")
    @result_handler(None, success_status=HTTP_201_CREATED)
    async def index_entity(
        self,
        data: IndexEntityRequest,
        action: FromDishka[IndexEntityAction],
    ) -> Result[bool, SearchError]:
        """Manually index an entity.

        Request Body:
            entity_type: Type of entity
            entity_id: ID of entity
            title: Searchable title
            content: Full searchable content
            tags: Optional list of tags
            metadata: Optional metadata dict
            boost: Relevance boost (0.1-10.0, default 1.0)

        Returns:
            201 on success
        """
        return await action.run(data)

    @get("/suggest")
    async def suggest(
        self,
        query: FromDishka[FullTextSearchQuery],
        q: str,
        limit: int = 5,
    ) -> list[str]:
        """Get search suggestions based on partial query.

        Query Parameters:
            q: Partial search query
            limit: Max suggestions (1-10, default 5)

        Returns:
            List of suggested search terms
        """
        result = await query.execute(
            FullTextSearchInput(
                query=q,
                limit=min(limit, 10),
                offset=0,
            )
        )

        # Return unique titles as suggestions
        seen = set()
        suggestions = []
        for r in result.results:
            if r.index_entry.title not in seen:
                seen.add(r.index_entry.title)
                suggestions.append(r.index_entry.title)

        return suggestions
