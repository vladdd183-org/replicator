# Быстрый старт: Оптимизация Docker образа

## 🎯 Цель

Уменьшить размер Docker образа с **2.5 ГБ до 500-800 МБ**, используя только CPU-only зависимости.

## 📋 Что было сделано

### 1. ✅ Оптимизированный Dockerfile

Создан `Dockerfile.optimized` с:
- **Multistage build** (builder + runtime)
- **Минимальный базовый образ** (python:3.11-slim)
- **Только CPU-only зависимости**
- **Оптимизированный .dockerignore**

### 2. ✅ Обновленные зависимости в pyproject.toml

```toml
# Было (закомментировано):
#    "opencv-python==4.8.*",        # ~100MB + GUI зависимости
#    "numpy",                       # без явной версии
#    "pymupdf",                     # без явной версии

# Стало:
"opencv-python-headless==4.8.*",  # ~50MB, без GUI
"numpy>=1.24.0,<2.0.0",           # явная версия
"ctranslate2>=3.0.0",             # CPU-only для argostranslate
"pymupdf>=1.23.0",                # явная версия
```

### 3. ✅ Скрипты для автоматизации

- `scripts/build-optimized.sh` - сборка оптимизированного образа
- `scripts/check-image-size.sh` - анализ размера и содержимого образа

### 4. ✅ Документация

- `CPU_OPTIMIZATION.md` - существующий документ о PaddlePaddle
- `CPU_OPTIMIZATION_RECOMMENDATIONS.md` - полное руководство по оптимизации
- Этот файл - быстрый старт

## 🚀 Инструкция по использованию

### Шаг 1: Обновить lock-файл зависимостей

```bash
cd /home/vladdd183/Рабочий\ стол/document-translator-service

# Удалить старый lock-файл
rm uv.lock

# Создать новый с обновленными зависимостями
uv lock
```

**Важно:** Это обновит `uv.lock` с учетом новых CPU-only зависимостей.

### Шаг 2: Собрать оптимизированный образ

#### Вариант A: Используя скрипт (рекомендуется)

```bash
./scripts/build-optimized.sh
```

Скрипт автоматически:
- Соберет образ
- Покажет время сборки
- Выведет размер нового образа
- Запустит анализ содержимого

#### Вариант B: Вручную

```bash
# Сборка
docker build -f Dockerfile.optimized -t document-translator:optimized .

# Проверка размера
docker images | grep document-translator

# Анализ
./scripts/check-image-size.sh document-translator:optimized
```

### Шаг 3: Проверить функциональность

#### Тест 1: Проверка импорта библиотек

```bash
docker run --rm document-translator:optimized python -c "
import paddlepaddle
import paddleocr
import cv2
import numpy
import pymupdf
import ctranslate2
print('✅ Все библиотеки импортированы успешно!')
print(f'PaddlePaddle версия: {paddlepaddle.__version__}')
print(f'NumPy версия: {numpy.__version__}')
print(f'OpenCV версия: {cv2.__version__}')
"
```

#### Тест 2: Проверка отсутствия CUDA

```bash
docker run --rm document-translator:optimized python -c "
import paddle
print(f'CUDA доступна: {paddle.is_compiled_with_cuda()}')
print(f'GPU устройства: {paddle.device.get_available_device()}')
"
```

Ожидаемый вывод:
```
CUDA доступна: False
GPU устройства: cpu
```

#### Тест 3: Запуск приложения

```bash
# Запуск контейнера
docker run -d -p 8000:8000 --name doc-translator document-translator:optimized

# Проверка healthcheck
docker ps

# Проверка логов
docker logs doc-translator

# Остановка
docker stop doc-translator
docker rm doc-translator
```

### Шаг 4: Анализ результатов

```bash
./scripts/check-image-size.sh document-translator:optimized
```

Скрипт покажет:
- Общий размер образа
- Размеры слоев
- Топ-15 самых больших Python пакетов
- Проверку на CUDA зависимости
- Версии ключевых пакетов
- Сравнение с целевым размером (800 МБ)

## 📊 Ожидаемые результаты

### Размер образа

| Компонент | Ожидаемый размер |
|-----------|------------------|
| Python 3.11-slim | ~150 МБ |
| PaddlePaddle CPU | ~200 МБ |
| PaddleOCR | ~50 МБ |
| OpenCV-headless | ~50 МБ |
| NumPy | ~30 МБ |
| CTranslate2 | ~50 МБ |
| Argostranslate | ~30 МБ |
| PyMuPDF | ~15 МБ |
| Litestar + зависимости | ~100 МБ |
| Ваш код | ~50 МБ |
| **ИТОГО** | **~700-800 МБ** |

### Время сборки

- **С кешем:** 2-3 минуты
- **Без кеша:** 5-7 минут

### Проверка CPU-only

Должны отсутствовать пакеты:
- ❌ nvidia-*
- ❌ cuda*
- ❌ cudnn*
- ❌ cublas*

## 🔧 Troubleshooting

### Проблема: Образ все еще большой (>1 ГБ)

**Решение:**

1. Проверьте, что используется `Dockerfile.optimized`, а не старый `Dockerfile`
2. Убедитесь, что обновлен `uv.lock` после изменений в `pyproject.toml`
3. Запустите анализ: `./scripts/check-image-size.sh`
4. Проверьте наличие CUDA пакетов: `docker run --rm IMAGE pip list | grep -i cuda`

### Проблема: Ошибка при установке зависимостей

**Решение:**

```bash
# Очистите Docker кеш
docker builder prune -af

# Пересоздайте lock-файл
rm uv.lock
uv lock

# Соберите заново
docker build --no-cache -f Dockerfile.optimized -t document-translator:optimized .
```

### Проблема: PaddlePaddle не работает

**Решение:**

Убедитесь, что в `pyproject.toml` настроен CPU-only репозиторий:

```toml
[tool.uv]
index-strategy = "unsafe-best-match"
extra-index-url = ["https://www.paddlepaddle.org.cn/packages/stable/cpu/"]

[tool.uv.sources]
paddlepaddle = { index = "paddlepaddle-cpu" }
```

### Проблема: opencv-python-headless отсутствует

**Решение:**

```bash
# Проверьте, что в pyproject.toml указан headless вариант
grep opencv-python pyproject.toml

# Должно быть:
# "opencv-python-headless==4.8.*"

# НЕ должно быть:
# "opencv-python==4.8.*"
```

## 📈 Дальнейшая оптимизация

Если нужно еще больше уменьшить размер:

### 1. Использовать distroless образ

```dockerfile
FROM gcr.io/distroless/python3-debian12
# Размер: ~50-80 МБ (без shell!)
```

### 2. Squash layers

```bash
docker build --squash -f Dockerfile.optimized -t document-translator:optimized .
```

### 3. Использовать .dockerignore

Убедитесь, что `.dockerignore` исключает:
- Тесты
- Документацию
- Git файлы
- IDE настройки
- Логи и временные файлы

### 4. Анализ с Dive

```bash
# Установка Dive
wget https://github.com/wagoodman/dive/releases/download/v0.10.0/dive_0.10.0_linux_amd64.deb
sudo dpkg -i dive_0.10.0_linux_amd64.deb

# Анализ
dive document-translator:optimized
```

## 📝 Checklist

- [x] Создан `Dockerfile.optimized`
- [x] Обновлен `pyproject.toml` с CPU-only зависимостями
- [x] Создан `.dockerignore`
- [x] Созданы скрипты сборки и анализа
- [ ] Обновлен `uv.lock` (запустите `rm uv.lock && uv lock`)
- [ ] Собран оптимизированный образ
- [ ] Проверена функциональность
- [ ] Измерен финальный размер
- [ ] Образ запушен в registry (если нужно)

## 🎓 Полезные команды

```bash
# Список всех образов с размерами
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Очистка неиспользуемых образов
docker image prune -a

# История слоев образа
docker history document-translator:optimized --no-trunc

# Экспорт образа
docker save document-translator:optimized | gzip > document-translator-optimized.tar.gz

# Импорт образа
docker load < document-translator-optimized.tar.gz
```

## 🤝 Поддержка

Если возникли проблемы:

1. Проверьте документацию: `CPU_OPTIMIZATION_RECOMMENDATIONS.md`
2. Запустите анализ: `./scripts/check-image-size.sh`
3. Проверьте логи сборки: `build.log`
4. Создайте issue в репозитории с выводом команд

## 📚 Дополнительные материалы

- [CPU_OPTIMIZATION.md](./CPU_OPTIMIZATION.md) - История оптимизации PaddlePaddle
- [CPU_OPTIMIZATION_RECOMMENDATIONS.md](./CPU_OPTIMIZATION_RECOMMENDATIONS.md) - Полное руководство
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)



