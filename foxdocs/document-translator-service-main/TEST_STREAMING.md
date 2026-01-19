# 🧪 Тестирование Streaming API

## Быстрый старт

### 1. Перезапуск сервера

**ВАЖНО:** После добавления новых endpoints нужно перезапустить сервер!

```bash
# Остановить текущий сервер (Ctrl+C)
# Запустить снова
uv run litestar run --host 0.0.0.0 --port 8000
```

### 2. Запуск тестов

#### Базовый тест (с дефолтными настройками)
```bash
uv run python test_streaming_websocket.py 1.jpg
```

#### С настройкой воркеров
```bash
# 3 OCR воркера, 2 Translation воркера
uv run python test_streaming_websocket.py 1.jpg --workers 3 2
```

#### Тест с заданными областями
```bash
uv run python test_streaming_websocket.py 1.jpg --mode regions --regions example_regions.json
```

#### Другие языки
```bash
uv run python test_streaming_websocket.py 1.jpg --from-lang en --to-lang ru
```

#### Полная команда с опциями
```bash
uv run python test_streaming_websocket.py 1.jpg \
  --host localhost \
  --port 8000 \
  --workers 4 2 \
  --from-lang zh \
  --to-lang ru
```

---

## Параметры теста

```
usage: test_streaming_websocket.py [-h] [--host HOST] [--port PORT]
                                   [--mode {image,regions}]
                                   [--workers OCR TRANSLATION]
                                   [--from-lang FROM_LANG]
                                   [--to-lang TO_LANG]
                                   [--regions REGIONS]
                                   image

Аргументы:
  image                     Путь к изображению
  --host HOST              WebSocket хост (default: localhost)
  --port PORT              WebSocket порт (default: 8000)
  --mode {image,regions}   Режим обработки (default: image)
  --workers OCR TRANSLATION  Количество воркеров (default: 2 2)
  --from-lang FROM_LANG    Исходный язык (default: zh)
  --to-lang TO_LANG        Целевой язык (default: ru)
  --regions REGIONS        Путь к JSON с областями (для режима regions)
```

---

## Поддерживаемые языки

- `zh` - Китайский (Chinese)
- `en` - Английский (English)
- `ru` - Русский (Russian)

---

## Что показывает тест

### События прогресса

#### 🔍 Детекция
```
🔍 [0.5s] Detection started...
📍 [3.2s] Regions detected: 15
   Region 0: 4 points
   Region 1: 4 points
   Region 2: 4 points
```

#### 📝 OCR
```
   📝 [4.1s] OCR #0 (conf: 0.95): 你好世界...
   📝 [5.2s] OCR #1 (conf: 0.92): 这是一个测试文档...
```

#### 🌐 Перевод
```
   🌐 [5.5s] Translation #0:
      Original:    你好世界
      Translated:  Привет мир
   🌐 [6.3s] Translation #1:
      Original:    这是一个测试文档
      Translated:  Это тестовый документ
```

#### ✅ Завершение
```
✅ [9.2s] Processing completed!
   Total regions: 15
   Processed: 14
   Failed: 1
```

### Метрики производительности

```
📊 PERFORMANCE METRICS
⏱️  Total processing time: 9.23s
⚡ Time to first result: 5.14s

📍 Regions detected: 15
📝 OCR completed: 14
🌐 Translations completed: 14
✅ No errors

⚡ Throughput: 1.52 regions/sec
```

---

## Проверка endpoints

### Проверка доступности

```bash
# Обычный endpoint (работает)
curl http://localhost:8000/ws/docs-translate/test

# Streaming endpoint (должен вернуть 426 Upgrade Required)
curl http://localhost:8000/ws/docs-translate/process-streaming
```

### Список всех endpoints

```bash
# Посмотреть OpenAPI документацию
open http://localhost:8000/api/docs
```

---

## Возможные ошибки

### ❌ HTTP 403 - Forbidden
**Причина:** Endpoints не зарегистрированы или сервер не перезапущен  
**Решение:** Перезапустите сервер

### ❌ Connection refused
**Причина:** Сервер не запущен  
**Решение:** Запустите сервер: `uv run litestar run`

### ❌ Invalid language parameter
**Причина:** Неправильный код языка  
**Решение:** Используйте: `zh`, `en`, `ru`

### ❌ License validation failed
**Причина:** Проблема с лицензией  
**Решение:** Проверьте license-helper сервис

---

## Примеры успешных логов

### Успешный тест
```
============================================================
  🚀 STREAMING WEBSOCKET TEST - FULL IMAGE
============================================================
📁 Image: 1.jpg
🔗 URL: ws://localhost:8000/ws/docs-translate/process-streaming
⚙️  Workers: OCR=2, Translation=2
🌍 Languages: zh → ru

✅ WebSocket connection established

============================================================
  📤 Step 1: Sending metadata
============================================================
{
  "action": "process_image_streaming",
  "filename": "1.jpg",
  ...
}

📩 Server response: ready
   Send image data as binary

============================================================
  📤 Step 2: Sending image data
============================================================
📊 Image size: 1,234,567 bytes
✅ Image sent successfully

============================================================
  📥 Step 3: Receiving streaming events
============================================================

🔍 [0.5s] Detection started...

📍 [3.2s] Regions detected: 15
   Region 0: 4 points
   Region 1: 4 points
   Region 2: 4 points

   🔄 [3.5s] OCR started: Region 0
   📝 [4.1s] OCR #0 (conf: 0.95): 你好世界...
   🔄 [4.2s] Translation started: Region 0
   🌐 [5.5s] Translation #0:
      Original:    你好世界
      Translated:  Привет мир

... (ещё 13 областей)

✅ [9.2s] Processing completed!
   Total regions: 15
   Processed: 14
   Failed: 1

============================================================
  ✅ PROCESSING COMPLETED
============================================================
Total regions: 15
Translated: 14
Total time: 9.23s

============================================================
  📊 PERFORMANCE METRICS
============================================================
⏱️  Total processing time: 9.23s
⚡ Time to first result: 5.14s

📍 Regions detected: 15
📝 OCR completed: 14
🌐 Translations completed: 14
✅ No errors

⚡ Throughput: 1.52 regions/sec

============================================================
```

---

## Полезные команды

```bash
# Проверка доступных изображений
ls -lh *.jpg *.png 2>/dev/null

# Запуск с разным количеством воркеров для сравнения
for workers in "1 1" "2 2" "3 2" "5 3"; do
  echo "Testing with workers: $workers"
  uv run python test_streaming_websocket.py 1.jpg --workers $workers
  echo "---"
done

# Проверка логов сервера
# (сервер выводит подробные логи о каждом событии)
```

---

## Для отладки

### Verbose режим
Добавьте `logfire.info()` выводы в код если нужны дополнительные детали.

### Проверка WebSocket соединения
```python
import asyncio
import websockets

async def test_connection():
    uri = "ws://localhost:8000/ws/docs-translate/process-streaming"
    async with websockets.connect(uri) as ws:
        print("✅ Connected!")
        await ws.close()

asyncio.run(test_connection())
```

---

**Happy Testing! 🚀**

