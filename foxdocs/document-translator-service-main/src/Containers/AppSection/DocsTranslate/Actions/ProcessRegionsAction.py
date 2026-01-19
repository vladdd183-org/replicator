"""
Process Regions Action

Action для обработки конкретных областей изображения с OCR и переводом.
Один Action = Один Use Case.
"""

from typing import Tuple
import logfire

from src.Ship.Parents.Action import Action
from ..Tasks.ProcessRegionsAndTranslateTask import ProcessRegionsAndTranslateTask
from ..Data.DocsTranslateSchemas import (
    ProcessRegionsAndTranslateRequest,
    ProcessRegionsAndTranslateResponse,
)


class ProcessRegionsAction(Action[Tuple[bytes, ProcessRegionsAndTranslateRequest], ProcessRegionsAndTranslateResponse]):
    """
    Action для обработки конкретных областей изображения с OCR и переводом.
    
    Use Case: Пользователь указывает области на изображении → получает распознанный и переведенный текст из этих областей.
    
    Проверка лицензии выполняется автоматически в базовом классе Action.
    """
    
    def __init__(self, process_regions_task: ProcessRegionsAndTranslateTask):
        """
        Инициализация Action.
        
        Args:
            process_regions_task: Task для обработки областей с переводом
        """
        self.process_regions_task = process_regions_task
    
    async def run(
        self, 
        data: Tuple[bytes, ProcessRegionsAndTranslateRequest]
    ) -> ProcessRegionsAndTranslateResponse:
        """
        Выполнить обработку конкретных областей с OCR и переводом.
        
        Args:
            data: Кортеж (байты изображения, параметры с областями)
            
        Returns:
            ProcessRegionsAndTranslateResponse: Результат с переводами по областям
        """
        image_data, request = data
        
        with logfire.span(
            "process_document_regions",
            from_lang=request.from_language.value,
            to_lang=request.to_language.value,
            regions_count=len(request.regions),
            image_size=len(image_data)
        ):
            # Бизнес-логика: валидация параметров
            await self._validate_processing_request(request.from_language, request.to_language)
            await self._validate_regions(request.regions)
            
            # Делегируем выполнение Task
            result = await self.process_regions_task.run(image_data, request)
            
            # Бизнес-логика: дополнительная обработка результатов
            await self._post_process_results(result)
            
            logfire.info(
                "Document regions processing completed",
                regions_processed=len(request.regions),
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
    
    async def _validate_regions(self, regions):
        """Валидация областей для обработки."""
        if not regions:
            raise ValueError("At least one region must be specified")
        
        for i, region in enumerate(regions):
            if len(region.points) < 3:
                raise ValueError(f"Region {i} must have at least 3 points")
        
        logfire.debug("Regions validated", regions_count=len(regions))
    
    async def _post_process_results(self, result):
        """Дополнительная обработка результатов."""
        logfire.debug(
            "Post-processing results",
            translated_regions=result.translated_regions,
            skipped_regions=result.skipped_regions
        )


__all__ = ["ProcessRegionsAction"]

