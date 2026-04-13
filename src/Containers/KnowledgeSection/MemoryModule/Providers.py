from __future__ import annotations

from dishka import Provider, Scope, provide

from src.Containers.KnowledgeSection.MemoryModule.Actions.StoreMemoryAction import StoreMemoryAction
from src.Containers.KnowledgeSection.MemoryModule.Actions.RetrieveMemoryAction import RetrieveMemoryAction


class MemoryModuleProvider(Provider):
    scope = Scope.REQUEST
    store_memory = provide(StoreMemoryAction)
    retrieve_memory = provide(RetrieveMemoryAction)
