"""Temporal error classes.

Все Temporal-ошибки — Pydantic frozen модели с http_status.
Используются для обработки ошибок Temporal в Porto архитектуре.
"""

from typing import ClassVar

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class TemporalError(BaseError):
    """Базовая ошибка Temporal операций.
    
    Все Temporal-специфичные ошибки наследуют от этого класса.
    
    Attributes:
        message: Человекочитаемое описание ошибки
        code: Машиночитаемый код ошибки
        http_status: HTTP статус код для API ответов
    """
    
    code: str = "TEMPORAL_ERROR"
    http_status: int = 500


class TemporalConnectionError(ErrorWithTemplate, TemporalError):
    """Ошибка подключения к Temporal серверу.
    
    Возникает когда не удаётся установить соединение с Temporal.
    
    Attributes:
        host: Адрес Temporal сервера
        namespace: Temporal namespace
    
    Example:
        error = TemporalConnectionError(
            host="localhost:7233",
            namespace="default",
        )
    """
    
    _message_template: ClassVar[str] = (
        "Failed to connect to Temporal server at {host} (namespace: {namespace})"
    )
    code: str = "TEMPORAL_CONNECTION_ERROR"
    http_status: int = 503  # Service Unavailable
    
    host: str = "unknown"
    namespace: str = "unknown"


class TemporalWorkflowError(ErrorWithTemplate, TemporalError):
    """Ошибка выполнения Temporal Workflow.
    
    Attributes:
        workflow_id: ID workflow
        workflow_type: Тип (имя класса) workflow
        cause: Причина ошибки
    
    Example:
        error = TemporalWorkflowError(
            workflow_id="order-123",
            workflow_type="CreateOrderWorkflow",
            cause="Activity timeout",
        )
    """
    
    _message_template: ClassVar[str] = (
        "Workflow '{workflow_type}' (id: {workflow_id}) failed: {cause}"
    )
    code: str = "TEMPORAL_WORKFLOW_ERROR"
    http_status: int = 500
    
    workflow_id: str
    workflow_type: str
    cause: str


class TemporalActivityError(ErrorWithTemplate, TemporalError):
    """Ошибка выполнения Temporal Activity.
    
    Attributes:
        activity_name: Имя activity
        workflow_id: ID родительского workflow
        cause: Причина ошибки
    
    Example:
        error = TemporalActivityError(
            activity_name="create_order",
            workflow_id="order-123",
            cause="Database connection failed",
        )
    """
    
    _message_template: ClassVar[str] = (
        "Activity '{activity_name}' in workflow '{workflow_id}' failed: {cause}"
    )
    code: str = "TEMPORAL_ACTIVITY_ERROR"
    http_status: int = 500
    
    activity_name: str
    workflow_id: str
    cause: str


class TemporalTimeoutError(ErrorWithTemplate, TemporalError):
    """Ошибка timeout в Temporal.
    
    Attributes:
        operation: Тип операции (workflow/activity)
        operation_id: ID операции
        timeout_seconds: Значение timeout
    
    Example:
        error = TemporalTimeoutError(
            operation="activity",
            operation_id="create_order",
            timeout_seconds=30,
        )
    """
    
    _message_template: ClassVar[str] = (
        "Temporal {operation} '{operation_id}' timed out after {timeout_seconds}s"
    )
    code: str = "TEMPORAL_TIMEOUT"
    http_status: int = 504  # Gateway Timeout
    
    operation: str  # "workflow" or "activity"
    operation_id: str
    timeout_seconds: float


class WorkflowNotFoundError(ErrorWithTemplate, TemporalError):
    """Workflow не найден.
    
    Attributes:
        workflow_id: ID искомого workflow
    
    Example:
        error = WorkflowNotFoundError(workflow_id="order-123")
    """
    
    _message_template: ClassVar[str] = "Workflow with id '{workflow_id}' not found"
    code: str = "WORKFLOW_NOT_FOUND"
    http_status: int = 404
    
    workflow_id: str


class WorkflowAlreadyExistsError(ErrorWithTemplate, TemporalError):
    """Workflow с таким ID уже существует.
    
    Attributes:
        workflow_id: ID существующего workflow
    
    Example:
        error = WorkflowAlreadyExistsError(workflow_id="order-123")
    """
    
    _message_template: ClassVar[str] = "Workflow with id '{workflow_id}' already exists"
    code: str = "WORKFLOW_ALREADY_EXISTS"
    http_status: int = 409  # Conflict
    
    workflow_id: str


class WorkflowCancelledError(ErrorWithTemplate, TemporalError):
    """Workflow был отменён.
    
    Attributes:
        workflow_id: ID отменённого workflow
        reason: Причина отмены
    
    Example:
        error = WorkflowCancelledError(
            workflow_id="order-123",
            reason="User requested cancellation",
        )
    """
    
    _message_template: ClassVar[str] = "Workflow '{workflow_id}' was cancelled: {reason}"
    code: str = "WORKFLOW_CANCELLED"
    http_status: int = 499  # Client Closed Request
    
    workflow_id: str
    reason: str = "Unknown"


class WorkflowFailedError(ErrorWithTemplate, TemporalError):
    """Workflow завершился с ошибкой (после всех retry).
    
    Attributes:
        workflow_id: ID workflow
        workflow_type: Тип workflow
        failure_message: Сообщение об ошибке
    
    Example:
        error = WorkflowFailedError(
            workflow_id="order-123",
            workflow_type="CreateOrderWorkflow",
            failure_message="Payment declined",
        )
    """
    
    _message_template: ClassVar[str] = (
        "Workflow '{workflow_type}' (id: {workflow_id}) failed permanently: {failure_message}"
    )
    code: str = "WORKFLOW_FAILED"
    http_status: int = 500
    
    workflow_id: str
    workflow_type: str
    failure_message: str


# Export all errors
__all__ = [
    "TemporalError",
    "TemporalConnectionError",
    "TemporalWorkflowError",
    "TemporalActivityError",
    "TemporalTimeoutError",
    "WorkflowNotFoundError",
    "WorkflowAlreadyExistsError",
    "WorkflowCancelledError",
    "WorkflowFailedError",
]
