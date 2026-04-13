"""Модели CellSpec и связанные типы для L2 Cell Engine.

Frozen-dataclass описывает контейнер как версионируемую адресуемую единицу:
статус, секция, списки actions/tasks/queries/events, зависимости, бюджет
ресурсов, health-check и вычисление ``spec_hash`` без самого поля ``spec_hash``.
"""

from __future__ import annotations

import hashlib, json
from dataclasses import dataclass, field
from enum import Enum


class CellStatus(str, Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    TESTING = "testing"
    VERIFIED = "verified"
    ACTIVE = "active"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class ResourceBudget:
    max_cpu_seconds: float = 60.0
    max_memory_mb: int = 512
    max_storage_mb: int = 1024
    max_network_calls: int = 1000


@dataclass(frozen=True)
class HealthCheckConfig:
    endpoint: str = "/health"
    interval_seconds: int = 30
    timeout_seconds: int = 5
    unhealthy_threshold: int = 3


@dataclass(frozen=True)
class CellSpec:
    name: str
    version: str
    description: str = ""
    section: str = ""
    spec_hash: str = ""

    actions: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    events_emitted: list[str] = field(default_factory=list)
    events_consumed: list[str] = field(default_factory=list)

    capabilities_required: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    adapters_required: list[str] = field(default_factory=list)

    resources: ResourceBudget = field(default_factory=ResourceBudget)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)

    status: CellStatus = CellStatus.DRAFT
    parent_spec_hash: str | None = None
    tags: list[str] = field(default_factory=list)


def compute_spec_hash(spec: CellSpec) -> str:
    """SHA-256 от JSON-сериализации spec (без поля spec_hash)."""
    # Serialize all fields except spec_hash
    data = {
        "name": spec.name,
        "version": spec.version,
        "description": spec.description,
        "section": spec.section,
        "actions": spec.actions,
        "tasks": spec.tasks,
        "queries": spec.queries,
        "events_emitted": spec.events_emitted,
        "events_consumed": spec.events_consumed,
        "capabilities_required": spec.capabilities_required,
        "dependencies": spec.dependencies,
        "adapters_required": spec.adapters_required,
        "status": spec.status.value,
        "parent_spec_hash": spec.parent_spec_hash,
        "tags": spec.tags,
    }
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode()).hexdigest()
