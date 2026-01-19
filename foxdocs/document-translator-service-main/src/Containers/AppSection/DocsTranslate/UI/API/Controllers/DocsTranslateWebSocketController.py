"""
DocsTranslate WebSocket Controllers

WebSocket handlers для операций OCR + перевод с поддержкой отправки файлов.
Используют функциональный подход с прямым управлением WebSocket соединением.
"""
import json
import time
from typing import Any, Dict, Union
import asyncio
import logfire

from litestar import WebSocket, websocket
from litestar.exceptions import WebSocketException, WebSocketDisconnect

from src.Containers.AppSection.DocsTranslate.Actions import (
    ProcessFullImageAction,
    ProcessRegionsAction,
    GetStatusAction,
)
from src.Ship.Licensing import execute_with_license_check
from src.Containers.AppSection.DocsTranslate.Data import (
    ProcessAndTranslateImageRequest,
    ProcessAndTranslateImageResponse,
    ProcessRegionsAndTranslateRequest,
    ProcessRegionsAndTranslateResponse,
    DocsTranslateStatus,
)
from src.Containers.AppSection.Translation.Data import SupportedLanguage
from src.Containers.AppSection.OCR.Data import PolygonRegionSchema
from src.Containers.AppSection.DocsTranslate.Exceptions import DocsTranslateException
from src.Containers.AppSection.OCR.Exceptions import (
    InvalidImageFormatException,
    ImageTooLargeException,
    InvalidPolygonException,
)

@websocket("/ws/docs-translate/test")
async def test_websocket_handler(socket: WebSocket) -> None:
    """
    Тестовый WebSocket handler для диагностики соединений.
    
    Простой endpoint для проверки работы WebSocket без dependency injection.
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        
        logfire.info(
            "🔌 DOCS_TRANSLATE TEST WebSocket: Connection accepted",
            client=client_info,
            path=socket.url.path,
            headers=dict(socket.headers) if socket.headers else {},
            query_params=dict(socket.query_params) if socket.query_params else {}
        )
        
        # Отправляем приветственное сообщение
        welcome_msg = {
            "status": "connected",
            "message": "DocsTranslate Test WebSocket connection established!",
            "client_info": client_info,
            "timestamp": time.time(),
            "service": "docs_translate"
        }
        
        logfire.info("📤 DOCS_TRANSLATE TEST WebSocket: Sending welcome message", message=welcome_msg)
        await socket.send_json(welcome_msg)
        logfire.info("✅ DOCS_TRANSLATE TEST WebSocket: Welcome message sent successfully")
        
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
                    "📥 DOCS_TRANSLATE TEST WebSocket: Message received",
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
                            "client": client_info,
                            "service": "docs_translate"
                        }
                    except json.JSONDecodeError:
                        # Если не JSON, то просто текст
                        response = {
                            "status": "echo",
                            "received_text": message,
                            "timestamp": time.time(),
                            "client": client_info,
                            "service": "docs_translate"
                        }
                elif isinstance(message, bytes):
                    response = {
                        "status": "echo",
                        "received_bytes_length": len(message),
                        "timestamp": time.time(),
                        "client": client_info,
                        "service": "docs_translate"
                    }
                else:
                    response = {
                        "status": "echo",
                        "received_type": type(message).__name__,
                        "timestamp": time.time(),
                        "client": client_info,
                        "service": "docs_translate"
                    }
                
                logfire.info("📤 DOCS_TRANSLATE TEST WebSocket: Sending response", response=response)
                await socket.send_json(response)
                
            except WebSocketDisconnect:
                logfire.info("🔌 DOCS_TRANSLATE TEST WebSocket: Client disconnected gracefully", client=client_info)
                break
                
            except Exception as e:
                logfire.error("❌ DOCS_TRANSLATE TEST WebSocket: Error processing message", error=str(e), client=client_info)
                try:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Error processing message: {str(e)}",
                        "timestamp": time.time(),
                        "client": client_info,
                        "service": "docs_translate"
                    })
                except:
                    break
    
    except WebSocketDisconnect:
        logfire.info("🔌 DOCS_TRANSLATE TEST WebSocket: Connection closed during handshake", client=client_info)
    except Exception as e:
        logfire.error("❌ DOCS_TRANSLATE TEST WebSocket: Connection error", error=str(e), client=client_info)
    finally:
        logfire.info("🔌 DOCS_TRANSLATE TEST WebSocket: Connection cleanup completed", client=client_info)


@websocket("/ws/docs-translate/process")
async def process_image_websocket_handler(
    socket: WebSocket
) -> None:
    """
    WebSocket handler для распознавания и перевода текста на всём изображении.
    
    Протокол обмена:
    1. JSON метаданные: {
        "action": "process_image", 
        "filename": "image.jpg", 
        "size": 12345,
        "from_language": "chinese",
        "to_language": "russian",
        "translate_empty_results": false,
        "min_confidence_threshold": 0.1
    }
    2. Сервер отвечает: {"status": "ready", "message": "Send image data as binary"}
    3. Бинарные данные изображения
    4. Сервер отвечает с результатом OCR + перевод
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        logfire.info("DocsTranslate Process WebSocket connection established", client=client_info)
        
        waiting_for_image = False
        processing_request = None
        
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
                    
                    # Извлекаем параметры обработки
                    try:
                        from_language = SupportedLanguage(message_data.get("from_language", "chinese"))
                        to_language = SupportedLanguage(message_data.get("to_language", "russian"))
                        translate_empty_results = message_data.get("translate_empty_results", False)
                        min_confidence_threshold = message_data.get("min_confidence_threshold", 0.1)
                        
                        # Создаём объект запроса
                        processing_request = ProcessAndTranslateImageRequest(
                            from_language=from_language,
                            to_language=to_language,
                            translate_empty_results=translate_empty_results,
                            min_confidence_threshold=min_confidence_threshold
                        )
                    except ValueError as e:
                        await socket.send_json({
                            "status": "error",
                            "message": f"Invalid language parameter: {str(e)}"
                        })
                        continue
                    
                    logfire.info(
                        "Received DocsTranslate process image metadata",
                        filename=filename,
                        expected_size=expected_size,
                        from_language=from_language.value,
                        to_language=to_language.value,
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
                    
                    if not processing_request:
                        await socket.send_json({
                            "status": "error",
                            "message": "No processing parameters found. Send metadata first."
                        })
                        continue
                    
                    logfire.info(
                        "Received image data for DocsTranslate processing",
                        size=len(message),
                        client=client_info
                    )
                    
                    # Сбрасываем флаг ожидания
                    waiting_for_image = False
                    
                    # Получаем ProcessFullImageAction через REQUEST scope
                    async with socket.app.state.di_container() as request_container:
                        action = await request_container.get(ProcessFullImageAction)
                        
                        try:
                            with logfire.span("websocket_docs_translate_process_image"):
                                # Отправляем статус начала обработки
                                await socket.send_json({
                                    "status": "processing",
                                    "message": "Processing image with OCR and translation..."
                                })
                                
                                # Вызываем execute с автоматической обработкой ошибок лицензии
                                result = await execute_with_license_check(
                                    action, 
                                    (message, processing_request),
                                    socket
                                )
                                
                                # Конвертируем результат в словарь для JSON
                                result_dict = {
                                    "results": [
                                        {
                                            "original_text": r.original_text,
                                            "confidence": r.confidence,
                                            "coordinates": r.coordinates,
                                            "translated_text": r.translated_text,
                                            "from_language": r.from_language.value,
                                            "to_language": r.to_language.value,
                                            "intermediate_language": r.intermediate_language.value if r.intermediate_language else None,
                                            "intermediate_text": r.intermediate_text
                                        }
                                        for r in result.results
                                    ],
                                    "total_regions": result.total_regions,
                                    "translated_regions": result.translated_regions,
                                    "skipped_regions": result.skipped_regions,
                                    "image_dimensions": result.image_dimensions,
                                    "ocr_processing_time": result.ocr_processing_time,
                                    "translation_processing_time": result.translation_processing_time,
                                    "total_processing_time": result.total_processing_time,
                                    "from_language": result.from_language.value,
                                    "to_language": result.to_language.value,
                                    "timestamp": result.timestamp.isoformat()
                                }
                                
                                logfire.info(
                                    "DocsTranslate image processed successfully via WebSocket",
                                    regions_found=result.total_regions,
                                    translated_regions=result.translated_regions,
                                    total_time=result.total_processing_time,
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
                        
                        except DocsTranslateException as e:
                            logfire.error("Translation failed", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": f"Translation failed: {str(e)}"
                            })
                        
                        except DocsTranslateException as e:
                            logfire.error("DocsTranslate processing failed", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": f"DocsTranslate processing failed: {str(e)}"
                            })
                
                else:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Unsupported data type: {type(message).__name__}"
                    })
                    
            except WebSocketDisconnect:
                logfire.info("DocsTranslate Process WebSocket disconnected by client", client=client_info)
                break
            except Exception as e:
                logfire.error("DocsTranslate Process WebSocket communication error", error=str(e), client=client_info)
                try:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Communication error: {str(e)}"
                    })
                except:
                    pass
                break
    
    except WebSocketDisconnect:
        logfire.info("DocsTranslate Process WebSocket connection closed by client", client=client_info)
    except Exception as e:
        logfire.error("DocsTranslate Process WebSocket connection error", error=str(e), client=client_info)
    finally:
        logfire.info("DocsTranslate Process WebSocket connection closed", client=client_info)


@websocket("/ws/docs-translate/process-regions")
async def process_regions_websocket_handler(
    socket: WebSocket
) -> None:
    """
    WebSocket handler для распознавания и перевода текста в полигональных областях.
    
    Протокол обмена:
    1. JSON метаданные с регионами: {
        "action": "process_regions",
        "filename": "image.jpg", 
        "size": 12345,
        "regions": [{"points": [[x1,y1], [x2,y2], ...], "region_id": "..."}],
        "from_language": "chinese",
        "to_language": "russian",
        "translate_empty_results": false,
        "min_confidence_threshold": 0.1
    }
    2. Сервер отвечает: {"status": "ready", "message": "Send image data as binary"}
    3. Бинарные данные изображения
    4. Сервер отвечает с результатом OCR + перевод полигонов
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        logfire.info("DocsTranslate Regions WebSocket connection established", client=client_info)
        
        waiting_for_image = False
        processing_request = None
        
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
                    if action != "process_regions":
                        await socket.send_json({
                            "status": "error",
                            "message": f"Invalid action: {action}. Expected 'process_regions'."
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
                    
                    # Извлекаем параметры обработки
                    try:
                        from_language = SupportedLanguage(message_data.get("from_language", "chinese"))
                        to_language = SupportedLanguage(message_data.get("to_language", "russian"))
                        translate_empty_results = message_data.get("translate_empty_results", False)
                        min_confidence_threshold = message_data.get("min_confidence_threshold", 0.1)
                        
                        # Создаём объект запроса
                        processing_request = ProcessRegionsAndTranslateRequest(
                            regions=regions,
                            from_language=from_language,
                            to_language=to_language,
                            translate_empty_results=translate_empty_results,
                            min_confidence_threshold=min_confidence_threshold
                        )
                    except ValueError as e:
                        await socket.send_json({
                            "status": "error",
                            "message": f"Invalid language parameter: {str(e)}"
                        })
                        continue
                    
                    # Устанавливаем флаг ожидания изображения
                    waiting_for_image = True
                    
                    logfire.info(
                        "Received DocsTranslate process regions metadata",
                        filename=filename,
                        expected_size=expected_size,
                        regions_count=len(regions),
                        from_language=from_language.value,
                        to_language=to_language.value,
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
                    
                    if not processing_request:
                        await socket.send_json({
                            "status": "error",
                            "message": "No processing parameters found. Send metadata with regions first."
                        })
                        continue
                    
                    logfire.info(
                        "Received image data for DocsTranslate regions processing",
                        size=len(message),
                        regions_count=len(processing_request.regions),
                        client=client_info
                    )
                    
                    # Сбрасываем флаги
                    waiting_for_image = False
                    current_request = processing_request
                    processing_request = None
                    
                    # Получаем ProcessRegionsAction через REQUEST scope
                    async with socket.app.state.di_container() as request_container:
                        action = await request_container.get(ProcessRegionsAction)
                        
                        try:
                            with logfire.span("websocket_docs_translate_process_regions"):
                                # Отправляем статус начала обработки
                                await socket.send_json({
                                    "status": "processing",
                                    "message": f"Processing {len(current_request.regions)} regions with OCR and translation..."
                                })
                                
                                # Вызываем execute с автоматической обработкой ошибок лицензии
                                result = await execute_with_license_check(
                                    action,
                                    (message, current_request),
                                    socket
                                )
                                
                                # Конвертируем результат в словарь для JSON
                                result_dict = {
                                    "results": [
                                        {
                                            "original_text": r.original_text,
                                            "confidence": r.confidence,
                                            "coordinates": r.coordinates,
                                            "translated_text": r.translated_text,
                                            "from_language": r.from_language.value,
                                            "to_language": r.to_language.value,
                                            "intermediate_language": r.intermediate_language.value if r.intermediate_language else None,
                                            "intermediate_text": r.intermediate_text
                                        }
                                        for r in result.results
                                    ],
                                    "total_regions": result.total_regions,
                                    "translated_regions": result.translated_regions,
                                    "skipped_regions": result.skipped_regions,
                                    "image_dimensions": result.image_dimensions,
                                    "ocr_processing_time": result.ocr_processing_time,
                                    "translation_processing_time": result.translation_processing_time,
                                    "total_processing_time": result.total_processing_time,
                                    "from_language": result.from_language.value,
                                    "to_language": result.to_language.value,
                                    "timestamp": result.timestamp.isoformat()
                                }
                                
                                logfire.info(
                                    "DocsTranslate regions processed successfully via WebSocket",
                                    regions_processed=result.total_regions,
                                    translated_regions=result.translated_regions,
                                    total_time=result.total_processing_time,
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
                        
                        except DocsTranslateException as e:
                            logfire.error("Translation failed", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": f"Translation failed: {str(e)}"
                            })
                        
                        except DocsTranslateException as e:
                            logfire.error("DocsTranslate processing failed", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": f"DocsTranslate processing failed: {str(e)}"
                            })
                
                else:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Unsupported data type: {type(message).__name__}"
                    })
                    
            except WebSocketDisconnect:
                logfire.info("DocsTranslate Regions WebSocket disconnected by client", client=client_info)
                break
            except Exception as e:
                logfire.error("DocsTranslate Regions WebSocket communication error", error=str(e), client=client_info)
                try:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Communication error: {str(e)}"
                    })
                except:
                    pass
                break
    
    except WebSocketDisconnect:
        logfire.info("DocsTranslate Regions WebSocket connection closed by client", client=client_info)
    except Exception as e:
        logfire.error("DocsTranslate Regions WebSocket connection error", error=str(e), client=client_info)
    finally:
        logfire.info("DocsTranslate Regions WebSocket connection closed", client=client_info)


@websocket("/ws/docs-translate/status")
async def status_websocket_handler(
    socket: WebSocket
) -> None:
    """
    WebSocket handler для получения статуса сервиса DocsTranslate.
    
    Простой endpoint без ожидания изображения - клиент подключается
    и сразу получает статус сервиса.
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        logfire.info("DocsTranslate Status WebSocket connection established", client=client_info)
        
        # Получаем GetStatusAction через REQUEST scope
        async with socket.app.state.di_container() as request_container:
            action = await request_container.get(GetStatusAction)
            
            try:
                with logfire.span("websocket_docs_translate_status"):
                    # Отправляем статус получения статуса
                    await socket.send_json({
                        "status": "checking",
                        "message": "Checking DocsTranslate service status..."
                    })
                    
                    # Вызываем execute (для GetStatusAction лицензия не проверяется: require_license = False)
                    status = await execute_with_license_check(action, None, socket)
                    
                    # Конвертируем результат в словарь для JSON
                    status_dict = {
                        "ocr_available": status.ocr_available,
                        "translation_available": status.translation_available,
                        "supported_ocr_formats": status.supported_ocr_formats,
                        "supported_language_pairs": status.supported_language_pairs,
                        "service_ready": status.service_ready,
                        "ocr_engine_info": status.ocr_engine_info,
                        "translation_status": status.translation_status
                    }
                    
                    logfire.info(
                        "DocsTranslate status retrieved via WebSocket",
                        service_ready=status.service_ready,
                        ocr_available=status.ocr_available,
                        translation_available=status.translation_available,
                        client=client_info
                    )
                    
                    await socket.send_json({
                        "status": "success",
                        "data": status_dict
                    })
            
            except DocsTranslateException as e:
                logfire.error("DocsTranslate status check failed", error=str(e), client=client_info)
                await socket.send_json({
                    "status": "error",
                    "message": f"Status check failed: {str(e)}"
                })
    
    except WebSocketDisconnect:
        logfire.info("DocsTranslate Status WebSocket connection closed by client", client=client_info)
    except Exception as e:
        logfire.error("DocsTranslate Status WebSocket connection error", error=str(e), client=client_info)
    finally:
        logfire.info("DocsTranslate Status WebSocket connection closed", client=client_info)


@websocket("/ws/docs-translate/process-streaming")
async def process_image_streaming_websocket_handler(
    socket: WebSocket
) -> None:
    """
    WebSocket handler для ПОТОКОВОЙ обработки изображения с OCR и переводом.
    
    Протокол обмена:
    1. JSON метаданные: {
        "action": "process_image_streaming", 
        "filename": "image.jpg", 
        "size": 12345,
        "from_language": "chinese",
        "to_language": "russian",
        "translate_empty_results": false,
        "min_confidence_threshold": 0.1,
        "streaming_config": {
            "ocr_workers": 2,
            "translation_workers": 2,
            "send_region_preview": true
        }
    }
    2. Сервер отвечает: {"status": "ready", "message": "Send image data as binary"}
    3. Бинарные данные изображения
    4. Сервер отправляет ПОТОК прогресса:
       - {"type": "progress", "event_type": "regions_detected", "data": {...}}
       - {"type": "progress", "event_type": "region_ocr_completed", "data": {...}}
       - {"type": "progress", "event_type": "region_translated", "data": {...}}
       - {"type": "completed", "message": "Processing completed"}
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        logfire.info("DocsTranslate Process STREAMING WebSocket connection established", client=client_info)
        
        waiting_for_image = False
        processing_request = None
        
        while True:
            try:
                # Получаем сообщение
                raw_message = await socket.receive()
                
                # Извлекаем данные из WebSocket message
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
                
                # Обработка метаданных (JSON)
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
                    message_data = message
                else:
                    if not isinstance(message, bytes):
                        await socket.send_json({
                            "status": "error",
                            "message": f"Unsupported data type: {type(message).__name__}"
                        })
                        continue
                    message_data = None
                
                # Обработка метаданных
                if message_data is not None:
                    if not isinstance(message_data, dict):
                        await socket.send_json({
                            "status": "error",
                            "message": "Invalid message format. Expected JSON object."
                        })
                        continue
                    
                    action = message_data.get("action")
                    if action != "process_image_streaming":
                        await socket.send_json({
                            "status": "error",
                            "message": f"Invalid action: {action}. Expected 'process_image_streaming'."
                        })
                        continue
                    
                    filename = message_data.get("filename", "unknown.jpg")
                    expected_size = message_data.get("size", 0)
                    
                    # Извлекаем параметры обработки
                    try:
                        from_language = SupportedLanguage(message_data.get("from_language", "chinese"))
                        to_language = SupportedLanguage(message_data.get("to_language", "russian"))
                        translate_empty_results = message_data.get("translate_empty_results", False)
                        min_confidence_threshold = message_data.get("min_confidence_threshold", 0.1)
                        
                        # Извлекаем streaming config
                        from src.Containers.AppSection.DocsTranslate.Data import StreamingConfig, StreamingProcessAndTranslateImageRequest
                        
                        streaming_config_data = message_data.get("streaming_config", {})
                        streaming_config = StreamingConfig(
                            send_region_preview=streaming_config_data.get("send_region_preview", True)
                        )
                        
                        # Создаём объект запроса
                        processing_request = StreamingProcessAndTranslateImageRequest(
                            from_language=from_language,
                            to_language=to_language,
                            translate_empty_results=translate_empty_results,
                            min_confidence_threshold=min_confidence_threshold,
                            streaming_config=streaming_config
                        )
                    except ValueError as e:
                        await socket.send_json({
                            "status": "error",
                            "message": f"Invalid parameter: {str(e)}"
                        })
                        continue
                    
                    logfire.info(
                        "Received DocsTranslate STREAMING process image metadata",
                        filename=filename,
                        expected_size=expected_size,
                        from_language=from_language.value,
                        to_language=to_language.value,
                        client=client_info
                    )
                    
                    # Устанавливаем флаг ожидания изображения
                    waiting_for_image = True
                    
                    await socket.send_json({
                        "status": "ready",
                        "message": "Send image data as binary"
                    })
                
                # Обработка изображения (bytes)
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
                    
                    if not processing_request:
                        await socket.send_json({
                            "status": "error",
                            "message": "No processing parameters found. Send metadata first."
                        })
                        continue
                    
                    logfire.info(
                        "Received image data for DocsTranslate STREAMING processing",
                        size=len(message),
                        client=client_info
                    )
                    
                    # Сбрасываем флаг ожидания
                    waiting_for_image = False
                    
                    # Получаем StreamingProcessFullImageAction через REQUEST scope
                    async with socket.app.state.di_container() as request_container:
                        from src.Containers.AppSection.DocsTranslate.Actions import StreamingProcessFullImageAction
                        action = await request_container.get(StreamingProcessFullImageAction)
                        
                        try:
                            with logfire.span("websocket_docs_translate_process_image_streaming"):
                                # Отправляем статус начала обработки
                                await socket.send_json({
                                    "status": "processing",
                                    "message": "Starting streaming processing with OCR and translation..."
                                })
                                
                                # Создаём progress callback
                                async def send_progress(event_type, event_data):
                                    """Отправляем промежуточные результаты клиенту."""
                                    try:
                                        # Конвертируем event_type в строку
                                        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
                                        
                                        await socket.send_json({
                                            "type": "progress",
                                            "event_type": event_type_str,
                                            "data": event_data
                                        })
                                    except Exception as e:
                                        logfire.error(
                                            "Failed to send progress event",
                                            event_type=str(event_type),
                                            error=str(e),
                                            error_type=type(e).__name__,
                                            client=client_info
                                        )
                                        # Пробрасываем ClientDisconnected исключения
                                        from litestar.exceptions import WebSocketDisconnect
                                        if isinstance(e, (WebSocketDisconnect, ConnectionError)):
                                            raise
                                
                                # Вызываем streaming action
                                result = await execute_with_license_check(
                                    action, 
                                    (message, processing_request, send_progress),
                                    socket
                                )
                                
                                logfire.info(
                                    "DocsTranslate STREAMING image processed successfully",
                                    regions_found=result.total_regions,
                                    translated_regions=result.translated_regions,
                                    total_time=result.total_processing_time,
                                    client=client_info
                                )
                                
                                await socket.send_json({
                                    "type": "completed",
                                    "message": "Streaming processing completed successfully",
                                    "summary": {
                                        "total_regions": result.total_regions,
                                        "translated_regions": result.translated_regions,
                                        "total_processing_time": result.total_processing_time
                                    }
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
                        
                        except DocsTranslateException as e:
                            logfire.error("Streaming processing failed", error=str(e), client=client_info)
                            await socket.send_json({
                                "status": "error",
                                "message": f"Processing failed: {str(e)}"
                            })
                
                else:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Unsupported data type: {type(message).__name__}"
                    })
                    
            except WebSocketDisconnect:
                logfire.info("DocsTranslate Process STREAMING WebSocket disconnected by client", client=client_info)
                break
            except Exception as e:
                logfire.error("DocsTranslate Process STREAMING WebSocket communication error", error=str(e), client=client_info)
                try:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Communication error: {str(e)}"
                    })
                except:
                    pass
                break
    
    except WebSocketDisconnect:
        logfire.info("DocsTranslate Process STREAMING WebSocket connection closed by client", client=client_info)
    except Exception as e:
        logfire.error("DocsTranslate Process STREAMING WebSocket connection error", error=str(e), client=client_info)
    finally:
        logfire.info("DocsTranslate Process STREAMING WebSocket connection closed", client=client_info)


@websocket("/ws/docs-translate/process-regions-streaming")
async def process_regions_streaming_websocket_handler(
    socket: WebSocket
) -> None:
    """
    WebSocket handler для ПОТОКОВОЙ обработки заданных областей с OCR и переводом.
    
    Аналогичен process-regions, но отправляет промежуточные результаты по мере готовности.
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        logfire.info("DocsTranslate Regions STREAMING WebSocket connection established", client=client_info)
        
        waiting_for_image = False
        processing_request = None
        
        while True:
            try:
                raw_message = await socket.receive()
                
                if isinstance(raw_message, dict):
                    if raw_message.get('type') == 'websocket.receive':
                        message = raw_message.get('text') or raw_message.get('bytes', raw_message)
                    elif raw_message.get('type') == 'websocket.disconnect':
                        break
                    else:
                        message = raw_message
                else:
                    message = raw_message
                
                # Обработка метаданных
                if isinstance(message, str):
                    try:
                        message_data = json.loads(message)
                    except json.JSONDecodeError:
                        await socket.send_json({"status": "error", "message": "Invalid JSON"})
                        continue
                elif isinstance(message, dict):
                    message_data = message
                else:
                    if not isinstance(message, bytes):
                        await socket.send_json({"status": "error", "message": f"Unsupported type: {type(message).__name__}"})
                        continue
                    message_data = None
                
                if message_data is not None:
                    action = message_data.get("action")
                    if action != "process_regions_streaming":
                        await socket.send_json({"status": "error", "message": f"Invalid action: {action}"})
                        continue
                    
                    regions_list = message_data.get("regions", [])
                    if not regions_list:
                        await socket.send_json({"status": "error", "message": "Regions required"})
                        continue
                    
                    try:
                        from_language = SupportedLanguage(message_data.get("from_language", "chinese"))
                        to_language = SupportedLanguage(message_data.get("to_language", "russian"))
                        
                        # Создаём схемы регионов
                        regions = [PolygonRegionSchema(**r) for r in regions_list]
                        
                        from src.Containers.AppSection.DocsTranslate.Data import StreamingConfig, StreamingProcessRegionsAndTranslateRequest
                        
                        streaming_config_data = message_data.get("streaming_config", {})
                        streaming_config = StreamingConfig(
                            send_region_preview=streaming_config_data.get("send_region_preview", True)
                        )
                        
                        processing_request = StreamingProcessRegionsAndTranslateRequest(
                            regions=regions,
                            from_language=from_language,
                            to_language=to_language,
                            translate_empty_results=message_data.get("translate_empty_results", False),
                            min_confidence_threshold=message_data.get("min_confidence_threshold", 0.1),
                            streaming_config=streaming_config
                        )
                    except Exception as e:
                        await socket.send_json({"status": "error", "message": f"Invalid parameters: {str(e)}"})
                        continue
                    
                    waiting_for_image = True
                    await socket.send_json({"status": "ready", "message": "Send image data"})
                
                elif isinstance(message, bytes):
                    if not waiting_for_image or not processing_request:
                        await socket.send_json({"status": "error", "message": "Send metadata first"})
                        continue
                    
                    waiting_for_image = False
                    
                    async with socket.app.state.di_container() as request_container:
                        from src.Containers.AppSection.DocsTranslate.Actions import StreamingProcessRegionsAction
                        action = await request_container.get(StreamingProcessRegionsAction)
                        
                        try:
                            await socket.send_json({"status": "processing", "message": "Starting streaming regions processing..."})
                            
                            async def send_progress(event_type, event_data):
                                """Отправляем промежуточные результаты клиенту."""
                                try:
                                    # Конвертируем event_type в строку
                                    event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
                                    
                                    await socket.send_json({
                                        "type": "progress",
                                        "event_type": event_type_str,
                                        "data": event_data
                                    })
                                except Exception as e:
                                    logfire.error(
                                        "Failed to send progress event",
                                        event_type=str(event_type),
                                        error=str(e),
                                        error_type=type(e).__name__,
                                        client=client_info
                                    )
                                    # Пробрасываем ClientDisconnected исключения
                                    from litestar.exceptions import WebSocketDisconnect
                                    if isinstance(e, (WebSocketDisconnect, ConnectionError)):
                                        raise
                            
                            result = await execute_with_license_check(
                                action, 
                                (message, processing_request, send_progress),
                                socket
                            )
                            
                            await socket.send_json({
                                "type": "completed",
                                "message": "Streaming regions processing completed",
                                "summary": {
                                    "total_regions": result.total_regions,
                                    "translated_regions": result.translated_regions,
                                    "total_processing_time": result.total_processing_time
                                }
                            })
                        
                        except DocsTranslateException as e:
                            logfire.error("Streaming regions processing failed", error=str(e), client=client_info)
                            await socket.send_json({"status": "error", "message": f"Processing failed: {str(e)}"})
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logfire.error("Streaming regions WebSocket error", error=str(e), client=client_info)
                try:
                    await socket.send_json({"status": "error", "message": f"Error: {str(e)}"})
                except:
                    pass
                break
    
    except WebSocketDisconnect:
        logfire.info("Streaming regions WebSocket closed by client", client=client_info)
    except Exception as e:
        logfire.error("Streaming regions WebSocket error", error=str(e), client=client_info)
    finally:
        logfire.info("Streaming regions WebSocket closed", client=client_info)


# Экспортируем handlers для регистрации в приложении
DocsTranslateTestWebSocketListener = test_websocket_handler
DocsTranslateProcessImageWebSocketListener = process_image_websocket_handler
DocsTranslateProcessRegionsWebSocketListener = process_regions_websocket_handler
DocsTranslateStatusWebSocketListener = status_websocket_handler
DocsTranslateProcessImageStreamingWebSocketListener = process_image_streaming_websocket_handler
DocsTranslateProcessRegionsStreamingWebSocketListener = process_regions_streaming_websocket_handler
