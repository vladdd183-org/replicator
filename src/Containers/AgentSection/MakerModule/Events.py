from __future__ import annotations

from pydantic import Field

from src.Ship.Parents.Event import DomainEvent


class BeadsCreated(DomainEvent):
    """BeadGraph успешно создан из StrategyPlan."""

    mission_id: str
    num_beads: int
    critical_path_length: int = 0


class VoteCompleted(DomainEvent):
    """Голосование по биду завершено."""

    bead_id: str
    k: int
    winning_agent: str = ""


class ConsensusReached(DomainEvent):
    """Консенсус достигнут по результатам K-голосования."""

    bead_id: str
    k: int
    agreement_ratio: float = 1.0
    agents: list[str] = Field(default_factory=list)
