"""
Streaming Process Regions Action

Action для потоковой обработки заданных областей изображения с OCR и переводом.
Один Action = Один Use Case (streaming вариант).
"""

from typing import Tuple, Callable, Awaitable, Dict, Any
import logfire

from src.Ship.Parents.Action import Action
from ..Tasks.StreamingProcessRegionsAndTranslateTask import StreamingProcessRegionsAndTranslateTask
from ..Data.DocsTranslateSchemas import (
    StreamingProcessRegionsAndTranslateRequest,
    ProcessRegionsAndTranslateResponse,
    ProgressEventType,
)


class StreamingProcessRegionsAction(Action[
    Tuple[bytes, StreamingProcessRegionsAndTranslateRequest, Callable[[ProgressEventType, Dict[str, Any]], Awaitable[None]]], 
    ProcessRegionsAndTranslateResponse
]):
    """
    Action для потоковой обработки заданных областей изображения с OCR и переводом.
    
    Use Case: Пользователь загружает изображение с заданными областями → 
    получает распознанный и переведенный текст в потоковом режиме 
    с промежуточными результатами.
    
    Проверка лицензии выполняется автоматически в базовом классе Action.
    """
    
    def __init__(self, streaming_task: StreamingProcessRegionsAndTranslateTask):
        """
        Инициализация Action.
        
        Args:
            streaming_task: Task для потоковой обработки областей с переводом
        """
        self.streaming_task = streaming_task
    
    async def run(
        self, 
        data: Tuple[bytes, StreamingProcessRegionsAndTranslateRequest, Callable[[ProgressEventType, Dict[str, Any]], Awaitable[None]]]
    ) -> ProcessRegionsAndTranslateResponse:
        """
        Выполнить потоковую обработку заданных областей с OCR и переводом.
        
        Args:
            data: Кортеж (байты изображения, параметры с областями, progress callback)
            
        Returns:
            ProcessRegionsAndTranslateResponse: Финальный результат с переводами
        """
        image_data, request, progress_callback = data
        
        with logfire.span(
            "streaming_process_document_regions",
            from_lang=request.from_language.value,
            to_lang=request.to_language.value,
            image_size=len(image_data),
            regions_count=len(request.regions)
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
                "Streaming document regions processing completed",
                translated_regions=result.translated_regions,
                total_time=result.total_processing_time
            )
            
            return result
    
    # Приватные методы для бизнес-логики
    async def _validate_streaming_request(self, request: StreamingProcessRegionsAndTranslateRequest):
        """Валидация параметров streaming обработки."""
        logfire.debug(
            "Validating streaming regions processing request",
            from_lang=request.from_language.value,
            to_lang=request.to_language.value,
            regions_count=len(request.regions)
        )
        
        # Дополнительная бизнес-валидация
        if len(request.regions) == 0:
            raise ValueError("Regions list cannot be empty")
        
        # Примечание: количество воркеров зафиксировано (OCR=1, Translation=2)
    
    async def _post_process_results(self, result: ProcessRegionsAndTranslateResponse):
        """Дополнительная обработка результатов."""
        logfire.debug(
            "Post-processing streaming regions results",
            translated_regions=result.translated_regions,
            skipped_regions=result.skipped_regions
        )


__all__ = ["StreamingProcessRegionsAction"]


