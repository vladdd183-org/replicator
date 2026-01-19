"""
Process Full Image Action

Action для обработки полного изображения с OCR и переводом.
Один Action = Один Use Case.
"""

from typing import Tuple
import logfire

from src.Ship.Parents.Action import Action
from ..Tasks.ProcessAndTranslateImageTask import ProcessAndTranslateImageTask
from ..Data.DocsTranslateSchemas import (
    ProcessAndTranslateImageRequest,
    ProcessAndTranslateImageResponse,
)


class ProcessFullImageAction(Action[Tuple[bytes, ProcessAndTranslateImageRequest], ProcessAndTranslateImageResponse]):
    """
    Action для обработки полного изображения с OCR и переводом.
    
    Use Case: Пользователь загружает изображение → получает распознанный и переведенный текст.
    
    Проверка лицензии выполняется автоматически в базовом классе Action.
    """
    
    def __init__(self, process_image_task: ProcessAndTranslateImageTask):
        """
        Инициализация Action.
        
        Args:
            process_image_task: Task для обработки изображения с переводом
        """
        self.process_image_task = process_image_task
    
    async def run(
        self, 
        data: Tuple[bytes, ProcessAndTranslateImageRequest]
    ) -> ProcessAndTranslateImageResponse:
        """
        Выполнить обработку полного изображения с OCR и переводом.
        
        Args:
            data: Кортеж (байты изображения, параметры обработки)
            
        Returns:
            ProcessAndTranslateImageResponse: Результат с переводами
        """
        image_data, request = data
        
        with logfire.span(
            "process_document_full_image",
            from_lang=request.from_language.value,
            to_lang=request.to_language.value,
            image_size=len(image_data)
        ):
            # Бизнес-логика: валидация параметров
            await self._validate_processing_request(request.from_language, request.to_language)
            
            # Делегируем выполнение Task
            result = await self.process_image_task.run(image_data, request)
            
            # Бизнес-логика: дополнительная обработка результатов
            await self._post_process_results(result)
            
            logfire.info(
                "Document full image processing completed",
                translated_regions=result.translated_regions,
                total_time=result.total_processing_time
            )
            
            return result
    
    # Приватные методы для бизнес-логики
    async def _validate_processing_request(self, from_language, to_language):
        """Валидация параметров обработки."""
        logfire.debug(
            "Validating processing request",
            from_lang=from_language.value,
            to_lang=to_language.value
        )
    
    async def _post_process_results(self, result):
        """Дополнительная обработка результатов."""
        logfire.debug(
            "Post-processing results",
            translated_regions=result.translated_regions,
            skipped_regions=result.skipped_regions
        )


__all__ = ["ProcessFullImageAction"]

