"""Temporal Saga error classes.

Все Saga-ошибки — Pydantic frozen модели с http_status.
Используются для Railway-Oriented Programming в Temporal Workflows.

Используется ErrorWithTemplate для автоматической генерации message.
"""

from typing import ClassVar

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class SagaError(BaseError):
    """Базовая ошибка Saga операций.
    
    Все Saga-специфичные ошибки наследуют от этого класса.
    
    Attributes:
        message: Человекочитаемое описание ошибки
        code: Машиночитаемый код ошибки
        http_status: HTTP статус код для API ответов
    """
    
    code: str = "SAGA_ERROR"
    http_status: int = 500


class SagaStepFailedError(ErrorWithTemplate, SagaError):
    """Ошибка при провале шага Saga.
    
    Содержит информацию о том, какой шаг упал и почему.
    Используется как основной тип ошибки в execute_saga.
    
    Attributes:
        failed_step: Имя шага, который упал
        cause: Причина ошибки (строка)
        completed_steps: Список успешно выполненных шагов
    
    Example:
        error = SagaStepFailedError(
            failed_step="payment",
            cause="Insufficient funds",
            completed_steps=["order", "reservation"],
        )
        # error.message == "Saga step 'payment' failed: Insufficient funds"
    """
    
    _message_template: ClassVar[str] = "Saga step '{failed_step}' failed: {cause}"
    code: str = "SAGA_STEP_FAILED"
    http_status: int = 500
    
    failed_step: str
    cause: str
    completed_steps: list[str] = []


class CompensationFailedError(ErrorWithTemplate, SagaError):
    """Ошибка при провале компенсации.
    
    КРИТИЧЕСКАЯ ОШИБКА — система может быть в неконсистентном состоянии.
    Требуется ручное вмешательство.
    
    Attributes:
        step_name: Имя шага, компенсация которого упала
        cause: Причина ошибки
        original_failure: Исходная ошибка, которая запустила компенсацию
    
    Example:
        error = CompensationFailedError(
            step_name="payment",
            cause="Refund service unavailable",
            original_failure="Delivery scheduling failed",
        )
    """
    
    _message_template: ClassVar[str] = (
        "Compensation for step '{step_name}' failed: {cause}. "
        "Original failure: {original_failure}"
    )
    code: str = "COMPENSATION_FAILED"
    http_status: int = 500
    
    step_name: str
    cause: str
    original_failure: str = "Unknown"


class SagaTimeoutError(ErrorWithTemplate, SagaError):
    """Ошибка при timeout выполнения Saga.
    
    Attributes:
        step_name: Шаг, на котором произошел timeout
        timeout_seconds: Сколько времени ждали
    
    Example:
        error = SagaTimeoutError(
            step_name="payment",
            timeout_seconds=60,
        )
    """
    
    _message_template: ClassVar[str] = (
        "Saga step '{step_name}' timed out after {timeout_seconds}s"
    )
    code: str = "SAGA_TIMEOUT"
    http_status: int = 504
    
    step_name: str
    timeout_seconds: float


class SagaCancellationError(ErrorWithTemplate, SagaError):
    """Ошибка при отмене Saga.
    
    Возникает когда Workflow был cancelled (например, по запросу).
    
    Attributes:
        workflow_id: ID отмененного workflow
        current_step: Шаг, на котором произошла отмена
        compensations_run: Количество выполненных компенсаций
    """
    
    _message_template: ClassVar[str] = (
        "Saga workflow '{workflow_id}' was cancelled at step '{current_step}'"
    )
    code: str = "SAGA_CANCELLED"
    http_status: int = 499  # Client Closed Request
    
    workflow_id: str
    current_step: str
    compensations_run: int = 0


class SagaValidationError(ErrorWithTemplate, SagaError):
    """Ошибка валидации входных данных Saga.
    
    Возникает перед началом выполнения при неверных входных данных.
    
    Attributes:
        validation_errors: Список ошибок валидации
    """
    
    _message_template: ClassVar[str] = "Saga input validation failed: {validation_errors}"
    code: str = "SAGA_VALIDATION_ERROR"
    http_status: int = 422
    
    validation_errors: list[str]


class SagaRetryExhaustedError(ErrorWithTemplate, SagaError):
    """Ошибка когда исчерпаны все попытки retry.
    
    Возникает когда activity провалилась после всех retry attempts.
    
    Attributes:
        step_name: Шаг, который исчерпал retry
        attempts: Количество попыток
        last_error: Последняя ошибка
    """
    
    _message_template: ClassVar[str] = (
        "Saga step '{step_name}' exhausted all {attempts} retry attempts: {last_error}"
    )
    code: str = "SAGA_RETRY_EXHAUSTED"
    http_status: int = 500
    
    step_name: str
    attempts: int
    last_error: str


class SagaInconsistentStateError(ErrorWithTemplate, SagaError):
    """Ошибка неконсистентного состояния Saga.
    
    КРИТИЧЕСКАЯ ОШИБКА — требуется ручное вмешательство.
    Возникает когда компенсация не может восстановить состояние.
    
    Attributes:
        workflow_id: ID workflow
        affected_steps: Шаги в неконсистентном состоянии
        details: Дополнительная информация
    """
    
    _message_template: ClassVar[str] = (
        "Saga '{workflow_id}' is in inconsistent state. "
        "Affected steps: {affected_steps}. {details}"
    )
    code: str = "SAGA_INCONSISTENT_STATE"
    http_status: int = 500
    
    workflow_id: str
    affected_steps: list[str]
    details: str = "Manual intervention required"


# Export all errors
__all__ = [
    "SagaError",
    "SagaStepFailedError",
    "CompensationFailedError",
    "SagaTimeoutError",
    "SagaCancellationError",
    "SagaValidationError",
    "SagaRetryExhaustedError",
    "SagaInconsistentStateError",
]
