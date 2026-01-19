"""
Пример использования проверки лицензии в WebSocket handlers

⚠️ ВАЖНО: Middleware не работает для WebSocket соединений!
Используйте функцию check_license() в начале каждого WebSocket handler
"""

from litestar import websocket
from litestar.exceptions import NotAuthorizedException
from litestar.connection import WebSocket

from src.Ship.Licensing import check_license
import logfire


# ============================================
# ПРИМЕР 1: Простая проверка при подключении
# ============================================

@websocket("/ws/simple")
async def simple_websocket_handler(socket: WebSocket) -> None:
    """
    Простой WebSocket handler с проверкой лицензии
    """
    
    # Принимаем соединение
    await socket.accept()
    
    try:
        # Проверяем лицензию при подключении
        await check_license()
        
        logfire.info("WebSocket connected with valid license")
        
        # Обрабатываем сообщения
        async for message in socket.iter_data():
            await socket.send_json({
                "echo": message,
                "status": "ok"
            })
            
    except NotAuthorizedException as e:
        # Лицензия невалидна - закрываем соединение
        logfire.warn(f"WebSocket rejected: {e}")
        await socket.close(code=1008, reason=str(e)[:100])  # Код 1008 = Policy Violation
    
    except Exception as e:
        logfire.error(f"WebSocket error: {e}", exc_info=True)
        await socket.close(code=1011, reason="Internal server error")


# ============================================
# ПРИМЕР 2: Периодическая проверка лицензии
# ============================================

@websocket("/ws/periodic-check")
async def periodic_check_websocket_handler(socket: WebSocket) -> None:
    """
    WebSocket handler с периодической проверкой лицензии
    (рекомендуется для долгих соединений)
    """
    
    await socket.accept()
    
    import asyncio
    from datetime import datetime
    
    try:
        # Начальная проверка лицензии
        await check_license()
        
        last_check = datetime.now()
        check_interval = 300  # Проверять каждые 5 минут
        
        async for message in socket.iter_data():
            # Периодическая проверка лицензии
            if (datetime.now() - last_check).total_seconds() > check_interval:
                try:
                    await check_license()
                    last_check = datetime.now()
                except NotAuthorizedException as e:
                    await socket.send_json({
                        "error": "License expired",
                        "message": str(e)
                    })
                    await socket.close(code=1008, reason="License expired")
                    return
            
            # Обрабатываем сообщение
            await socket.send_json({
                "received": message,
                "timestamp": datetime.now().isoformat()
            })
            
    except NotAuthorizedException as e:
        await socket.close(code=1008, reason=str(e)[:100])
    except Exception as e:
        logfire.error(f"WebSocket error: {e}", exc_info=True)
        await socket.close(code=1011, reason="Internal server error")


# ============================================
# ПРИМЕР 3: С использованием декоратора
# ============================================

from functools import wraps
from typing import Callable, Any


def require_license(handler: Callable) -> Callable:
    """
    Декоратор для WebSocket handlers, требующий валидную лицензию
    
    Usage:
        @websocket("/ws/protected")
        @require_license
        async def my_handler(socket: WebSocket):
            # Лицензия уже проверена
            pass
    """
    
    @wraps(handler)
    async def wrapper(socket: WebSocket, *args: Any, **kwargs: Any) -> None:
        await socket.accept()
        
        try:
            # Проверяем лицензию
            await check_license()
            
            # Вызываем оригинальный handler
            return await handler(socket, *args, **kwargs)
            
        except NotAuthorizedException as e:
            logfire.warn(f"WebSocket rejected due to license: {e}")
            await socket.send_json({
                "error": "License validation failed",
                "message": str(e)
            })
            await socket.close(code=1008, reason=str(e)[:100])
        
        except Exception as e:
            logfire.error(f"WebSocket error: {e}", exc_info=True)
            await socket.close(code=1011, reason="Internal server error")
    
    return wrapper


# Использование декоратора:

@websocket("/ws/decorated")
@require_license
async def decorated_websocket_handler(socket: WebSocket) -> None:
    """
    WebSocket handler с декоратором проверки лицензии
    """
    
    # Лицензия уже проверена декоратором
    logfire.info("WebSocket handler started with valid license")
    
    async for message in socket.iter_data():
        await socket.send_json({
            "echo": message,
            "license_status": "valid"
        })


# ============================================
# ПРИМЕР 4: Реальный пример для вашего проекта
# ============================================

@websocket("/ws/ocr/process")
async def ocr_websocket_handler(socket: WebSocket) -> None:
    """
    WebSocket handler для OCR обработки с проверкой лицензии
    """
    
    await socket.accept()
    
    try:
        # Проверяем лицензию перед началом обработки
        license_info = await check_license()
        
        logfire.info(
            "OCR WebSocket connected",
            license_expires=license_info.get("expires_at")
        )
        
        # Отправляем подтверждение клиенту
        await socket.send_json({
            "status": "connected",
            "license": "valid",
            "message": "Ready to process images"
        })
        
        # Обрабатываем изображения
        async for data in socket.iter_json():
            command = data.get("command")
            
            if command == "process_image":
                image_data = data.get("image")
                
                # Здесь ваша логика обработки OCR
                # ...
                
                await socket.send_json({
                    "status": "processed",
                    "result": "OCR text here..."
                })
            
            elif command == "ping":
                # Также проверяем лицензию при ping
                await check_license()
                await socket.send_json({"status": "pong"})
            
            else:
                await socket.send_json({
                    "error": "Unknown command"
                })
    
    except NotAuthorizedException as e:
        await socket.send_json({
            "error": "license_invalid",
            "message": str(e)
        })
        await socket.close(code=1008, reason="License validation failed")
    
    except Exception as e:
        logfire.error(f"OCR WebSocket error: {e}", exc_info=True)
        await socket.send_json({
            "error": "server_error",
            "message": "Internal server error"
        })
        await socket.close(code=1011)


# ============================================
# РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ
# ============================================

"""
1. ВСЕГДА проверяйте лицензию в начале WebSocket handler:
   
   await socket.accept()
   await check_license()  # <- Важно!

2. Для долгих соединений (>5 минут) добавьте периодическую проверку

3. Обрабатывайте NotAuthorizedException правильно:
   - Отправьте понятное сообщение клиенту
   - Закройте соединение с кодом 1008 (Policy Violation)

4. Используйте декоратор @require_license для упрощения кода

5. Логируйте все проверки лицензии для аудита

6. НЕ полагайтесь только на middleware - он не работает для WebSocket!
"""





