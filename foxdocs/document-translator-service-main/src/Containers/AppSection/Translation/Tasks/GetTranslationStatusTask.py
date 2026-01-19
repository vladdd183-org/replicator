"""
Get Translation Status Task

Атомарная задача для получения статуса системы перевода.
"""

from src.Ship.Parents import Task
from src.Containers.AppSection.Translation.Services.TranslationService import TranslationService
from src.Containers.AppSection.Translation.Data.TranslationSchemas import TranslationStatus


class GetTranslationStatusTask(Task):
    """
    Task для получения статуса системы перевода.
    
    Возвращает информацию о доступных языковых пакетах и маршрутах перевода.
    """
    
    def __init__(self, translation_service: TranslationService):
        """
        Инициализация задачи.
        
        Args:
            translation_service: Сервис для перевода текста
        """
        super().__init__()
        self.translation_service = translation_service
    
    async def run(self) -> TranslationStatus:
        """
        Получение статуса системы перевода.
        
        Returns:
            TranslationStatus: Статус с информацией о доступных пакетах и маршрутах
        """
        return self.translation_service.get_status()


__all__ = ["GetTranslationStatusTask"]




