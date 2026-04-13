from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class PRCreated(DomainEvent):
    pr_number: int = 0
    pr_url: str = ""
    title: str = ""


class PRMerged(DomainEvent):
    pr_number: int = 0
