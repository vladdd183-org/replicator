"""
Task для валидации изображения

Атомарная операция проверки корректности изображения перед обработкой.
Поддерживает конвертацию PDF в изображения.
"""
import io
from typing import Dict, Any, Tuple
from PIL import Image
import logfire

from src.Ship.Parents.Task import Task
from src.Containers.AppSection.OCR.Exceptions import (
    InvalidImageFormatException,
    ImageTooLargeException,
)

# Импорт для работы с PDF
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logfire.error("PyMuPDF not installed. PDF support disabled. Install with: pip install PyMuPDF")


class ValidateImageTask(Task):
    """
    Валидация изображения перед OCR обработкой.
    
    Single Responsibility: Проверить что изображение корректно,
    имеет поддерживаемый формат и не превышает лимиты размера.
    
    Example:
        task = ValidateImageTask()
        metadata = await task.run(image_bytes, max_size_mb=10)
    """
    
    # Поддерживаемые форматы изображений
    SUPPORTED_FORMATS = {'JPEG', 'PNG', 'BMP', 'WEBP', 'TIFF', 'PDF'}
    
    async def run(
        self,
        image_data: bytes,
        max_size_mb: float = 10.0
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Валидировать файл и вернуть байты изображения с метаданными.
        
        Поддерживает автоматическую конвертацию PDF в изображение (первая страница).
        
        Args:
            image_data: Байты файла (изображение или PDF)
            max_size_mb: Максимальный размер в мегабайтах
            
        Returns:
            Кортеж: (байты_изображения, метаданные)
            - Для обычных изображений возвращает исходные байты
            - Для PDF конвертирует первую страницу в PNG и возвращает байты PNG
            
        Raises:
            InvalidImageFormatException: При неподдерживаемом формате
            ImageTooLargeException: При превышении размера
        """
        try:
            with logfire.span("validate_image_task"):
                # Проверяем размер
                size_bytes = len(image_data)
                size_mb = size_bytes / (1024 * 1024)
                max_size_bytes = int(max_size_mb * 1024 * 1024)
                
                if size_mb > max_size_mb:
                    raise ImageTooLargeException(size_bytes, max_size_bytes)
                
                # Определяем тип файла
                file_type = self._detect_file_type(image_data)
                
                # Если это PDF, конвертируем в изображение
                if file_type == "PDF":
                    if not PDF_SUPPORT:
                        raise InvalidImageFormatException("PDF format not supported. Install PyMuPDF: pip install PyMuPDF")
                    
                    logfire.info("Converting PDF to image")
                    converted_image_data, pdf_metadata = self._convert_pdf_to_image(image_data)
                    
                    # Валидируем конвертированное изображение
                    image = Image.open(io.BytesIO(converted_image_data))
                    
                    # Собираем метаданные с информацией о конвертации
                    metadata = {
                        "width": image.width,
                        "height": image.height,
                        "mode": image.mode,
                        "format": "PNG",  # Конвертированные PDF всегда в PNG
                        "original_format": "PDF",
                        "original_size_bytes": size_bytes,
                        "original_size_mb": round(size_mb, 2),
                        "converted_size_bytes": len(converted_image_data),
                        "converted_size_mb": round(len(converted_image_data) / (1024 * 1024), 2),
                        "pdf_pages": pdf_metadata.get("pages", 1),
                        "converted_page": 1,  # Всегда конвертируем первую страницу
                    }
                    
                    logfire.info(
                        "PDF converted to image successfully",
                        **metadata
                    )
                    
                    return converted_image_data, metadata
                
                else:
                    # Обычное изображение
                    try:
                        image = Image.open(io.BytesIO(image_data))
                    except Exception as e:
                        raise InvalidImageFormatException(f"Unable to open image: {e}")
                    
                    # Проверяем формат
                    if image.format and image.format.upper() not in self.SUPPORTED_FORMATS:
                        raise InvalidImageFormatException(image.format)
                    
                    # Собираем метаданные
                    metadata = {
                        "width": image.width,
                        "height": image.height,
                        "mode": image.mode,
                        "format": image.format,
                        "size_bytes": size_bytes,
                        "size_mb": round(size_mb, 2),
                    }
                    
                    logfire.info(
                        "Image validated successfully",
                        **metadata
                    )
                    
                    return image_data, metadata
                
        except (InvalidImageFormatException, ImageTooLargeException):
            raise
        except Exception as e:
            logfire.error(
                "Image validation failed",
                error=str(e)
            )
            raise InvalidImageFormatException(
                f"Failed to validate image: {str(e)}"
            )
    
    def _detect_file_type(self, data: bytes) -> str:
        """
        Определить тип файла по магическим байтам.
        
        Args:
            data: Байты файла
            
        Returns:
            Тип файла: 'PDF', 'JPEG', 'PNG', 'BMP', 'WEBP', 'TIFF' или 'UNKNOWN'
        """
        if len(data) < 8:
            return "UNKNOWN"
        
        # Проверяем магические байты для различных форматов
        if data[:4] == b'%PDF':
            return "PDF"
        elif data[:2] == b'\xff\xd8':
            return "JPEG"
        elif data[:8] == b'\x89PNG\r\n\x1a\n':
            return "PNG"
        elif data[:2] == b'BM':
            return "BMP"
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return "WEBP"
        elif data[:4] in [b'II*\x00', b'MM\x00*']:
            return "TIFF"
        else:
            return "UNKNOWN"
    
    def _convert_pdf_to_image(self, pdf_data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """
        Конвертировать первую страницу PDF в PNG изображение.
        
        Args:
            pdf_data: Байты PDF файла
            
        Returns:
            Кортеж: (байты_png_изображения, метаданные_pdf)
            
        Raises:
            InvalidImageFormatException: При ошибке конвертации
        """
        try:
            # Открываем PDF из памяти
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            
            if doc.page_count == 0:
                raise InvalidImageFormatException("PDF file has no pages")
            
            # Получаем первую страницу
            page = doc[0]
            
            # Конвертируем в изображение с высоким качеством
            # matrix для увеличения разрешения (2x)
            matrix = fitz.Matrix(1.0, 1.0)
            pix = page.get_pixmap(matrix=matrix)
            
            # Конвертируем в PNG байты
            png_data = pix.tobytes("png")
            
            # Собираем метаданные PDF
            pdf_metadata = {
                "pages": doc.page_count,
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "page_width": page.rect.width,
                "page_height": page.rect.height,
            }
            
            # Закрываем документ
            doc.close()
            
            logfire.info(
                "PDF successfully converted to PNG",
                pages=pdf_metadata["pages"],
                png_size=len(png_data),
                original_size=len(pdf_data)
            )
            
            return png_data, pdf_metadata
            
        except Exception as e:
            logfire.error(
                "Failed to convert PDF to image",
                error=str(e),
                error_type=type(e).__name__
            )
            raise InvalidImageFormatException(f"Failed to convert PDF to image: {str(e)}")


