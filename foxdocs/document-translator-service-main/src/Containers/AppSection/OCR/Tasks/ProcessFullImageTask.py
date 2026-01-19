"""
Task для обработки полного изображения

Атомарная операция распознавания текста на всём изображении.
"""
import io
from typing import List, Tuple
from PIL import Image
import numpy as np
import logfire

from src.Ship.Parents.Task import Task
from src.Containers.AppSection.OCR.Services import OCRService
from src.Containers.AppSection.OCR.Exceptions import ImageProcessingException


class ProcessFullImageTask(Task):
    """
    Распознавание текста на полном изображении.
    
    Single Responsibility: Выполнить OCR на всём изображении и вернуть
    найденные текстовые области с координатами и уверенностью.
    
    Example:
        task = ProcessFullImageTask(ocr_service)
        results = await task.run(image_bytes)
        # results: [(coordinates, text, confidence), ...]
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
        image_data: bytes
    ) -> List[Tuple[List[List[float]], str, float]]:
        """
        Выполнить распознавание текста на изображении.
        
        Args:
            image_data: Байты изображения
            
        Returns:
            Список кортежей (координаты, текст, уверенность)
            
        Raises:
            ImageProcessingException: При ошибке обработки изображения
        """
        try:
            with logfire.span(
                "process_full_image_task",
                image_size=len(image_data)
            ):
                # Открываем изображение
                image = Image.open(io.BytesIO(image_data))
                
                # Логируем метаданные
                logfire.debug(
                    "Image opened",
                    width=image.width,
                    height=image.height,
                    mode=image.mode,
                    format=image.format
                )
                
                # Конвертируем в RGB если нужно
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Конвертируем в numpy array
                img_array = np.array(image)
                
                # Выполняем OCR
                results = self.ocr_service.process_full_image(image_data)
                
                logfire.info(
                    "Full image processed",
                    regions_found=len(results)
                )
                
                return results
                
        except Exception as e:
            logfire.error(
                "Failed to process full image",
                error=str(e)
            )
            raise ImageProcessingException(
                f"Failed to process image: {str(e)}"
            )
