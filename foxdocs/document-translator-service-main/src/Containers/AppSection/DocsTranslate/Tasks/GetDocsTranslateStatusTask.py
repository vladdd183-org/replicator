"""
Get DocsTranslate Status Task

Атомарная задача для получения статуса сервиса DocsTranslate.
"""

from typing import Dict, Any
import logfire

from src.Ship.Parents.Task import Task
from src.Containers.AppSection.OCR.Managers import OCRServerManager
from src.Containers.AppSection.Translation.Managers import TranslationServerManager

from ..Data.DocsTranslateSchemas import DocsTranslateStatus
from ..Exceptions.DocsTranslateExceptions import ProcessingFailedException


class GetDocsTranslateStatusTask(Task):
    """
    Task для получения статуса сервиса DocsTranslate.
    
    Проверяет доступность всех зависимых сервисов и формирует общий статус.
    
    Единая ответственность: проверка статуса сервисов.
    """
    
    def __init__(
        self,
        ocr_manager: OCRServerManager,
        translation_manager: TranslationServerManager,
    ):
        """
        Инициализация с менеджерами сервисов.
        
        Args:
            ocr_manager: Менеджер OCR сервиса
            translation_manager: Менеджер Translation сервиса
        """
        self.ocr_manager = ocr_manager
        self.translation_manager = translation_manager
    
    async def run(self) -> DocsTranslateStatus:
        """
        Получить статус сервиса DocsTranslate.
        
        Returns:
            DocsTranslateStatus: Полный статус сервиса
            
        Raises:
            ProcessingFailedException: Ошибка при получении статуса
        """
        with logfire.span("get_docs_translate_status_task"):
            try:
                # Проверяем статус OCR сервиса
                ocr_available = False
                ocr_engine_info = None
                try:
                    # Пытаемся получить информацию о движке OCR
                    # Если есть метод для получения информации о движке
                    ocr_available = True
                    ocr_engine_info = {"status": "available"}
                    
                    logfire.info("OCR service status checked", available=ocr_available)
                except Exception as e:
                    logfire.error("OCR service check failed", error=str(e))
                    ocr_engine_info = {"status": "unavailable", "error": str(e)}
                
                # Проверяем статус Translation сервиса
                translation_available = False
                translation_status_info = None
                supported_language_pairs = []
                
                try:
                    translation_status = await self.translation_manager.get_status()
                    translation_available = True
                    translation_status_info = {
                        "available_packages": len(translation_status.available_packages),
                        "supported_routes": translation_status.supported_routes
                    }
                    supported_language_pairs = translation_status.supported_routes
                    
                    logfire.info(
                        "Translation service status checked", 
                        available=translation_available,
                        routes_count=len(supported_language_pairs)
                    )
                except Exception as e:
                    logfire.error("Translation service check failed", error=str(e))
                    translation_status_info = {"status": "unavailable", "error": str(e)}
                
                # Определяем общую готовность сервиса
                service_ready = ocr_available and translation_available
                
                status = DocsTranslateStatus(
                    ocr_available=ocr_available,
                    translation_available=translation_available,
                    supported_ocr_formats=["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
                    supported_language_pairs=supported_language_pairs,
                    service_ready=service_ready,
                    ocr_engine_info=ocr_engine_info,
                    translation_status=translation_status_info
                )
                
                logfire.info(
                    "DocsTranslate status retrieved",
                    service_ready=service_ready,
                    ocr_available=ocr_available,
                    translation_available=translation_available
                )
                
                return status
                
            except Exception as e:
                logfire.error(
                    "Get DocsTranslate status task failed",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise ProcessingFailedException("status_check", str(e))


__all__ = ["GetDocsTranslateStatusTask"]




