from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class ModuleGenerated(DomainEvent):
    section: str
    module_name: str
    files_count: int


class ProjectGenerated(DomainEvent):
    project_name: str
    target_path: str
    modules_count: int
