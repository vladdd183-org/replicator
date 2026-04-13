from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class BuildCompleted(DomainEvent):
    flake_ref: str
    output_path: str


class BuildFailed(DomainEvent):
    flake_ref: str
    error: str


class FlakeGenerated(DomainEvent):
    project_name: str
