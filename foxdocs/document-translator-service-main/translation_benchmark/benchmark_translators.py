#!/usr/bin/env python3
"""
Бенчмарк для сравнения переводчиков с китайского на русский

Сравнивает:
1. Argos Translate (zh -> en -> ru через промежуточный английский)
2. M2M100 (facebook/m2m100_418M) - прямой перевод zh -> ru

ВАЖНО: Использует ТОЛЬКО CPU, без NVIDIA/CUDA библиотек!
"""

import time
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import psutil
import os
from dataclasses import dataclass
from tabulate import tabulate

# Для argostranslate
try:
    import argostranslate.package
    import argostranslate.translate
    ARGOS_AVAILABLE = True
except ImportError:
    ARGOS_AVAILABLE = False
    print("⚠️ Argostranslate не установлен!")

# Для M2M100 с CTranslate2
try:
    import ctranslate2
    from transformers import M2M100Tokenizer
    M2M100_AVAILABLE = True
except ImportError:
    M2M100_AVAILABLE = False
    print("⚠️ CTranslate2/Transformers не установлены!")

# Для M2M100 с ONNX Runtime
try:
    from optimum.onnxruntime import ORTModelForSeq2SeqLM
    from transformers import M2M100Tokenizer as M2M100TokenizerONNX
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("⚠️ Optimum/ONNX Runtime не установлены!")

# Для T5 с CTranslate2
try:
    import ctranslate2
    from transformers import T5Tokenizer
    T5_AVAILABLE = True
except ImportError:
    T5_AVAILABLE = False
    print("⚠️ T5/CTranslate2 не установлены!")


@dataclass
class TranslationResult:
    """Результат перевода одного текста"""
    original: str
    translated: str
    time_seconds: float
    cpu_percent: float
    memory_mb: float


@dataclass
class BenchmarkResult:
    """Результат бенчмарка для одного переводчика"""
    translator_name: str
    description: str  # Описание переводчика
    results: List[TranslationResult]
    total_time: float
    avg_time_per_text: float
    min_time: float  # Минимальное время перевода
    max_time: float  # Максимальное время перевода
    total_texts: int
    avg_cpu_percent: float
    avg_memory_mb: float
    peak_memory_mb: float


class ResourceMonitor:
    """Мониторинг использования ресурсов"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def get_current_stats(self) -> Tuple[float, float]:
        """
        Получить текущие статистики
        
        Returns:
            Tuple[float, float]: (CPU%, память в MB)
        """
        cpu_percent = self.process.cpu_percent(interval=0.1)
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        return cpu_percent, memory_mb


class ArgosTranslateWrapper:
    """Обёртка для Argos Translate с переводом zh -> en -> ru"""
    
    def __init__(self):
        self.name = "Argos Translate (zh→en→ru)"
        self.initialized = False
        self.monitor = ResourceMonitor()
        
    def initialize(self):
        """Инициализация и установка необходимых пакетов"""
        if not ARGOS_AVAILABLE:
            raise RuntimeError("Argostranslate не доступен!")
        
        print(f"\n🔧 Инициализация {self.name}...")
        
        # Обновляем индекс пакетов
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        # Проверяем и устанавливаем необходимые пакеты
        required_packages = [
            ("zh", "en"),  # Китайский -> Английский
            ("en", "ru"),  # Английский -> Русский
        ]
        
        installed_packages = argostranslate.package.get_installed_packages()
        installed_codes = [(pkg.from_code, pkg.to_code) for pkg in installed_packages]
        
        for from_code, to_code in required_packages:
            if (from_code, to_code) not in installed_codes:
                print(f"  📦 Установка пакета {from_code} -> {to_code}...")
                package_to_install = next(
                    (
                        pkg for pkg in available_packages
                        if pkg.from_code == from_code and pkg.to_code == to_code
                    ),
                    None
                )
                if package_to_install:
                    argostranslate.package.install_from_path(
                        package_to_install.download()
                    )
                    print(f"  ✅ Пакет {from_code} -> {to_code} установлен")
                else:
                    raise RuntimeError(f"Пакет {from_code} -> {to_code} не найден!")
            else:
                print(f"  ✅ Пакет {from_code} -> {to_code} уже установлен")
        
        self.initialized = True
        print(f"✅ {self.name} инициализирован\n")
    
    def translate(self, text: str) -> TranslationResult:
        """
        Перевести текст с китайского на русский через английский
        
        Args:
            text: Исходный текст на китайском
            
        Returns:
            TranslationResult: Результат перевода с метриками
        """
        if not self.initialized:
            raise RuntimeError("Переводчик не инициализирован!")
        
        start_time = time.time()
        
        # Первый этап: китайский -> английский
        intermediate_text = argostranslate.translate.translate(text, "zh", "en")
        
        # Второй этап: английский -> русский
        final_text = argostranslate.translate.translate(intermediate_text, "en", "ru")
        
        elapsed_time = time.time() - start_time
        cpu_percent, memory_mb = self.monitor.get_current_stats()
        
        return TranslationResult(
            original=text,
            translated=final_text,
            time_seconds=elapsed_time,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb
        )


class M2M100Wrapper:
    """Обёртка для M2M100 через CTranslate2 (прямой перевод zh -> ru)"""
    
    def __init__(self, model_name: str = "facebook/m2m100_418M"):
        self.name = f"M2M100-CT2 ({model_name.split('/')[-1]})"
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.initialized = False
        self.monitor = ResourceMonitor()
        
        # Путь для конвертированной модели
        from pathlib import Path
        self.ct2_model_path = Path.home() / ".cache" / "ctranslate2" / model_name.replace("/", "_")
    
    def initialize(self):
        """Инициализация модели M2M100 через CTranslate2"""
        if not M2M100_AVAILABLE:
            raise RuntimeError("CTranslate2/Transformers не доступны!")
        
        print(f"\n🔧 Инициализация {self.name} (с CTranslate2 оптимизацией)...")
        
        # Убеждаемся что используем CPU
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        # Загружаем токенизатор
        print("  📦 Загрузка токенизатора...")
        self.tokenizer = M2M100Tokenizer.from_pretrained(self.model_name)
        
        # Проверяем нужна ли конвертация модели
        if not self.ct2_model_path.exists():
            print("  🔄 Конвертация модели в CTranslate2 формат (только при первом запуске)...")
            print("     Это может занять 2-5 минут...")
            self._convert_model_to_ct2()
        else:
            print("  ✅ Используем уже конвертированную модель")
        
        # Загружаем модель через CTranslate2
        print("  📥 Загрузка CTranslate2 модели...")
        self.model = ctranslate2.Translator(
            str(self.ct2_model_path),
            device="cpu",
            compute_type="int8",  # Квантизация для ускорения на CPU
            inter_threads=4,       # Параллельные потоки
            intra_threads=4
        )
        
        self.initialized = True
        print(f"✅ {self.name} инициализирован (CPU mode, int8 квантизация)\n")
    
    def _convert_model_to_ct2(self):
        """Конвертировать модель из transformers в CTranslate2 формат"""
        try:
            import subprocess
            import sys
            
            # Создаём директорию для модели
            self.ct2_model_path.mkdir(parents=True, exist_ok=True)
            
            # Конвертируем через ct2-transformers-converter
            cmd = [
                sys.executable, "-m", "ctranslate2.converters.transformers",
                "--model", self.model_name,
                "--output_dir", str(self.ct2_model_path),
                "--quantization", "int8",  # int8 квантизация для CPU
                "--force"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("  ✅ Конвертация завершена")
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Ошибка конвертации: {e.stderr}")
            raise RuntimeError("Не удалось конвертировать модель в CTranslate2 формат")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            raise
    
    def translate(self, text: str) -> TranslationResult:
        """
        Перевести текст с китайского на русский напрямую через CTranslate2
        
        Args:
            text: Исходный текст на китайском
            
        Returns:
            TranslationResult: Результат перевода с метриками
        """
        if not self.initialized:
            raise RuntimeError("Переводчик не инициализирован!")
        
        start_time = time.time()
        
        # Устанавливаем исходный язык
        self.tokenizer.src_lang = "zh"
        
        # Токенизируем входной текст
        tokens = self.tokenizer.convert_ids_to_tokens(
            self.tokenizer.encode(text)
        )
        
        # Получаем ID токена для целевого языка (русский)
        target_prefix = [self.tokenizer.lang_code_to_token["ru"]]
        
        # Выполняем перевод через CTranslate2
        results = self.model.translate_batch(
            [tokens],
            target_prefix=[target_prefix],
            beam_size=4,          # Beam search для качества
            max_decoding_length=512
        )
        
        # Конвертируем токены обратно в текст
        output_tokens = results[0].hypotheses[0]
        output_ids = self.tokenizer.convert_tokens_to_ids(output_tokens)
        translated_text = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        
        elapsed_time = time.time() - start_time
        cpu_percent, memory_mb = self.monitor.get_current_stats()
        
        return TranslationResult(
            original=text,
            translated=translated_text,
            time_seconds=elapsed_time,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb
        )


class T5TranslateWrapper:
    """Обёртка для T5 (utrobinmv/t5_translate_en_ru_zh) через CTranslate2"""
    
    def __init__(self, model_name: str = "utrobinmv/t5_translate_en_ru_zh_base_200", short_name: str = None):
        self.short_name = short_name or model_name.split('/')[-1]
        self.name = f"T5-CT2 ({self.short_name})"
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.initialized = False
        self.monitor = ResourceMonitor()
        
        # Путь для конвертированной модели
        from pathlib import Path
        self.ct2_model_path = Path.home() / ".cache" / "ctranslate2" / model_name.replace("/", "_")
    
    def initialize(self):
        """Инициализация модели T5 через CTranslate2"""
        if not T5_AVAILABLE:
            raise RuntimeError("T5/CTranslate2 не доступны!")
        
        print(f"\n🔧 Инициализация {self.name} (с CTranslate2 оптимизацией)...")
        
        # Убеждаемся что используем CPU
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        # Загружаем токенизатор
        print("  📦 Загрузка токенизатора T5...")
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
        
        # Проверяем нужна ли конвертация модели
        if not self.ct2_model_path.exists():
            print("  🔄 Конвертация T5 модели в CTranslate2 формат (только при первом запуске)...")
            print("     Это может занять 2-5 минут...")
            self._convert_model_to_ct2()
        else:
            print("  ✅ Используем уже конвертированную модель")
        
        # Загружаем модель через CTranslate2
        print("  📥 Загрузка CTranslate2 модели...")
        self.model = ctranslate2.Translator(
            str(self.ct2_model_path),
            device="cpu",
            compute_type="int8",  # Квантизация для ускорения на CPU
            inter_threads=4,
            intra_threads=4
        )
        
        self.initialized = True
        print(f"✅ {self.name} инициализирован (CPU mode, int8 квантизация)\n")
    
    def _convert_model_to_ct2(self):
        """Конвертировать T5 модель из transformers в CTranslate2 формат"""
        try:
            import subprocess
            import sys
            
            # Создаём директорию для модели
            self.ct2_model_path.mkdir(parents=True, exist_ok=True)
            
            # Конвертируем через ct2-transformers-converter
            cmd = [
                sys.executable, "-m", "ctranslate2.converters.transformers",
                "--model", self.model_name,
                "--output_dir", str(self.ct2_model_path),
                "--quantization", "int8",
                "--force"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("  ✅ Конвертация завершена")
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Ошибка конвертации: {e.stderr}")
            raise RuntimeError("Не удалось конвертировать T5 модель в CTranslate2 формат")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            raise
    
    def translate(self, text: str) -> TranslationResult:
        """
        Перевести текст с китайского на русский через T5 + CTranslate2
        
        Args:
            text: Исходный текст на китайском
            
        Returns:
            TranslationResult: Результат перевода с метриками
        """
        if not self.initialized:
            raise RuntimeError("Переводчик не инициализирован!")
        
        start_time = time.time()
        
        # T5 требует префикс для указания целевого языка
        prefixed_text = "translate to ru: " + text
        
        # Токенизируем входной текст
        tokens = self.tokenizer.convert_ids_to_tokens(
            self.tokenizer.encode(prefixed_text)
        )
        
        # Выполняем перевод через CTranslate2
        results = self.model.translate_batch(
            [tokens],
            beam_size=4,
            max_decoding_length=512
        )
        
        # Конвертируем токены обратно в текст
        output_tokens = results[0].hypotheses[0]
        output_ids = self.tokenizer.convert_tokens_to_ids(output_tokens)
        translated_text = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        
        elapsed_time = time.time() - start_time
        cpu_percent, memory_mb = self.monitor.get_current_stats()
        
        return TranslationResult(
            original=text,
            translated=translated_text,
            time_seconds=elapsed_time,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb
        )


class M2M100ONNXWrapper:
    """Обёртка для M2M100 через ONNX Runtime (прямой перевод zh -> ru)"""
    
    def __init__(self, model_name: str = "Xenova/m2m100_418M"):
        self.name = f"M2M100-ONNX ({model_name.split('/')[-1]})"
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.initialized = False
        self.monitor = ResourceMonitor()
    
    def initialize(self):
        """Инициализация модели M2M100 через ONNX Runtime с оптимизациями для CPU"""
        if not ONNX_AVAILABLE:
            raise RuntimeError("Optimum/ONNX Runtime не доступны!")
        
        print(f"\n🔧 Инициализация {self.name} (с ONNX Runtime CPU оптимизациями)...")
        
        # Убеждаемся что используем CPU
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        # Загружаем токенизатор
        print("  📦 Загрузка токенизатора...")
        self.tokenizer = M2M100TokenizerONNX.from_pretrained("facebook/m2m100_418M")
        
        # Создаём оптимизированные session options для CPU
        from onnxruntime import SessionOptions, GraphOptimizationLevel, ExecutionMode
        
        session_options = SessionOptions()
        
        # Оптимизации для CPU инференса
        session_options.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL
        
        # Для небольших моделей с редкими запросами используем физические ядра
        # Избегаем overhead межпоточной синхронизации
        cpu_count = psutil.cpu_count(logical=False) or 1
        session_options.intra_op_num_threads = cpu_count
        
        # Последовательное выполнение (лучше для seq2seq моделей)
        session_options.execution_mode = ExecutionMode.ORT_SEQUENTIAL
        
        # Отключаем spinning для снижения CPU usage
        session_options.add_session_config_entry("session.intra_op.allow_spinning", "0")
        
        # Включаем оптимизации для CPU
        session_options.add_session_config_entry("session.disable_prepacking", "0")
        
        print(f"  ⚙️  CPU оптимизации: {cpu_count} потоков, SEQUENTIAL, без spinning")
        
        # Загружаем ONNX модель (уже квантизованную)
        print("  📥 Загрузка ONNX модели (может занять время при первом запуске)...")
        print("     Используется готовая квантизованная модель с HuggingFace...")
        
        try:
            # Пробуем загрузить готовую ONNX модель с оптимизированными настройками
            # Используем самую маленькую и быструю квантизацию: q4f16 (4-bit + float16)
            print("  📦 Загрузка q4f16 квантизованной модели (самая быстрая для CPU)...")
            
            self.model = ORTModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                subfolder="onnx",
                use_cache=True,
                use_merged=True,  # Используем merged версии (быстрее)
                provider="CPUExecutionProvider",
                session_options=session_options,  # Применяем оптимизации
                # Указываем конкретные файлы с q4f16 квантизацией
                encoder_file_name="encoder_model_q4f16.onnx",
                decoder_file_name="decoder_model_merged_q4f16.onnx",
                decoder_with_past_file_name="decoder_with_past_model_q4f16.onnx"
            )
            print("  ✅ Загружена q4f16 квантизованная ONNX модель (самая маленькая)")
        except Exception as e:
            print(f"  ⚠️  q4f16 модель не найдена, пробую quantized версию...")
            try:
                # Пробуем старую quantized версию
                self.model = ORTModelForSeq2SeqLM.from_pretrained(
                    self.model_name,
                    subfolder="onnx",
                    use_cache=True,
                    use_merged=True,
                    provider="CPUExecutionProvider",
                    session_options=session_options,
                    encoder_file_name="encoder_model_quantized.onnx",
                    decoder_file_name="decoder_model_merged_quantized.onnx",
                    decoder_with_past_file_name="decoder_with_past_model_quantized.onnx"
                )
                print("  ✅ Загружена quantized ONNX модель")
            except Exception as e2:
                # В крайнем случае конвертируем
                print(f"  ⚠️  Готовая ONNX модель не найдена, конвертируем...")
                self.model = ORTModelForSeq2SeqLM.from_pretrained(
                    "facebook/m2m100_418M",
                    export=True,
                    provider="CPUExecutionProvider",
                    session_options=session_options
                )
                print("  ✅ Модель сконвертирована в ONNX")
        
        self.initialized = True
        print(f"✅ {self.name} инициализирован (ONNX Runtime, CPU оптимизации)\n")
    
    def translate(self, text: str) -> TranslationResult:
        """
        Перевести текст с китайского на русский напрямую через ONNX Runtime
        
        Args:
            text: Исходный текст на китайском
            
        Returns:
            TranslationResult: Результат перевода с метриками
        """
        if not self.initialized:
            raise RuntimeError("Переводчик не инициализирован!")
        
        start_time = time.time()
        
        # Устанавливаем исходный язык
        self.tokenizer.src_lang = "zh"
        
        # Токенизация
        inputs = self.tokenizer(text, return_tensors="pt")
        
        # Генерируем перевод через ONNX Runtime
        generated_tokens = self.model.generate(
            **inputs,
            forced_bos_token_id=self.tokenizer.get_lang_id("ru"),
            max_length=512,
            num_beams=4  # Beam search для качества
        )
        
        # Декодируем результат
        translated_text = self.tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True
        )[0]
        
        elapsed_time = time.time() - start_time
        cpu_percent, memory_mb = self.monitor.get_current_stats()
        
        return TranslationResult(
            original=text,
            translated=translated_text,
            time_seconds=elapsed_time,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb
        )


def load_test_data(file_path: Path) -> List[str]:
    """Загрузить тестовые данные из файла"""
    if not file_path.exists():
        raise FileNotFoundError(f"Файл {file_path} не найден!")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    print(f"📄 Загружено {len(lines)} текстов для тестирования\n")
    return lines


def run_benchmark(translator, texts: List[str]) -> BenchmarkResult:
    """
    Запустить бенчмарк для одного переводчика
    
    Args:
        translator: Переводчик (ArgosTranslateWrapper или M2M100Wrapper)
        texts: Список текстов для перевода
        
    Returns:
        BenchmarkResult: Результаты бенчмарка
    """
    print(f"🚀 Запуск бенчмарка: {translator.name}")
    print(f"   Количество текстов: {len(texts)}\n")
    
    results = []
    start_time = time.time()
    peak_memory = 0.0
    
    for i, text in enumerate(texts, 1):
        print(f"  [{i}/{len(texts)}] Перевод: {text[:30]}...")
        
        result = translator.translate(text)
        results.append(result)
        
        peak_memory = max(peak_memory, result.memory_mb)
        
        print(f"             → {result.translated[:50]}...")
        print(f"             ⏱️  {result.time_seconds:.3f}s | "
              f"💻 CPU: {result.cpu_percent:.1f}% | "
              f"🧠 RAM: {result.memory_mb:.1f}MB\n")
    
    total_time = time.time() - start_time
    avg_time = total_time / len(texts)
    avg_cpu = sum(r.cpu_percent for r in results) / len(results)
    avg_memory = sum(r.memory_mb for r in results) / len(results)
    min_time = min(r.time_seconds for r in results)
    max_time = max(r.time_seconds for r in results)
    
    # Создаём описание переводчика
    if "T5-Small" in translator.name:
        description = "Компактная T5 модель (~60M параметров) с CTranslate2 int8 квантизацией для быстрого перевода zh→ru"
    elif "T5-Base" in translator.name:
        description = "Базовая T5 модель (~220M параметров) с CTranslate2 int8 квантизацией для качественного перевода zh→ru"
    elif "M2M100-ONNX" in translator.name:
        description = "M2M100 418M с ONNX Runtime оптимизацией (q4f16) для быстрого перевода zh→ru"
    elif "M2M100-CT2" in translator.name:
        description = "M2M100 418M с CTranslate2 int8 квантизацией для универсального перевода (100 языков)"
    elif "Argos" in translator.name:
        description = "Двухэтапный перевод zh→en→ru через CTranslate2, компактный и надёжный"
    else:
        description = f"Перевод с китайского на русский через {translator.name}"
    
    print(f"✅ Бенчмарк {translator.name} завершён!\n")
    
    return BenchmarkResult(
        translator_name=translator.name,
        description=description,
        results=results,
        total_time=total_time,
        avg_time_per_text=avg_time,
        min_time=min_time,
        max_time=max_time,
        total_texts=len(texts),
        avg_cpu_percent=avg_cpu,
        avg_memory_mb=avg_memory,
        peak_memory_mb=peak_memory
    )


def print_comparison_table(all_results: Dict[str, BenchmarkResult]):
    """Вывести сравнительную таблицу результатов для всех переводчиков"""
    
    if not all_results:
        print("⚠️  Нет результатов для сравнения")
        return
    
    print("\n" + "="*120)
    print("📊 СРАВНИТЕЛЬНАЯ ТАБЛИЦА ПЕРЕВОДОВ")
    print("="*120 + "\n")
    
    # Получаем список всех переводчиков
    translators = list(all_results.keys())
    results_list = [all_results[t] for t in translators]
    
    # Таблица переводов
    headers = ["№", "Оригинал (ZH)"] + [all_results[t].translator_name for t in translators]
    translation_data = []
    
    num_texts = len(results_list[0].results)
    for i in range(num_texts):
        row = [i + 1]
        
        # Оригинальный текст (берем из первого переводчика)
        original = results_list[0].results[i].original
        row.append(original[:35] + "..." if len(original) > 35 else original)
        
        # Переводы от всех переводчиков
        for result in results_list:
            translated = result.results[i].translated
            row.append(translated[:40] + "..." if len(translated) > 40 else translated)
        
        translation_data.append(row)
    
    print(tabulate(
        translation_data,
        headers=headers,
        tablefmt="grid",
        maxcolwidths=[5, 35] + [40] * len(translators)
    ))
    
    print("\n" + "="*120)
    print("⚡ МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("="*120 + "\n")
    
    # Таблица производительности
    performance_data = []
    for result in results_list:
        performance_data.append([
            result.translator_name,
            f"{result.total_time:.2f}s",
            f"{result.avg_time_per_text:.3f}s",
            f"{result.avg_cpu_percent:.1f}%",
            f"{result.avg_memory_mb:.1f} MB",
            f"{result.peak_memory_mb:.1f} MB",
        ])
    
    print(tabulate(
        performance_data,
        headers=[
            "Переводчик",
            "Общее время",
            "Время на 1 текст",
            "Средний CPU",
            "Средняя RAM",
            "Пиковая RAM"
        ],
        tablefmt="grid",
        maxcolwidths=[35, 15, 15, 15, 15, 15]
    ))
    
    # Сравнение скорости
    print("\n" + "="*120)
    print("🏆 ВЫВОДЫ")
    print("="*120 + "\n")
    
    # Находим самого быстрого
    fastest = min(results_list, key=lambda r: r.avg_time_per_text)
    print(f"⚡ Самый быстрый: {fastest.translator_name} ({fastest.avg_time_per_text:.3f}s на текст)")
    
    # Сравнение с другими
    for result in results_list:
        if result != fastest:
            ratio = result.avg_time_per_text / fastest.avg_time_per_text
            print(f"   • {result.translator_name}: медленнее в {ratio:.2f}x раз")
    
    print()
    
    # Находим наиболее эффективного по памяти
    most_efficient = min(results_list, key=lambda r: r.avg_memory_mb)
    print(f"🧠 Наиболее эффективный по памяти: {most_efficient.translator_name} ({most_efficient.avg_memory_mb:.1f} MB)")
    
    # Сравнение с другими
    for result in results_list:
        if result != most_efficient:
            ratio = result.avg_memory_mb / most_efficient.avg_memory_mb
            print(f"   • {result.translator_name}: использует в {ratio:.2f}x раз больше памяти")
    
    print("\n" + "="*120 + "\n")


def save_results_to_markdown(results: Dict[str, BenchmarkResult], test_data: List[str], output_file: str = "benchmark_results.md"):
    """
    Сохранить результаты бенчмарка в красиво оформленный Markdown файл
    
    Args:
        results: Словарь с результатами каждого переводчика
        test_data: Список исходных текстов
        output_file: Имя выходного файла
    """
    from datetime import datetime
    import platform
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Заголовок
        f.write("# 📊 Результаты бенчмарка переводчиков\n\n")
        f.write(f"**Дата тестирования:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Информация о системе
        f.write("## 💻 Информация о системе\n\n")
        f.write(f"- **ОС:** {platform.system()} {platform.release()}\n")
        f.write(f"- **Процессор:** {platform.processor() or platform.machine()}\n")
        f.write(f"- **Архитектура:** {platform.architecture()[0]}\n")
        f.write(f"- **Python:** {platform.python_version()}\n")
        f.write(f"- **Количество тестовых фраз:** {len(test_data)}\n\n")
        
        # Список переводчиков
        f.write("## 🌐 Протестированные переводчики\n\n")
        for i, (key, translator) in enumerate(results.items(), 1):
            f.write(f"{i}. **{translator.translator_name}** - {translator.description}\n")
        f.write("\n")
        
        # Общая статистика
        f.write("## 📈 Сводная статистика производительности\n\n")
        
        # Таблица метрик
        f.write("| Переводчик | Общее время | Время/текст | Средний CPU | Средняя RAM | Пиковая RAM |\n")
        f.write("|------------|-------------|-------------|-------------|-------------|-------------|\n")
        
        for key, result in results.items():
            f.write(f"| **{result.translator_name}** | "
                   f"{result.total_time:.2f}s | "
                   f"{result.avg_time_per_text:.3f}s | "
                   f"{result.avg_cpu_percent:.1f}% | "
                   f"{result.avg_memory_mb:.1f} MB | "
                   f"{result.peak_memory_mb:.1f} MB |\n")
        f.write("\n")
        
        # Выводы
        f.write("## 🏆 Выводы\n\n")
        
        # Самый быстрый
        fastest = min(results.items(), key=lambda x: x[1].total_time)
        f.write(f"### ⚡ Самый быстрый: {fastest[1].translator_name}\n\n")
        f.write(f"- **Общее время:** {fastest[1].total_time:.2f}s\n")
        f.write(f"- **Среднее время на текст:** {fastest[1].avg_time_per_text:.3f}s\n\n")
        
        # Сравнение скорости с другими
        f.write("**Сравнение скорости:**\n\n")
        sorted_by_speed = sorted(results.items(), key=lambda x: x[1].total_time)
        for key, result in sorted_by_speed:
            if key != fastest[0]:
                ratio = result.total_time / fastest[1].total_time
                f.write(f"- {result.translator_name}: в **{ratio:.2f}x** раз медленнее\n")
        f.write("\n")
        
        # Самый экономичный по памяти
        most_efficient = min(results.items(), key=lambda x: x[1].peak_memory_mb)
        f.write(f"### 🧠 Самый экономичный по памяти: {most_efficient[1].translator_name}\n\n")
        f.write(f"- **Пиковая память:** {most_efficient[1].peak_memory_mb:.1f} MB\n")
        f.write(f"- **Средняя память:** {most_efficient[1].avg_memory_mb:.1f} MB\n\n")
        
        # Сравнение памяти
        f.write("**Сравнение использования памяти:**\n\n")
        sorted_by_memory = sorted(results.items(), key=lambda x: x[1].peak_memory_mb)
        for key, result in sorted_by_memory:
            if key != most_efficient[0]:
                diff = result.peak_memory_mb - most_efficient[1].peak_memory_mb
                f.write(f"- {result.translator_name}: на **{diff:.1f} MB** больше\n")
        f.write("\n")
        
        # Рекомендации
        f.write("## 💡 Рекомендации\n\n")
        
        # Для скорости
        f.write("### Для максимальной скорости:\n")
        f.write(f"Используйте **{fastest[1].translator_name}** "
               f"({fastest[1].avg_time_per_text:.3f}s на текст)\n\n")
        
        # Для экономии памяти
        f.write("### Для минимального использования памяти:\n")
        f.write(f"Используйте **{most_efficient[1].translator_name}** "
               f"({most_efficient[1].peak_memory_mb:.1f} MB)\n\n")
        
        # Детальные результаты переводов
        f.write("---\n\n")
        f.write("## 📝 Детальные результаты переводов\n\n")
        
        # Для каждого текста
        for i, original_text in enumerate(test_data, 1):
            f.write(f"### Текст #{i}\n\n")
            f.write(f"**Оригинал (китайский):**\n```\n{original_text}\n```\n\n")
            
            f.write("**Переводы:**\n\n")
            for key, result in results.items():
                if i <= len(result.results):
                    translation = result.results[i-1]
                    f.write(f"- **{result.translator_name}:**\n")
                    f.write(f"  ```\n  {translation.translated}\n  ```\n")
                    f.write(f"  - Время: {translation.time_seconds:.3f}s\n")
                    f.write(f"  - CPU: {translation.cpu_percent:.1f}%\n")
                    f.write(f"  - RAM: {translation.memory_mb:.1f} MB\n\n")
        
        # График производительности (ASCII art)
        f.write("---\n\n")
        f.write("## 📊 Визуализация производительности\n\n")
        
        f.write("### Время выполнения (секунды)\n\n")
        max_time = max(r.total_time for r in results.values())
        for key, result in sorted(results.items(), key=lambda x: x[1].total_time):
            bar_length = int((result.total_time / max_time) * 50)
            bar = "█" * bar_length
            f.write(f"`{result.translator_name:25}` {bar} {result.total_time:.2f}s\n")
        f.write("\n")
        
        f.write("### Использование памяти (MB)\n\n")
        max_memory = max(r.peak_memory_mb for r in results.values())
        for key, result in sorted(results.items(), key=lambda x: x[1].peak_memory_mb):
            bar_length = int((result.peak_memory_mb / max_memory) * 50)
            bar = "█" * bar_length
            f.write(f"`{result.translator_name:25}` {bar} {result.peak_memory_mb:.1f} MB\n")
        f.write("\n")
        
        # Технические детали
        f.write("---\n\n")
        f.write("## 🔧 Технические детали\n\n")
        
        for key, result in results.items():
            f.write(f"### {result.translator_name}\n\n")
            f.write(f"{result.description}\n\n")
            f.write("**Характеристики:**\n")
            f.write(f"- Общее время: {result.total_time:.2f}s\n")
            f.write(f"- Среднее время на текст: {result.avg_time_per_text:.3f}s\n")
            f.write(f"- Мин. время: {result.min_time:.3f}s\n")
            f.write(f"- Макс. время: {result.max_time:.3f}s\n")
            f.write(f"- Средняя загрузка CPU: {result.avg_cpu_percent:.1f}%\n")
            f.write(f"- Средняя память: {result.avg_memory_mb:.1f} MB\n")
            f.write(f"- Пиковая память: {result.peak_memory_mb:.1f} MB\n\n")
        
        # Подвал
        f.write("---\n\n")
        f.write("*Этот отчет создан автоматически скриптом `benchmark_translators.py`*\n")
    
    print(f"\n✅ Результаты сохранены в файл: {output_file}")


def main():
    """Основная функция бенчмарка"""
    
    print("\n" + "="*100)
    print("🌐 БЕНЧМАРК ПЕРЕВОДЧИКОВ: Китайский → Русский (CPU ONLY)")
    print("="*100 + "\n")
    
    # Принудительно отключаем CUDA
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    print(f"💻 Устройство: CPU (CUDA отключена)")
    print(f"🧮 Количество ядер: {psutil.cpu_count()}")
    print(f"🧠 Доступная RAM: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB\n")
    
    # Путь к тестовым данным
    script_dir = Path(__file__).parent
    test_data_path = script_dir / "chinese_test_data.txt"
    
    # Загружаем тестовые данные
    try:
        texts = load_test_data(test_data_path)
    except FileNotFoundError as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)
    
    # Инициализируем переводчики
    # ВАЖНО: Порядок влияет на измерения памяти!
    # Первый переводчик показывает "чистую" память, следующие - с учётом предыдущих
    translators = []
    
    # T5 Small CTranslate2 (запускаем первым для честного сравнения памяти)
    if T5_AVAILABLE:
        t5_small = T5TranslateWrapper(
            model_name="utrobinmv/t5_translate_en_ru_zh_small_1024",
            short_name="T5-Small"
        )
        try:
            t5_small.initialize()
            translators.append(("t5_small_ct2", t5_small))
        except Exception as e:
            print(f"❌ Ошибка инициализации T5-Small-CT2: {e}\n")
    else:
        print("⚠️  T5-Small-CT2 пропущен (не установлен)\n")
    
    # T5 Base CTranslate2
    if T5_AVAILABLE:
        t5_base = T5TranslateWrapper(
            model_name="utrobinmv/t5_translate_en_ru_zh_base_200",
            short_name="T5-Base"
        )
        try:
            t5_base.initialize()
            translators.append(("t5_base_ct2", t5_base))
        except Exception as e:
            print(f"❌ Ошибка инициализации T5-Base-CT2: {e}\n")
    else:
        print("⚠️  T5-Base-CT2 пропущен (не установлен)\n")
    
    # M2M100 ONNX Runtime
    if ONNX_AVAILABLE:
        m2m_onnx = M2M100ONNXWrapper()
        try:
            m2m_onnx.initialize()
            translators.append(("m2m100_onnx", m2m_onnx))
        except Exception as e:
            print(f"❌ Ошибка инициализации M2M100-ONNX: {e}\n")
    else:
        print("⚠️  M2M100-ONNX пропущен (не установлен)\n")
    
    # M2M100 CTranslate2
    if M2M100_AVAILABLE:
        m2m = M2M100Wrapper()
        try:
            m2m.initialize()
            translators.append(("m2m100_ct2", m2m))
        except Exception as e:
            print(f"❌ Ошибка инициализации M2M100-CT2: {e}\n")
    else:
        print("⚠️  M2M100-CT2 пропущен (не установлен)\n")
    
    # Argos Translate (запускаем последним)
    if ARGOS_AVAILABLE:
        argos = ArgosTranslateWrapper()
        try:
            argos.initialize()
            translators.append(("argos", argos))
        except Exception as e:
            print(f"❌ Ошибка инициализации Argos Translate: {e}\n")
    else:
        print("⚠️  Argos Translate пропущен (не установлен)\n")
    
    if len(translators) < 1:
        print("❌ Необходимо установить хотя бы один переводчик!")
        sys.exit(1)
    
    # Запускаем бенчмарки
    results = {}
    for name, translator in translators:
        results[name] = run_benchmark(translator, texts)
    
    # Выводим сравнительную таблицу для всех переводчиков
    if results:
        print_comparison_table(results)
        
        # Сохраняем результаты в Markdown файл
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"benchmark_results_{timestamp}.md"
        save_results_to_markdown(results, texts, output_file)
    else:
        print("⚠️  Нет результатов для вывода")
    
    print("🎉 Бенчмарк завершён!\n")


if __name__ == "__main__":
    main()

