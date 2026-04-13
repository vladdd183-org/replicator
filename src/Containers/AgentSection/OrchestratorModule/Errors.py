from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class OrchestratorError(BaseError):
    """Базовая ошибка модуля оркестрации."""

    code: str = "ORCHESTRATOR_ERROR"


class BeadExecutionError(OrchestratorError):
    """Ошибка при исполнении бида или графа бидов."""

    code: str = "BEAD_EXECUTION_ERROR"
    bead_id: str = ""


class WorkcellCreationError(OrchestratorError):
    """Не удалось создать рабочую ячейку для исполнения бида."""

    code: str = "WORKCELL_CREATION_ERROR"
    bead_id: str = ""
    reason: str = ""
