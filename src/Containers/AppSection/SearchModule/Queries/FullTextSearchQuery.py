"""Full-text search query."""

import time
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.SearchModule.Models.SearchIndex import SearchIndex


class FullTextSearchInput(BaseModel):
    """Input for full-text search."""
    
    model_config = ConfigDict(frozen=True)
    
    query: str
    entity_types: list[str] | None = None
    tags: list[str] | None = None
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class SearchResult:
    """Single search result."""
    
    index_entry: SearchIndex
    score: float
    highlight: str | None


@dataclass(frozen=True)
class FullTextSearchOutput:
    """Output of full-text search."""
    
    results: list[SearchResult]
    total: int
    query: str
    took_ms: float
    facets: dict | None


class FullTextSearchQuery(Query[FullTextSearchInput, FullTextSearchOutput]):
    """Query for full-text search across all indexed entities.
    
    This is a simplified implementation using SQL LIKE.
    In production, use Elasticsearch, Meilisearch, or PostgreSQL FTS.
    """
    
    async def execute(self, params: FullTextSearchInput) -> FullTextSearchOutput:
        """Execute full-text search."""
        start_time = time.perf_counter()
        
        # Build query
        query = SearchIndex.objects()
        count_query = SearchIndex.count()
        
        # Apply entity type filter
        if params.entity_types:
            query = query.where(
                SearchIndex.entity_type.is_in(params.entity_types)
            )
            count_query = count_query.where(
                SearchIndex.entity_type.is_in(params.entity_types)
            )
        
        # Simple text search (LIKE)
        # In production, use proper FTS
        search_term = f"%{params.query}%"
        query = query.where(
            (SearchIndex.title.like(search_term)) |
            (SearchIndex.content.like(search_term))
        )
        count_query = count_query.where(
            (SearchIndex.title.like(search_term)) |
            (SearchIndex.content.like(search_term))
        )
        
        # Get total count
        total = await count_query
        
        # Get results with pagination
        entries = await (
            query
            .order_by(SearchIndex.boost, ascending=False)
            .order_by(SearchIndex.updated_at, ascending=False)
            .limit(params.limit)
            .offset(params.offset)
        )
        
        # Calculate scores and highlights
        results: list[SearchResult] = []
        for entry in entries:
            # Simple relevance scoring
            score = entry.boost
            if params.query.lower() in entry.title.lower():
                score += 2.0
            if entry.content and params.query.lower() in entry.content.lower():
                score += 1.0
            
            # Generate highlight snippet
            highlight = self._generate_highlight(
                entry.title,
                entry.content,
                params.query,
            )
            
            results.append(SearchResult(
                index_entry=entry,
                score=score,
                highlight=highlight,
            ))
        
        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        
        # Calculate facets
        facets = await self._calculate_facets(params)
        
        took_ms = (time.perf_counter() - start_time) * 1000
        
        return FullTextSearchOutput(
            results=results,
            total=total,
            query=params.query,
            took_ms=took_ms,
            facets=facets,
        )
    
    def _generate_highlight(
        self,
        title: str,
        content: str | None,
        query: str,
    ) -> str | None:
        """Generate highlighted snippet with query terms."""
        # Simple highlight: find query in content and extract surrounding text
        text = content or title
        query_lower = query.lower()
        text_lower = text.lower()
        
        pos = text_lower.find(query_lower)
        if pos == -1:
            return text[:150] + "..." if len(text) > 150 else text
        
        # Extract snippet around match
        start = max(0, pos - 50)
        end = min(len(text), pos + len(query) + 50)
        
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    async def _calculate_facets(
        self,
        params: FullTextSearchInput,
    ) -> dict:
        """Calculate facets (aggregations) for search results."""
        search_term = f"%{params.query}%"
        
        # Count by entity type
        all_entries = await (
            SearchIndex.select(SearchIndex.entity_type, SearchIndex.tags)
            .where(
                (SearchIndex.title.like(search_term)) |
                (SearchIndex.content.like(search_term))
            )
            .limit(1000)
        )
        
        type_counts: dict[str, int] = {}
        tag_counts: dict[str, int] = {}
        
        for entry in all_entries:
            # Count entity types
            etype = entry["entity_type"]
            type_counts[etype] = type_counts.get(etype, 0) + 1
            
            # Count tags
            tags = entry.get("tags") or []
            if isinstance(tags, list):
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "entity_types": [
                {"value": k, "count": v}
                for k, v in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
            ],
            "tags": [
                {"value": k, "count": v}
                for k, v in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            ],
        }



