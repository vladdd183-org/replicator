"""
OCR Engine Manager - Менеджер для связи OCR контейнера с другими контейнерами

Предоставляет интерфейс для взаимодействия между контейнерами.
"""
from typing import Any, List, Optional
import logfire

from src.Ship.Parents.Manager import ServerManager
from src.Containers.AppSection.OCR.Data import ProcessImageResponseSchema


class OCREngineManager(ServerManager[ProcessImageResponseSchema]):
    """
    Менеджер для взаимодействия OCR контейнера с другими контейнерами.
    
    Реализует интерфейс ServerManager для предоставления OCR функциональности
    другим контейнерам приложения.
    """
    
    def __init__(self, action_provider: Any, state=None):
        """
        Инициализация менеджера.
        
        Args:
            action_provider: Провайдер действий для выполнения OCR операций
            state: Состояние приложения
        """
        super().__init__(action_provider, state)
        logfire.info("OCREngineManager initialized")
    
    async def get(self, id: Any) -> ProcessImageResponseSchema | None:
        """
        Получить результат OCR по идентификатору.
        
        Args:
            id: Идентификатор запроса
            
        Returns:
            Результат OCR или None если не найден
        """
        # В данной реализации мы не храним результаты по ID
        # Это может быть расширено для кеширования результатов
        logfire.info("OCR get operation called", request_id=str(id))
        return None
    
    async def list(self, **filters) -> List[ProcessImageResponseSchema]:
        """
        Получить список результатов OCR с фильтрами.
        
        Args:
            **filters: Фильтры для поиска
            
        Returns:
            Список результатов OCR
        """
        # В данной реализации мы не храним историю результатов
        # Это может быть расширено для ведения истории OCR операций
        logfire.info("OCR list operation called", filters=filters)
        return []
    
    def get_status(self) -> dict:
        """
        Получить статус OCR сервиса.
        
        Returns:
            Словарь со статусом сервиса
        """
        return {
            "manager": "OCREngineManager",
            "status": "active",
            "container": "OCR"
        }