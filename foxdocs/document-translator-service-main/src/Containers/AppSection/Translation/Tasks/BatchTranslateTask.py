"""
Batch Translate Task

Атомарная задача для пакетного перевода текстов.
"""

from src.Ship.Parents import Task
from src.Containers.AppSection.Translation.Services.TranslationService import TranslationService
from src.Containers.AppSection.Translation.Data.TranslationSchemas import (
    BatchTranslationRequest,
    BatchTranslationResponse,
)


class BatchTranslateTask(Task):
    """
    Task для пакетного перевода текстов.
    
    Выполняет атомарную операцию пакетного перевода с использованием TranslationService.
    """
    
    def __init__(self, translation_service: TranslationService):
        """
        Инициализация задачи.
        
        Args:
            translation_service: Сервис для перевода текста
        """
        super().__init__()
        self.translation_service = translation_service
    
    async def run(self, request: BatchTranslationRequest) -> BatchTranslationResponse:
        """
        Выполнение пакетного перевода.
        
        Args:
            request: Запрос на пакетный перевод
            
        Returns:
            BatchTranslationResponse: Ответ с переведёнными текстами
        """
        return await self.translation_service.translate_batch(request)


__all__ = ["BatchTranslateTask"]




