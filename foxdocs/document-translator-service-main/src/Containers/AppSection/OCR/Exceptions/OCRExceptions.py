"""
OCR-специфичные исключения

Исключения для обработки ошибок в OCR контейнере.
"""
from src.Ship.Parents.Exception import PortoException as BaseException


class OCRException(BaseException):
    """Базовое исключение для OCR операций"""
    pass


class OCRInitializationException(OCRException):
    """Ошибка инициализации OCR движка"""
    def __init__(self, message: str = "Failed to initialize OCR engine"):
        super().__init__(message)


class ImageProcessingException(OCRException):
    """Ошибка обработки изображения"""
    def __init__(self, message: str = "Failed to process image"):
        super().__init__(message)


class InvalidImageFormatException(OCRException):
    """Неподдерживаемый формат изображения"""
    def __init__(self, format: str):
        super().__init__(f"Unsupported image format: {format}")


class ImageTooLargeException(OCRException):
    """Изображение слишком большое"""
    def __init__(self, size: int, max_size: int):
        super().__init__(
            f"Image size {size} bytes exceeds maximum {max_size} bytes"
        )


class InvalidPolygonException(OCRException):
    """Некорректный полигон"""
    def __init__(self, reason: str):
        super().__init__(f"Invalid polygon: {reason}")


class OCRProcessingException(OCRException):
    """Ошибка в процессе распознавания"""
    def __init__(self, message: str = "OCR processing failed"):
        super().__init__(message)
