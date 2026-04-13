from __future__ import annotations

from typing import Any

from returns.result import Failure, Result, Success

from src.Containers.KnowledgeSection.MemoryModule.Actions.StoreMemoryAction import MemoryStore
from src.Containers.KnowledgeSection.MemoryModule.Errors import MemoryError, MemoryNotFoundError
from src.Ship.Parents.Action import Action


class RetrieveMemoryAction(Action[str, dict[str, Any], MemoryError]):
    async def run(self, data: str) -> Result[dict[str, Any], MemoryError]:
        store = MemoryStore.get_instance()
        result = store.retrieve(data)
        if result is None:
            return Failure(MemoryNotFoundError(message=f"Memory not found: {data}", key=data))
        return Success(result)
