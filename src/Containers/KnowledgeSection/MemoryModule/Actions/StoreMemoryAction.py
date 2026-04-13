from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, Field
from returns.result import Failure, Result, Success

from src.Containers.KnowledgeSection.MemoryModule.Errors import MemoryError
from src.Ship.Parents.Action import Action


class StoreMemoryRequest(BaseModel):
    model_config = {"frozen": True}

    key: str
    value: str
    category: str = "general"
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryStore:
    """Simple in-memory store for agent memories. Singleton."""

    _instance: ClassVar[MemoryStore | None] = None
    _store: ClassVar[dict[str, dict[str, Any]]] = {}

    @classmethod
    def get_instance(cls) -> MemoryStore:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def store(
        self,
        key: str,
        value: str,
        category: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._store[key] = {"value": value, "category": category, "metadata": metadata or {}}

    def retrieve(self, key: str) -> dict[str, Any] | None:
        return self._store.get(key)

    def search(self, category: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        results = []
        for k, v in self._store.items():
            if category and v["category"] != category:
                continue
            results.append({"key": k, **v})
            if len(results) >= limit:
                break
        return results


class StoreMemoryAction(Action[StoreMemoryRequest, str, MemoryError]):
    async def run(self, data: StoreMemoryRequest) -> Result[str, MemoryError]:
        try:
            store = MemoryStore.get_instance()
            store.store(data.key, data.value, data.category, data.metadata)
            return Success(data.key)
        except Exception as e:
            return Failure(MemoryError(message=f"Failed to store memory: {e}"))
