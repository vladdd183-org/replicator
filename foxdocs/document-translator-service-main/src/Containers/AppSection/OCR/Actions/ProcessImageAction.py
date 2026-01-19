"""
Action для обработки полного изображения

Оркестрация процесса распознавания текста на всём изображении.
"""
import time
from typing import Dict, Any
import logfire

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.OCR.Tasks import (
    ValidateImageTask,
    ProcessFullImageTask,
)
from src.Containers.AppSection.OCR.Data import (
    OCRResultSchema,
    ProcessImageResponseSchema,
)


class ProcessImageAction(Action):
    """
    Оркестрация полного процесса OCR для изображения.
    
    Flow:
    1. Валидация изображения
    2. Распознавание текста на всём изображении
    3. Формирование структурированного ответа
    
    Example:
        action = ProcessImageAction(validate_task, process_task)
        response = await action.run(image_bytes)
    """
    
    def __init__(
        self,
        validate_task: ValidateImageTask,
        process_task: ProcessFullImageTask,
    ):
        """
        Инициализация action.
        
        Args:
            validate_task: Task для валидации изображения
            process_task: Task для обработки изображения
        """
        self.validate_task = validate_task
        self.process_task = process_task
    
    async def run(self, image_data: bytes) -> ProcessImageResponseSchema:
        """
        Выполнить полный процесс распознавания текста.
        
        Args:
            image_data: Байты изображения
            
        Returns:
            Структурированный ответ с результатами OCR
            
        Raises:
            InvalidImageFormatException: При неподдерживаемом формате
            ImageTooLargeException: При превышении размера
            ImageProcessingException: При ошибке обработки
        """
        start_time = time.time()
        
        with logfire.span(
            "process_image_action",
            image_size=len(image_data)
        ):
            # Шаг 1: Валидация изображения (с возможной конвертацией PDF)
            with logfire.span("validation"):
                validated_image_data, metadata = await self.validate_task.run(image_data)
                logfire.info(
                    "Image validated",
                    width=metadata["width"],
                    height=metadata["height"],
                    format=metadata["format"],
                    original_format=metadata.get("original_format")
                )
            
            # Шаг 2: Распознавание текста (используем валидированные данные изображения)
            with logfire.span("ocr_processing"):
                ocr_results = await self.process_task.run(validated_image_data)
                logfire.info(
                    "OCR completed",
                    regions_found=len(ocr_results)
                )
            
            # Шаг 3: Формирование ответа
            with logfire.span("response_preparation"):
                results = []
                for coordinates, text, confidence in ocr_results:
                    results.append(
                        OCRResultSchema(
                            text=text,
                            confidence=confidence,
                            coordinates=coordinates
                        )
                    )
                
                processing_time = time.time() - start_time
                
                response = ProcessImageResponseSchema(
                    results=results,
                    total_regions=len(results),
                    image_dimensions={
                        "width": metadata["width"],
                        "height": metadata["height"]
                    },
                    processing_time=processing_time
                )
                

                
                logfire.info(
                    "Process image action completed",
                    total_regions=len(results),
                    processing_time=processing_time
                )
                
                return response


