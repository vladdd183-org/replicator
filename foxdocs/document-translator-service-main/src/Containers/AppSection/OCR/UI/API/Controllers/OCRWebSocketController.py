"""
OCR WebSocket Controllers

WebSocket handlers для OCR операций с поддержкой отправки файлов.
Используют функциональный подход с прямым управлением WebSocket соединением.
"""
import json
import time
from typing import Any, Dict, Union
import asyncio
import logfire

from litestar import WebSocket, websocket
from litestar.exceptions import WebSocketException, WebSocketDisconnect

from src.Containers.AppSection.OCR.Actions import (
    ProcessImageAction,
    ProcessPolygonsAction,
)
from src.Containers.AppSection.OCR.Data import (
    PolygonRegionSchema,
    ProcessImageResponseSchema,
    ProcessPolygonsResponseSchema,
)
from src.Containers.AppSection.OCR.Exceptions import (
    OCRException,
    InvalidImageFormatException,
    ImageTooLargeException,
    InvalidPolygonException,
)

@websocket("/ws/ocr/test")
async def test_websocket_handler(socket: WebSocket) -> None:
    """
    Тестовый WebSocket handler для диагностики соединений.
    
    Простой endpoint для проверки работы WebSocket без dependency injection.
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        
        logfire.info(
            "🔌 TEST WebSocket: Connection accepted",
            client=client_info,
            path=socket.url.path,
            headers=dict(socket.headers) if socket.headers else {},
            query_params=dict(socket.query_params) if socket.query_params else {}
        )
        
        # Отправляем приветственное сообщение
        welcome_msg = {
            "status": "connected",
            "message": "Test WebSocket connection established!",
            "client_info": client_info,
            "timestamp": time.time()
        }
        
        logfire.info("📤 TEST WebSocket: Sending welcome message", message=welcome_msg)
        await socket.send_json(welcome_msg)
        logfire.info("✅ TEST WebSocket: Welcome message sent successfully")
        
        # Основной цикл обработки сообщений
        while True:
            try:
                # Получаем сообщение (низкоуровневый dict)
                raw_message = await socket.receive()
                
                # Извлекаем реальные данные из WebSocket message
                if isinstance(raw_message, dict):
                    if raw_message.get('type') == 'websocket.receive':
                        if 'text' in raw_message:
                            message = raw_message['text']
                        elif 'bytes' in raw_message:
                            message = raw_message['bytes']
                        else:
                            message = raw_message
                    elif raw_message.get('type') == 'websocket.disconnect':
                        break
                    else:
                        message = raw_message
                else:
                    message = raw_message
                
                logfire.info(
                    "📥 TEST WebSocket: Message received",
                    message_type=type(message).__name__,
                    message_content=str(message)[:200] if message else "None",
                    client=client_info
                )
                
                # Обрабатываем разные типы сообщений
                if isinstance(message, str):
                    try:
                        # Пытаемся распарсить как JSON
                        json_data = json.loads(message)
                        response = {
                            "status": "echo",
                            "received_json": json_data,
                            "timestamp": time.time(),
                            "client": client_info
                        }
                    except json.JSONDecodeError:
                        # Если не JSON, то просто текст
                        response = {
                            "status": "echo",
                            "received_text": message,
                            "timestamp": time.time(),
                            "client": client_info
                        }
                elif isinstance(message, bytes):
                    response = {
                        "status": "echo",
                        "received_bytes_length": len(message),
                        "timestamp": time.time(),
                        "client": client_info
                    }
                else:
                    response = {
                        "status": "echo",
                        "received_type": type(message).__name__,
                        "timestamp": time.time(),
                        "client": client_info
                    }
                
                logfire.info("📤 TEST WebSocket: Sending response", response=response)
                await socket.send_json(response)
                
            except WebSocketDisconnect:
                logfire.info("🔌 TEST WebSocket: Client disconnected gracefully", client=client_info)
                break
                
            except Exception as e:
                logfire.error("❌ TEST WebSocket: Error processing message", error=str(e), client=client_info)
                try:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Error processing message: {str(e)}",
                        "timestamp": time.time(),
                        "client": client_info
                    })
                except:
                    break
    
    except WebSocketDisconnect:
        logfire.info("🔌 TEST WebSocket: Connection closed during handshake", client=client_info)
    except Exception as e:
        logfire.error("❌ TEST WebSocket: Connection error", error=str(e), client=client_info)
    finally:
        logfire.info("🔌 TEST WebSocket: Connection cleanup completed", client=client_info)


@websocket("/ws/ocr/process")
async def process_image_websocket_handler(
    socket: WebSocket
) -> None:
    """
    WebSocket handler для распознавания текста на всём изображении.
    
    Протокол обмена:
    1. JSON метаданные: {"action": "process_image", "filename": "image.jpg", "size": 12345}
    2. Сервер отвечает: {"status": "ready", "message": "Send image data as binary"}
    3. Бинарные данные изображения
    4. Сервер отвечает с результатом OCR
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        logfire.info("OCR Process WebSocket connection established", client=client_info)
        
        waiting_for_image = False
        
        while True:
            try:
                # Получаем сообщение (низкоуровневый dict)
                raw_message = await socket.receive()
                
                # Извлекаем реальные данные из WebSocket message
                if isinstance(raw_message, dict):
                    if raw_message.get('type') == 'websocket.receive':
                        if 'text' in raw_message:
                            message = raw_message['text']
                        elif 'bytes' in raw_message:
                            message = raw_message['bytes']
                        else:
                            message = raw_message
                    elif raw_message.get('type') == 'websocket.disconnect':
                        break
                    else:
                        message = raw_message
                else:
                    message = raw_message
                
                # Если это строка, то это JSON метаданные
                if isinstance(message, str):
                    try:
                        message_data = json.loads(message)
                    except json.JSONDecodeError:
                        await socket.send_json({
                            "status": "error",
                            "message": "Invalid JSON format. Expected metadata object."
                        })
                        continue
                elif isinstance(message, dict):
                    # Litestar уже распарсил JSON в dict
                    message_data = message
                else:
                    # Если не строка и не dict, проверяем на байты
                    if not isinstance(message, bytes):
                        await socket.send_json({
                            "status": "error",
                            "message": f"Unsupported data type: {type(message).__name__}"
                        })
                        continue
                    # Переходим к обработке байтов
                    message_data = None
                
                # Обрабатываем метаданные, если они есть
                if message_data is not None:
                    if not isinstance(message_data, dict):
                        await socket.send_json({
                            "status": "error",
                            "message": "Invalid message format. Expected JSON object."
                        })
                        continue
                    
                    action = message_data.get("action")
                    if action != "process_image":
                        await socket.send_json({
                            "status": "error",
                            "message": f"Invalid action: {action}. Expected 'process_image'."
                        })
                        continue
                    
                    filename = message_data.get("filename", "unknown.jpg")
                    expected_size = message_data.get("size", 0)
                    
                    logfire.info(
                        "Received process image metadata",
                        filename=filename,
                        expected_size=expected_size,
                        client=client_info
                    )
                    
                    # Устанавливаем флаг ожидания изображения
                    waiting_for_image = True
                    
                    await socket.send_json({
                        "status": "ready",
                        "message": "Send image data as binary"
                    })
                
                # Если это байты, то это изображение
                elif isinstance(message, bytes):
                    if not waiting_for_image:
                        await socket.send_json({
                            "status": "error",
                            "message": "Send metadata first before sending image data"
                        })
                        continue
                    
                    if len(message) == 0:
                        await socket.send_json({
                            "status": "error",
                            "message": "No image data received"
                        })
                        continue
                    
                    logfire.info(
                        "Received image data",
                        size=len(message),
                        client=client_info
                    )
                    
                    # Сбрасываем флаг ожидания
                    waiting_for_image = False
                    
                    # Получаем ProcessImageAction через REQUEST scope
                    async with socket.app.state.di_container() as request_container:
                        process_image_action = await request_container.get(ProcessImageAction)
                        
                        try:
                            with logfire.span("websocket_ocr_process_image"):
                                # Отправляем статус начала обработки
                                await socket.send_json({
                                    "status": "processing",
                                    "message": "Processing image..."
                                })
                                
                                result = await process_image_action.run(message)
                                
                                # Конвертируем результат в словарь для JSON
                                result_dict = {
                                    "results": [
                                        {
                                            "text": r.text,
                                            "confidence": r.confidence,
                                            "coordinates": r.coordinates
                                        }
                                        for r in result.results
                                    ],
                                    "total_regions": result.total_regions,
                                    "image_dimensions": result.image_dimensions,
                                    "processing_time": result.processing_time,
                                    "timestamp": result.timestamp.isoformat()
                                }
                                
                                logfire.info(
                                    "Image processed successfully via WebSocket",
                                    regions_found=result.total_regions,
                                    processing_time=result.processing_time,
                                    client=client_info
                                )
                                
                                await socket.send_json({
                                    "status": "success",
                                    "data": result_dict
                                })
                        
                        except InvalidImageFormatException as e:
                            logfire.error("Invalid image format", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": f"Invalid image format: {str(e)}"
                            })
                        
                        except ImageTooLargeException as e:
                            logfire.error("Image too large", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": str(e)
                            })
                        
                        except OCRException as e:
                            logfire.error("OCR processing failed", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": f"OCR processing failed: {str(e)}"
                            })
                
                else:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Unsupported data type: {type(message).__name__}"
                    })
                    
            except WebSocketDisconnect:
                logfire.info("OCR Process WebSocket disconnected by client", client=client_info)
                break
            except Exception as e:
                logfire.error("OCR Process WebSocket communication error", error=str(e), client=client_info)
                try:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Communication error: {str(e)}"
                    })
                except:
                    pass
                break
    
    except WebSocketDisconnect:
        logfire.info("OCR Process WebSocket connection closed by client", client=client_info)
    except Exception as e:
        logfire.error("OCR Process WebSocket connection error", error=str(e), client=client_info)
    finally:
        logfire.info("OCR Process WebSocket connection closed", client=client_info)


@websocket("/ws/ocr/process-polygons")
async def process_polygons_websocket_handler(
    socket: WebSocket
) -> None:
    """
    WebSocket handler для распознавания текста в полигональных областях.
    
    Протокол обмена:
    1. JSON метаданные с регионами: {
        "action": "process_polygons",
        "filename": "image.jpg", 
        "size": 12345,
        "regions": [{"points": [[x1,y1], [x2,y2], ...], "region_id": "..."}]
    }
    2. Сервер отвечает: {"status": "ready", "message": "Send image data as binary"}
    3. Бинарные данные изображения
    4. Сервер отвечает с результатом OCR полигонов
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        logfire.info("OCR Polygons WebSocket connection established", client=client_info)
        
        waiting_for_image = False
        regions_data = None
        
        while True:
            try:
                # Получаем сообщение (низкоуровневый dict)
                raw_message = await socket.receive()
                
                # Извлекаем реальные данные из WebSocket message
                if isinstance(raw_message, dict):
                    if raw_message.get('type') == 'websocket.receive':
                        if 'text' in raw_message:
                            message = raw_message['text']
                        elif 'bytes' in raw_message:
                            message = raw_message['bytes']
                        else:
                            message = raw_message
                    elif raw_message.get('type') == 'websocket.disconnect':
                        break
                    else:
                        message = raw_message
                else:
                    message = raw_message
                
                # Если это строка, то это JSON метаданные с регионами
                if isinstance(message, str):
                    try:
                        message_data = json.loads(message)
                    except json.JSONDecodeError:
                        await socket.send_json({
                            "status": "error",
                            "message": "Invalid JSON format. Expected metadata object."
                        })
                        continue
                elif isinstance(message, dict):
                    # Litestar уже распарсил JSON в dict
                    message_data = message
                else:
                    # Если не строка и не dict, проверяем на байты
                    if not isinstance(message, bytes):
                        await socket.send_json({
                            "status": "error",
                            "message": f"Unsupported data type: {type(message).__name__}"
                        })
                        continue
                    # Переходим к обработке байтов
                    message_data = None
                
                # Обрабатываем метаданные, если они есть
                if message_data is not None:
                    if not isinstance(message_data, dict):
                        await socket.send_json({
                            "status": "error",
                            "message": "Invalid message format. Expected JSON object."
                        })
                        continue
                    
                    action = message_data.get("action")
                    if action != "process_polygons":
                        await socket.send_json({
                            "status": "error",
                            "message": f"Invalid action: {action}. Expected 'process_polygons'."
                        })
                        continue
                    
                    filename = message_data.get("filename", "unknown.jpg")
                    expected_size = message_data.get("size", 0)
                    regions_list = message_data.get("regions", [])
                    
                    # Валидируем регионы
                    if not isinstance(regions_list, list) or len(regions_list) == 0:
                        await socket.send_json({
                            "status": "error",
                            "message": "Regions must be a non-empty array"
                        })
                        continue
                    
                    # Создаём схемы регионов
                    regions = []
                    try:
                        for idx, region_data in enumerate(regions_list):
                            region = PolygonRegionSchema(**region_data)
                            regions.append(region)
                    except Exception as e:
                        await socket.send_json({
                            "status": "error",
                            "message": f"Invalid region at index {idx}: {str(e)}"
                        })
                        continue
                    
                    # Сохраняем регионы и устанавливаем флаг ожидания изображения
                    regions_data = regions
                    waiting_for_image = True
                    
                    logfire.info(
                        "Received process polygons metadata",
                        filename=filename,
                        expected_size=expected_size,
                        regions_count=len(regions),
                        client=client_info
                    )
                    
                    await socket.send_json({
                        "status": "ready",
                        "message": "Send image data as binary"
                    })
                
                # Если это байты, то это изображение с регионами
                elif isinstance(message, bytes):
                    if not waiting_for_image:
                        await socket.send_json({
                            "status": "error",
                            "message": "Send metadata with regions first before sending image data"
                        })
                        continue
                    
                    if len(message) == 0:
                        await socket.send_json({
                            "status": "error",
                            "message": "No image data received"
                        })
                        continue
                    
                    if not regions_data:
                        await socket.send_json({
                            "status": "error",
                            "message": "No regions found. Send metadata with regions first."
                        })
                        continue
                    
                    logfire.info(
                        "Received image data for polygons",
                        size=len(message),
                        regions_count=len(regions_data),
                        client=client_info
                    )
                    
                    # Сбрасываем флаги
                    waiting_for_image = False
                    current_regions = regions_data
                    regions_data = None
                    
                    # Получаем ProcessPolygonsAction через REQUEST scope
                    async with socket.app.state.di_container() as request_container:
                        process_polygons_action = await request_container.get(ProcessPolygonsAction)
                        
                        try:
                            with logfire.span("websocket_ocr_process_polygons"):
                                # Отправляем статус начала обработки
                                await socket.send_json({
                                    "status": "processing",
                                    "message": f"Processing {len(current_regions)} polygon regions..."
                                })
                                
                                result = await process_polygons_action.run(message, current_regions)
                                
                                # Конвертируем результат в словарь для JSON
                                result_dict = {
                                    "results": [
                                        {
                                            "region_id": r.region_id,
                                            "text": r.text,
                                            "confidence": r.confidence,
                                            "processing_time": r.processing_time,
                                            "polygon_coordinates": r.polygon_coordinates
                                        }
                                        for r in result.results
                                    ],
                                    "total_regions": result.total_regions,
                                    "image_dimensions": result.image_dimensions,
                                    "processing_time": result.processing_time,
                                    "timestamp": result.timestamp.isoformat()
                                }
                                
                                logfire.info(
                                    "Polygons processed successfully via WebSocket",
                                    regions_processed=result.total_regions,
                                    processing_time=result.processing_time,
                                    client=client_info
                                )
                                
                                await socket.send_json({
                                    "status": "success",
                                    "data": result_dict
                                })
                        
                        except InvalidImageFormatException as e:
                            logfire.error("Invalid image format", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": f"Invalid image format: {str(e)}"
                            })
                        
                        except ImageTooLargeException as e:
                            logfire.error("Image too large", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": str(e)
                            })
                        
                        except InvalidPolygonException as e:
                            logfire.error("Invalid polygon", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": f"Invalid polygon: {str(e)}"
                            })
                        
                        except OCRException as e:
                            logfire.error("OCR processing failed", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": f"OCR processing failed: {str(e)}"
                            })
                
                else:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Unsupported data type: {type(message).__name__}"
                    })
                    
            except WebSocketDisconnect:
                logfire.info("OCR Polygons WebSocket disconnected by client", client=client_info)
                break
            except Exception as e:
                logfire.error("OCR Polygons WebSocket communication error", error=str(e), client=client_info)
                try:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Communication error: {str(e)}"
                    })
                except:
                    pass
                break
    
    except WebSocketDisconnect:
        logfire.info("OCR Polygons WebSocket connection closed by client", client=client_info)
    except Exception as e:
        logfire.error("OCR Polygons WebSocket connection error", error=str(e), client=client_info)
    finally:
        logfire.info("OCR Polygons WebSocket connection closed", client=client_info)


# Экспортируем handlers для регистрации в приложении
OCRTestWebSocketListener = test_websocket_handler
OCRProcessImageWebSocketListener = process_image_websocket_handler
OCRProcessPolygonsWebSocketListener = process_polygons_websocket_handler
