"""
Декораторы для проверки лицензии в WebSocket handlers
"""

from functools import wraps
from typing import Callable, Any

from litestar.connection import WebSocket
from litestar.exceptions import NotAuthorizedException

from .Middleware import check_license
import logfire


def require_license(handler: Callable) -> Callable:
    """
    Декоратор для WebSocket handlers, требующий валидную лицензию
    
    Использование:
        @websocket("/ws/protected")
        @require_license
        async def my_handler(socket: WebSocket):
            # Лицензия уже проверена декоратором
            async for message in socket.iter_data():
                await socket.send_json({"echo": message})
    
    Args:
        handler: WebSocket handler функция
        
    Returns:
        Обернутая функция с проверкой лицензии
    """
    
    @wraps(handler)
    async def wrapper(socket: WebSocket, *args: Any, **kwargs: Any) -> None:
        """Wrapper with license validation"""
        
        # Принимаем соединение
        await socket.accept()
        
        try:
            # Проверяем лицензию
            license_info = await check_license()
            
            logfire.info(
                "WebSocket connected with valid license",
                handler=handler.__name__,
                expires_at=license_info.get("expires_at")
            )
            
            # Вызываем оригинальный handler
            return await handler(socket, *args, **kwargs)
            
        except NotAuthorizedException as e:
            # Лицензия невалидна
            logfire.warn(
                f"WebSocket rejected due to license",
                handler=handler.__name__,
                error=str(e)
            )
            
            # Отправляем сообщение об ошибке клиенту
            try:
                await socket.send_json({
                    "error": "license_invalid",
                    "message": str(e),
                    "code": 1008
                })
            except:
                pass  # Соединение может быть уже закрыто
            
            # Закрываем соединение с кодом Policy Violation
            await socket.close(code=1008, reason=str(e)[:100])
        
        except Exception as e:
            # Другие ошибки
            logfire.error(
                f"WebSocket error in license decorator",
                handler=handler.__name__,
                error=str(e),
                exc_info=True
            )
            
            try:
                await socket.send_json({
                    "error": "server_error",
                    "message": "Internal server error"
                })
            except:
                pass
            
            await socket.close(code=1011, reason="Internal server error")
    
    return wrapper


def require_license_periodic(check_interval: int = 300):
    """
    Декоратор с периодической проверкой лицензии
    Рекомендуется для долгих WebSocket соединений
    
    Использование:
        @websocket("/ws/long-running")
        @require_license_periodic(check_interval=300)  # Проверять каждые 5 минут
        async def my_handler(socket: WebSocket):
            async for message in socket.iter_data():
                # Лицензия проверяется автоматически каждые 5 минут
                await socket.send_json({"echo": message})
    
    Args:
        check_interval: Интервал проверки в секундах (по умолчанию 300 = 5 минут)
        
    Returns:
        Декоратор
    """
    
    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        async def wrapper(socket: WebSocket, *args: Any, **kwargs: Any) -> None:
            from datetime import datetime
            
            await socket.accept()
            
            try:
                # Начальная проверка лицензии
                await check_license()
                
                logfire.info(
                    f"WebSocket connected with periodic license check",
                    handler=handler.__name__,
                    check_interval=check_interval
                )
                
                # Сохраняем время последней проверки в socket state
                socket.state = {"last_license_check": datetime.now()}
                
                # Вызываем оригинальный handler
                # Handler должен сам периодически проверять лицензию
                # через вызов _check_license_if_needed(socket)
                return await handler(socket, *args, **kwargs)
                
            except NotAuthorizedException as e:
                logfire.warn(f"WebSocket rejected: {e}", handler=handler.__name__)
                
                try:
                    await socket.send_json({
                        "error": "license_invalid",
                        "message": str(e)
                    })
                except:
                    pass
                
                await socket.close(code=1008, reason=str(e)[:100])
            
            except Exception as e:
                logfire.error(
                    f"WebSocket error",
                    handler=handler.__name__,
                    error=str(e),
                    exc_info=True
                )
                await socket.close(code=1011)
        
        return wrapper
    
    return decorator


async def check_license_if_needed(socket: WebSocket, interval: int = 300) -> None:
    """
    Вспомогательная функция для периодической проверки лицензии
    
    Использование в handler:
        async for message in socket.iter_data():
            await check_license_if_needed(socket, interval=300)
            # ... обработка сообщения
    
    Args:
        socket: WebSocket соединение
        interval: Интервал проверки в секундах
        
    Raises:
        NotAuthorizedException: Если лицензия невалидна
    """
    from datetime import datetime
    
    if not hasattr(socket, 'state') or 'last_license_check' not in socket.state:
        socket.state = {"last_license_check": datetime.now()}
        return
    
    last_check = socket.state["last_license_check"]
    
    if (datetime.now() - last_check).total_seconds() > interval:
        # Пора проверить лицензию
        await check_license()
        socket.state["last_license_check"] = datetime.now()
        
        logfire.debug(
            "Periodic license check passed",
            interval=interval
        )





