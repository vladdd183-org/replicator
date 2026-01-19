"""
Action для обработки полигональных областей

Оркестрация процесса распознавания текста в заданных полигональных областях.
"""
import time
from typing import List, Dict, Any
import logfire
from PIL import Image
import io

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.OCR.Tasks import (
    ValidateImageTask,
    ProcessPolygonRegionTask,
)
from src.Containers.AppSection.OCR.Data import (
    PolygonRegionSchema,
    PolygonOCRResultSchema,
    ProcessPolygonsResponseSchema,
)


class ProcessPolygonsAction(Action):
    """
    Оркестрация процесса OCR для полигональных областей.
    
    Flow:
    1. Валидация изображения
    2. Обработка каждой полигональной области
    3. Формирование структурированного ответа
    
    Example:
        action = ProcessPolygonsAction(validate_task, process_polygon_task)
        response = await action.run(image_bytes, polygon_regions)
    """
    
    def __init__(
        self,
        validate_task: ValidateImageTask,
        process_polygon_task: ProcessPolygonRegionTask,
    ):
        """
        Инициализация action.
        
        Args:
            validate_task: Task для валидации изображения
            process_polygon_task: Task для обработки полигональной области
        """
        self.validate_task = validate_task
        self.process_polygon_task = process_polygon_task
    
    async def run(
        self, 
        image_data: bytes, 
        polygon_regions: List[PolygonRegionSchema]
    ) -> ProcessPolygonsResponseSchema:
        """
        Выполнить распознавание текста в полигональных областях.
        
        Args:
            image_data: Байты изображения
            polygon_regions: Список полигональных областей для обработки
            
        Returns:
            Структурированный ответ с результатами OCR для каждой области
            
        Raises:
            InvalidImageFormatException: При неподдерживаемом формате
            ImageTooLargeException: При превышении размера
            InvalidPolygonException: При некорректных полигонах
            ImageProcessingException: При ошибке обработки
        """
        start_time = time.time()
        
        with logfire.span(
            "process_polygons_action",
            image_size=len(image_data),
            regions_count=len(polygon_regions)
        ):
            # Шаг 1: Валидация изображения (с возможной конвертацией PDF)
            with logfire.span("validation"):
                validated_image_data, metadata = await self.validate_task.run(image_data)
                logfire.info(
                    "Image validated for polygon processing",
                    width=metadata["width"],
                    height=metadata["height"],
                    format=metadata["format"],
                    original_format=metadata.get("original_format"),
                    regions_count=len(polygon_regions)
                )
            
            # Шаг 2: Обработка каждой полигональной области
            results = []
            
            for i, region in enumerate(polygon_regions):
                region_start_time = time.time()
                
                with logfire.span(f"process_polygon_region_{i}"):
                    try:
                        # Обрабатываем полигональную область (используем валидированные данные)
                        text, confidence = await self.process_polygon_task.run(
                            validated_image_data, 
                            region.points
                        )
                        
                        region_processing_time = time.time() - region_start_time
                        
                        result = PolygonOCRResultSchema(
                            region_id=region.region_id or f"region_{i}",
                            text=text,
                            confidence=confidence,
                            processing_time=region_processing_time,
                            polygon_coordinates=region.points
                        )
                        
                        results.append(result)
                        
                        logfire.debug(
                            "Polygon region processed successfully",
                            region_id=result.region_id,
                            text_length=len(text),
                            confidence=confidence,
                            processing_time=region_processing_time
                        )
                        
                    except Exception as e:
                        # Логируем ошибку, но продолжаем обработку других областей
                        region_processing_time = time.time() - region_start_time
                        
                        logfire.error(
                            "Failed to process polygon region",
                            region_id=region.region_id or f"region_{i}",
                            error=str(e),
                            processing_time=region_processing_time
                        )
                        
                        # Добавляем результат с пустым текстом и нулевой уверенностью
                        error_result = PolygonOCRResultSchema(
                            region_id=region.region_id or f"region_{i}",
                            text="",
                            confidence=0.0,
                            processing_time=region_processing_time,
                            polygon_coordinates=region.points
                        )
                        results.append(error_result)
            
            # Шаг 3: Формирование ответа
            with logfire.span("response_preparation"):
                total_processing_time = time.time() - start_time
                
                response = ProcessPolygonsResponseSchema(
                    results=results,
                    total_regions=len(results),
                    image_dimensions={
                        "width": metadata["width"],
                        "height": metadata["height"]
                    },
                    processing_time=total_processing_time
                )
                
                # Подсчитываем статистику
                successful_regions = sum(1 for r in results if r.confidence > 0)
                avg_confidence = (
                    sum(r.confidence for r in results) / len(results) 
                    if results else 0.0
                )
                
                logfire.info(
                    "Process polygons action completed",
                    total_regions=len(results),
                    successful_regions=successful_regions,
                    avg_confidence=avg_confidence,
                    processing_time=total_processing_time
                )
                
                return response


