# 🔧 Технические заметки о реализации

## 📐 Архитектура бенчмарка

### Структура классов

```
ResourceMonitor          # Мониторинг CPU/RAM в реальном времени
    └── get_current_stats()

ArgosTranslateWrapper    # Обёртка для Argos Translate
    ├── initialize()     # Загрузка пакетов zh→en, en→ru
    └── translate()      # Двухэтапный перевод

M2M100Wrapper           # Обёртка для M2M100
    ├── initialize()     # Загрузка модели facebook/m2m100_418M
    └── translate()      # Прямой перевод zh→ru

Dataclasses:
    ├── TranslationResult      # Результат одного перевода + метрики
    └── BenchmarkResult        # Агрегированные результаты бенчмарка
```

## 🔍 Детали реализации

### 1. Argos Translate (zh → en → ru)

**Особенности:**
- Использует два отдельных языковых пакета
- Перевод в два этапа: сначала zh→en, затем en→ru
- Основан на CTranslate2 (оптимизирован для CPU) - подтягивается автоматически
- Легковесный, меньше требований к памяти

**Код:**
```python
# Первый этап: китайский → английский
intermediate_text = argostranslate.translate.translate(text, "zh", "en")

# Второй этап: английский → русский
final_text = argostranslate.translate.translate(intermediate_text, "en", "ru")
```

**Установка пакетов:**
```python
argostranslate.package.update_package_index()
# Автоматически скачивает и устанавливает пакеты zh→en и en→ru
```

### 2. M2M100 (прямой zh → ru) через CTranslate2

**Особенности:**
- Многоязычная модель (100 языков, 9900 направлений)
- Прямой перевод без промежуточных этапов
- 418M параметров
- **Использует CTranslate2 с int8 квантизацией** для ускорения на CPU
- Автоматическая конвертация из Transformers при первом запуске
- Требует ~800MB RAM (меньше чем PyTorch благодаря квантизации)

**Код:**
```python
# Токенизация
tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))

# Целевой язык
target_prefix = [tokenizer.lang_code_to_token["ru"]]

# Перевод через CTranslate2 (оптимизировано!)
results = model.translate_batch(
    [tokens],
    target_prefix=[target_prefix],
    beam_size=4,
    max_decoding_length=512
)

# Декодирование
output_tokens = results[0].hypotheses[0]
output_ids = tokenizer.convert_tokens_to_ids(output_tokens)
translated = tokenizer.decode(output_ids, skip_special_tokens=True)
```

**Автоматическая конвертация:**
```python
# При первом запуске автоматически конвертирует модель:
# facebook/m2m100_418M (PyTorch) → CTranslate2 формат с int8 квантизацией
# Конвертированная модель сохраняется в ~/.cache/ctranslate2/
```

**Принудительный CPU режим с CTranslate2:**
```python
# Отключаем CUDA
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Загружаем через CTranslate2 с оптимизациями
model = ctranslate2.Translator(
    model_path,
    device="cpu",
    compute_type="int8",  # int8 квантизация (быстрее, меньше памяти)
    inter_threads=4,       # Параллельные потоки
    intra_threads=4
)
```

## 📊 Мониторинг ресурсов

### CPU мониторинг
```python
process = psutil.Process()
cpu_percent = process.cpu_percent(interval=0.1)  # 100ms интервал
```

**Примечание:** CPU% показывает использование относительно одного ядра
- 100% = 1 ядро полностью загружено
- 400% = 4 ядра полностью загружены

### RAM мониторинг
```python
memory_mb = process.memory_info().rss / 1024 / 1024  # Резидентная память в MB
```

**RSS (Resident Set Size)** - реальный объём физической памяти, занимаемой процессом.

## 🎯 Методология бенчмарка

### Измерение времени
```python
start_time = time.time()
# ... перевод ...
elapsed_time = time.time() - start_time
```

### Агрегация метрик
- **Общее время**: Сумма времени всех переводов
- **Среднее время**: Общее время / количество текстов
- **Средний CPU**: Среднее арифметическое всех измерений
- **Средняя RAM**: Среднее арифметическое всех измерений
- **Пиковая RAM**: Максимальное значение за весь бенчмарк

## 🔬 CPU оптимизации

### PyTorch CPU Backend

PyTorch автоматически использует оптимизированные CPU инструкции:
- **AVX2** - SIMD инструкции для векторных операций
- **MKL/OpenBLAS** - оптимизированные библиотеки линейной алгебры
- **OpenMP** - многопоточность для параллельных вычислений

### CTranslate2 оптимизации

CTranslate2 использует:
- **Квантизация весов** - уменьшение размера модели
- **Векторизация** - SIMD инструкции
- **Батчинг** - обработка нескольких запросов одновременно (в будущем)

### Рекомендации для максимальной производительности

1. **Использовать все ядра CPU:**
   ```bash
   export OMP_NUM_THREADS=$(nproc)
   export MKL_NUM_THREADS=$(nproc)
   ```

2. **Отключить Intel Hyperthreading** (может снизить производительность)

3. **Использовать процессор с AVX2/AVX512:**
   ```bash
   # Проверить поддержку
   cat /proc/cpuinfo | grep avx2
   ```

## 📈 Ожидаемые результаты

### На современном CPU (8 ядер, 3.5GHz, AVX2)

**Argos Translate:**
- Скорость: ~0.5-1 сек/текст
- RAM: 300-500 MB
- CPU: 40-60% (1-2 ядра активны)

**M2M100:**
- Скорость: ~0.3-0.8 сек/текст
- RAM: 800-1500 MB
- CPU: 60-90% (все ядра активны)

### Факторы влияющие на производительность

1. **Длина текста** - более длинные тексты требуют больше времени
2. **Количество ядер CPU** - больше ядер = быстрее M2M100
3. **Размер RAM** - больше RAM = меньше swap-а
4. **Первый запуск** - медленнее из-за загрузки моделей в память

## 🐛 Известные проблемы и решения

### 1. CUDA найдена, но не нужна

**Проблема:** PyTorch установился с CUDA поддержкой
**Решение:**
```bash
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 2. Out of Memory (OOM)

**Проблема:** Недостаточно RAM для M2M100
**Решения:**
- Закрыть другие приложения
- Увеличить swap
- Уменьшить размер батча (в коде установлен 1)
- Использовать меньшую модель

### 3. Медленная загрузка моделей

**Проблема:** Первый запуск долго загружает модели
**Решение:**
- Это нормально (загрузка ~1-2 GB)
- Последующие запуски будут быстрее (кеш HuggingFace)

### 4. Argos пакеты не устанавливаются

**Проблема:** Ошибка при загрузке языковых пакетов
**Решение:**
```python
# Вручную обновить индекс
import argostranslate.package
argostranslate.package.update_package_index()
```

## 🔮 Возможные улучшения

### 1. Батчинг
Обрабатывать несколько текстов за раз для ускорения:
```python
# Вместо:
for text in texts:
    result = translate(text)

# Можно:
results = translate_batch(texts, batch_size=8)
```

### 2. Многопроцессорность
Параллельная обработка на разных ядрах:
```python
from multiprocessing import Pool
with Pool(processes=4) as pool:
    results = pool.map(translate, texts)
```

### 3. Квантизация M2M100
Использовать 8-bit квантизацию для уменьшения размера:
```python
model = M2M100ForConditionalGeneration.from_pretrained(
    "facebook/m2m100_418M",
    load_in_8bit=True  # Требует bitsandbytes
)
```

### 4. Кеширование переводов
Хранить уже переведённые тексты:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def translate_cached(text: str) -> str:
    return translate(text)
```

## 📚 Полезные ссылки

- **Argos Translate API**: https://argos-translate.readthedocs.io/
- **M2M100 Paper**: https://arxiv.org/abs/2010.11125
- **CTranslate2 Docs**: https://opennmt.net/CTranslate2/
- **PyTorch CPU Optimizations**: https://pytorch.org/docs/stable/notes/cpu_threading_torchscript_inference.html
- **HuggingFace Transformers**: https://huggingface.co/docs/transformers/

## 📝 Логирование и отладка

Для детального логирования добавьте в начало скрипта:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Для профилирования производительности:
```python
import cProfile
cProfile.run('main()', 'benchmark_stats')

# Анализ результатов
import pstats
stats = pstats.Stats('benchmark_stats')
stats.sort_stats('cumulative').print_stats(20)
```

## 🎓 Заключение

Этот бенчмарк предоставляет объективное сравнение двух подходов к переводу:
- **Argos**: Лёгкий, двухэтапный, меньше памяти
- **M2M100**: Тяжёлый, прямой, возможно точнее

Выбор зависит от ваших требований к скорости, точности и ресурсам.

