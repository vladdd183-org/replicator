"""
Process Document Action

Главный Action для обработки документов с OCR и переводом.
Оркестрирует весь процесс от изображения до переведённого текста.
"""

from typing import Union
import logfire

from src.Ship.Parents.Action import Action
from ..Tasks.ProcessAndTranslateImageTask import ProcessAndTranslateImageTask
from ..Tasks.ProcessRegionsAndTranslateTask import ProcessRegionsAndTranslateTask
from ..Tasks.GetDocsTranslateStatusTask import GetDocsTranslateStatusTask
from ..Data.DocsTranslateSchemas import (
    ProcessAndTranslateImageRequest,
    ProcessAndTranslateImageResponse,
    ProcessRegionsAndTranslateRequest,
    ProcessRegionsAndTranslateResponse,
    DocsTranslateStatus,
)


class ProcessDocumentAction(Action):
    """
    Action для обработки документов с OCR и переводом.
    
    Координирует выполнение различных операций обработки документов:
    - Полная обработка изображения с переводом
    - Обработка конкретных областей с переводом
    - Получение статуса сервиса
    
    Содержит бизнес-логику выбора стратегии обработки.
    """
    
    def __init__(
        self,
        process_image_task: ProcessAndTranslateImageTask,
        process_regions_task: ProcessRegionsAndTranslateTask,
        status_task: GetDocsTranslateStatusTask,
    ):
        """
        Инициализация Action.
        
        Args:
            process_image_task: Task для обработки полного изображения
            process_regions_task: Task для обработки областей
            status_task: Task для получения статуса
        """
        self.process_image_task = process_image_task
        self.process_regions_task = process_regions_task
        self.status_task = status_task
    
    async def run(
        self, 
        data: Union[
            ProcessAndTranslateImageRequest, 
            ProcessRegionsAndTranslateRequest, 
            None
        ]
    ) -> Union[
        ProcessAndTranslateImageResponse, 
        ProcessRegionsAndTranslateResponse, 
        DocsTranslateStatus
    ]:
        """
        Основной метод выполнения Action.
        
        Этот метод требуется базовым классом Action, но в данном случае
        мы используем специализированные методы для разных типов операций.
        
        Args:
            data: Данные для обработки
            
        Returns:
            Результат обработки в зависимости от типа запроса
        """
        if isinstance(data, ProcessAndTranslateImageRequest):
            # Этот метод будет вызван через process_full_image
            raise ValueError("Use process_full_image method for image processing")
        elif isinstance(data, ProcessRegionsAndTranslateRequest):
            # Этот метод будет вызван через process_regions
            raise ValueError("Use process_regions method for regions processing")
        elif data is None:
            return await self.get_status()
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
    
    async def process_full_image(
        self, 
        image_data: bytes, 
        request: ProcessAndTranslateImageRequest
    ) -> ProcessAndTranslateImageResponse:
        """
        Обработать полное изображение с OCR и переводом.
        
        DEPRECATED: Используйте ProcessFullImageAction.execute() вместо этого.
        
        Бизнес-логика:
        1. Проверяет поддержку языковой пары
        2. Выполняет OCR всего изображения
        3. Переводит найденные тексты
        4. Возвращает объединённые результаты
        
        Args:
            image_data: Байты изображения
            request: Параметры обработки
            
        Returns:
            ProcessAndTranslateImageResponse: Результат с переводами
        """
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
    
    async def process_regions(
        self, 
        image_data: bytes, 
        request: ProcessRegionsAndTranslateRequest
    ) -> ProcessRegionsAndTranslateResponse:
        """
        Обработать конкретные области изображения с OCR и переводом.
        
        DEPRECATED: Используйте ProcessRegionsAction.execute() вместо этого.
        
        Бизнес-логика:
        1. Проверяет поддержку языковой пары
        2. Валидирует области для обработки
        3. Выполняет OCR в заданных областях
        4. Переводит найденные тексты
        5. Возвращает результаты по областям
        
        Args:
            image_data: Байты изображения
            request: Параметры обработки с областями
            
        Returns:
            ProcessRegionsAndTranslateResponse: Результат с переводами
        """
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
    
    async def get_status(self) -> DocsTranslateStatus:
        """
        Получить статус сервиса DocsTranslate.
        
        Returns:
            DocsTranslateStatus: Статус с информацией о доступности сервисов
        """
        with logfire.span("get_docs_translate_status"):
            status = await self.status_task.run()
            
            logfire.info(
                "DocsTranslate status retrieved",
                service_ready=status.service_ready,
                ocr_available=status.ocr_available,
                translation_available=status.translation_available
            )
            
            return status
    
    # Приватные методы для бизнес-логики
    async def _validate_processing_request(self, from_language, to_language):
        """Валидация параметров обработки."""
        # Здесь можно добавить дополнительную бизнес-логику валидации
        # Например, проверку доступности языковой пары
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
        # Здесь можно добавить бизнес-логику постобработки
        # Например, фильтрацию по качеству перевода, логирование статистики и т.д.
        logfire.debug(
            "Post-processing results",
            translated_regions=result.translated_regions,
            skipped_regions=result.skipped_regions
        )


__all__ = ["ProcessDocumentAction"]




