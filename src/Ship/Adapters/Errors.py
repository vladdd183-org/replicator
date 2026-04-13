"""Ошибки адаптерного слоя (L0).

Все ошибки -- frozen Pydantic модели, наследники BaseError.
"""

from src.Ship.Core.Errors import BaseError


class AdapterError(BaseError):
    """Базовая ошибка адаптеров."""

    code: str = "ADAPTER_ERROR"
    http_status: int = 502


class StorageNotFoundError(AdapterError):
    """Запрошенный объект не найден в хранилище."""

    code: str = "STORAGE_NOT_FOUND"
    http_status: int = 404
    identifier: str = ""


class StorageWriteError(AdapterError):
    """Ошибка записи в хранилище."""

    code: str = "STORAGE_WRITE_ERROR"
    http_status: int = 500


class MessagingTimeoutError(AdapterError):
    """Таймаут при ожидании ответа через messaging."""

    code: str = "MESSAGING_TIMEOUT"
    http_status: int = 504
    topic: str = ""
    timeout_seconds: float = 0.0


class MessagingPublishError(AdapterError):
    """Ошибка публикации сообщения."""

    code: str = "MESSAGING_PUBLISH_ERROR"
    http_status: int = 500


class IdentityVerificationError(AdapterError):
    """Ошибка верификации токена/идентичности."""

    code: str = "IDENTITY_VERIFICATION_ERROR"
    http_status: int = 401


class IdentityIssuanceError(AdapterError):
    """Ошибка выдачи токена."""

    code: str = "IDENTITY_ISSUANCE_ERROR"
    http_status: int = 500


class StateNotFoundError(AdapterError):
    """Запрошенный stream не найден."""

    code: str = "STATE_NOT_FOUND"
    http_status: int = 404
    stream_id: str = ""


class StateWriteError(AdapterError):
    """Ошибка записи состояния."""

    code: str = "STATE_WRITE_ERROR"
    http_status: int = 500


class ComputeTimeoutError(AdapterError):
    """Таймаут исполнения вычисления."""

    code: str = "COMPUTE_TIMEOUT"
    http_status: int = 504
    function_id: str = ""
    timeout_seconds: float = 0.0


class ComputeExecutionError(AdapterError):
    """Ошибка исполнения вычисления."""

    code: str = "COMPUTE_EXECUTION_ERROR"
    http_status: int = 500
    function_id: str = ""
    exit_code: int = -1
