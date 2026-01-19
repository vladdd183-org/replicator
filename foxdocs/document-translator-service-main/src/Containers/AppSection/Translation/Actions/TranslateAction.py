"""
Translate Action

Бизнес-логика для операций перевода.
"""

from typing import Union
from src.Ship.Parents import Action
from src.Containers.AppSection.Translation.Tasks.TranslateTextTask import TranslateTextTask
from src.Containers.AppSection.Translation.Tasks.BatchTranslateTask import BatchTranslateTask
from src.Containers.AppSection.Translation.Tasks.GetTranslationStatusTask import GetTranslationStatusTask
from src.Containers.AppSection.Translation.Data.TranslationSchemas import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    TranslationStatus,
)


class TranslateAction(Action):
    """
    Action для выполнения операций перевода.
    
    Координирует выполнение различных задач перевода и содержит бизнес-логику.
    """
    
    def __init__(
        self,
        translate_task: TranslateTextTask,
        batch_translate_task: BatchTranslateTask,
        status_task: GetTranslationStatusTask,
    ):
        """
        Инициализация Action.
        
        Args:
            translate_task: Задача для перевода одного текста
            batch_translate_task: Задача для пакетного перевода
            status_task: Задача для получения статуса системы
        """
        self.translate_task = translate_task
        self.batch_translate_task = batch_translate_task
        self.status_task = status_task
    
    async def run(self, data: Union[TranslationRequest, BatchTranslationRequest, None]) -> Union[TranslationResponse, BatchTranslationResponse, TranslationStatus]:
        """
        Основной метод выполнения Action.
        
        Этот метод требуется базовым классом Action, но в данном случае
        мы используем специализированные методы для разных типов операций.
        
        Args:
            data: Данные для обработки
            
        Returns:
            Результат обработки
        """
        if isinstance(data, TranslationRequest):
            return await self.translate_text(data)
        elif isinstance(data, BatchTranslationRequest):
            return await self.translate_batch(data)
        elif data is None:
            return await self.get_status()
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
    
    async def translate_text(self, request: TranslationRequest) -> TranslationResponse:
        """
        Перевод одного текста.
        
        DEPRECATED: Создайте отдельные Actions для каждого Use Case.
        
        Args:
            request: Запрос на перевод
            
        Returns:
            TranslationResponse: Ответ с переведённым текстом
        """
        return await self.translate_task.run(request)
    
    async def translate_batch(self, request: BatchTranslationRequest) -> BatchTranslationResponse:
        """
        Пакетный перевод текстов.
        
        DEPRECATED: Создайте отдельные Actions для каждого Use Case.
        
        Args:
            request: Запрос на пакетный перевод
            
        Returns:
            BatchTranslationResponse: Ответ с переведёнными текстами
        """
        return await self.batch_translate_task.run(request)
    
    async def get_status(self) -> TranslationStatus:
        """
        Получение статуса системы перевода.
        
        Returns:
            TranslationStatus: Статус с информацией о доступных пакетах и маршрутах
        """
        return await self.status_task.run()


__all__ = ["TranslateAction"]
