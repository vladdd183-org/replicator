# Оптимизация Docker образа для CPU-only версии

## Проблема
Исходный Docker образ включал GPU/CUDA зависимости от PaddlePaddle, которые добавляли **2.67 ГБ** лишнего веса:

### Ненужные NVIDIA/CUDA пакеты:
- nvidia-cublas-cu12 (594 MB)
- nvidia-cudnn-cu12 (706 MB)
- nvidia-cusolver-cu12 (267 MB)
- nvidia-cusparse-cu12 (288 MB)
- nvidia-cusparselt-cu12 (287 MB)
- nvidia-nccl-cu12 (322 MB)
- nvidia-cufft-cu12 (193 MB)
- И другие CUDA библиотеки

## Решение

### 1. Обновление pyproject.toml
Добавлена конфигурация для использования CPU-only репозитория PaddlePaddle:

```toml
[tool.uv]
# Приоритет источников пакетов
index-strategy = "unsafe-best-match"
extra-index-url = ["https://www.paddlepaddle.org.cn/packages/stable/cpu/"]

[tool.uv.sources]
paddlepaddle = { index = "paddlepaddle-cpu" }

[[tool.uv.index]]
name = "paddlepaddle-cpu"  
url = "https://www.paddlepaddle.org.cn/packages/stable/cpu/"
```

### 2. Оптимизация Dockerfile
- Использована многоступенчатая сборка (multi-stage build)
- Разделение на builder и runtime этапы
- Удаление build-зависимостей из финального образа
- Явное отключение CUDA через переменные окружения

### 3. Перегенерация uv.lock
- Удален старый lock файл с GPU зависимостями
- Сгенерирован новый с CPU-only версией PaddlePaddle

## Результаты
- **Удалены все CUDA/NVIDIA пакеты** (экономия ~2.67 ГБ)
- Используется официальная CPU версия PaddlePaddle из китайского репозитория
- Оптимизирован процесс сборки через multi-stage build
- Явно указаны переменные окружения для отключения GPU

## Проверка
После сборки образа проверьте его размер:
```bash
docker images | grep doctrans-cpu-test
```

Ожидаемый результат: значительное уменьшение размера образа на ~2.5-3 ГБ.

## Важные замечания
- Приложение работает **только на CPU**, что подтверждается кодом
- PaddleOCR инициализируется без GPU параметров
- Переменные окружения `CUDA_VISIBLE_DEVICES=""`, `USE_CUDA=0`, `USE_GPU=0` гарантируют работу на CPU






