"""
Streaming Process Full Image Action

Action для потоковой обработки полного изображения с OCR и переводом.
Один Action = Один Use Case (streaming вариант).
"""

from typing import Tuple, Callable, Awaitable, Dict, Any
import logfire

from src.Ship.Parents.Action import Action
from ..Tasks.StreamingProcessAndTranslateTask import StreamingProcessAndTranslateTask
from ..Data.DocsTranslateSchemas import (
    StreamingProcessAndTranslateImageRequest,
    ProcessAndTranslateImageResponse,
    ProgressEventType,
)


class StreamingProcessFullImageAction(Action[
    Tuple[bytes, StreamingProcessAndTranslateImageRequest, Callable[[ProgressEventType, Dict[str, Any]], Awaitable[None]]], 
    ProcessAndTranslateImageResponse
]):
    """
    Action для потоковой обработки полного изображения с OCR и переводом.
    
    Use Case: Пользователь загружает изображение → получает распознанный 
    и переведенный текст в потоковом режиме с промежуточными результатами.
    
    Проверка лицензии выполняется автоматически в базовом классе Action.
    """
    
    def __init__(self, streaming_task: StreamingProcessAndTranslateTask):
        """
        Инициализация Action.
        
        Args:
            streaming_task: Task для потоковой обработки изображения с переводом
        """
        self.streaming_task = streaming_task
    
    async def run(
        self, 
        data: Tuple[bytes, StreamingProcessAndTranslateImageRequest, Callable[[ProgressEventType, Dict[str, Any]], Awaitable[None]]]
    ) -> ProcessAndTranslateImageResponse:
        """
        Выполнить потоковую обработку полного изображения с OCR и переводом.
        
        Args:
            data: Кортеж (байты изображения, параметры обработки, progress callback)
            
        Returns:
            ProcessAndTranslateImageResponse: Финальный результат с переводами
        """
        image_data, request, progress_callback = data
        
        with logfire.span(
            "streaming_process_document_full_image",
            from_lang=request.from_language.value,
            to_lang=request.to_language.value,
            image_size=len(image_data)
        ):
            # Бизнес-логика: валидация параметров
            await self._validate_streaming_request(request)
            
            # Делегируем выполнение Task
            result = await self.streaming_task.run_streaming(
                image_data, 
                request, 
                progress_callback
            )
            
            # Бизнес-логика: дополнительная обработка результатов
            await self._post_process_results(result)
            
            logfire.info(
                "Streaming document full image processing completed",
                translated_regions=result.translated_regions,
                total_time=result.total_processing_time
            )
            
            return result
    
    # Приватные методы для бизнес-логики
    async def _validate_streaming_request(self, request: StreamingProcessAndTranslateImageRequest):
        """Валидация параметров streaming обработки."""
        logfire.debug(
            "Validating streaming processing request",
            from_lang=request.from_language.value,
            to_lang=request.to_language.value
        )
        
        # Дополнительная бизнес-валидация при необходимости
        # Например: проверка доступности языковых пар и т.д.
        # Примечание: количество воркеров зафиксировано (OCR=1, Translation=2)
    
    async def _post_process_results(self, result: ProcessAndTranslateImageResponse):
        """Дополнительная обработка результатов."""
        logfire.debug(
            "Post-processing streaming results",
            translated_regions=result.translated_regions,
            skipped_regions=result.skipped_regions
        )


__all__ = ["StreamingProcessFullImageAction"]


