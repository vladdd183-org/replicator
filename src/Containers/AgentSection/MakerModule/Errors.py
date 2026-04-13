from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class MakerError(BaseError):
    """Базовая ошибка модуля исполнения (MAKER)."""

    code: str = "MAKER_ERROR"


class DecompositionError(MakerError):
    """Не удалось декомпозировать стратегию в BeadGraph."""

    code: str = "DECOMPOSITION_ERROR"
    phase_name: str = ""


class NoConsensusError(MakerError):
    """K-голосование не достигло консенсуса."""

    code: str = "NO_CONSENSUS"
    bead_id: str = ""
    k: int = 1
    attempts: int = 0
