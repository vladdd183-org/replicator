from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class CompassError(BaseError):
    """Базовая ошибка модуля стратегического планирования."""

    code: str = "COMPASS_ERROR"


class LowConfidenceError(CompassError):
    """Уверенность стратегии ниже допустимого порога."""

    code: str = "LOW_CONFIDENCE"
    confidence: float = 0.0
    threshold: float = 0.5


class StrategyFormationError(CompassError):
    """Не удалось сформировать стратегию из MissionSpec."""

    code: str = "STRATEGY_FORMATION_ERROR"
