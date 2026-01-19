"""
OCR Client Manager для доступа к OCR функциональности из DocsTranslate контейнера.

В монолитной архитектуре напрямую использует OCRServerManager.
В микросервисной архитектуре будет делать HTTP запросы к OCR сервису.
"""

from typing import List, Optional
from src.Containers.AppSection.OCR.Managers import OCRServerManager
from src.Containers.AppSection.OCR.Data import (
    ProcessImageResponseSchema,
    ProcessPolygonsResponseSchema,
    PolygonRegionSchema,
)
from src.Ship.Parents import ClientManager


class OCRClientManager(ClientManager[ProcessImageResponseSchema]):
    """
    Client Manager для доступа к OCR функциональности из DocsTranslate контейнера.
    
    В текущей монолитной реализации напрямую использует OCRServerManager.
    При переходе к микросервисам будет заменён на HTTP клиент.
    """
    
    def __init__(self, ocr_server_manager: OCRServerManager):
        """
        Инициализация с OCR server manager.
        
        В микросервисной архитектуре здесь будет HTTP клиент.
        
        Args:
            ocr_server_manager: Менеджер OCR сервера
        """
        super().__init__(endpoint="http://ocr-service")  # Для будущей микросервисной архитектуры
        self.ocr_manager = ocr_server_manager
    
    async def process_full_image(self, image_data: bytes) -> ProcessImageResponseSchema:
        """
        Распознать текст на всём изображении.
        
        Args:
            image_data: Байты изображения
            
        Returns:
            ProcessImageResponseSchema: Результат распознавания
        """
        return await self.ocr_manager.process_full_image(image_data)
    
    async def process_polygon_regions(
        self, 
        image_data: bytes, 
        regions: List[PolygonRegionSchema]
    ) -> ProcessPolygonsResponseSchema:
        """
        Распознать текст в заданных полигональных областях.
        
        Args:
            image_data: Байты изображения
            regions: Список полигональных областей
            
        Returns:
            ProcessPolygonsResponseSchema: Результаты по областям
        """
        return await self.ocr_manager.process_polygon_regions(image_data, regions)
    
    async def extract_text_from_image(self, image_data: bytes) -> List[str]:
        """
        Извлечь только текст из изображения.
        
        Args:
            image_data: Байты изображения
            
        Returns:
            List[str]: Список распознанных текстов
        """
        return await self.ocr_manager.extract_text_from_image(image_data)
    
    async def extract_text_from_regions(
        self, 
        image_data: bytes, 
        regions: List[PolygonRegionSchema]
    ) -> List[str]:
        """
        Извлечь только текст из заданных областей.
        
        Args:
            image_data: Байты изображения
            regions: Полигональные области
            
        Returns:
            List[str]: Список текстов из областей
        """
        return await self.ocr_manager.extract_text_from_regions(image_data, regions)
    
    # Реализация абстрактных методов базового класса
    async def get(self, id) -> Optional[ProcessImageResponseSchema]:
        """
        Метод для совместимости с базовым интерфейсом.
        В OCR контексте не используется.
        """
        return None
    
    async def list(self, **filters) -> List[ProcessImageResponseSchema]:
        """
        Метод для совместимости с базовым интерфейсом.
        В OCR контексте не используется.
        """
        return []


__all__ = ["OCRClientManager"]




