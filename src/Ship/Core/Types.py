"""Базовые типы проекта Replicator.

Содержит как оригинальные Porto-типы, так и расширения
для адаптерной нейтральности и Cell-модели.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, NewType, Protocol, TypeVar, runtime_checkable
from uuid import UUID

from src.Ship.Parents.Event import DomainEvent

__all__ = [
    "Entity",
    "Identifiable",
    "DomainEvent",
    "T",
    "CID",
    "Identity",
    "Capability",
    "ComputeResult",
    "IntentType",
    "Priority",
    "BeadType",
    "Complexity",
    "GovernanceLevel",
]

T = TypeVar("T")

CID = NewType("CID", str)


@runtime_checkable
class Entity(Protocol):
    """Protocol for entities with an ID."""

    id: UUID


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for objects that have an identifier."""

    @property
    def id(self) -> UUID: ...


@dataclass(frozen=True)
class Identity:
    """Идентичность субъекта: кто он и что ему разрешено."""

    subject: str
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Capability:
    """Capability-токен: resource + action + constraints."""

    resource: str
    action: str
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComputeResult:
    """Результат вычисления через ComputePort."""

    output: bytes
    output_id: str
    duration_ms: int
    exit_code: int = 0
    evidence: dict[str, Any] = field(default_factory=dict)


class IntentType(str, Enum):
    SELF_EVOLVE = "self_evolve"
    GENERATE = "generate"
    LEGACY = "legacy"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BeadType(str, Enum):
    CODE = "code"
    TEST = "test"
    CONFIG = "config"
    DOC = "doc"
    REVIEW = "review"


class Complexity(str, Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class GovernanceLevel(str, Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"
