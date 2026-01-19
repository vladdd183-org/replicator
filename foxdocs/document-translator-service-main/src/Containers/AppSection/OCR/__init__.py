"""
OCR Container

Porto контейнер для функциональности оптического распознавания текста (OCR).

Предоставляет:
- Распознавание текста на всём изображении
- Распознавание текста в полигональных областях
- Поддержка различных форматов изображений
- Параллельная обработка множественных областей

Технологии:
- PaddleOCR v5 для распознавания
- Logfire для логирования
- Pydantic для валидации данных
"""

from .Actions import (
    ProcessImageAction,
)
from .Tasks import (
    ValidateImageTask,
    ProcessFullImageTask,
    ProcessPolygonRegionTask,
)
from .Data import (
    OCRResultSchema,
    PolygonRegionSchema,
    PolygonOCRResultSchema,
    ProcessImageResponseSchema,
    ProcessPolygonsResponseSchema,
)
from .Exceptions import (
    OCRException,
    OCRInitializationException,
    ImageProcessingException,
    InvalidImageFormatException,
    ImageTooLargeException,
    InvalidPolygonException,
    OCRProcessingException,
)
from .Managers import OCREngineManager
from .UI.API.Controllers import OCRController
from .Providers import OCRProvider

__all__ = [
    # Actions
    "ProcessImageAction",
    # Tasks
    "ValidateImageTask",
    "ProcessFullImageTask", 
    "ProcessPolygonRegionTask",
    # Data
    "OCRResultSchema",
    "PolygonRegionSchema",
    "PolygonOCRResultSchema",
    "ProcessImageResponseSchema",
    "ProcessPolygonsResponseSchema",
    # Exceptions
    "OCRException",
    "OCRInitializationException",
    "ImageProcessingException",
    "InvalidImageFormatException",
    "ImageTooLargeException",
    "InvalidPolygonException",
    "OCRProcessingException",
    # Managers
    "OCREngineManager",
    # Controllers
    "OCRController",
    # Providers
    "OCRProvider",
]


