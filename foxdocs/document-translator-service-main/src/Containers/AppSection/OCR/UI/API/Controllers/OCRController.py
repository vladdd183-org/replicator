"""
OCR Controller

REST API endpoints для OCR операций.
"""
import json
from typing import Annotated, Any
from dishka import FromDishka
from dishka.integrations.litestar import inject
from litestar import Controller, post, Request
from litestar.datastructures import UploadFile
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST
from litestar.exceptions import HTTPException
from litestar.enums import RequestEncodingType
import logfire

from src.Containers.AppSection.OCR.Actions import (
    ProcessImageAction,
    ProcessPolygonsAction,
)
from src.Containers.AppSection.OCR.Data import (
    PolygonRegionSchema,
    ProcessImageResponseSchema,
    ProcessPolygonsResponseSchema,
)
from src.Containers.AppSection.OCR.Exceptions import (
    OCRException,
    InvalidImageFormatException,
    ImageTooLargeException,
    InvalidPolygonException,
)


class OCRController(Controller):
    """
    Controller для OCR операций.
    
    Предоставляет два endpoint:
    - /ocr/process - распознавание текста на всём изображении
    - /ocr/process-polygons - распознавание текста в полигональных областях
    """
    
    path = "/api/ocr"
    tags = ["OCR"]
    
    @post(
        "/process",
        status_code=HTTP_200_OK,
        summary="Распознать текст на изображении",
        description="""
        Распознавание текста на всём изображении.
        
        Загрузите изображение через multipart/form-data.
        Поддерживаемые форматы: JPEG, PNG, BMP, WEBP, TIFF.
        Максимальный размер: 10MB.
        
        Возвращает список всех найденных текстовых областей с координатами.
        """,
    )
    @inject
    async def process_image(
        self,
        request: Request[Any, Any, Any],
        process_image_action: FromDishka[ProcessImageAction],
    ) -> ProcessImageResponseSchema:
        """
        Обработать изображение и распознать текст.
        
        Args:
            request: HTTP запрос с файлом
            process_image_action: Action для обработки изображения
            
        Returns:
            Результаты распознавания текста
            
        Raises:
            HTTPException: При ошибках обработки
        """
        try:
            with logfire.span("ocr_process_image_endpoint"):
                # Получаем файл из формы
                form_data = await request.form()
                file = form_data.get("file")
                
                if not file or not isinstance(file, UploadFile):
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail="File not provided in form data"
                    )
                
                # Читаем содержимое файла
                file_content = await file.read()
                
                logfire.info(
                    "Processing image",
                    filename=file.filename,
                    size=len(file_content)
                )
                
                # Выполняем обработку
                try:
                    result = await process_image_action.run(file_content)
                    
                    logfire.info(
                        "Image processed successfully",
                        regions_found=result.total_regions
                    )
                    
                    return result
                    
                except InvalidImageFormatException as e:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=f"Invalid image format: {str(e)}"
                    )
                except ImageTooLargeException as e:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=str(e)
                    )
                except OCRException as e:
                    logfire.error(
                        "OCR processing failed",
                        error=str(e)
                    )
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=f"OCR processing failed: {str(e)}"
                    )
                    
        except HTTPException:
            raise
        except Exception as e:
            logfire.error(
                "Unexpected error in process_image",
                error=str(e)
            )
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Failed to process image: {str(e)}"
            )
    
    @post(
        "/process-polygons",
        status_code=HTTP_200_OK,
        summary="Распознать текст в полигональных областях",
        description="""
        Распознавание текста в заданных полигональных областях.
        
        Загрузите изображение и список полигонов через multipart/form-data:
        - file: изображение (JPEG, PNG, BMP, WEBP, TIFF)
        - regions: JSON массив с полигонами
        
        Каждый полигон должен содержать:
        - points: массив координат [[x1,y1], [x2,y2], ...] (минимум 3 точки)
        - region_id: опциональный идентификатор области
        
        Ответ содержит для каждой области:
        - text: распознанный текст
        - confidence: уверенность распознавания (0-1)
        - processing_time: время обработки в секундах
        - polygon_coordinates: исходные координаты полигона
        
        Для 4-угольных областей автоматически применяется перспективное выпрямление.
        """,
    )
    @inject
    async def process_polygons(
        self,
        request: Request[Any, Any, Any],
        process_polygons_action: FromDishka[ProcessPolygonsAction],
    ) -> ProcessPolygonsResponseSchema:
        """
        Обработать полигональные области на изображении.
        
        Args:
            request: HTTP запрос с файлом и регионами
            process_polygons_action: Action для обработки полигонов
            
        Returns:
            Результаты распознавания по областям
            
        Raises:
            HTTPException: При ошибках обработки
        """
        try:
            with logfire.span("ocr_process_polygons_endpoint"):
                # Получаем данные из формы
                form_data = await request.form()
                
                # Получаем файл
                file = form_data.get("file")
                if not file or not isinstance(file, UploadFile):
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail="File not provided in form data"
                    )
                
                # Получаем regions
                regions_json = form_data.get("regions")
                if not regions_json:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail="Regions not provided in form data"
                    )
                
                # Парсим JSON с регионами
                try:
                    if isinstance(regions_json, str):
                        regions_data = json.loads(regions_json)
                    else:
                        regions_data = regions_json
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=f"Invalid JSON in regions field: {str(e)}"
                    )
                
                # Валидируем и создаём схемы регионов
                if not isinstance(regions_data, list):
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail="Regions must be an array"
                    )
                
                regions = []
                for idx, region_data in enumerate(regions_data):
                    try:
                        region = PolygonRegionSchema(**region_data)
                        regions.append(region)
                    except Exception as e:
                        raise HTTPException(
                            status_code=HTTP_400_BAD_REQUEST,
                            detail=f"Invalid region at index {idx}: {str(e)}"
                        )
                
                if not regions:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail="At least one region must be provided"
                    )
                
                # Читаем файл
                file_content = await file.read()
                
                logfire.info(
                    "Processing polygons",
                    filename=file.filename,
                    size=len(file_content),
                    regions_count=len(regions)
                )
                
                # Выполняем обработку
                try:
                    result = await process_polygons_action.run(
                        file_content,
                        regions
                    )
                    
                    logfire.info(
                        "Polygons processed successfully",
                        regions_processed=result.total_regions
                    )
                    
                    return result
                    
                except InvalidImageFormatException as e:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=f"Invalid image format: {str(e)}"
                    )
                except ImageTooLargeException as e:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=str(e)
                    )
                except InvalidPolygonException as e:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=f"Invalid polygon: {str(e)}"
                    )
                except OCRException as e:
                    logfire.error(
                        "OCR processing failed",
                        error=str(e)
                    )
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=f"OCR processing failed: {str(e)}"
                    )
                    
        except HTTPException:
            raise
        except Exception as e:
            logfire.error(
                "Unexpected error in process_polygons",
                error=str(e)
            )
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Failed to process polygons: {str(e)}"
            )
