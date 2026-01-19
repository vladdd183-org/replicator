"""Query for search index statistics."""

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.Containers.AppSection.SearchModule.Models.SearchIndex import SearchIndex
from src.Ship.Parents.Query import Query


class GetIndexStatsInput(BaseModel):
    """Input for index stats query."""

    model_config = ConfigDict(frozen=True)


@dataclass(frozen=True)
class IndexStats:
    """Search index statistics."""

    total_documents: int
    entity_types: dict[str, int]
    last_indexed_at: datetime | None
    index_size_estimate: str


class GetIndexStatsQuery(Query[GetIndexStatsInput, IndexStats]):
    """Query for search index statistics."""

    async def execute(self, params: GetIndexStatsInput) -> IndexStats:
        """Get index statistics."""
        # Total documents
        total = await SearchIndex.count()

        # Count by entity type
        entries = await SearchIndex.select(SearchIndex.entity_type).limit(10000)
        type_counts: dict[str, int] = {}
        for entry in entries:
            etype = entry["entity_type"]
            type_counts[etype] = type_counts.get(etype, 0) + 1

        # Last indexed
        last_entry = await (
            SearchIndex.objects().order_by(SearchIndex.updated_at, ascending=False).first()
        )
        last_indexed_at = last_entry.updated_at if last_entry else None

        # Estimate size (rough)
        size_estimate = self._estimate_size(total)

        return IndexStats(
            total_documents=total,
            entity_types=type_counts,
            last_indexed_at=last_indexed_at,
            index_size_estimate=size_estimate,
        )

    def _estimate_size(self, total: int) -> str:
        """Estimate index size based on document count."""
        # Rough estimate: ~1KB per document
        bytes_estimate = total * 1024

        if bytes_estimate < 1024:
            return f"{bytes_estimate} B"
        elif bytes_estimate < 1024 * 1024:
            return f"{bytes_estimate / 1024:.1f} KB"
        elif bytes_estimate < 1024 * 1024 * 1024:
            return f"{bytes_estimate / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_estimate / (1024 * 1024 * 1024):.1f} GB"
