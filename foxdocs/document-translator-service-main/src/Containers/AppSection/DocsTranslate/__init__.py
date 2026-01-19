"""
DocsTranslate Container

Контейнер для комбинированных операций OCR + Translation.
Объединяет функциональность распознавания текста и перевода.
"""

from .Actions.ProcessDocumentAction import ProcessDocumentAction
from .Data.DocsTranslateSchemas import (
    ProcessAndTranslateImageRequest,
    ProcessAndTranslateImageResponse,
    ProcessRegionsAndTranslateRequest, 
    ProcessRegionsAndTranslateResponse,
    DocsTranslateStatus,
    TranslatedOCRResult,
)
from .Managers.OCRClientManager import OCRClientManager
from .Managers.TranslationClientManager import TranslationClientManager

__all__ = [
    # Actions
    "ProcessDocumentAction",
    
    # Data Schemas
    "ProcessAndTranslateImageRequest",
    "ProcessAndTranslateImageResponse",
    "ProcessRegionsAndTranslateRequest",
    "ProcessRegionsAndTranslateResponse", 
    "DocsTranslateStatus",
    "TranslatedOCRResult",
    
    # Managers
    "OCRClientManager",
    "TranslationClientManager",
]




