from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class SpecCompiled(DomainEvent):
    mission_id: str
    title: str
    intent_type: str


class SpecValidated(DomainEvent):
    mission_id: str
