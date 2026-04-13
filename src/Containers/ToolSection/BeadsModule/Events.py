from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class BeadCreated(DomainEvent):
    bead_id: str
    title: str


class BeadClaimed(DomainEvent):
    bead_id: str


class BeadClosed(DomainEvent):
    bead_id: str
    reason: str = ""
