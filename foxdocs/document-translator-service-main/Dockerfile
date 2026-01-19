# syntax=docker/dockerfile:1.4

# ===================================================================
# ОПТИМИЗИРОВАННЫЙ CPU-ONLY DOCKERFILE
# Размер: ~500-800 МБ (вместо 2.5-3 ГБ)
# ===================================================================

# ===================================================================
# СТАДИЯ 1: Builder - установка зависимостей
# ===================================================================
FROM python:3.11-slim AS builder

# КРИТИЧНО: Устанавливаем переменные окружения для CPU-ONLY
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # === БЛОКИРУЕМ ВСЕ CUDA/GPU ===
    CUDA_VISIBLE_DEVICES="" \
    USE_CUDA=0 \
    USE_GPU=0 \
    # Блокируем бинарные пакеты с CUDA (headless версии разрешены - они CPU-only)
    PIP_NO_BINARY=opencv-python,opencv-contrib-python

WORKDIR /app

# Устанавливаем минимальные build-зависимости + библиотеки для OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    wget \
    libglib2.0-0 \
    libsm6 \
    libgl1 \
    libxext6 \
    libxrender1 \
    libgthread-2.0-0 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Обновляем pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Копируем constraints файл для блокировки NVIDIA пакетов
COPY .pip-constraints.txt ./

# Копируем файлы зависимостей
COPY pyproject.toml ./

# === КЛЮЧЕВОЙ МОМЕНТ: Устанавливаем зависимости ВРУЧНУЮ ===
# НЕ используем uv, т.к. он может игнорировать constraints!

# ШАГ 1: Сначала устанавливаем numpy и зависимости для сборки
# setuptools<60 нужен для совместимости с scikit-image
# PyYAML==6.0.2 требуется для paddlex и совместим со всеми пакетами
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    "numpy>=1.24.0,<2.0.0" \
    "setuptools<60" \
    "pyyaml==6.0.2" \
    Cython

# ШАГ 2: Устанавливаем базовые зависимости (OpenCV CPU-only версии)
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    pillow==11.* \
    opencv-python-headless==4.10.* \
    opencv-contrib-python-headless==4.10.*

# ШАГ 3: Web framework
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    litestar==2.17.0 \
    pydantic==2.9.* \
    pydantic-settings==2.* \
    dishka==1.4.* \
    logfire==2.7.* \
    uvicorn[standard]==0.32.* \
    python-multipart==0.0.20

# ШАГ 4: PaddlePaddle CPU-only (требуется специальный index)
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    paddlepaddle==3.2.0 \
    --index-url https://www.paddlepaddle.org.cn/packages/stable/cpu/

# ШАГ 5: Сначала устанавливаем scikit-image отдельно (проблемная зависимость)
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    "scikit-image>=0.19.0"

# ШАГ 6: Устанавливаем общие зависимости
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    "typing-extensions>=4.0.0" \
    "packaging>=20.0" \
    "requests>=2.25.0" \
    "filelock>=3.0.0" \
    "huggingface-hub" \
    "pandas" \
    "prettytable" \
    "colorlog" \
    "chardet" \
    "aistudio-sdk" \
    "modelscope" \
    "py-cpuinfo" \
    "ruamel.yaml" \
    "ujson" \
    "protobuf" \
    "networkx" \
    "opt-einsum"

# Устанавливаем paddlex[ocr-core] БЕЗ constraints и PIP_NO_BINARY
# Это позволит установить opencv-contrib-python из готового wheel (CPU-only с PyPI)
# Временно отключаем обе переменные только для этой команды
RUN PIP_CONSTRAINT='' PIP_NO_BINARY='' pip install --no-cache-dir \
    "paddlex[ocr-core]==3.2.1"

# Устанавливаем paddleocr
RUN pip install --no-cache-dir \
    --no-deps \
    paddleocr==3.2.0

# ШАГ 7: Translation и PDF
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    "pymupdf>=1.23.0"

# argostranslate - устанавливаем без зависимостей (PyYAML уже установлен)
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    --no-deps \
    "argostranslate==1.9.*"

# Сначала устанавливаем torch CPU-only из специального индекса PyTorch
# Используем версию 2.5.0+cpu которая совместима со stanza
RUN PIP_CONSTRAINT='' pip install --no-cache-dir \
    torch==2.5.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Устанавливаем зависимости stanza
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    "tqdm>=1.56.0"

# Теперь устанавливаем stanza (она будет использовать уже установленный torch)
RUN pip install --no-cache-dir \
    --no-deps \
    "stanza==1.1.1"

# Устанавливаем остальные зависимости argostranslate
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    "ctranslate2>=3.16.0" \
    "sentencepiece>=0.1.96" \
    "requests>=2.25.1"

# Обновляем setuptools до нормальной версии после сборки проблемных пакетов
# и устанавливаем недостающие зависимости для runtime
RUN pip install --no-cache-dir \
    -c .pip-constraints.txt \
    "setuptools>=65.0" \
    "more-itertools"

# Проверяем, что NVIDIA пакетов НЕТ
RUN echo "=== Проверка отсутствия NVIDIA пакетов ===" && \
    if pip list | grep -i nvidia; then \
        echo "❌ ОШИБКА: Обнаружены NVIDIA пакеты!" && exit 1; \
    else \
        echo "✅ SUCCESS: NVIDIA пакетов нет!"; \
    fi

# Копируем исходный код и скрипты
COPY src /app/src
COPY scripts /app/scripts

# ШАГ 8: Прогрузка моделей
# Создаем директории для кешей
RUN mkdir -p /app/.cache /app/.argos /app/.paddlex /app/.stanza && \
    chmod -R 777 /app/.cache /app/.argos /app/.paddlex /app/.stanza

# Устанавливаем переменные окружения для кешей
ENV HOME=/app \
    XDG_CACHE_HOME=/app/.cache \
    ARGOS_DATA_DIR=/app/.argos \
    STANZA_RESOURCES_DIR=/app/.stanza \
    PYTHONWARNINGS="ignore::FutureWarning"

# Запускаем скрипт прогрузки моделей
# || true чтобы сборка не упала если модели не скачаются
RUN python /app/scripts/prewarm_models.py || echo "⚠️  Models preload failed, will download at runtime"

# ===================================================================
# СТАДИЯ 2: Runtime - финальный минимальный образ
# ===================================================================
FROM python:3.11-slim

# Переменные окружения для runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CUDA_VISIBLE_DEVICES="" \
    USE_CUDA=0 \
    USE_GPU=0 \
    HOME=/app \
    XDG_CACHE_HOME=/app/.cache \
    ARGOS_DATA_DIR=/app/.argos \
    PYTHONWARNINGS="ignore::FutureWarning"

WORKDIR /app

# Устанавливаем только runtime зависимости
# Включая библиотеки для OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libgl1 \
    libxext6 \
    libxrender1 \
    libgthread-2.0-0 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Копируем Python пакеты из builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем исходный код
COPY --from=builder /app/src /app/src

# Копируем предзагруженные модели и кеши из builder
COPY --from=builder /app/.cache /app/.cache
COPY --from=builder /app/.argos /app/.argos
COPY --from=builder /app/.paddlex /app/.paddlex
COPY --from=builder /app/.stanza /app/.stanza

# Создаем non-root пользователя и даем права на директории
# Директории с моделями уже скопированы из builder
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Переменная окружения для stanza - использовать app директорию
ENV STANZA_RESOURCES_DIR=/app/.stanza

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Запуск приложения (используем factory функцию create_app_instance)
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.Main:create_app_instance", "--factory", "--host", "0.0.0.0", "--port", "8000"]

