"""SearchModule DI providers."""

from typing import TYPE_CHECKING

from dishka import Provider, Scope, provide
from litestar import Request

from src.Containers.AppSection.SearchModule.Actions.IndexEntityAction import (
    IndexEntityAction,
)
from src.Containers.AppSection.SearchModule.Data.UnitOfWork import SearchUnitOfWork
from src.Containers.AppSection.SearchModule.Queries.FullTextSearchQuery import (
    FullTextSearchQuery,
)
from src.Containers.AppSection.SearchModule.Queries.GetIndexStatsQuery import (
    GetIndexStatsQuery,
)
from src.Containers.AppSection.SearchModule.Tasks.IndexEntityTask import (
    IndexEntityTask,
    RemoveFromIndexTask,
)

if TYPE_CHECKING:
    from litestar import Litestar


class SearchModuleProvider(Provider):
    """App-scoped provider for SearchModule."""

    scope = Scope.APP

    index_entity_task = provide(IndexEntityTask)
    remove_from_index_task = provide(RemoveFromIndexTask)


class SearchRequestProvider(Provider):
    """Request-scoped provider for SearchModule."""

    scope = Scope.REQUEST

    full_text_search_query = provide(FullTextSearchQuery)
    get_index_stats_query = provide(GetIndexStatsQuery)
    index_entity_action = provide(IndexEntityAction)

    @provide
    def search_uow(self, request: Request) -> SearchUnitOfWork:
        """Provide SearchUnitOfWork with event emitter from app."""
        app: "Litestar" = request.app
        return SearchUnitOfWork(_emit=app.emit, _app=app)


class SearchCLIProvider(Provider):
    """CLI context provider — UoW without event emitter."""

    scope = Scope.REQUEST

    full_text_search_query = provide(FullTextSearchQuery)
    get_index_stats_query = provide(GetIndexStatsQuery)
    index_entity_action = provide(IndexEntityAction)

    @provide
    def search_uow(self) -> SearchUnitOfWork:
        """Provide SearchUnitOfWork without event emitter for CLI."""
        return SearchUnitOfWork(_emit=None, _app=None)
