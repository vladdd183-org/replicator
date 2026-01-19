"""
Process And Translate Image Task

Атомарная задача для обработки изображения с OCR и последующим переводом.
"""

import time
from typing import List
import logfire

from src.Ship.Parents.Task import Task
from src.Containers.AppSection.OCR.Managers import OCRServerManager
from src.Containers.AppSection.Translation.Managers import TranslationServerManager
from src.Containers.AppSection.Translation.Data import SupportedLanguage

from ..Data.DocsTranslateSchemas import (
    ProcessAndTranslateImageRequest,
    ProcessAndTranslateImageResponse,
    TranslatedOCRResult,
)
from ..Exceptions.DocsTranslateExceptions import (
    OCRServiceUnavailableException,
    TranslationServiceUnavailableException,
    ProcessingFailedException,
    NoTextFoundException,
)


class ProcessAndTranslateImageTask(Task):
    """
    Task для обработки полного изображения с OCR и переводом.
    
    Выполняет:
    1. OCR распознавание всего изображения
    2. Перевод найденных текстов
    3. Объединение результатов
    
    Единая ответственность: обработка изображения с переводом.
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
    
    async def run(
        self, 
        image_data: bytes, 
        request: ProcessAndTranslateImageRequest
    ) -> ProcessAndTranslateImageResponse:
        """
        Выполнить обработку изображения с переводом.
        
        Args:
            image_data: Байты изображения
            request: Параметры обработки
            
        Returns:
            ProcessAndTranslateImageResponse: Результат с переводами
            
        Raises:
            OCRServiceUnavailableException: OCR сервис недоступен
            TranslationServiceUnavailableException: Translation сервис недоступен
            ProcessingFailedException: Ошибка при обработке
            NoTextFoundException: Текст не найден
        """
        start_time = time.time()
        
        with logfire.span(
            "process_and_translate_image_task",
            image_size=len(image_data),
            from_lang=request.from_language.value,
            to_lang=request.to_language.value
        ):
            try:
                # Этап 1: OCR обработка
                with logfire.span("ocr_processing"):
                    ocr_start = time.time()
                    ocr_result = await self.ocr_manager.process_full_image(image_data)
                    ocr_processing_time = time.time() - ocr_start
                    
                    logfire.info(
                        "OCR processing completed",
                        regions_found=len(ocr_result.results),
                        processing_time=ocr_processing_time
                    )
                
                if not ocr_result.results:
                    raise NoTextFoundException("No text regions found on image")
                
                # Этап 2: Фильтрация результатов по confidence
                filtered_results = [
                    result for result in ocr_result.results
                    if (result.confidence >= request.min_confidence_threshold and 
                        result.text.strip()) or request.translate_empty_results
                ]
                
                if not filtered_results:
                    raise NoTextFoundException(
                        f"No text regions meet confidence threshold {request.min_confidence_threshold}"
                    )
                
                logfire.info(
                    "Filtered OCR results",
                    total_regions=len(ocr_result.results),
                    filtered_regions=len(filtered_results),
                    threshold=request.min_confidence_threshold
                )
                
                # Этап 3: Перевод текстов
                with logfire.span("translation_processing"):
                    translation_start = time.time()
                    translated_results = await self._translate_ocr_results(
                        filtered_results,
                        request.from_language,
                        request.to_language
                    )
                    translation_processing_time = time.time() - translation_start
                    
                    logfire.info(
                        "Translation processing completed",
                        translated_regions=len(translated_results),
                        processing_time=translation_processing_time
                    )
                
                # Этап 4: Формирование ответа
                total_processing_time = time.time() - start_time
                
                response = ProcessAndTranslateImageResponse(
                    results=translated_results,
                    total_regions=len(ocr_result.results),
                    translated_regions=len(translated_results),
                    skipped_regions=len(ocr_result.results) - len(translated_results),
                    image_dimensions=ocr_result.image_dimensions,
                    ocr_processing_time=ocr_processing_time,
                    translation_processing_time=translation_processing_time,
                    total_processing_time=total_processing_time,
                    from_language=request.from_language,
                    to_language=request.to_language
                )
                
                logfire.info(
                    "Process and translate image task completed",
                    total_regions=response.total_regions,
                    translated_regions=response.translated_regions,
                    total_time=total_processing_time
                )
                
                return response
                
            except Exception as e:
                if isinstance(e, (OCRServiceUnavailableException, 
                               TranslationServiceUnavailableException,
                               NoTextFoundException)):
                    raise
                
                logfire.error(
                    "Process and translate image task failed",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise ProcessingFailedException("image_processing", str(e))
    
    async def _translate_ocr_results(
        self,
        ocr_results: List,
        from_language: SupportedLanguage,
        to_language: SupportedLanguage
    ) -> List[TranslatedOCRResult]:
        """
        Перевести результаты OCR.
        
        Args:
            ocr_results: Результаты OCR
            from_language: Исходный язык
            to_language: Целевой язык
            
        Returns:
            List[TranslatedOCRResult]: Переведённые результаты
        """
        translated_results = []
        
        # Извлекаем тексты для пакетного перевода
        texts_to_translate = [result.text for result in ocr_results if result.text.strip()]
        
        if not texts_to_translate:
            logfire.error("No texts to translate after filtering")
            return []
        
        try:
            # Выполняем пакетный перевод
            batch_translation = await self.translation_manager.translate_batch(
                texts=texts_to_translate,
                from_language=from_language,
                to_language=to_language
            )
            
            # Объединяем результаты OCR с переводами
            translation_index = 0
            for ocr_result in ocr_results:
                if ocr_result.text.strip() and translation_index < len(batch_translation.translations):
                    translation = batch_translation.translations[translation_index]
                    
                    translated_result = TranslatedOCRResult(
                        original_text=ocr_result.text,
                        confidence=ocr_result.confidence,
                        coordinates=ocr_result.coordinates,
                        translated_text=translation.translated_text,
                        from_language=translation.from_language,
                        to_language=translation.to_language,
                        intermediate_language=translation.intermediate_language,
                        intermediate_text=translation.intermediate_text
                    )
                    
                    translated_results.append(translated_result)
                    translation_index += 1
            
            return translated_results
            
        except Exception as e:
            logfire.error(
                "Translation of OCR results failed",
                error=str(e),
                texts_count=len(texts_to_translate)
            )
            raise TranslationServiceUnavailableException(str(e))


__all__ = ["ProcessAndTranslateImageTask"]




