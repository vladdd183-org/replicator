from __future__ import annotations

from pydantic import Field

from src.Ship.Parents.Event import DomainEvent


class BeadStarted(DomainEvent):
    """Исполнение бида начато."""

    bead_id: str
    bead_title: str = ""
    agent_id: str = ""


class BeadCompleted(DomainEvent):
    """Бид успешно исполнен."""

    bead_id: str
    duration_ms: int = 0
    artifacts: list[str] = Field(default_factory=list)


class BeadFailed(DomainEvent):
    """Исполнение бида завершилось ошибкой."""

    bead_id: str
    error_message: str = ""
    duration_ms: int = 0


class GraphExecutionCompleted(DomainEvent):
    """Исполнение всего BeadGraph завершено."""

    overall_status: str
    total_beads: int = 0
    successful_beads: int = 0
    failed_beads: int = 0
    total_duration_ms: int = 0
