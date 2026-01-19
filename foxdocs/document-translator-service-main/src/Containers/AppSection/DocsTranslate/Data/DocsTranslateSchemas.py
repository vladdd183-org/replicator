"""
DocsTranslate Data Schemas

Схемы данных для комбинированных операций OCR + Translation.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum

from src.Containers.AppSection.OCR.Data import OCRResultSchema, PolygonRegionSchema
from src.Containers.AppSection.Translation.Data import (
    SupportedLanguage,
    TranslationResponse,
)


class TranslatedOCRResult(BaseModel):
    """
    Результат OCR с переводом.
    
    Объединяет результат распознавания текста с его переводом.
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Оригинальные данные OCR
    original_text: str = Field(description="Исходный распознанный текст")
    confidence: float = Field(ge=0.0, le=1.0, description="Уверенность распознавания")
    coordinates: List[List[float]] = Field(description="Координаты области")
    
    # Данные перевода
    translated_text: str = Field(description="Переведённый текст")
    from_language: SupportedLanguage = Field(description="Исходный язык")
    to_language: SupportedLanguage = Field(description="Целевой язык")
    
    # Дополнительная информация о переводе
    intermediate_language: Optional[SupportedLanguage] = Field(
        None, description="Промежуточный язык (если использовался)"
    )
    intermediate_text: Optional[str] = Field(
        None, description="Текст на промежуточном языке"
    )


class ProcessAndTranslateImageRequest(BaseModel):
    """Запрос на обработку изображения с переводом."""
    model_config = ConfigDict(from_attributes=True)
    
    from_language: SupportedLanguage = Field(
        default=SupportedLanguage.CHINESE,
        description="Язык текста на изображении"
    )
    to_language: SupportedLanguage = Field(
        default=SupportedLanguage.RUSSIAN,
        description="Целевой язык перевода"
    )
    translate_empty_results: bool = Field(
        default=False,
        description="Переводить ли пустые или некачественные результаты OCR"
    )
    min_confidence_threshold: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Минимальный порог уверенности для перевода"
    )


class ProcessAndTranslateImageResponse(BaseModel):
    """Ответ на запрос обработки изображения с переводом."""
    model_config = ConfigDict(from_attributes=True)
    
    results: List[TranslatedOCRResult] = Field(
        default_factory=list,
        description="Результаты OCR с переводами"
    )
    total_regions: int = Field(ge=0, description="Общее количество найденных областей")
    translated_regions: int = Field(ge=0, description="Количество переведённых областей")
    skipped_regions: int = Field(ge=0, description="Количество пропущенных областей")
    
    # Информация об изображении
    image_dimensions: Dict[str, int] = Field(description="Размеры изображения")
    
    # Время обработки
    ocr_processing_time: float = Field(ge=0.0, description="Время OCR обработки")
    translation_processing_time: float = Field(ge=0.0, description="Время перевода")
    total_processing_time: float = Field(ge=0.0, description="Общее время обработки")
    
    # Языки
    from_language: SupportedLanguage = Field(description="Исходный язык")
    to_language: SupportedLanguage = Field(description="Целевой язык")
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Время обработки"
    )


class ProcessRegionsAndTranslateRequest(BaseModel):
    """Запрос на обработку конкретных областей с переводом."""
    model_config = ConfigDict(from_attributes=True)
    
    regions: List[PolygonRegionSchema] = Field(
        min_length=1,
        description="Полигональные области для обработки"
    )
    from_language: SupportedLanguage = Field(
        default=SupportedLanguage.CHINESE,
        description="Язык текста на изображении"
    )
    to_language: SupportedLanguage = Field(
        default=SupportedLanguage.RUSSIAN,
        description="Целевой язык перевода"
    )
    translate_empty_results: bool = Field(
        default=False,
        description="Переводить ли пустые результаты OCR"
    )
    min_confidence_threshold: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Минимальный порог уверенности для перевода"
    )


class ProcessRegionsAndTranslateResponse(BaseModel):
    """Ответ на запрос обработки областей с переводом."""
    model_config = ConfigDict(from_attributes=True)
    
    results: List[TranslatedOCRResult] = Field(
        default_factory=list,
        description="Результаты OCR с переводами по областям"
    )
    total_regions: int = Field(ge=0, description="Общее количество обработанных областей")
    translated_regions: int = Field(ge=0, description="Количество переведённых областей")
    skipped_regions: int = Field(ge=0, description="Количество пропущенных областей")
    
    # Информация об изображении
    image_dimensions: Dict[str, int] = Field(description="Размеры изображения")
    
    # Время обработки
    ocr_processing_time: float = Field(ge=0.0, description="Время OCR обработки")
    translation_processing_time: float = Field(ge=0.0, description="Время перевода")
    total_processing_time: float = Field(ge=0.0, description="Общее время обработки")
    
    # Языки
    from_language: SupportedLanguage = Field(description="Исходный язык")
    to_language: SupportedLanguage = Field(description="Целевой язык")
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Время обработки"
    )


class DocsTranslateStatus(BaseModel):
    """Статус сервиса DocsTranslate."""
    model_config = ConfigDict(from_attributes=True)
    
    ocr_available: bool = Field(description="Доступность OCR сервиса")
    translation_available: bool = Field(description="Доступность сервиса перевода")
    supported_ocr_formats: List[str] = Field(
        default_factory=lambda: ["jpg", "jpeg", "png", "bmp", "tiff"],
        description="Поддерживаемые форматы изображений"
    )
    supported_language_pairs: List[str] = Field(
        default_factory=list,
        description="Поддерживаемые пары языков для перевода"
    )
    service_ready: bool = Field(description="Готовность сервиса к работе")
    
    # Дополнительная информация
    ocr_engine_info: Optional[Dict[str, Any]] = Field(
        None, description="Информация о движке OCR"
    )
    translation_status: Optional[Dict[str, Any]] = Field(
        None, description="Статус системы перевода"
    )


# ============================================
# STREAMING SCHEMAS
# ============================================

class StreamingConfig(BaseModel):
    """
    Конфигурация для streaming обработки документов.
    
    Количество воркеров зафиксировано на оптимальных значениях:
    - OCR воркеры: 1 (из-за thread-safety PaddleOCR)
    - Translation воркеры: 2 (оптимально для параллелизма)
    """
    model_config = ConfigDict(from_attributes=True)
    
    send_region_preview: bool = Field(
        default=True,
        description="Отправлять ли координаты областей сразу после детекции"
    )


class ProgressEventType(str, Enum):
    """Типы событий прогресса обработки."""
    
    # Этап 1: Детекция областей
    DETECTION_STARTED = "detection_started"
    REGIONS_DETECTED = "regions_detected"
    
    # Этап 2: OCR обработка
    REGION_OCR_STARTED = "region_ocr_started"
    REGION_OCR_COMPLETED = "region_ocr_completed"
    REGION_OCR_FAILED = "region_ocr_failed"
    
    # Этап 3: Перевод
    REGION_TRANSLATION_STARTED = "region_translation_started"
    REGION_TRANSLATED = "region_translated"
    REGION_TRANSLATION_FAILED = "region_translation_failed"
    
    # Финальные события
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_FAILED = "processing_failed"


class RegionDetectedEvent(BaseModel):
    """Событие: область текста обнаружена."""
    model_config = ConfigDict(from_attributes=True)
    
    region_index: int = Field(ge=0, description="Индекс области")
    coordinates: List[List[float]] = Field(description="Координаты полигона")
    total_regions: int = Field(ge=0, description="Общее количество найденных областей")


class RegionOCRCompletedEvent(BaseModel):
    """Событие: OCR области завершён."""
    model_config = ConfigDict(from_attributes=True)
    
    region_index: int = Field(ge=0, description="Индекс области")
    original_text: str = Field(description="Распознанный текст")
    confidence: float = Field(ge=0.0, le=1.0, description="Уверенность распознавания")
    coordinates: List[List[float]] = Field(description="Координаты полигона")


class RegionTranslatedEvent(BaseModel):
    """Событие: область переведена."""
    model_config = ConfigDict(from_attributes=True)
    
    region_index: int = Field(ge=0, description="Индекс области")
    original_text: str = Field(description="Исходный текст")
    translated_text: str = Field(description="Переведённый текст")
    confidence: float = Field(ge=0.0, le=1.0, description="Уверенность OCR")
    coordinates: List[List[float]] = Field(description="Координаты полигона")
    from_language: SupportedLanguage = Field(description="Исходный язык")
    to_language: SupportedLanguage = Field(description="Целевой язык")
    intermediate_language: Optional[SupportedLanguage] = Field(
        None, description="Промежуточный язык"
    )
    intermediate_text: Optional[str] = Field(None, description="Промежуточный текст")


class RegionProcessingFailedEvent(BaseModel):
    """Событие: ошибка обработки области."""
    model_config = ConfigDict(from_attributes=True)
    
    region_index: int = Field(ge=0, description="Индекс области")
    error_message: str = Field(description="Сообщение об ошибке")
    stage: Literal["ocr", "translation"] = Field(description="Этап на котором произошла ошибка")


class ProcessingCompletedEvent(BaseModel):
    """Событие: обработка завершена."""
    model_config = ConfigDict(from_attributes=True)
    
    total_regions: int = Field(ge=0, description="Общее количество областей")
    successfully_processed: int = Field(ge=0, description="Успешно обработано")
    failed_regions: int = Field(ge=0, description="Не удалось обработать")
    total_processing_time: float = Field(ge=0.0, description="Общее время обработки (сек)")


class ProgressEvent(BaseModel):
    """
    Универсальное событие прогресса обработки.
    
    Используется для отправки промежуточных результатов через WebSocket.
    """
    model_config = ConfigDict(from_attributes=True)
    
    event_type: ProgressEventType = Field(description="Тип события")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Время события"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Данные события (зависят от типа)"
    )


class StreamingProcessAndTranslateImageRequest(ProcessAndTranslateImageRequest):
    """
    Расширенный запрос на обработку изображения с streaming режимом.
    
    Наследует все параметры от ProcessAndTranslateImageRequest
    и добавляет конфигурацию streaming.
    """
    model_config = ConfigDict(from_attributes=True)
    
    streaming_config: StreamingConfig = Field(
        default_factory=StreamingConfig,
        description="Конфигурация streaming обработки"
    )


class StreamingProcessRegionsAndTranslateRequest(ProcessRegionsAndTranslateRequest):
    """
    Расширенный запрос на обработку областей с streaming режимом.
    
    Наследует все параметры от ProcessRegionsAndTranslateRequest
    и добавляет конфигурацию streaming.
    """
    model_config = ConfigDict(from_attributes=True)
    
    streaming_config: StreamingConfig = Field(
        default_factory=StreamingConfig,
        description="Конфигурация streaming обработки"
    )


__all__ = [
    "TranslatedOCRResult",
    "ProcessAndTranslateImageRequest",
    "ProcessAndTranslateImageResponse", 
    "ProcessRegionsAndTranslateRequest",
    "ProcessRegionsAndTranslateResponse",
    "DocsTranslateStatus",
    # Streaming schemas
    "StreamingConfig",
    "ProgressEventType",
    "RegionDetectedEvent",
    "RegionOCRCompletedEvent",
    "RegionTranslatedEvent",
    "RegionProcessingFailedEvent",
    "ProcessingCompletedEvent",
    "ProgressEvent",
    "StreamingProcessAndTranslateImageRequest",
    "StreamingProcessRegionsAndTranslateRequest",
]




