"""
OCR Server Manager для экспорта функциональности OCR в другие контейнеры.

Предоставляет централизованный доступ к операциям распознавания текста.
"""

from typing import List, Optional
from dishka import FromDishka

from ..Actions import ProcessImageAction, ProcessPolygonsAction
from ..Data import (
    ProcessImageResponseSchema,
    ProcessPolygonsResponseSchema,
    PolygonRegionSchema,
)
from src.Ship.Parents import ServerManager


class OCRServerManager(ServerManager[ProcessImageResponseSchema]):
    """
    Server Manager для OCR контейнера.
    
    Предоставляет унифицированный интерфейс для:
    - Распознавания текста на полном изображении
    - Распознавания текста в заданных полигональных областях
    
    Используется другими контейнерами для доступа к OCR функциональности.
    """
    
    def __init__(
        self,
        process_image_action: FromDishka[ProcessImageAction],
        process_polygons_action: FromDishka[ProcessPolygonsAction],
    ):
        """
        Инициализация с OCR actions.
        
        Args:
            process_image_action: Action для обработки полного изображения
            process_polygons_action: Action для обработки полигональных областей
        """
        self.process_image_action = process_image_action
        self.process_polygons_action = process_polygons_action
    
    async def process_full_image(self, image_data: bytes) -> ProcessImageResponseSchema:
        """
        Распознать текст на всём изображении.
        
        Args:
            image_data: Байты изображения
            
        Returns:
            ProcessImageResponseSchema: Результат распознавания
            
        Raises:
            InvalidImageFormatException: При неподдерживаемом формате
            ImageTooLargeException: При превышении размера
            ImageProcessingException: При ошибке обработки
        """
        return await self.process_image_action.run(image_data)
    
    async def process_polygon_regions(
        self, 
        image_data: bytes, 
        regions: List[PolygonRegionSchema]
    ) -> ProcessPolygonsResponseSchema:
        """
        Распознать текст в заданных полигональных областях.
        
        Args:
            image_data: Байты изображения
            regions: Список полигональных областей для обработки
            
        Returns:
            ProcessPolygonsResponseSchema: Результаты распознавания по областям
            
        Raises:
            InvalidImageFormatException: При неподдерживаемом формате
            ImageTooLargeException: При превышении размера
            ImageProcessingException: При ошибке обработки
        """
        return await self.process_polygons_action.run(image_data, regions)
    
    # Реализация абстрактных методов базового класса (для совместимости)
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
    
    # Дополнительные удобные методы
    async def extract_text_from_image(self, image_data: bytes) -> List[str]:
        """
        Извлечь только текст из изображения (без координат и confidence).
        
        Args:
            image_data: Байты изображения
            
        Returns:
            List[str]: Список распознанных текстов
        """
        result = await self.process_full_image(image_data)
        return [ocr_result.text for ocr_result in result.results if ocr_result.text.strip()]
    
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
            List[str]: Список распознанных текстов из областей
        """
        result = await self.process_polygon_regions(image_data, regions)
        return [region_result.text for region_result in result.results if region_result.text.strip()]


__all__ = ["OCRServerManager"]




