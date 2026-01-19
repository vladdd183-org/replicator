"""
Translation WebSocket Controllers

WebSocket handlers для операций перевода текста.
Используют функциональный подход с прямым управлением WebSocket соединением.
"""
import json
import time
from typing import Any, Dict, Union
import asyncio
import logfire
from litestar import WebSocket, websocket
from litestar.exceptions import WebSocketException, WebSocketDisconnect

from src.Containers.AppSection.Translation.Actions.TranslateAction import TranslateAction
from src.Containers.AppSection.Translation.Data.TranslationSchemas import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    TranslationStatus,
    SupportedLanguage,
)
from src.Containers.AppSection.Translation.Exceptions.TranslationExceptions import (
    TranslationException,
    TranslationServiceNotInitializedException,
    LanguagePackageNotInstalledException,
    UnsupportedLanguagePairException,
    EmptyTextException,
)


@websocket("/ws/translation/test")
async def test_websocket_handler(socket: WebSocket) -> None:
    """
    Тестовый WebSocket handler для диагностики соединений.
    
    Простой endpoint для проверки работы WebSocket без dependency injection.
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        
        logfire.info(
            "🔌 TRANSLATION TEST WebSocket: Connection accepted",
            client=client_info,
            path=socket.url.path,
            headers=dict(socket.headers) if socket.headers else {},
            query_params=dict(socket.query_params) if socket.query_params else {}
        )
        
        # Отправляем приветственное сообщение
        welcome_msg = {
            "status": "connected",
            "message": "Translation Test WebSocket connection established!",
            "client_info": client_info,
            "timestamp": time.time(),
            "service": "translation"
        }
        
        logfire.info("📤 TRANSLATION TEST WebSocket: Sending welcome message", message=welcome_msg)
        await socket.send_json(welcome_msg)
        logfire.info("✅ TRANSLATION TEST WebSocket: Welcome message sent successfully")
        
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
                    "📥 TRANSLATION TEST WebSocket: Message received",
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
                            "service": "translation"
                        }
                    except json.JSONDecodeError:
                        # Если не JSON, то просто текст
                        response = {
                            "status": "echo",
                            "received_text": message,
                            "timestamp": time.time(),
                            "client": client_info,
                            "service": "translation"
                        }
                elif isinstance(message, bytes):
                    response = {
                        "status": "echo",
                        "received_bytes_length": len(message),
                        "timestamp": time.time(),
                        "client": client_info,
                        "service": "translation"
                    }
                else:
                    response = {
                        "status": "echo",
                        "received_type": type(message).__name__,
                        "timestamp": time.time(),
                        "client": client_info,
                        "service": "translation"
                    }
                
                logfire.info("📤 TRANSLATION TEST WebSocket: Sending response", response=response)
                await socket.send_json(response)
                
            except WebSocketDisconnect:
                logfire.info("🔌 TRANSLATION TEST WebSocket: Client disconnected gracefully", client=client_info)
                break
                
            except Exception as e:
                logfire.error("❌ TRANSLATION TEST WebSocket: Error processing message", error=str(e), client=client_info)
                try:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Error processing message: {str(e)}",
                        "timestamp": time.time(),
                        "client": client_info,
                        "service": "translation"
                    })
                except:
                    break
    
    except WebSocketDisconnect:
        logfire.info("🔌 TRANSLATION TEST WebSocket: Connection closed during handshake", client=client_info)
    except Exception as e:
        logfire.error("❌ TRANSLATION TEST WebSocket: Connection error", error=str(e), client=client_info)
    finally:
        logfire.info("🔌 TRANSLATION TEST WebSocket: Connection cleanup completed", client=client_info)


@websocket("/ws/translation/translate")
async def translate_websocket_handler(
    socket: WebSocket
) -> None:
    """
    WebSocket handler для перевода одного текста.
    
    Протокол обмена:
    1. JSON запрос: {
        "action": "translate",
        "text": "Привет мир",
        "from_language": "ru",
        "to_language": "en"
    }
    2. Сервер отвечает с результатом перевода
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        logfire.info("Translation WebSocket connection established", client=client_info)
        
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
                
                # Обрабатываем JSON запрос
                if isinstance(message, str):
                    try:
                        message_data = json.loads(message)
                    except json.JSONDecodeError:
                        await socket.send_json({
                            "status": "error",
                            "message": "Invalid JSON format. Expected request object."
                        })
                        continue
                elif isinstance(message, dict):
                    # Litestar уже распарсил JSON в dict
                    message_data = message
                else:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Unsupported data type: {type(message).__name__}"
                    })
                    continue
                
                # Валидируем структуру запроса
                if not isinstance(message_data, dict):
                    await socket.send_json({
                        "status": "error",
                        "message": "Invalid message format. Expected JSON object."
                    })
                    continue
                
                action = message_data.get("action")
                if action != "translate":
                    await socket.send_json({
                        "status": "error",
                        "message": f"Invalid action: {action}. Expected 'translate'."
                    })
                    continue
                
                # Извлекаем параметры перевода
                text = message_data.get("text")
                from_language = message_data.get("from_language")
                to_language = message_data.get("to_language")
                
                if not text:
                    await socket.send_json({
                        "status": "error",
                        "message": "Text is required for translation"
                    })
                    continue
                
                if not from_language or not to_language:
                    await socket.send_json({
                        "status": "error",
                        "message": "Both from_language and to_language are required"
                    })
                    continue
                
                # Создаём объект запроса
                try:
                    translation_request = TranslationRequest(
                        text=text,
                        from_language=SupportedLanguage(from_language),
                        to_language=SupportedLanguage(to_language)
                    )
                except ValueError as e:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Invalid language parameter: {str(e)}"
                    })
                    continue
                
                logfire.info(
                    "Received translation request",
                    text_length=len(text),
                    from_language=from_language,
                    to_language=to_language,
                    client=client_info
                )
                
                # Получаем TranslateAction через REQUEST scope
                async with socket.app.state.di_container() as request_container:
                    translate_action = await request_container.get(TranslateAction)
                    
                    try:
                        with logfire.span("websocket_translation_translate"):
                            # Отправляем статус начала обработки
                            await socket.send_json({
                                "status": "processing",
                                "message": "Translating text..."
                            })
                            
                            result = await translate_action.translate_text(translation_request)
                            
                            # Конвертируем результат в словарь для JSON
                            result_dict = {
                                "original_text": result.original_text,
                                "translated_text": result.translated_text,
                                "from_language": result.from_language.value,
                                "to_language": result.to_language.value,
                                "intermediate_language": result.intermediate_language.value if result.intermediate_language else None,
                                "intermediate_text": result.intermediate_text
                            }
                            
                            logfire.info(
                                "Translation completed successfully via WebSocket",
                                from_language=result.from_language.value,
                                to_language=result.to_language.value,
                                original_length=len(result.original_text),
                                translated_length=len(result.translated_text),
                                client=client_info
                            )
                            
                            await socket.send_json({
                                "status": "success",
                                "data": result_dict
                            })
                    
                    except EmptyTextException as e:
                        logfire.error("Empty text provided", error=str(e), client=client_info)
                        await socket.send_json({
                            "status": "error",
                            "message": f"Empty text cannot be translated: {str(e)}"
                        })
                    
                    except UnsupportedLanguagePairException as e:
                        logfire.error("Unsupported language pair", error=str(e), client=client_info)
                        await socket.send_json({
                            "status": "error",
                            "message": f"Unsupported language pair: {str(e)}"
                        })
                    
                    except TranslationServiceNotInitializedException as e:
                        logfire.error("Translation service not initialized", error=str(e), client=client_info)
                        await socket.send_json({
                            "status": "error",
                            "message": f"Translation service not available: {str(e)}"
                        })
                    
                    except LanguagePackageNotInstalledException as e:
                        logfire.error("Language package not installed", error=str(e), client=client_info)
                        await socket.send_json({
                            "status": "error",
                            "message": f"Language package not installed: {str(e)}"
                        })
                    
                    except TranslationException as e:
                        logfire.error("Translation failed", error=str(e), client=client_info)
                        await socket.send_json({
                            "status": "error",
                            "message": f"Translation failed: {str(e)}"
                        })
                    
            except WebSocketDisconnect:
                logfire.info("Translation WebSocket disconnected by client", client=client_info)
                break
            except Exception as e:
                logfire.error("Translation WebSocket communication error", error=str(e), client=client_info)
                try:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Communication error: {str(e)}"
                    })
                except:
                    pass
                break
    
    except WebSocketDisconnect:
        logfire.info("Translation WebSocket connection closed by client", client=client_info)
    except Exception as e:
        logfire.error("Translation WebSocket connection error", error=str(e), client=client_info)
    finally:
        logfire.info("Translation WebSocket connection closed", client=client_info)


@websocket("/ws/translation/batch")
async def batch_translate_websocket_handler(
    socket: WebSocket
) -> None:
    """
    WebSocket handler для пакетного перевода текстов.
    
    Протокол обмена:
    1. JSON запрос: {
        "action": "batch_translate",
        "texts": ["Привет", "Мир"],
        "from_language": "ru",
        "to_language": "en"
    }
    2. Сервер отвечает с результатом пакетного перевода
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        logfire.info("Batch Translation WebSocket connection established", client=client_info)
        
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
                
                # Обрабатываем JSON запрос
                if isinstance(message, str):
                    try:
                        message_data = json.loads(message)
                    except json.JSONDecodeError:
                        await socket.send_json({
                            "status": "error",
                            "message": "Invalid JSON format. Expected request object."
                        })
                        continue
                elif isinstance(message, dict):
                    # Litestar уже распарсил JSON в dict
                    message_data = message
                else:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Unsupported data type: {type(message).__name__}"
                    })
                    continue
                
                # Валидируем структуру запроса
                if not isinstance(message_data, dict):
                    await socket.send_json({
                        "status": "error",
                        "message": "Invalid message format. Expected JSON object."
                    })
                    continue
                
                action = message_data.get("action")
                if action != "batch_translate":
                    await socket.send_json({
                        "status": "error",
                        "message": f"Invalid action: {action}. Expected 'batch_translate'."
                    })
                    continue
                
                # Извлекаем параметры перевода
                texts = message_data.get("texts")
                from_language = message_data.get("from_language")
                to_language = message_data.get("to_language")
                
                if not texts or not isinstance(texts, list) or len(texts) == 0:
                    await socket.send_json({
                        "status": "error",
                        "message": "Texts must be a non-empty array"
                    })
                    continue
                
                if not from_language or not to_language:
                    await socket.send_json({
                        "status": "error",
                        "message": "Both from_language and to_language are required"
                    })
                    continue
                
                # Создаём объект запроса
                try:
                    batch_request = BatchTranslationRequest(
                        texts=texts,
                        from_language=SupportedLanguage(from_language),
                        to_language=SupportedLanguage(to_language)
                    )
                except ValueError as e:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Invalid language parameter: {str(e)}"
                    })
                    continue
                
                logfire.info(
                    "Received batch translation request",
                    texts_count=len(texts),
                    from_language=from_language,
                    to_language=to_language,
                    client=client_info
                )
                
                # Получаем TranslateAction через REQUEST scope
                async with socket.app.state.di_container() as request_container:
                    translate_action = await request_container.get(TranslateAction)
                    
                    try:
                        with logfire.span("websocket_translation_batch"):
                            # Отправляем статус начала обработки
                            await socket.send_json({
                                "status": "processing",
                                "message": f"Translating {len(texts)} texts..."
                            })
                            
                            result = await translate_action.translate_batch(batch_request)
                            
                            # Конвертируем результат в словарь для JSON
                            result_dict = {
                                "translations": [
                                    {
                                        "original_text": t.original_text,
                                        "translated_text": t.translated_text,
                                        "from_language": t.from_language.value,
                                        "to_language": t.to_language.value,
                                        "intermediate_language": t.intermediate_language.value if t.intermediate_language else None,
                                        "intermediate_text": t.intermediate_text
                                    }
                                    for t in result.translations
                                ],
                                "total_count": result.total_count
                            }
                            
                            logfire.info(
                                "Batch translation completed successfully via WebSocket",
                                from_language=from_language,
                                to_language=to_language,
                                texts_count=len(texts),
                                completed_count=result.total_count,
                                client=client_info
                            )
                            
                            await socket.send_json({
                                "status": "success",
                                "data": result_dict
                            })
                    
                    except UnsupportedLanguagePairException as e:
                        logfire.error("Unsupported language pair", error=str(e), client=client_info)
                        await socket.send_json({
                            "status": "error",
                            "message": f"Unsupported language pair: {str(e)}"
                        })
                    
                    except TranslationServiceNotInitializedException as e:
                        logfire.error("Translation service not initialized", error=str(e), client=client_info)
                        await socket.send_json({
                            "status": "error",
                            "message": f"Translation service not available: {str(e)}"
                        })
                    
                    except LanguagePackageNotInstalledException as e:
                        logfire.error("Language package not installed", error=str(e), client=client_info)
                        await socket.send_json({
                            "status": "error",
                            "message": f"Language package not installed: {str(e)}"
                        })
                    
                    except TranslationException as e:
                        logfire.error("Batch translation failed", error=str(e), client=client_info)
                        await socket.send_json({
                            "status": "error",
                            "message": f"Batch translation failed: {str(e)}"
                        })
                    
            except WebSocketDisconnect:
                logfire.info("Batch Translation WebSocket disconnected by client", client=client_info)
                break
            except Exception as e:
                logfire.error("Batch Translation WebSocket communication error", error=str(e), client=client_info)
                try:
                    await socket.send_json({
                        "status": "error",
                        "message": f"Communication error: {str(e)}"
                    })
                except:
                    pass
                break
    
    except WebSocketDisconnect:
        logfire.info("Batch Translation WebSocket connection closed by client", client=client_info)
    except Exception as e:
        logfire.error("Batch Translation WebSocket connection error", error=str(e), client=client_info)
    finally:
        logfire.info("Batch Translation WebSocket connection closed", client=client_info)


@websocket("/ws/translation/status")
async def status_websocket_handler(
    socket: WebSocket
) -> None:
    """
    WebSocket handler для получения статуса системы перевода.
    
    Простой endpoint без ожидания дополнительных данных - клиент подключается
    и сразу получает статус системы.
    """
    client_info = f"{socket.client.host}:{socket.client.port}" if socket.client else "unknown"
    
    try:
        await socket.accept()
        logfire.info("Translation Status WebSocket connection established", client=client_info)
        
        # Получаем TranslateAction через REQUEST scope
        async with socket.app.state.di_container() as request_container:
            translate_action = await request_container.get(TranslateAction)
            
            try:
                with logfire.span("websocket_translation_status"):
                    # Отправляем статус получения статуса
                    await socket.send_json({
                        "status": "checking",
                        "message": "Checking translation service status..."
                    })
                    
                    status = await translate_action.get_status()
                    
                    # Конвертируем результат в словарь для JSON
                    status_dict = {
                        "available_packages": [
                            {
                                "from_code": p.from_code,
                                "to_code": p.to_code,
                                "package_name": p.package_name,
                                "is_installed": p.is_installed
                            }
                            for p in status.available_packages
                        ],
                        "supported_routes": status.supported_routes
                    }
                    
                    logfire.info(
                        "Translation status retrieved via WebSocket",
                        packages_count=len(status.available_packages),
                        routes_count=len(status.supported_routes),
                        client=client_info
                    )
                    
                    await socket.send_json({
                        "status": "success",
                        "data": status_dict
                    })
            
            except TranslationServiceNotInitializedException as e:
                logfire.error("Translation service not initialized", error=str(e), client=client_info)
                await socket.send_json({
                    "status": "error",
                    "message": f"Translation service not available: {str(e)}"
                })
            
            except TranslationException as e:
                logfire.error("Translation status check failed", error=str(e), client=client_info)
                await socket.send_json({
                    "status": "error",
                    "message": f"Status check failed: {str(e)}"
                })
    
    except WebSocketDisconnect:
        logfire.info("Translation Status WebSocket connection closed by client", client=client_info)
    except Exception as e:
        logfire.error("Translation Status WebSocket connection error", error=str(e), client=client_info)
    finally:
        logfire.info("Translation Status WebSocket connection closed", client=client_info)


# Экспортируем handlers для регистрации в приложении
TranslationTestWebSocketListener = test_websocket_handler
TranslationWebSocketListener = translate_websocket_handler
BatchTranslationWebSocketListener = batch_translate_websocket_handler
TranslationStatusWebSocketListener = status_websocket_handler

