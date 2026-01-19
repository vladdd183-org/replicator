"""
Streaming Process And Translate Image Task

Атомарная задача для потоковой обработки изображения с OCR и переводом.
Использует pipeline архитектуру с параллельными воркерами.
"""

import time
import asyncio
from typing import List, Callable, Awaitable, Dict, Any
from PIL import Image
import io
import logfire

from src.Ship.Parents.Task import Task
from src.Containers.AppSection.OCR.Services import OCRService
from src.Containers.AppSection.Translation.Managers import TranslationServerManager
from src.Containers.AppSection.Translation.Data import SupportedLanguage

from ..Data.DocsTranslateSchemas import (
    StreamingProcessAndTranslateImageRequest,
    ProcessAndTranslateImageResponse,
    TranslatedOCRResult,
    ProgressEventType,
)
from ..Exceptions.DocsTranslateExceptions import (
    OCRServiceUnavailableException,
    TranslationServiceUnavailableException,
    ProcessingFailedException,
    NoTextFoundException,
)


class StreamingProcessAndTranslateTask(Task):
    """
    Task для потоковой обработки полного изображения с OCR и переводом.
    
    Использует pipeline архитектуру:
    1. Детекция всех текстовых областей (быстро)
    2. Параллельная обработка областей:
       - Воркеры OCR: распознавание текста
       - Воркеры Translation: перевод текста
    3. Промежуточные результаты отправляются сразу через callback
    
    Единая ответственность: потоковая обработка изображения с переводом.
    """
    
    # Фиксированные оптимальные значения воркеров
    OCR_WORKERS = 1  # Из-за thread-safety PaddleOCR (threading.Lock)
    TRANSLATION_WORKERS = 2  # Оптимально для параллелизма с OCR
    
    def __init__(
        self,
        ocr_service: OCRService,
        translation_manager: TranslationServerManager,
    ):
        """
        Инициализация с сервисами.
        
        Args:
            ocr_service: Сервис OCR для прямого доступа к детекции
            translation_manager: Менеджер Translation сервиса
        """
        self.ocr_service = ocr_service
        self.translation_manager = translation_manager
    
    async def run(self, data):
        """
        Заглушка для соответствия интерфейсу Task.
        
        Для streaming обработки используйте метод run_streaming().
        
        Raises:
            NotImplementedError: Всегда, так как нужно использовать run_streaming()
        """
        raise NotImplementedError(
            "StreamingProcessAndTranslateTask requires run_streaming() method with progress_callback. "
            "Use run_streaming(image_data, request, progress_callback) instead."
        )
    
    async def run_streaming(
        self, 
        image_data: bytes, 
        request: StreamingProcessAndTranslateImageRequest,
        progress_callback: Callable[[ProgressEventType, Dict[str, Any]], Awaitable[None]]
    ) -> ProcessAndTranslateImageResponse:
        """
        Выполнить потоковую обработку изображения с переводом.
        
        Args:
            image_data: Байты изображения
            request: Параметры обработки с streaming config
            progress_callback: Async callback для отправки прогресса
                Сигнатура: async def callback(event_type, event_data)
            
        Returns:
            ProcessAndTranslateImageResponse: Финальный результат с переводами
            
        Raises:
            OCRServiceUnavailableException: OCR сервис недоступен
            TranslationServiceUnavailableException: Translation сервис недоступен
            ProcessingFailedException: Ошибка при обработке
            NoTextFoundException: Текст не найден
        """
        start_time = time.time()
        
        with logfire.span(
            "streaming_process_and_translate_image_task",
            image_size=len(image_data),
            from_lang=request.from_language.value,
            to_lang=request.to_language.value,
            ocr_workers=self.OCR_WORKERS,
            translation_workers=self.TRANSLATION_WORKERS
        ):
            try:
                # === Этап 1: Детекция областей ===
                await progress_callback(ProgressEventType.DETECTION_STARTED, {
                    "message": "Starting text regions detection..."
                })
                
                with logfire.span("detection_phase"):
                    detection_start = time.time()
                    
                    # Получаем размеры изображения для метаданных
                    image = Image.open(io.BytesIO(image_data))
                    image_dimensions = {"width": image.width, "height": image.height}
                    
                    # Детектируем области (БЕЗ распознавания) - в отдельном потоке
                    detected_regions = await asyncio.to_thread(
                        self.ocr_service.detect_text_regions_only,
                        image_data
                    )
                    
                    detection_time = time.time() - detection_start
                    
                    logfire.info(
                        "Text regions detected",
                        regions_count=len(detected_regions),
                        detection_time=detection_time
                    )
                
                if not detected_regions:
                    raise NoTextFoundException("No text regions found on image")
                
                # Отправляем информацию о найденных областях
                if request.streaming_config.send_region_preview:
                    await progress_callback(ProgressEventType.REGIONS_DETECTED, {
                        "total_regions": len(detected_regions),
                        "regions": [
                            {
                                "region_index": idx,
                                "coordinates": region
                            }
                            for idx, region in enumerate(detected_regions)
                        ]
                    })
                
                # === Этап 2: Pipeline обработка ===
                translated_results = await self._pipeline_process_regions(
                    image_data=image_data,
                    detected_regions=detected_regions,
                    from_language=request.from_language,
                    to_language=request.to_language,
                    min_confidence=request.min_confidence_threshold,
                    translate_empty=request.translate_empty_results,
                    ocr_workers_count=self.OCR_WORKERS,
                    translation_workers_count=self.TRANSLATION_WORKERS,
                    progress_callback=progress_callback
                )
                
                # === Этап 3: Формирование финального ответа ===
                total_processing_time = time.time() - start_time
                
                # Рассчитываем время каждого этапа
                ocr_processing_time = detection_time  # Детекция + распознавание
                translation_processing_time = 0  # Рассчитается из логов воркеров
                
                response = ProcessAndTranslateImageResponse(
                    results=translated_results,
                    total_regions=len(detected_regions),
                    translated_regions=len(translated_results),
                    skipped_regions=len(detected_regions) - len(translated_results),
                    image_dimensions=image_dimensions,
                    ocr_processing_time=ocr_processing_time,
                    translation_processing_time=translation_processing_time,
                    total_processing_time=total_processing_time,
                    from_language=request.from_language,
                    to_language=request.to_language
                )
                
                # Отправляем событие завершения
                await progress_callback(ProgressEventType.PROCESSING_COMPLETED, {
                    "total_regions": len(detected_regions),
                    "successfully_processed": len(translated_results),
                    "failed_regions": len(detected_regions) - len(translated_results),
                    "total_processing_time": total_processing_time
                })
                
                logfire.info(
                    "Streaming process and translate completed",
                    total_regions=response.total_regions,
                    translated_regions=response.translated_regions,
                    total_time=total_processing_time
                )
                
                return response
                
            except Exception as e:
                if isinstance(e, (OCRServiceUnavailableException, 
                               TranslationServiceUnavailableException,
                               NoTextFoundException)):
                    raise
                
                logfire.error(
                    "Streaming process and translate task failed",
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                # Отправляем событие ошибки
                await progress_callback(ProgressEventType.PROCESSING_FAILED, {
                    "error_message": str(e),
                    "error_type": type(e).__name__
                })
                
                raise ProcessingFailedException("streaming_image_processing", str(e))
    
    async def _pipeline_process_regions(
        self,
        image_data: bytes,
        detected_regions: List[List[List[float]]],
        from_language: SupportedLanguage,
        to_language: SupportedLanguage,
        min_confidence: float,
        translate_empty: bool,
        ocr_workers_count: int,
        translation_workers_count: int,
        progress_callback: Callable[[ProgressEventType, Dict[str, Any]], Awaitable[None]]
    ) -> List[TranslatedOCRResult]:
        """
        Pipeline обработка областей с параллельными воркерами.
        
        Architecture:
            OCR Queue → [OCR Worker 1, OCR Worker 2, ...] → Translation Queue 
            → [Translation Worker 1, Translation Worker 2, ...] → Results
        
        Args:
            image_data: Байты изображения
            detected_regions: Список координат областей
            from_language: Исходный язык
            to_language: Целевой язык
            min_confidence: Минимальный порог уверенности
            translate_empty: Переводить ли пустые результаты
            ocr_workers_count: Количество OCR воркеров
            translation_workers_count: Количество Translation воркеров
            progress_callback: Callback для отправки прогресса
            
        Returns:
            List[TranslatedOCRResult]: Переведённые результаты
        """
        with logfire.span("pipeline_processing"):
            # Очереди для pipeline
            ocr_queue: asyncio.Queue = asyncio.Queue()
            translation_queue: asyncio.Queue = asyncio.Queue()
            
            # Результаты (потокобезопасное хранилище)
            results_lock = asyncio.Lock()
            translated_results: List[TranslatedOCRResult] = []
            failed_regions_count = 0
            
            # Заполняем OCR очередь всеми областями
            for idx, region_coords in enumerate(detected_regions):
                await ocr_queue.put((idx, region_coords))
            
            # Sentinel values для завершения воркеров
            for _ in range(ocr_workers_count):
                await ocr_queue.put(None)
            
            # === OCR Worker ===
            async def ocr_worker(worker_id: int):
                """Воркер для распознавания текста в областях."""
                nonlocal failed_regions_count
                
                logfire.info(f"OCR Worker {worker_id} started")
                
                while True:
                    item = await ocr_queue.get()
                    
                    if item is None:  # Sentinel value - завершаем воркер
                        ocr_queue.task_done()
                        logfire.info(f"OCR Worker {worker_id} finished")
                        break
                    
                    region_index, region_coords = item
                    
                    try:
                        # Отправляем событие начала OCR
                        await progress_callback(ProgressEventType.REGION_OCR_STARTED, {
                            "region_index": region_index
                        })
                        
                        # Распознаём текст в области (в отдельном потоке чтобы не блокировать event loop)
                        text, confidence = await asyncio.to_thread(
                            self.ocr_service.process_polygon_region,
                            image_data, 
                            region_coords
                        )
                        
                        logfire.info(
                            f"OCR Worker {worker_id} processed region {region_index}",
                            text=text[:50] if text else "",
                            confidence=confidence
                        )
                        
                        # Отправляем событие завершения OCR
                        await progress_callback(ProgressEventType.REGION_OCR_COMPLETED, {
                            "region_index": region_index,
                            "original_text": text,
                            "confidence": confidence,
                            "coordinates": region_coords
                        })
                        
                        # Фильтрация по confidence
                        if (confidence >= min_confidence and text.strip()) or translate_empty:
                            # Добавляем в очередь перевода
                            logfire.info(f"OCR Worker {worker_id}: Adding region {region_index} to translation queue")
                            await translation_queue.put((region_index, region_coords, text, confidence))
                        else:
                            logfire.info(
                                f"Region {region_index} skipped (low confidence)",
                                confidence=confidence,
                                threshold=min_confidence
                            )
                    
                    except Exception as e:
                        logfire.error(
                            f"OCR Worker {worker_id} failed on region {region_index}",
                            error=str(e)
                        )
                        
                        async with results_lock:
                            failed_regions_count += 1
                        
                        await progress_callback(ProgressEventType.REGION_OCR_FAILED, {
                            "region_index": region_index,
                            "error_message": str(e)
                        })
                    
                    finally:
                        ocr_queue.task_done()
            
            # === Translation Worker ===
            async def translation_worker(worker_id: int):
                """Воркер для перевода текстов."""
                nonlocal failed_regions_count
                
                logfire.info(f"🔵 Translation Worker {worker_id} started and waiting for tasks...")
                
                while True:
                    logfire.info(f"🔵 Translation Worker {worker_id} waiting for item from queue...")
                    item = await translation_queue.get()
                    logfire.info(f"🔵 Translation Worker {worker_id} got item: {item is not None}")
                    
                    if item is None:  # Sentinel value - завершаем воркер
                        translation_queue.task_done()
                        logfire.info(f"🔵 Translation Worker {worker_id} finished")
                        break
                    
                    region_index, region_coords, original_text, confidence = item
                    
                    try:
                        # Отправляем событие начала перевода
                        await progress_callback(ProgressEventType.REGION_TRANSLATION_STARTED, {
                            "region_index": region_index
                        })
                        
                        # Переводим текст
                        translation = await self.translation_manager.translate_text(
                            text=original_text,
                            from_language=from_language,
                            to_language=to_language
                        )
                        
                        logfire.info(
                            f"🔵 Translation Worker {worker_id} translated region {region_index}",
                            original=original_text[:30],
                            translated=translation.translated_text[:30]
                        )
                        
                        # Создаём результат
                        translated_result = TranslatedOCRResult(
                            original_text=original_text,
                            confidence=confidence,
                            coordinates=region_coords,
                            translated_text=translation.translated_text,
                            from_language=translation.from_language,
                            to_language=translation.to_language,
                            intermediate_language=translation.intermediate_language,
                            intermediate_text=translation.intermediate_text
                        )
                        
                        # Добавляем результат в список (потокобезопасно)
                        async with results_lock:
                            translated_results.append(translated_result)
                        
                        # Отправляем событие завершения перевода
                        await progress_callback(ProgressEventType.REGION_TRANSLATED, {
                            "region_index": region_index,
                            "original_text": original_text,
                            "translated_text": translation.translated_text,
                            "confidence": confidence,
                            "coordinates": region_coords,
                            "from_language": translation.from_language.value,
                            "to_language": translation.to_language.value,
                            "intermediate_language": translation.intermediate_language.value if translation.intermediate_language else None,
                            "intermediate_text": translation.intermediate_text
                        })
                    
                    except Exception as e:
                        logfire.error(
                            f"Translation Worker {worker_id} failed on region {region_index}",
                            error=str(e)
                        )
                        
                        async with results_lock:
                            failed_regions_count += 1
                        
                        await progress_callback(ProgressEventType.REGION_TRANSLATION_FAILED, {
                            "region_index": region_index,
                            "error_message": str(e),
                            "stage": "translation"
                        })
                    
                    finally:
                        translation_queue.task_done()
            
            # Запускаем воркеры параллельно
            logfire.info(
                "Starting pipeline workers",
                ocr_workers=ocr_workers_count,
                translation_workers=translation_workers_count
            )
            
            # Создаём задачи для ВСЕХ воркеров одновременно (OCR и Translation)
            ocr_workers = [
                asyncio.create_task(ocr_worker(i)) 
                for i in range(ocr_workers_count)
            ]
            
            translation_workers = [
                asyncio.create_task(translation_worker(i)) 
                for i in range(translation_workers_count)
            ]
            
            # Ждём пока все OCR воркеры завершатся
            await asyncio.gather(*ocr_workers)
            
            # Добавляем sentinel values для translation воркеров ПОСЛЕ завершения OCR
            for _ in range(translation_workers_count):
                await translation_queue.put(None)
            
            # Ждём пока все Translation воркеры завершатся
            await asyncio.gather(*translation_workers)
            
            logfire.info(
                "Pipeline processing completed",
                total_translated=len(translated_results),
                total_failed=failed_regions_count
            )
            
            return translated_results


__all__ = ["StreamingProcessAndTranslateTask"]





