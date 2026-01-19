"""
DocsTranslate Exceptions

Исключения для операций комбинированной обработки OCR + Translation.
"""

from src.Ship.Parents.Exception import PortoException


class DocsTranslateException(PortoException):
    """Базовое исключение для DocsTranslate операций."""
    
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code=status_code)


class OCRServiceUnavailableException(DocsTranslateException):
    """OCR сервис недоступен."""
    
    def __init__(self, reason: str = "OCR service is not available"):
        super().__init__(f"OCR service unavailable: {reason}", status_code=503)
        self.reason = reason


class TranslationServiceUnavailableException(DocsTranslateException):
    """Translation сервис недоступен."""
    
    def __init__(self, reason: str = "Translation service is not available"):
        super().__init__(f"Translation service unavailable: {reason}", status_code=503)
        self.reason = reason


class DocsTranslateServiceNotInitializedException(DocsTranslateException):
    """Сервис DocsTranslate не инициализирован."""
    
    def __init__(self):
        super().__init__(
            "DocsTranslate service is not initialized. Please initialize OCR and Translation services first.",
            status_code=503
        )


class ProcessingFailedException(DocsTranslateException):
    """Ошибка при обработке изображения."""
    
    def __init__(self, stage: str, original_error: str):
        super().__init__(f"Processing failed at stage '{stage}': {original_error}", status_code=500)
        self.stage = stage
        self.original_error = original_error


class NoTextFoundException(DocsTranslateException):
    """На изображении не найден текст для перевода."""
    
    def __init__(self, reason: str = "No text found on image"):
        super().__init__(f"No text to translate: {reason}", status_code=422)
        self.reason = reason


class TranslationQualityException(DocsTranslateException):
    """Качество перевода ниже допустимого уровня."""
    
    def __init__(self, text: str, confidence: float, threshold: float):
        super().__init__(
            f"Translation quality too low. Text: '{text[:50]}...', "
            f"Confidence: {confidence:.2f}, Threshold: {threshold:.2f}",
            status_code=422
        )
        self.text = text
        self.confidence = confidence
        self.threshold = threshold


class UnsupportedLanguagePairForDocsException(DocsTranslateException):
    """Неподдерживаемая языковая пара для документов."""
    
    def __init__(self, from_lang: str, to_lang: str):
        super().__init__(
            f"Unsupported language pair for document translation: {from_lang} -> {to_lang}",
            status_code=400
        )
        self.from_language = from_lang
        self.to_language = to_lang


__all__ = [
    "DocsTranslateException",
    "OCRServiceUnavailableException",
    "TranslationServiceUnavailableException", 
    "DocsTranslateServiceNotInitializedException",
    "ProcessingFailedException",
    "NoTextFoundException",
    "TranslationQualityException",
    "UnsupportedLanguagePairForDocsException",
]
