"""
Helper functions for license checking in WebSocket handlers.

Provides centralized error handling for license validation in WebSocket connections.
"""

from typing import Any, TypeVar
import logfire
from litestar import WebSocket
from litestar.exceptions import NotAuthorizedException

from src.Ship.Parents.Action import Action

T = TypeVar('T')


async def execute_with_license_check(
    action: Action[Any, T],
    data: Any,
    websocket: WebSocket
) -> T:
    """
    Выполнить Action с автоматической обработкой ошибок лицензии для WebSocket.
    
    Эта функция:
    1. Вызывает action.execute() (проверка лицензии внутри)
    2. Если лицензия невалидна - отправляет WS error message и закрывает соединение
    3. Если все ОК - возвращает результат
    
    Args:
        action: Action для выполнения
        data: Данные для передачи в action
        websocket: WebSocket соединение
        
    Returns:
        Результат выполнения action
        
    Raises:
        NotAuthorizedException: Если лицензия невалидна (после отправки WS сообщения)
        
    Example:
        # Вместо:
        result = await action.execute((image_data, request))
        
        # Используйте:
        result = await execute_with_license_check(
            action, 
            (image_data, request), 
            socket
        )
    """
    try:
        # Выполняем action - проверка лицензии произойдет автоматически
        return await action.execute(data)
        
    except NotAuthorizedException as e:
        # Лицензия невалидна - отправляем сообщение клиенту
        client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
        
        logfire.warn(
            "🔐 WebSocket: License validation failed",
            client=client_info,
            path=websocket.url.path,
            error=str(e)
        )
        
        # Отправляем error сообщение
        try:
            await websocket.send_json({
                "status": "error",
                "error": "license_invalid",
                "message": str(e),
                "code": 1008  # Policy Violation
            })
        except Exception as send_error:
            # Соединение может быть уже закрыто
            logfire.debug(
                "Failed to send license error message",
                client=client_info,
                error=str(send_error)
            )
        
        # Закрываем соединение с соответствующим кодом
        try:
            await websocket.close(
                code=1008,  # Policy Violation
                reason="License validation failed"[:123]  # WebSocket reason ограничен 123 байтами
            )
        except Exception as close_error:
            # Соединение может быть уже закрыто
            logfire.debug(
                "Failed to close WebSocket after license error",
                client=client_info,
                error=str(close_error)
            )
        
        # Пробрасываем исключение дальше, чтобы прервать обработку
        raise


__all__ = ["execute_with_license_check"]

