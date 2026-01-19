"""
Task для обработки полигональной области

Атомарная операция распознавания текста в заданной полигональной области.
"""
import io
from typing import List, Tuple
from PIL import Image
import numpy as np
import logfire

from src.Ship.Parents.Task import Task
from src.Containers.AppSection.OCR.Services import OCRService
from src.Containers.AppSection.OCR.Exceptions import (
    ImageProcessingException,
    InvalidPolygonException,
)


class ProcessPolygonRegionTask(Task):
    """
    Распознавание текста в полигональной области.
    
    Single Responsibility: Выполнить OCR в заданной полигональной области
    изображения и вернуть распознанный текст с уверенностью.
    
    Example:
        task = ProcessPolygonRegionTask(ocr_service)
        text, confidence = await task.run(image_bytes, polygon_points)
    """
    
    def __init__(self, ocr_service: OCRService):
        """
        Инициализация задачи.
        
        Args:
            ocr_service: Сервис OCR для обработки изображений
        """
        self.ocr_service = ocr_service
    
    async def run(
        self,
        image_data: bytes,
        points: List[List[float]]
    ) -> Tuple[str, float]:
        """
        Выполнить распознавание текста в полигональной области.
        
        Args:
            image_data: Байты изображения
            points: Координаты вершин полигона
            
        Returns:
            Кортеж (текст, уверенность)
            
        Raises:
            InvalidPolygonException: При некорректном полигоне
            ImageProcessingException: При ошибке обработки
        """
        try:
            # Валидация полигона
            if len(points) < 3:
                raise InvalidPolygonException(
                    f"Polygon must have at least 3 points, got {len(points)}"
                )
            
            with logfire.span(
                "process_polygon_region_task",
                polygon_points=len(points)
            ):
                # Открываем изображение
                image = Image.open(io.BytesIO(image_data))
                
                # Проверяем что координаты в пределах изображения
                for point in points:
                    if len(point) != 2:
                        raise InvalidPolygonException(
                            "Each point must have exactly 2 coordinates [x, y]"
                        )
                    x, y = point
                    if x < 0 or x > image.width or y < 0 or y > image.height:
                        logfire.error(
                            "Polygon point outside image bounds",
                            point=point,
                            image_size=(image.width, image.height)
                        )
                
                # Конвертируем в RGB если нужно
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Конвертируем в numpy array
                img_array = np.array(image)
                
                # Обрабатываем полигональную область
                # Используем более мягкие ограничения по размеру для маленьких областей
                text, confidence = self.ocr_service.process_polygon_region(
                    image_data,
                    points,
                    min_region_size=(5, 5)  # Более мягкие ограничения для лучшей обработки маленьких областей
                )
                
                logfire.debug(
                    "Polygon region processed",
                    text_length=len(text),
                    confidence=confidence
                )
                
                return (text, confidence)
                
        except (InvalidPolygonException, ImageProcessingException):
            raise
        except Exception as e:
            logfire.error(
                "Failed to process polygon region",
                error=str(e)
            )
            raise ImageProcessingException(
                f"Failed to process polygon region: {str(e)}"
            )
