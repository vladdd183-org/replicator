"""SearchModule DI providers."""

from dishka import Provider, Scope, provide

from src.Containers.AppSection.SearchModule.Tasks.IndexEntityTask import (
    IndexEntityTask,
    RemoveFromIndexTask,
)
from src.Containers.AppSection.SearchModule.Queries.FullTextSearchQuery import (
    FullTextSearchQuery,
)
from src.Containers.AppSection.SearchModule.Queries.GetIndexStatsQuery import (
    GetIndexStatsQuery,
)
from src.Containers.AppSection.SearchModule.Actions.IndexEntityAction import (
    IndexEntityAction,
)


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



