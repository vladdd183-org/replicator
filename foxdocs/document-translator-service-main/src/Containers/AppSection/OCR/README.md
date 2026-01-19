# 📷 OCR Container

## 🎯 Описание

OCR (Optical Character Recognition) контейнер предоставляет функциональность для распознавания текста на изображениях с использованием PaddleOCR v5.

## ✨ Возможности

- **Полное распознавание**: Автоматическое обнаружение и распознавание всего текста на изображении
- **Полигональные области**: Распознавание текста в заданных пользователем областях произвольной формы
- **Перспективное выпрямление**: Автоматическое выпрямление 4-угольных областей
- **Параллельная обработка**: Эффективная обработка множественных областей
- **Синглтон менеджер**: Единственный экземпляр OCR движка для экономии ресурсов

## 🏗️ Архитектура

```
OCR/
├── Actions/                    # Бизнес-логика
│   ├── ProcessImageAction      # Обработка полного изображения
│   └── ProcessPolygonsAction   # Обработка полигональных областей
├── Tasks/                      # Атомарные операции
│   ├── ValidateImageTask       # Валидация изображения
│   ├── ProcessFullImageTask    # OCR всего изображения
│   └── ProcessPolygonRegionTask # OCR полигональной области
├── Managers/                   # Управление ресурсами
│   └── OCREngineManager        # Синглтон для PaddleOCR
├── Data/                       # Схемы данных
│   └── OCRSchemas              # Pydantic модели
├── Exceptions/                 # Обработка ошибок
│   └── OCRExceptions           # Специфичные исключения
└── UI/API/Controllers/         # HTTP endpoints
    └── OCRController           # REST API контроллер
```

## 📡 API Endpoints

### 1. Распознавание всего изображения

```http
POST /api/ocr/process
Content-Type: multipart/form-data

file: <изображение>
```

**Ответ:**
```json
{
  "results": [
    {
      "text": "Распознанный текст",
      "confidence": 0.98,
      "coordinates": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    }
  ],
  "total_regions": 5,
  "image_dimensions": {"width": 1920, "height": 1080},
  "processing_time": 1.23,
  "timestamp": "2024-01-01T12:00:00"
}
```

### 2. Распознавание в полигональных областях

```http
POST /api/ocr/process-polygons
Content-Type: multipart/form-data

file: <изображение>
regions: [
  {
    "points": [[100,100], [300,100], [300,200], [100,200]],
    "region_id": "header"
  },
  {
    "points": [[100,250], [500,250], [450,350], [150,350]],
    "region_id": "content"
  }
]
```

**Ответ:**
```json
{
  "results": [
    {
      "region_id": "header",
      "text": "Заголовок документа",
      "confidence": 0.98,
      "processing_time": 0.15
    },
    {
      "region_id": "content",
      "text": "Основной текст",
      "confidence": 0.95,
      "processing_time": 0.18
    }
  ],
  "total_regions": 2,
  "image_dimensions": {"width": 1920, "height": 1080},
  "processing_time": 0.45,
  "timestamp": "2024-01-01T12:00:00"
}
```

## 🚀 Использование

### Python клиент

```python
import httpx
import json

# Распознавание всего изображения
async def process_full_image():
    async with httpx.AsyncClient() as client:
        with open("document.jpg", "rb") as f:
            files = {"file": f}
            response = await client.post(
                "http://localhost:8000/api/ocr/process",
                files=files
            )
        return response.json()

# Распознавание полигональных областей
async def process_polygons():
    regions = [
        {
            "points": [[100,100], [300,100], [300,200], [100,200]],
            "region_id": "title"
        }
    ]
    
    async with httpx.AsyncClient() as client:
        with open("document.jpg", "rb") as f:
            files = {"file": f}
            data = {"regions": json.dumps(regions)}
            response = await client.post(
                "http://localhost:8000/api/ocr/process-polygons",
                files=files,
                data=data
            )
        return response.json()
```

### cURL примеры

```bash
# Полное изображение
curl -X POST http://localhost:8000/api/ocr/process \
  -F "file=@document.jpg"

# Полигональные области
curl -X POST http://localhost:8000/api/ocr/process-polygons \
  -F "file=@document.jpg" \
  -F 'regions=[{"points":[[100,100],[300,100],[300,200],[100,200]],"region_id":"header"}]'
```

## 🔧 Конфигурация

OCR движок инициализируется автоматически при старте приложения со следующими настройками:

- **Язык**: Китайский + Английский (ch)
- **Предобработка**: Отключена (для чистого распознавания)
- **Модель**: PP-OCRv5_server_rec (для полигонов)
- **Максимальный размер файла**: 10MB

## 📊 Производительность

- **Инициализация**: ~2-3 секунды при старте приложения
- **Полное изображение**: ~0.5-2 секунды в зависимости от размера
- **Полигональная область**: ~0.1-0.3 секунды на область
- **Параллельная обработка**: До 10 областей одновременно

## 🛡️ Обработка ошибок

Контейнер предоставляет специфичные исключения:

- `InvalidImageFormatException` - Неподдерживаемый формат
- `ImageTooLargeException` - Превышен размер файла
- `InvalidPolygonException` - Некорректный полигон
- `OCRProcessingException` - Ошибка обработки


## 📚 Зависимости

- **PaddleOCR** >= 3.2.0 - OCR движок
- **PaddlePaddle** >= 3.1.1 - ML фреймворк
- **Pillow** >= 11.3.0 - Обработка изображений
- **OpenCV** >= 4.8.0 - Компьютерное зрение
- **NumPy** >= 1.24.0 - Численные вычисления

## 🔗 Связанные компоненты

- `Ship.Parents.Action` - Базовый класс для Actions
- `Ship.Parents.Task` - Базовый класс для Tasks
- `Ship.Parents.Manager` - Базовый класс для Managers
- `Logfire` - Логирование и трассировка


