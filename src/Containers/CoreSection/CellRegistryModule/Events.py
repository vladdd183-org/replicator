from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class CellRegistered(DomainEvent):
    cell_name: str
    version: str
    spec_hash: str


class CellStatusUpdated(DomainEvent):
    cell_name: str
    old_status: str
    new_status: str
