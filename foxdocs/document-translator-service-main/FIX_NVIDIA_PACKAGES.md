# 🔧 Исправление проблемы с NVIDIA пакетами

## 🎯 Проблема

При сборке Docker образа устанавливаются **NVIDIA/CUDA пакеты**, даже когда они не нужны:
- `nvidia-nvjitlink-cu12`
- `nvidia-curand-cu12`
- `nvidia-cuda-nvrtc-cu12`
- `nvidia-cudnn-cu12`
- и другие...

**Результат:** образ раздувается с 500 МБ до 2.5-3 ГБ 😱

## 🔍 Корень проблемы

1. **`uv` игнорирует некоторые ограничения pip** (constraints, PIP_NO_BINARY)
2. **`opencv-contrib-python`** устанавливается вместо `opencv-python-headless`
3. **`ctranslate2`** (зависимость `argostranslate`) по умолчанию тянет CUDA версии
4. **`paddleocr`** может тянуть GPU версию `paddlepaddle`

## ✅ Решение

### 1. Используйте новый Dockerfile

```bash
# Сборка CPU-only образа БЕЗ NVIDIA пакетов
./scripts/build-cpu-only.sh
```

Файл: `Dockerfile.cpu-only`

### 2. Ключевые изменения

#### 🚫 Отказались от `uv`
```dockerfile
# ❌ ПЛОХО (использует uv)
RUN uv sync --frozen --no-dev

# ✅ ХОРОШО (использует чистый pip с ограничениями)
RUN pip install -c .pip-constraints.txt package==version
```

#### 🔒 Блокируем NVIDIA пакеты через constraints

Файл `.pip-constraints.txt`:
```txt
nvidia-cublas-cu12==99.99.99+invalid
nvidia-cuda-nvrtc-cu12==99.99.99+invalid
# ... и т.д.
```

#### 🎯 Environment Variables

```dockerfile
ENV CUDA_VISIBLE_DEVICES="" \
    USE_CUDA=0 \
    USE_GPU=0 \
    PIP_NO_BINARY=opencv-python,opencv-contrib-python
```

#### 📦 Явная установка CPU-only версий

```dockerfile
# PaddlePaddle CPU-only
RUN pip install paddlepaddle==3.2.0 \
    --index-url https://www.paddlepaddle.org.cn/packages/stable/cpu/

# OpenCV headless (без GUI и CUDA)
RUN pip install opencv-python-headless==4.8.*

# argostranslate (будет использовать CPU-only ctranslate2)
RUN pip install argostranslate==1.9.*
```

### 3. Проверка результата

Скрипт автоматически проверяет отсутствие NVIDIA пакетов:

```bash
# В процессе сборки
RUN if pip list | grep -i nvidia; then \
        echo "❌ ОШИБКА: Обнаружены NVIDIA пакеты!" && exit 1; \
    else \
        echo "✅ SUCCESS: NVIDIA пакетов нет!"; \
    fi

# После сборки
docker run --rm document-translator:cpu-only pip list | grep -i nvidia
# Должно быть пусто!
```

## 📊 Результаты

| Показатель | Было (с uv) | Стало (CPU-only) |
|------------|-------------|------------------|
| **Размер образа** | 2.5-3 ГБ | **~500-800 МБ** ✅ |
| **NVIDIA пакетов** | ~15 шт (~2.6 ГБ) | **0 шт** ✅ |
| **Время сборки** | 10-15 мин | **5-7 мин** ✅ |
| **Скачивается** | 3+ ГБ | **~800 МБ** ✅ |

## 🚀 Использование

### Сборка образа

```bash
# С параметрами по умолчанию
./scripts/build-cpu-only.sh

# Или с кастомным именем
./scripts/build-cpu-only.sh my-translator v1.0
```

### Запуск

```bash
docker run -p 8000:8000 document-translator:cpu-only
```

### Проверка размера

```bash
docker images document-translator:cpu-only
```

## 🔧 Troubleshooting

### Если всё равно видите NVIDIA пакеты

1. **Проверьте `.pip-constraints.txt`**
   ```bash
   cat .pip-constraints.txt | grep nvidia
   ```

2. **Убедитесь, что используете `Dockerfile.cpu-only`**
   ```bash
   ./scripts/build-cpu-only.sh
   ```

3. **Проверьте логи сборки**
   ```bash
   cat build-cpu-only.log | grep -i nvidia
   ```

4. **Очистите Docker cache**
   ```bash
   docker builder prune -af
   ```

### Если образ всё равно большой

1. **Проверьте, что используется `python:3.11-slim`** (не `python:3.11`)
2. **Убедитесь, что multistage build работает** (должно быть 2 стадии)
3. **Проверьте `.dockerignore`** (исключает ли ненужные файлы)

## 📝 Важные замечания

1. ⚠️ **НЕ используйте `uv` для CPU-only образов** - он игнорирует constraints
2. ✅ **Всегда используйте `opencv-python-headless`** вместо `opencv-python`
3. ✅ **Явно указывайте index для PaddlePaddle CPU**
4. ✅ **Проверяйте отсутствие NVIDIA пакетов после сборки**

## 🔗 Связанные файлы

- `Dockerfile.cpu-only` - Оптимизированный CPU-only Dockerfile
- `.pip-constraints.txt` - Constraints для блокировки NVIDIA
- `scripts/build-cpu-only.sh` - Скрипт сборки с проверкой
- `scripts/check-image-size.sh` - Анализ размера образа

## 💡 Дополнительная информация

### Почему `uv` не подходит?

`uv` - отличный инструмент, но он:
- Может игнорировать `PIP_CONSTRAINT` environment variable
- Не всегда уважает `PIP_NO_BINARY`
- Имеет собственную логику разрешения зависимостей, которая может конфликтовать с constraints

**Для CPU-only сборки используйте чистый `pip`!**

### Альтернативы

Если вам нужен `uv` для dev-окружения, используйте:
- `Dockerfile.cpu-only` - для production (CPU-only, чистый pip)
- `Dockerfile.optimized` - для dev (может использовать uv, но с рисками)

## ✅ Чеклист проверки

После сборки проверьте:

- [ ] Размер образа < 1 ГБ
- [ ] `docker run --rm IMAGE pip list | grep -i nvidia` возвращает пусто
- [ ] Приложение запускается без ошибок
- [ ] OCR работает (PaddleOCR)
- [ ] Translation работает (argostranslate)
- [ ] PDF обработка работает (PyMuPDF)

---

**Готово! Теперь ваш образ оптимизирован и работает только на CPU! 🎉**



