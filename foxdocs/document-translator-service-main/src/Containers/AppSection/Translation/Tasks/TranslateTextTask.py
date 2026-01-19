"""
Translate Text Task

Атомарная задача для перевода текста.
"""

from src.Ship.Parents import Task
from src.Containers.AppSection.Translation.Services.TranslationService import TranslationService
from src.Containers.AppSection.Translation.Data.TranslationSchemas import (
    TranslationRequest,
    TranslationResponse,
)


class TranslateTextTask(Task):
    """
    Task для перевода одного текста.
    
    Выполняет атомарную операцию перевода с использованием TranslationService.
    """
    
    def __init__(self, translation_service: TranslationService):
        """
        Инициализация задачи.
        
        Args:
            translation_service: Сервис для перевода текста
        """
        super().__init__()
        self.translation_service = translation_service
    
    async def run(self, request: TranslationRequest) -> TranslationResponse:
        """
        Выполнение перевода текста.
        
        Args:
            request: Запрос на перевод
            
        Returns:
            TranslationResponse: Ответ с переведённым текстом
        """
        return await self.translation_service.translate(request)


__all__ = ["TranslateTextTask"]




