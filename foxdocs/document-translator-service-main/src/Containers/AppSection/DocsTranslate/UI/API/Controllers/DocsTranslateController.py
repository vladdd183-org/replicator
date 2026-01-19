"""
DocsTranslate Controller

REST API контроллер для операций обработки документов с OCR и переводом.
"""

import json
from typing import Any
from litestar import Controller, post, get, Request
from litestar.datastructures import UploadFile
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST
from litestar.exceptions import HTTPException
from dishka import FromDishka
from dishka.integrations.litestar import inject
import logfire
from src.Containers.AppSection.DocsTranslate.Actions import (
    ProcessFullImageAction,
    ProcessRegionsAction,
    GetStatusAction,
)
from src.Containers.AppSection.DocsTranslate.Data.DocsTranslateSchemas import (
    ProcessAndTranslateImageRequest,
    ProcessAndTranslateImageResponse,
    ProcessRegionsAndTranslateRequest,
    ProcessRegionsAndTranslateResponse,
    DocsTranslateStatus,
)
from src.Containers.AppSection.Translation.Data import SupportedLanguage


class DocsTranslateController(Controller):
    """
    REST API контроллер для DocsTranslate операций.
    
    Обрабатывает HTTP запросы для:
    - Обработки изображений с OCR и переводом
    - Обработки конкретных областей изображений
    - Получения статуса сервиса
    """
    
    path = "/api/v1/docs-translate"
    tags = ["DocsTranslate"]
    
    @post(
        "/process-image",
        status_code=HTTP_200_OK,
        summary="Обработать изображение с OCR и переводом",
        description="""
        Обработка изображения с OCR и переводом.
        
        Загрузите изображение и параметры через multipart/form-data:
        - file: изображение (JPEG, PNG, BMP, WEBP, TIFF)
        - from_language: исходный язык (zh, en, ru) - по умолчанию 'zh'
        - to_language: целевой язык (zh, en, ru) - по умолчанию 'ru'
        - min_confidence_threshold: минимальный порог уверенности (0.0-1.0) - по умолчанию 0.1
        - translate_empty_results: переводить ли пустые результаты (true/false) - по умолчанию false
        
        Выполняет полный цикл:
        1. Проверка лицензии (автоматически в Action)
        2. OCR распознавание всего изображения
        3. Перевод найденных текстов
        4. Возврат результатов с координатами и переводами
        """,
    )
    @inject
    async def process_image(
        self,
        request: Request[Any, Any, Any],
        action: FromDishka[ProcessFullImageAction],
    ) -> ProcessAndTranslateImageResponse:
        """
        Обработать изображение с OCR и переводом.
        
        Args:
            request: HTTP запрос с файлом и параметрами
            action: Action для обработки документов
            
        Returns:
            ProcessAndTranslateImageResponse: Результаты OCR с переводами
            
        Raises:
            HTTPException: При ошибках обработки
        """
        try:
            with logfire.span("docs_translate_process_image_endpoint"):
                # Получаем данные из формы
                form_data = await request.form()
                
                # Получаем файл
                file = form_data.get("file")
                if not file or not isinstance(file, UploadFile):
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail="File not provided in form data"
                    )
                
                # Читаем содержимое файла
                image_data = await file.read()
                
                # Получаем параметры с значениями по умолчанию
                from_language_str = form_data.get("from_language", "zh")
                to_language_str = form_data.get("to_language", "ru")
                min_confidence_threshold = float(form_data.get("min_confidence_threshold", "0.1"))
                translate_empty_results = form_data.get("translate_empty_results", "false").lower() == "true"
                
                # Валидируем языки
                try:
                    from_language = SupportedLanguage(from_language_str)
                    to_language = SupportedLanguage(to_language_str)
                except ValueError as e:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=f"Invalid language: {str(e)}. Supported: zh, en, ru"
                    )
                
                # Создаем объект запроса
                process_request = ProcessAndTranslateImageRequest(
                    from_language=from_language,
                    to_language=to_language,
                    translate_empty_results=translate_empty_results,
                    min_confidence_threshold=min_confidence_threshold
                )
                
                logfire.info(
                    "Processing image with translation",
                    filename=file.filename,
                    size=len(image_data),
                    from_lang=from_language.value,
                    to_lang=to_language.value
                )
                
                # Выполняем обработку через Action.execute()
                # Проверка лицензии произойдет автоматически внутри execute()
                result = await action.execute((image_data, process_request))
                
                logfire.info(
                    "Image processed and translated successfully",
                    translated_regions=result.translated_regions,
                    total_time=result.total_processing_time
                )
                
                return result
                
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
        "/process-regions",
        status_code=HTTP_200_OK,
        summary="Обработать области изображения с OCR и переводом",
        description="""
        Обработка конкретных областей изображения с OCR и переводом.
        
        Загрузите изображение и параметры через multipart/form-data:
        - file: изображение (JPEG, PNG, BMP, WEBP, TIFF)
        - regions: JSON массив с полигонами для обработки
        - from_language: исходный язык (zh, en, ru) - по умолчанию 'zh'
        - to_language: целевой язык (zh, en, ru) - по умолчанию 'ru'
        - min_confidence_threshold: минимальный порог уверенности (0.0-1.0) - по умолчанию 0.1
        - translate_empty_results: переводить ли пустые результаты (true/false) - по умолчанию false
        
        Каждый полигон в regions должен содержать:
        - points: массив координат [[x1,y1], [x2,y2], ...] (минимум 3 точки)
        - region_id: опциональный идентификатор области
        
        Выполняет обработку только в заданных полигональных областях:
        1. Проверка лицензии (автоматически в Action)
        2. OCR распознавание в указанных областях
        3. Перевод найденных текстов
        4. Возврат результатов по областям
        """,
    )
    @inject
    async def process_regions(
        self,
        request: Request[Any, Any, Any],
        action: FromDishka[ProcessRegionsAction],
    ) -> ProcessRegionsAndTranslateResponse:
        """
        Обработать конкретные области изображения с OCR и переводом.
        
        Args:
            request: HTTP запрос с файлом, областями и параметрами
            action: Action для обработки документов
            
        Returns:
            ProcessRegionsAndTranslateResponse: Результаты OCR с переводами по областям
            
        Raises:
            HTTPException: При ошибках обработки
        """
        try:
            with logfire.span("docs_translate_process_regions_endpoint"):
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
                
                # Валидируем регионы
                if not isinstance(regions_data, list):
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail="Regions must be an array"
                    )
                
                # Читаем содержимое файла
                image_data = await file.read()
                
                # Получаем параметры с значениями по умолчанию
                from_language_str = form_data.get("from_language", "zh")
                to_language_str = form_data.get("to_language", "ru")
                min_confidence_threshold = float(form_data.get("min_confidence_threshold", "0.1"))
                translate_empty_results = form_data.get("translate_empty_results", "false").lower() == "true"
                
                # Валидируем языки
                try:
                    from_language = SupportedLanguage(from_language_str)
                    to_language = SupportedLanguage(to_language_str)
                except ValueError as e:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=f"Invalid language: {str(e)}. Supported: zh, en, ru"
                    )
                
                # Импортируем и создаем схемы регионов
                from src.Containers.AppSection.OCR.Data import PolygonRegionSchema
                
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
                
                # Создаем объект запроса
                process_request = ProcessRegionsAndTranslateRequest(
                    regions=regions,
                    from_language=from_language,
                    to_language=to_language,
                    translate_empty_results=translate_empty_results,
                    min_confidence_threshold=min_confidence_threshold
                )
                
                logfire.info(
                    "Processing regions with translation",
                    filename=file.filename,
                    size=len(image_data),
                    regions_count=len(regions),
                    from_lang=from_language.value,
                    to_lang=to_language.value
                )
                
                # Выполняем обработку через Action.execute()
                # Проверка лицензии произойдет автоматически внутри execute()
                result = await action.execute((image_data, process_request))
                
                logfire.info(
                    "Regions processed and translated successfully",
                    translated_regions=result.translated_regions,
                    total_time=result.total_processing_time
                )
                
                return result
                
        except HTTPException:
            raise
        except Exception as e:
            logfire.error(
                "Unexpected error in process_regions",
                error=str(e)
            )
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Failed to process regions: {str(e)}"
            )
    
    @get("/status")
    @inject
    async def get_status(
        self,
        action: FromDishka[GetStatusAction],
    ) -> DocsTranslateStatus:
        """
        Получить статус сервиса DocsTranslate.
        
        Возвращает информацию о:
        - Доступности OCR сервиса
        - Доступности Translation сервиса
        - Поддерживаемых форматах изображений
        - Поддерживаемых языковых парах
        - Общей готовности сервиса
        
        Этот endpoint НЕ требует лицензии (публичный).
        
        Args:
            action: Action для получения статуса
            
        Returns:
            DocsTranslateStatus: Полный статус сервиса
        """
        # Вызываем execute() для единообразия
        # Проверка лицензии отключена в GetStatusAction (require_license = False)
        return await action.execute(None)


__all__ = ["DocsTranslateController"]
