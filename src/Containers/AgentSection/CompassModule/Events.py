from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class StrategyFormed(DomainEvent):
    """Стратегия успешно сформирована из MissionSpec."""

    mission_id: str
    approach: str
    confidence: float
    num_phases: int


class AnomalyDetected(DomainEvent):
    """Обнаружена аномалия при анализе миссии."""

    mission_id: str
    description: str
    severity: str
