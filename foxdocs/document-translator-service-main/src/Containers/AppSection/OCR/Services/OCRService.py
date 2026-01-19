"""
OCR Service - основной сервис для распознавания текста

Содержит бизнес-логику для работы с PaddleOCR.
"""
import os
import threading
from typing import Optional, List, Tuple
from pathlib import Path
import numpy as np
import cv2
from paddleocr import PaddleOCR, TextRecognition
import logfire
from src.Containers.AppSection.OCR.Exceptions import (
    OCRInitializationException,
    OCRProcessingException,
)


class OCRService:
    """
    Сервис для работы с OCR движками.
    
    Загружает и инициализирует модели при старте приложения.
    Обеспечивает thread-safe доступ к единственному экземпляру.
    """
    
    _instance: Optional['OCRService'] = None
    _lock = threading.Lock()
    _initialized = False
    _ocr_lock = threading.Lock()  # Lock для защиты OCR операций от race conditions
    
    @staticmethod
    def _find_local_model_paths() -> dict:
        """Находим пути к локальным моделям PaddleOCR в стандартных путях кеширования."""
        model_paths = {}
        
        # Стандартные пути кеширования PaddleOCR в Docker контейнере
        possible_cache_paths = [
            # Новый формат PaddleX (как видно из логов)
            Path("/app/.paddlex/official_models"),
            # Старый формат PaddleOCR
            Path("/app/.cache/paddle/whl"),
            # Альтернативный путь в HOME
            Path("/app/.paddleocr"),
            # Дополнительные пути на случай других настроек
            Path(os.environ.get("HOME", "/app")) / ".paddlex" / "official_models",
            Path(os.environ.get("XDG_CACHE_HOME", "/app/.cache")) / "paddle" / "whl",
            Path(os.environ.get("HOME", "/app")) / ".paddleocr",
        ]
        
        # Ищем основные модели, которые используются в проекте
        required_models = {
            "text_detection": "PP-OCRv5_server_det",  # Детекция текста
            "text_recognition": "PP-OCRv5_server_rec",  # Распознавание текста
        }
        
        logfire.info("Searching for PaddleOCR models in standard cache paths...")
        
        for cache_path in possible_cache_paths:
            if not cache_path.exists():
                logfire.debug(f"Cache path does not exist: {cache_path}")
                continue
                
            logfire.debug(f"Checking cache path: {cache_path}")
            
            for model_type, model_name in required_models.items():
                # Пропускаем если модель уже найдена
                if model_type in model_paths:
                    continue
                    
                # Ищем директории с именем модели
                model_dirs = list(cache_path.rglob(f"*{model_name}*"))
                if model_dirs:
                    # Проверяем наличие файлов модели (.pdmodel, .pdiparams и т.д.)
                    for model_dir in model_dirs:
                        if model_dir.is_dir() and (
                            any(model_dir.glob("*.pdmodel")) or
                            any(model_dir.glob("*.pdiparams")) or
                            any(model_dir.glob("inference.pdmodel"))
                        ):
                            model_paths[model_type] = str(model_dir)
                            logfire.info(f"Found {model_type} model at: {model_dir}")
                            break
            
            # Если нашли все требуемые модели в одном из путей кеша
            if len(model_paths) >= len(required_models):
                break
        
        logfire.info(f"Model search completed. Found {len(model_paths)} models: {list(model_paths.keys())}")
        return model_paths
    
    @staticmethod
    def _check_models_exist() -> bool:
        """Проверяем наличие основных моделей PaddleOCR локально."""
        model_paths = OCRService._find_local_model_paths()
        return len(model_paths) >= 2  # Нужны обе модели: детекция и распознавание
    
    def __new__(cls) -> 'OCRService':
        """Реализация паттерна Singleton"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(OCRService, cls).__new__(cls)
                    logfire.info("Creating new OCRService instance")
        return cls._instance
    
    def __init__(self):
        """Инициализация OCR движков"""
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            try:
                logfire.info("Initializing OCR engines...")
                
                # Проверяем наличие моделей локально и получаем пути
                local_model_paths = self._find_local_model_paths()
                models_exist = len(local_model_paths) >= 2
                
                logfire.info(
                    "OCR models availability check", 
                    models_exist=models_exist,
                    found_models=list(local_model_paths.keys())
                )
                
                # Инициализируем основной OCR движок (детекция + распознавание)
                try:
                    if models_exist:
                        # Используем локальные модели для избежания обращения к серверу
                        logfire.info("Initializing OCR with local model paths", model_paths=local_model_paths)
                        
                        self.ocr_engine = PaddleOCR(
                            use_angle_cls=False,  # Поворот текста
                            lang='ch',
                            use_doc_orientation_classify=False,  # Отключаем классификацию ориентации документа
                            use_doc_unwarping=False,
                            # Указываем локальные пути к моделям
                            text_detection_model_dir=local_model_paths.get("text_detection"),
                            text_recognition_model_dir=local_model_paths.get("text_recognition"),
                        )
                        logfire.info("Main OCR engine initialized successfully with local models")
                    else:
                        # Fallback: инициализация без указания путей (будет скачивать модели)
                        logfire.info("OCR models not found locally, initializing with download")
                        
                        self.ocr_engine = PaddleOCR(
                            use_angle_cls=False,  # Поворот текста
                            lang='ch',
                            use_doc_orientation_classify=False,  # Отключаем классификацию ориентации документа
                            use_doc_unwarping=False,
                        )
                        logfire.info("Main OCR engine initialized successfully with downloaded models")
                except Exception as ocr_error:
                    logfire.error("Failed to initialize main OCR engine", error=str(ocr_error))
                    # Если не удалось инициализировать из-за отсутствия интернета, 
                    # попробуем работать только с локальными моделями
                    if "No available model hosting platforms" in str(ocr_error):
                        if models_exist:
                            # Попробуем повторно с локальными моделями
                            logfire.info("Retrying OCR initialization with local models only")
                            self.ocr_engine = PaddleOCR(
                                use_angle_cls=False,
                                lang='ch',
                                use_doc_orientation_classify=False,
                                use_doc_unwarping=False,
                            )
                        else:
                            raise OCRInitializationException("OCR models not available locally and cannot download from remote")
                    else:
                        raise
                
                # Инициализируем отдельный движок только для распознавания текста
                # (для случаев, когда у нас уже есть вырезанные области)
                try:
                    logfire.info("Initializing TextRecognition model for polygon regions")
                    
                    if models_exist and local_model_paths.get("text_recognition"):
                        # Используем локальную модель
                        logfire.info("Initializing TextRecognition with local model", 
                                   model_path=local_model_paths["text_recognition"])
                        self.text_recognizer = TextRecognition(
                            model_dir=local_model_paths["text_recognition"]
                        )
                    else:
                        # Fallback: используем имя модели (будет скачивать)
                        logfire.info("Initializing TextRecognition with model name")
                        self.text_recognizer = TextRecognition(model_name="PP-OCRv5_server_rec")
                    
                    logfire.info("TextRecognition engine initialized successfully")
                except Exception as text_rec_error:
                    logfire.error("Failed to initialize TextRecognition engine", error=str(text_rec_error))
                    # TextRecognition не критичен, можно работать без него
                    self.text_recognizer = None
                
                self._initialized = True
                logfire.info(
                    "OCR engines initialized successfully",
                    main_engine=str(type(self.ocr_engine)),
                    text_recognizer=str(type(self.text_recognizer)) if self.text_recognizer else "None"
                )
                
            except Exception as e:
                logfire.error(
                    "Failed to initialize OCR engines", 
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise OCRInitializationException(f"OCR initialization failed: {str(e)}")
    
    def process_full_image(self, image_data: bytes) -> List[Tuple[List[List[float]], str, float]]:
        """
        Обработать полное изображение и найти весь текст.
        
        Args:
            image_data: Байты изображения
            
        Returns:
            Список кортежей: (координаты_полигона, текст, уверенность)
            
        Raises:
            OCRProcessingException: При ошибке обработки
        """
        try:
            with logfire.span("ocr_process_full_image"):
                # Декодируем изображение
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    raise OCRProcessingException("Failed to decode image")
                
                logfire.info(
                    "Processing full image",
                    image_shape=image.shape,
                    image_size=len(image_data)
                )
                
                # Запускаем полный OCR (детекция + распознавание)
                # Защищаем OCR операции от race conditions
                with self._ocr_lock:
                    results = self.ocr_engine.ocr(image)
                
                if not results or not results[0]:
                    logfire.info("No text found in image")
                    return []
                
                # Обрабатываем результаты
                processed_results = []
                result_data = results[0]
                
                # Проверяем, какой формат данных мы получили
                if isinstance(result_data, dict):
                    # Новый формат с полями rec_texts, rec_scores, rec_polys
                    rec_texts = result_data.get('rec_texts', [])
                    rec_scores = result_data.get('rec_scores', [])
                    rec_polys = result_data.get('rec_polys', [])
                    
                    # Объединяем данные
                    for i in range(len(rec_texts)):
                        text = rec_texts[i] if i < len(rec_texts) else ""
                        confidence = rec_scores[i] if i < len(rec_scores) else 0.0
                        
                        # Получаем координаты полигона
                        if i < len(rec_polys):
                            poly = rec_polys[i]
                            # Преобразуем numpy array в список списков
                            if hasattr(poly, 'tolist'):
                                bbox = poly.tolist()
                            else:
                                bbox = poly
                        else:
                            bbox = [[0, 0], [0, 0], [0, 0], [0, 0]]
                        
                        # Убеждаемся, что bbox это список списков координат
                        if not isinstance(bbox, list) or not bbox:
                            bbox = [[0, 0], [0, 0], [0, 0], [0, 0]]
                        
                        processed_results.append((bbox, text, confidence))
                        
                        logfire.debug("Processing OCR result", 
                                    text=text, 
                                    confidence=confidence,
                                    bbox_shape=f"{len(bbox)}x{len(bbox[0]) if bbox else 0}")
                
                else:
                    # Старый формат - список строк с bbox и текстом
                    for line in result_data:
                        logfire.debug("Processing OCR result line", line_data=str(line)[:200])
                        
                        if len(line) == 2:
                            bbox, text_info = line
                            if isinstance(text_info, tuple) and len(text_info) == 2:
                                text, confidence = text_info
                            else:
                                text = str(text_info)
                                confidence = 0.0
                        else:
                            # Альтернативный формат
                            bbox = line[0] if len(line) > 0 else []
                            text = str(line[1]) if len(line) > 1 else ""
                            try:
                                confidence = float(line[2]) if len(line) > 2 else 0.0
                            except (ValueError, TypeError):
                                confidence = 0.0
                        
                        # Убеждаемся, что bbox это список списков координат
                        if not isinstance(bbox, list) or not bbox:
                            bbox = [[0, 0], [0, 0], [0, 0], [0, 0]]
                        
                        processed_results.append((bbox, text, confidence))
                
                logfire.info(
                    "Full image processing completed",
                    regions_found=len(processed_results),
                    avg_confidence=sum(r[2] for r in processed_results) / len(processed_results) if processed_results else 0
                )
                
                return processed_results
                
        except Exception as e:
            logfire.error(
                "Error in full image processing",
                error=str(e),
                error_type=type(e).__name__
            )
            raise OCRProcessingException(f"Full image processing failed: {str(e)}")
    
    def process_polygon_region(
        self, 
        image_data: bytes, 
        polygon_points: List[List[float]],
        min_region_size: Tuple[int, int] = (10, 10)
    ) -> Tuple[str, float]:
        """
        Обработать полигональную область изображения.
        
        Args:
            image_data: Байты изображения
            polygon_points: Координаты полигона [[x1,y1], [x2,y2], ...]
            min_region_size: Минимальный размер области (ширина, высота) для обработки
            
        Returns:
            Кортеж: (распознанный_текст, уверенность)
            
        Raises:
            OCRProcessingException: При ошибке обработки
        """
        try:
            with logfire.span("ocr_process_polygon_region"):
                # Декодируем изображение
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    raise OCRProcessingException("Failed to decode image")
                
                logfire.info(
                    "Processing polygon region",
                    polygon_points=polygon_points,
                    image_shape=image.shape
                )
                
                # Извлекаем область по полигону
                cropped_image = self._extract_polygon_region(image, polygon_points, min_region_size)
                
                if cropped_image is None:
                    logfire.error("Failed to extract polygon region")
                    return "", 0.0
                
                # Дополнительная проверка размера вырезанной области
                min_width, min_height = min_region_size
                if cropped_image.shape[0] < min_height or cropped_image.shape[1] < min_width:
                    logfire.error(
                        "Extracted region is too small for OCR",
                        region_shape=cropped_image.shape,
                        min_region_size=min_region_size,
                        polygon_points=polygon_points
                    )
                    return "", 0.0
                
                # # Для 4-угольных областей применяем перспективное выпрямление
                # if len(polygon_points) == 4:
                #     cropped_image = self._apply_perspective_correction(
                #         cropped_image, 
                #         polygon_points
                #     )
                
                # Используем только TextRecognition для вырезанной области (без детекции)
                # Защищаем OCR операции от race conditions с помощью lock
                with self._ocr_lock:
                    if self.text_recognizer:
                        text, confidence = self._recognize_text_only(cropped_image)
                    else:
                        # Fallback: используем основной OCR движок для небольшой области
                        logfire.info("Using main OCR engine as fallback for polygon region")
                        results = self.ocr_engine.ocr(cropped_image)
                        if results and results[0]:
                            # Берем первый результат
                            result_data = results[0]
                            if isinstance(result_data, dict):
                                text = result_data.get('rec_texts', [''])[0] if result_data.get('rec_texts') else ""
                                confidence = result_data.get('rec_scores', [0.0])[0] if result_data.get('rec_scores') else 0.0
                            else:
                                text = result_data[0][1][0] if len(result_data) > 0 and len(result_data[0]) > 1 else ""
                                confidence = result_data[0][1][1] if len(result_data) > 0 and len(result_data[0]) > 1 and len(result_data[0][1]) > 1 else 0.0
                        else:
                            text, confidence = "", 0.0
                
                combined_text = text
                avg_confidence = confidence
                
                logfire.info(
                    "Polygon region processing completed",
                    text_length=len(combined_text),
                    confidence=avg_confidence
                )
                
                return combined_text, avg_confidence
                
        except Exception as e:
            logfire.error(
                "Error in polygon region processing",
                error=str(e),
                error_type=type(e).__name__,
                polygon_points=polygon_points
            )
            raise OCRProcessingException(f"Polygon region processing failed: {str(e)}")
    
    def _recognize_text_only(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Распознавание текста без детекции областей (только для уже вырезанных изображений).
        
        Args:
            image: Вырезанное изображение для распознавания
            
        Returns:
            Кортеж: (распознанный_текст, уверенность)
        """
        import tempfile
        import os
        from PIL import Image
        
        try:
            # Конвертируем numpy array в PIL Image для TextRecognition
            if image.dtype != np.uint8:
                image = image.astype(np.uint8)
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Сохраняем временно как файл для TextRecognition
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_input_path = temp_file.name
                pil_image.save(temp_input_path, quality=95)
            
            try:
                # Выполняем только распознавание текста
                result = self.text_recognizer.predict(input=temp_input_path, batch_size=1)
                logfire.debug(f"TextRecognition result: {result}")
                
                # Извлекаем текст и уверенность из результата TextRecognition
                text = ""
                confidence = 0.0
                
                if result:
                    # TextRecognition возвращает список словарей
                    for res_item in result:
                        if isinstance(res_item, dict):
                            rec_text = res_item.get('rec_text', '')
                            rec_score = res_item.get('rec_score', 0.0)
                            
                            if rec_text:
                                text = rec_text  # Для одной области берём первый результат
                                confidence = rec_score
                                break
                
                return text.strip() if text else "", confidence
                
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path)
            
        except Exception as e:
            logfire.error(
                "Error in text recognition",
                error=str(e),
                error_type=type(e).__name__
            )
            return "", 0.0
    
    def detect_text_regions_only(self, image_data: bytes) -> List[List[List[float]]]:
        """
        Детекция текстовых областей БЕЗ распознавания текста.
        
        Используется для streaming режима: сначала быстро находим все области,
        затем распознаём их параллельно.
        
        Args:
            image_data: Байты изображения
            
        Returns:
            Список координат полигонов: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], ...]
            
        Raises:
            OCRProcessingException: При ошибке обработки
        """
        try:
            with logfire.span("ocr_detect_text_regions_only"):
                # Декодируем изображение
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    raise OCRProcessingException("Failed to decode image")
                
                logfire.info(
                    "Detecting text regions only",
                    image_shape=image.shape,
                    image_size=len(image_data)
                )
                
                # Используем только детектор (без распознавания)
                # PaddleOCR имеет метод text_detector для этого
                # Защищаем OCR операции от race conditions
                with self._ocr_lock:
                    if hasattr(self.ocr_engine, 'text_detector'):
                        # Новая версия PaddleOCR
                        detection_results = self.ocr_engine.text_detector(image)
                        if detection_results is None or len(detection_results) == 0:
                            logfire.info("No text regions detected")
                            return []
                        
                        # Извлекаем координаты
                        regions = []
                        for detection in detection_results:
                            if isinstance(detection, np.ndarray):
                                bbox = detection.tolist()
                            elif isinstance(detection, list):
                                bbox = detection
                            else:
                                continue
                            
                            # Убеждаемся что bbox это список списков координат
                            if isinstance(bbox, list) and len(bbox) > 0:
                                regions.append(bbox)
                        
                        logfire.info(
                            "Text regions detection completed",
                            regions_found=len(regions)
                        )
                        return regions
                    else:
                        # Fallback: используем полный OCR и извлекаем только координаты
                        # Используем тот же метод, что и process_image (проверенный и рабочий)
                        logfire.debug("Using full OCR for detection (fallback)")
                        
                        results = self.ocr_engine.ocr(image)
                        
                        if not results or not results[0]:
                            logfire.info("No text regions detected")
                            return []
                        
                        # Извлекаем только координаты из результатов OCR
                        regions = []
                        result_data = results[0]
                        
                        logfire.debug(
                            "OCR result format check",
                            is_dict=isinstance(result_data, dict),
                            is_list=isinstance(result_data, list),
                            type=type(result_data).__name__,
                            length=len(result_data) if hasattr(result_data, '__len__') else 'N/A'
                        )
                        
                        # Обработка разных форматов результатов PaddleOCR
                        if isinstance(result_data, dict):
                            # Новый формат с dict (rec_texts, rec_scores, rec_polys)
                            rec_polys = result_data.get('rec_polys', [])
                            logfire.debug(f"Extracted rec_polys count: {len(rec_polys)}")
                            
                            for poly in rec_polys:
                                if hasattr(poly, 'tolist'):
                                    bbox = poly.tolist()
                                else:
                                    bbox = poly
                                if isinstance(bbox, list) and len(bbox) > 0:
                                    regions.append(bbox)
                        
                        elif isinstance(result_data, list):
                            # Старый формат PaddleOCR: [[bbox, (text, confidence)], ...]
                            for item in result_data:
                                if isinstance(item, (list, tuple)) and len(item) >= 1:
                                    bbox = item[0]  # Первый элемент - координаты bbox
                                    if isinstance(bbox, np.ndarray):
                                        bbox = bbox.tolist()
                                    if isinstance(bbox, list) and len(bbox) > 0:
                                        regions.append(bbox)
                        
                        logfire.info(
                            "Text regions detection completed",
                            regions_found=len(regions)
                        )
                        return regions
                
        except Exception as e:
            logfire.error(
                "Error in text regions detection",
                error=str(e),
                error_type=type(e).__name__
            )
            raise OCRProcessingException(f"Text regions detection failed: {str(e)}")
    
    def _extract_polygon_region(
        self, 
        image: np.ndarray, 
        polygon_points: List[List[float]],
        min_region_size: Tuple[int, int] = (10, 10)
    ) -> Optional[np.ndarray]:
        """
        Извлечь полигональную область из изображения.
        
        Args:
            image: Исходное изображение
            polygon_points: Координаты полигона
            min_region_size: Минимальный размер области (ширина, высота)
            
        Returns:
            Вырезанная область или None при ошибке
        """
        try:
            # Преобразуем координаты в numpy массив
            points = np.array(polygon_points, dtype=np.int32)
            
            # Создаем маску
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [points], 255)
            
            # Находим ограничивающий прямоугольник
            x, y, w, h = cv2.boundingRect(points)
            
            # Проверяем минимальные размеры области
            min_width, min_height = min_region_size
            
            if w < min_width or h < min_height:
                logfire.error(
                    "Polygon region too small for OCR processing",
                    width=w,
                    height=h,
                    min_width=min_width,
                    min_height=min_height,
                    polygon_points=polygon_points
                )
                
                # Для очень маленьких областей увеличиваем размер с отступами
                padding = max(min_width - w, min_height - h, 5)  # Минимум 5px отступ
                
                # Вычисляем новые координаты с отступами
                x_padded = max(0, x - padding)
                y_padded = max(0, y - padding)
                w_padded = min(image.shape[1] - x_padded, w + 2 * padding)
                h_padded = min(image.shape[0] - y_padded, h + 2 * padding)
                
                logfire.info(
                    "Expanding small polygon region",
                    original_size=(w, h),
                    expanded_size=(w_padded, h_padded),
                    padding=padding
                )
                
                # Вырезаем расширенную область
                cropped_image = image[y_padded:y_padded+h_padded, x_padded:x_padded+w_padded]
                
                # Создаем маску для расширенной области
                expanded_mask = np.zeros((h_padded, w_padded), dtype=np.uint8)
                
                # Пересчитываем координаты полигона относительно новой области
                adjusted_points = points.copy()
                adjusted_points[:, 0] -= x_padded
                adjusted_points[:, 1] -= y_padded
                
                # Заполняем маску
                cv2.fillPoly(expanded_mask, [adjusted_points], 255)
                
                # Применяем маску, но делаем фон белым для лучшего распознавания
                result = np.full_like(cropped_image, 255)  # Белый фон
                result = cv2.bitwise_and(cropped_image, cropped_image, mask=expanded_mask)
                
                # Заменяем черные пиксели (замаскированные) на белые
                result[expanded_mask == 0] = 255
                
                return result
            else:
                # Стандартная обработка для областей нормального размера
                cropped_image = image[y:y+h, x:x+w]
                cropped_mask = mask[y:y+h, x:x+w]
                
                # Применяем маску
                cropped_image = cv2.bitwise_and(cropped_image, cropped_image, mask=cropped_mask)
                
                return cropped_image
            
        except Exception as e:
            logfire.error(
                "Error extracting polygon region",
                error=str(e),
                polygon_points=polygon_points
            )
            return None
    
    def _apply_perspective_correction(
        self, 
        image: np.ndarray, 
        polygon_points: List[List[float]]
    ) -> np.ndarray:
        """
        Применить перспективное выпрямление для 4-угольной области.
        
        Args:
            image: Исходное изображение
            polygon_points: 4 точки полигона
            
        Returns:
            Выпрямленное изображение
        """
        try:
            if len(polygon_points) != 4:
                return image
            
            # Сортируем точки: верх-лево, верх-право, низ-право, низ-лево
            points = np.array(polygon_points, dtype=np.float32)
            
            # Находим центр
            center = np.mean(points, axis=0)
            
            # Сортируем точки по углам
            def sort_points(pts):
                # Сортируем по y-координате
                top_pts = pts[pts[:, 1] < center[1]]
                bottom_pts = pts[pts[:, 1] >= center[1]]
                
                # Сортируем верхние точки по x
                if len(top_pts) >= 2:
                    top_pts = top_pts[np.argsort(top_pts[:, 0])]
                
                # Сортируем нижние точки по x (справа налево)
                if len(bottom_pts) >= 2:
                    bottom_pts = bottom_pts[np.argsort(bottom_pts[:, 0])[::-1]]
                
                return np.vstack([top_pts, bottom_pts])
            
            sorted_points = sort_points(points)
            
            # Вычисляем размеры выходного изображения
            width = max(
                np.linalg.norm(sorted_points[0] - sorted_points[1]),
                np.linalg.norm(sorted_points[2] - sorted_points[3])
            )
            height = max(
                np.linalg.norm(sorted_points[0] - sorted_points[3]),
                np.linalg.norm(sorted_points[1] - sorted_points[2])
            )
            
            # Определяем целевые точки
            dst_points = np.array([
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1]
            ], dtype=np.float32)
            
            # Вычисляем матрицу преобразования
            matrix = cv2.getPerspectiveTransform(sorted_points, dst_points)
            
            # Применяем преобразование
            corrected = cv2.warpPerspective(
                image, 
                matrix, 
                (int(width), int(height))
            )
            
            logfire.info(
                "Applied perspective correction",
                original_shape=image.shape,
                corrected_shape=corrected.shape
            )
            
            return corrected
            
        except Exception as e:
            logfire.error(
                "Error in perspective correction",
                error=str(e)
            )
            return image
    
    def is_initialized(self) -> bool:
        """Проверить, инициализирован ли сервис"""
        return self._initialized
    
    def get_engine_info(self) -> dict:
        """Получить информацию о движках OCR"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "main_engine": str(type(self.ocr_engine)),
            "text_recognizer": str(type(self.text_recognizer)),
            "thread_safe": True
        }
