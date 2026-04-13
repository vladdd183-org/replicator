from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class MemoryStored(DomainEvent):
    key: str
    category: str = "general"


class MemoryRetrieved(DomainEvent):
    key: str
    hit: bool = True
