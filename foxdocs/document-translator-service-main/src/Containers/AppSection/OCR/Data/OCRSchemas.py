"""
OCR Data Transfer Objects and Pydantic Schemas

Минималистичные и понятные схемы данных для OCR операций.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class OCRResultSchema(BaseModel):
    """
    Результат распознавания одной текстовой области.
    
    Attributes:
        text: Распознанный текст
        confidence: Уверенность распознавания (0-1)
        coordinates: Координаты области [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    """
    model_config = ConfigDict(from_attributes=True)
    
    text: str = Field(
        description="Распознанный текст"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Уверенность распознавания"
    )
    coordinates: List[List[float]] = Field(
        description="Координаты углов области"
    )


class PolygonRegionSchema(BaseModel):
    """
    Полигональная область для распознавания.
    
    Attributes:
        points: Координаты вершин полигона
        region_id: Опциональный идентификатор области
    """
    model_config = ConfigDict(from_attributes=True)
    
    points: List[List[float]] = Field(
        min_length=3,
        description="Координаты вершин полигона (минимум 3 точки)"
    )
    region_id: Optional[str] = Field(
        default=None,
        description="Идентификатор области для связи с результатами"
    )


class PolygonOCRResultSchema(BaseModel):
    """
    Результат распознавания в полигональной области.
    
    Attributes:
        region_id: Идентификатор области
        text: Распознанный текст в области
        confidence: Средняя уверенность распознавания
        processing_time: Время обработки области
        polygon_coordinates: Исходные координаты полигона
    """
    model_config = ConfigDict(from_attributes=True)
    
    region_id: Optional[str] = Field(
        description="Идентификатор области"
    )
    text: str = Field(
        description="Распознанный текст"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Уверенность распознавания"
    )
    processing_time: float = Field(
        ge=0.0,
        description="Время обработки в секундах"
    )
    polygon_coordinates: List[List[float]] = Field(
        description="Исходные координаты полигона [[x1,y1], [x2,y2], ...]"
    )


class ProcessImageResponseSchema(BaseModel):
    """
    Ответ на запрос распознавания всего изображения.
    
    Attributes:
        results: Список распознанных текстовых областей
        total_regions: Общее количество найденных областей
        image_dimensions: Размеры обработанного изображения
        processing_time: Общее время обработки
        timestamp: Время обработки
    """
    model_config = ConfigDict(from_attributes=True)
    
    results: List[OCRResultSchema] = Field(
        default_factory=list,
        description="Список распознанных областей"
    )
    total_regions: int = Field(
        ge=0,
        description="Количество найденных областей"
    )
    image_dimensions: Dict[str, int] = Field(
        description="Размеры изображения (width, height)"
    )
    processing_time: float = Field(
        ge=0.0,
        description="Время обработки в секундах"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Время обработки"
    )


class ProcessPolygonsResponseSchema(BaseModel):
    """
    Ответ на запрос распознавания в полигональных областях.
    
    Attributes:
        results: Результаты для каждой области
        total_regions: Количество обработанных областей
        image_dimensions: Размеры исходного изображения
        processing_time: Общее время обработки
        timestamp: Время обработки
    """
    model_config = ConfigDict(from_attributes=True)
    
    results: List[PolygonOCRResultSchema] = Field(
        default_factory=list,
        description="Результаты распознавания по областям"
    )
    total_regions: int = Field(
        ge=0,
        description="Количество обработанных областей"
    )
    image_dimensions: Dict[str, int] = Field(
        description="Размеры изображения (width, height)"
    )
    processing_time: float = Field(
        ge=0.0,
        description="Время обработки в секундах"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Время обработки"
    )


