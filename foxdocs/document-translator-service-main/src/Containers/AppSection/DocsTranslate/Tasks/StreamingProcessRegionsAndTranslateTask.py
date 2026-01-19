"""
Streaming Process Regions And Translate Task

Атомарная задача для потоковой обработки заданных областей с OCR и переводом.
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
    StreamingProcessRegionsAndTranslateRequest,
    ProcessRegionsAndTranslateResponse,
    TranslatedOCRResult,
    ProgressEventType,
)
from ..Exceptions.DocsTranslateExceptions import (
    OCRServiceUnavailableException,
    TranslationServiceUnavailableException,
    ProcessingFailedException,
    NoTextFoundException,
)


class StreamingProcessRegionsAndTranslateTask(Task):
    """
    Task для потоковой обработки заданных областей изображения с OCR и переводом.
    
    Использует pipeline архитектуру:
    1. Принимает готовые области от пользователя
    2. Параллельная обработка областей:
       - Воркеры OCR: распознавание текста
       - Воркеры Translation: перевод текста
    3. Промежуточные результаты отправляются сразу через callback
    
    Единая ответственность: потоковая обработка заданных областей с переводом.
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
            ocr_service: Сервис OCR для распознавания областей
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
            "StreamingProcessRegionsAndTranslateTask requires run_streaming() method with progress_callback. "
            "Use run_streaming(image_data, request, progress_callback) instead."
        )
    
    async def run_streaming(
        self, 
        image_data: bytes, 
        request: StreamingProcessRegionsAndTranslateRequest,
        progress_callback: Callable[[ProgressEventType, Dict[str, Any]], Awaitable[None]]
    ) -> ProcessRegionsAndTranslateResponse:
        """
        Выполнить потоковую обработку заданных областей с переводом.
        
        Args:
            image_data: Байты изображения
            request: Параметры обработки с областями и streaming config
            progress_callback: Async callback для отправки прогресса
                Сигнатура: async def callback(event_type, event_data)
            
        Returns:
            ProcessRegionsAndTranslateResponse: Финальный результат с переводами
            
        Raises:
            OCRServiceUnavailableException: OCR сервис недоступен
            TranslationServiceUnavailableException: Translation сервис недоступен
            ProcessingFailedException: Ошибка при обработке
            NoTextFoundException: Текст не найден
        """
        start_time = time.time()
        
        with logfire.span(
            "streaming_process_regions_and_translate_task",
            image_size=len(image_data),
            regions_count=len(request.regions),
            from_lang=request.from_language.value,
            to_lang=request.to_language.value,
            ocr_workers=self.OCR_WORKERS,
            translation_workers=self.TRANSLATION_WORKERS
        ):
            try:
                # Получаем размеры изображения для метаданных
                image = Image.open(io.BytesIO(image_data))
                image_dimensions = {"width": image.width, "height": image.height}
                
                # Отправляем информацию о количестве областей для обработки
                if request.streaming_config.send_region_preview:
                    await progress_callback(ProgressEventType.REGIONS_DETECTED, {
                        "total_regions": len(request.regions),
                        "regions": [
                            {
                                "region_index": idx,
                                "coordinates": region.points,
                                "region_id": region.region_id
                            }
                            for idx, region in enumerate(request.regions)
                        ]
                    })
                
                # === Pipeline обработка ===
                translated_results = await self._pipeline_process_regions(
                    image_data=image_data,
                    regions=request.regions,
                    from_language=request.from_language,
                    to_language=request.to_language,
                    min_confidence=request.min_confidence_threshold,
                    translate_empty=request.translate_empty_results,
                    ocr_workers_count=self.OCR_WORKERS,
                    translation_workers_count=self.TRANSLATION_WORKERS,
                    progress_callback=progress_callback
                )
                
                # === Формирование финального ответа ===
                total_processing_time = time.time() - start_time
                
                # Рассчитываем время каждого этапа
                ocr_processing_time = 0  # Рассчитается из логов воркеров
                translation_processing_time = 0  # Рассчитается из логов воркеров
                
                response = ProcessRegionsAndTranslateResponse(
                    results=translated_results,
                    total_regions=len(request.regions),
                    translated_regions=len(translated_results),
                    skipped_regions=len(request.regions) - len(translated_results),
                    image_dimensions=image_dimensions,
                    ocr_processing_time=ocr_processing_time,
                    translation_processing_time=translation_processing_time,
                    total_processing_time=total_processing_time,
                    from_language=request.from_language,
                    to_language=request.to_language
                )
                
                # Отправляем событие завершения
                await progress_callback(ProgressEventType.PROCESSING_COMPLETED, {
                    "total_regions": len(request.regions),
                    "successfully_processed": len(translated_results),
                    "failed_regions": len(request.regions) - len(translated_results),
                    "total_processing_time": total_processing_time
                })
                
                logfire.info(
                    "Streaming process regions and translate completed",
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
                    "Streaming process regions and translate task failed",
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                # Отправляем событие ошибки
                await progress_callback(ProgressEventType.PROCESSING_FAILED, {
                    "error_message": str(e),
                    "error_type": type(e).__name__
                })
                
                raise ProcessingFailedException("streaming_regions_processing", str(e))
    
    async def _pipeline_process_regions(
        self,
        image_data: bytes,
        regions: List,
        from_language: SupportedLanguage,
        to_language: SupportedLanguage,
        min_confidence: float,
        translate_empty: bool,
        ocr_workers_count: int,
        translation_workers_count: int,
        progress_callback: Callable[[ProgressEventType, Dict[str, Any]], Awaitable[None]]
    ) -> List[TranslatedOCRResult]:
        """
        Pipeline обработка заданных областей с параллельными воркерами.
        
        Architecture:
            OCR Queue → [OCR Worker 1, OCR Worker 2, ...] → Translation Queue 
            → [Translation Worker 1, Translation Worker 2, ...] → Results
        
        Args:
            image_data: Байты изображения
            regions: Список заданных полигональных областей
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
        with logfire.span("pipeline_processing_regions"):
            # Очереди для pipeline
            ocr_queue: asyncio.Queue = asyncio.Queue()
            translation_queue: asyncio.Queue = asyncio.Queue()
            
            # Результаты (потокобезопасное хранилище)
            results_lock = asyncio.Lock()
            translated_results: List[TranslatedOCRResult] = []
            failed_regions_count = 0
            
            # Заполняем OCR очередь всеми областями
            for idx, region in enumerate(regions):
                await ocr_queue.put((idx, region))
            
            # Sentinel values для завершения воркеров
            for _ in range(ocr_workers_count):
                await ocr_queue.put(None)
            
            # === OCR Worker ===
            async def ocr_worker(worker_id: int):
                """Воркер для распознавания текста в областях."""
                nonlocal failed_regions_count
                
                logfire.info(f"OCR Worker {worker_id} started (regions)")
                
                while True:
                    item = await ocr_queue.get()
                    
                    if item is None:  # Sentinel value - завершаем воркер
                        ocr_queue.task_done()
                        logfire.info(f"OCR Worker {worker_id} finished (regions)")
                        break
                    
                    region_index, region = item
                    
                    try:
                        # Отправляем событие начала OCR
                        await progress_callback(ProgressEventType.REGION_OCR_STARTED, {
                            "region_index": region_index
                        })
                        
                        # Распознаём текст в области (в отдельном потоке чтобы не блокировать event loop)
                        text, confidence = await asyncio.to_thread(
                            self.ocr_service.process_polygon_region,
                            image_data, 
                            region.points
                        )
                        
                        logfire.info(
                            f"OCR Worker {worker_id} processed region {region_index}",
                            region_id=region.region_id,
                            text=text[:50] if text else "",
                            confidence=confidence
                        )
                        
                        # Отправляем событие завершения OCR
                        await progress_callback(ProgressEventType.REGION_OCR_COMPLETED, {
                            "region_index": region_index,
                            "region_id": region.region_id,
                            "original_text": text,
                            "confidence": confidence,
                            "coordinates": region.points
                        })
                        
                        # Фильтрация по confidence
                        if (confidence >= min_confidence and text.strip()) or translate_empty:
                            # Добавляем в очередь перевода
                            logfire.info(f"OCR Worker {worker_id}: Adding region {region_index} to translation queue")
                            await translation_queue.put((region_index, region, text, confidence))
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
                
                logfire.info(f"🔵 Translation Worker {worker_id} started (regions) and waiting for tasks...")
                
                while True:
                    logfire.info(f"🔵 Translation Worker {worker_id} (regions) waiting for item from queue...")
                    item = await translation_queue.get()
                    logfire.info(f"🔵 Translation Worker {worker_id} (regions) got item: {item is not None}")
                    
                    if item is None:  # Sentinel value - завершаем воркер
                        translation_queue.task_done()
                        logfire.info(f"🔵 Translation Worker {worker_id} finished (regions)")
                        break
                    
                    region_index, region, original_text, confidence = item
                    
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
                            region_id=region.region_id,
                            original=original_text[:30],
                            translated=translation.translated_text[:30]
                        )
                        
                        # Создаём результат
                        translated_result = TranslatedOCRResult(
                            original_text=original_text,
                            confidence=confidence,
                            coordinates=region.points,  # Используем polygon coordinates
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
                            "region_id": region.region_id,
                            "original_text": original_text,
                            "translated_text": translation.translated_text,
                            "confidence": confidence,
                            "coordinates": region.points,
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
                "Starting pipeline workers for regions",
                ocr_workers=ocr_workers_count,
                translation_workers=translation_workers_count,
                total_regions=len(regions)
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
                "Pipeline processing of regions completed",
                total_translated=len(translated_results),
                total_failed=failed_regions_count
            )
            
            return translated_results


__all__ = ["StreamingProcessRegionsAndTranslateTask"]





