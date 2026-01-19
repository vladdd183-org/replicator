# 📡 WebSocket Streaming API - Руководство для Frontend

## 🎯 Обзор

Streaming API позволяет получать результаты OCR и перевода **в реальном времени** по мере их готовности, вместо ожидания завершения всего процесса.

### ✨ Преимущества
- 🚀 **Быстрая обратная связь**: Первые результаты за 3-5 секунд
- 📊 **Прогресс в реальном времени**: Пользователь видит каждый шаг
- ⚡ **Производительность**: До 4x быстрее чем batch обработка
- 🔄 **Параллелизм**: OCR и перевод выполняются одновременно

---

## 🔌 Endpoints

### 1. Обработка полного изображения
```
ws://your-domain/ws/docs-translate/process-streaming
```

### 2. Обработка конкретных регионов
```
ws://your-domain/ws/docs-translate/process-regions-streaming
```

---

## 📨 Протокол обмена

### Шаг 1: Установка соединения

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/docs-translate/process-streaming');

ws.onopen = () => {
  console.log('✅ Connected');
};

ws.onerror = (error) => {
  console.error('❌ WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('🔌 Connection closed:', event.code, event.reason);
};
```

### Шаг 2: Отправка метаданных

**Для обработки полного изображения:**

```javascript
const metadata = {
  action: "process_image_streaming",
  filename: "document.jpg",
  size: imageFile.size,
  from_language: "zh",  // zh, en, ru
  to_language: "ru",
  min_confidence_threshold: 0.1,
  translate_empty_results: false,
  streaming_config: {
    send_region_preview: true  // Отправлять ли координаты регионов
  }
  // Примечание: количество воркеров зафиксировано (OCR=1, Translation=2)
};

ws.send(JSON.stringify(metadata));
```

**Для обработки конкретных регионов:**

```javascript
const metadata = {
  action: "process_regions_streaming",
  filename: "document.jpg",
  size: imageFile.size,
  regions: [
    {
      region_id: "region_1",
      points: [[100, 100], [200, 100], [200, 150], [100, 150]]  // 4 точки полигона
    },
    {
      region_id: "region_2",
      points: [[100, 200], [300, 200], [300, 250], [100, 250]]
    }
  ],
  from_language: "zh",
  to_language: "ru",
  min_confidence_threshold: 0.1,
  translate_empty_results: false,
  streaming_config: {
    send_region_preview: true
  }
  // Примечание: количество воркеров зафиксировано (OCR=1, Translation=2)
};

ws.send(JSON.stringify(metadata));
```

### Шаг 3: Ожидание подтверждения

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.status === 'ready') {
    console.log('✅ Server ready for image data');
    // Переходим к шагу 4
  }
};
```

### Шаг 4: Отправка изображения

```javascript
// Отправляем изображение как binary data
const imageBlob = await fetch('path/to/image.jpg').then(r => r.blob());
const imageBuffer = await imageBlob.arrayBuffer();

ws.send(imageBuffer);
```

### Шаг 5: Получение streaming событий

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'progress':
      handleProgressEvent(message.event_type, message.data);
      break;
      
    case 'completed':
      handleCompletion(message.summary);
      break;
      
    default:
      if (message.status === 'error') {
        handleError(message.message);
      } else if (message.status === 'processing') {
        console.log('🔄', message.message);
      }
  }
};
```

---

## 📊 Типы событий (Progress Events)

### 1. `detection_started`
Началась детекция текстовых областей

```javascript
{
  "type": "progress",
  "event_type": "detection_started",
  "data": {}
}
```

### 2. `regions_detected`
Все текстовые области обнаружены

```javascript
{
  "type": "progress",
  "event_type": "regions_detected",
  "data": {
    "total_regions": 14,
    "regions": [
      {
        "region_index": 0,
        "coordinates": [[100, 100], [200, 100], [200, 150], [100, 150]]
      },
      // ... остальные регионы
    ]
  }
}
```

### 3. `region_ocr_started`
Началось OCR для конкретной области

```javascript
{
  "type": "progress",
  "event_type": "region_ocr_started",
  "data": {
    "region_index": 0
  }
}
```

### 4. `region_ocr_completed`
OCR для области завершено

```javascript
{
  "type": "progress",
  "event_type": "region_ocr_completed",
  "data": {
    "region_index": 0,
    "original_text": "你好世界",
    "confidence": 0.95,
    "coordinates": [[100, 100], [200, 100], [200, 150], [100, 150]]
  }
}
```

### 5. `region_ocr_failed`
OCR для области не удалось

```javascript
{
  "type": "progress",
  "event_type": "region_ocr_failed",
  "data": {
    "region_index": 0,
    "error_message": "Region too small for OCR",
    "stage": "ocr"
  }
}
```

### 6. `region_translation_started`
Начался перевод для конкретной области

```javascript
{
  "type": "progress",
  "event_type": "region_translation_started",
  "data": {
    "region_index": 0
  }
}
```

### 7. `region_translated`
Перевод для области завершен

```javascript
{
  "type": "progress",
  "event_type": "region_translated",
  "data": {
    "region_index": 0,
    "original_text": "你好世界",
    "translated_text": "Привет мир",
    "confidence": 0.95,
    "coordinates": [[100, 100], [200, 100], [200, 150], [100, 150]],
    "from_language": "zh",
    "to_language": "ru",
    "intermediate_language": "en",  // Может быть null
    "intermediate_text": "Hello World"  // Может быть null
  }
}
```

### 8. `region_translation_failed`
Перевод для области не удался

```javascript
{
  "type": "progress",
  "event_type": "region_translation_failed",
  "data": {
    "region_index": 0,
    "error_message": "Translation service unavailable",
    "stage": "translation"
  }
}
```

### 9. `processing_completed`
Вся обработка завершена

```javascript
{
  "type": "progress",
  "event_type": "processing_completed",
  "data": {
    "total_regions": 14,
    "successfully_processed": 13,
    "failed_regions": 1,
    "total_processing_time": 12.43
  }
}
```

---

## ✅ Финальное сообщение

После всех progress событий приходит финальное сообщение:

```javascript
{
  "type": "completed",
  "message": "Streaming processing completed successfully",
  "summary": {
    "total_regions": 14,
    "translated_regions": 13,
    "total_processing_time": 12.43
  }
}
```

---

## ❌ Обработка ошибок

### Ошибка во время обработки

```javascript
{
  "status": "error",
  "message": "Processing failed: No text regions found on image"
}
```

### Типичные ошибки

| Код | Причина | Решение |
|-----|---------|---------|
| `No text regions found` | На изображении нет текста | Проверьте качество изображения |
| `Invalid image format` | Неподдерживаемый формат | Используйте JPG, PNG |
| `Image too large` | Изображение слишком большое | Уменьшите размер до 10MB |
| `Translation service unavailable` | Сервис перевода недоступен | Проверьте статус сервиса |
| `Unsupported language pair` | Неподдерживаемая языковая пара | Используйте zh→ru, en→ru |

---

## 🎨 Полный пример React

```typescript
import React, { useState, useCallback, useRef } from 'react';

interface TranslationResult {
  regionIndex: number;
  originalText: string;
  translatedText: string;
  confidence: number;
  coordinates: number[][];
}

interface ProgressState {
  stage: 'idle' | 'connecting' | 'detecting' | 'ocr' | 'translating' | 'completed' | 'error';
  totalRegions: number;
  detectedRegions: number;
  ocrCompleted: number;
  translationsCompleted: number;
  results: TranslationResult[];
  error?: string;
}

export const StreamingOCRTranslator: React.FC = () => {
  const [progress, setProgress] = useState<ProgressState>({
    stage: 'idle',
    totalRegions: 0,
    detectedRegions: 0,
    ocrCompleted: 0,
    translationsCompleted: 0,
    results: []
  });

  const wsRef = useRef<WebSocket | null>(null);

  const processImage = useCallback(async (imageFile: File) => {
    setProgress({
      stage: 'connecting',
      totalRegions: 0,
      detectedRegions: 0,
      ocrCompleted: 0,
      translationsCompleted: 0,
      results: []
    });

    const ws = new WebSocket('ws://localhost:8000/ws/docs-translate/process-streaming');
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ Connected');
      
      // Отправляем метаданные
      const metadata = {
        action: "process_image_streaming",
        filename: imageFile.name,
        size: imageFile.size,
        from_language: "zh",
        to_language: "ru",
        min_confidence_threshold: 0.1,
        translate_empty_results: false,
        streaming_config: {
          send_region_preview: true
        }
        // Примечание: количество воркеров зафиксировано (OCR=1, Translation=2)
      };
      
      ws.send(JSON.stringify(metadata));
    };

    ws.onmessage = async (event) => {
      const message = JSON.parse(event.data);

      if (message.status === 'ready') {
        // Отправляем изображение
        const imageBuffer = await imageFile.arrayBuffer();
        ws.send(imageBuffer);
      } 
      else if (message.status === 'processing') {
        console.log('🔄', message.message);
      }
      else if (message.type === 'progress') {
        handleProgressEvent(message.event_type, message.data);
      }
      else if (message.type === 'completed') {
        setProgress(prev => ({
          ...prev,
          stage: 'completed'
        }));
        ws.close();
      }
      else if (message.status === 'error') {
        setProgress(prev => ({
          ...prev,
          stage: 'error',
          error: message.message
        }));
        ws.close();
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setProgress(prev => ({
        ...prev,
        stage: 'error',
        error: 'WebSocket connection failed'
      }));
    };

    ws.onclose = () => {
      console.log('🔌 Connection closed');
    };
  }, []);

  const handleProgressEvent = useCallback((eventType: string, data: any) => {
    switch (eventType) {
      case 'detection_started':
        setProgress(prev => ({ ...prev, stage: 'detecting' }));
        break;

      case 'regions_detected':
        setProgress(prev => ({
          ...prev,
          stage: 'ocr',
          totalRegions: data.total_regions,
          detectedRegions: data.total_regions
        }));
        break;

      case 'region_ocr_completed':
        setProgress(prev => ({
          ...prev,
          ocrCompleted: prev.ocrCompleted + 1
        }));
        break;

      case 'region_translated':
        setProgress(prev => ({
          ...prev,
          stage: 'translating',
          translationsCompleted: prev.translationsCompleted + 1,
          results: [
            ...prev.results,
            {
              regionIndex: data.region_index,
              originalText: data.original_text,
              translatedText: data.translated_text,
              confidence: data.confidence,
              coordinates: data.coordinates
            }
          ]
        }));
        break;

      case 'processing_completed':
        console.log('✅ Processing completed!', data);
        break;
    }
  }, []);

  const cancel = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setProgress({
      stage: 'idle',
      totalRegions: 0,
      detectedRegions: 0,
      ocrCompleted: 0,
      translationsCompleted: 0,
      results: []
    });
  }, []);

  return (
    <div className="streaming-ocr-translator">
      <h2>Streaming OCR Translator</h2>
      
      <input
        type="file"
        accept="image/*"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) processImage(file);
        }}
      />

      {progress.stage !== 'idle' && (
        <div className="progress-info">
          <div>Stage: {progress.stage}</div>
          <div>Total regions: {progress.totalRegions}</div>
          <div>OCR completed: {progress.ocrCompleted}/{progress.totalRegions}</div>
          <div>Translations: {progress.translationsCompleted}/{progress.totalRegions}</div>
          
          {progress.stage !== 'completed' && (
            <button onClick={cancel}>Cancel</button>
          )}
        </div>
      )}

      {progress.error && (
        <div className="error">Error: {progress.error}</div>
      )}

      <div className="results">
        {progress.results.map((result) => (
          <div key={result.regionIndex} className="result-item">
            <div>Region #{result.regionIndex}</div>
            <div>Original: {result.originalText}</div>
            <div>Translated: {result.translatedText}</div>
            <div>Confidence: {(result.confidence * 100).toFixed(1)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 🔧 Настройка производительности

### Количество воркеров

**⚠️ Количество воркеров зафиксировано:**
- **OCR воркеры: 1** (из-за thread-safety PaddleOCR)
- **Translation воркеры: 2** (оптимально для параллелизма)

**Почему фиксированные значения:**
- PaddleOCR не является thread-safe
- Используется `threading.Lock` для защиты от race conditions
- Несколько OCR воркеров выстраиваются в очередь (нет реального параллелизма)
- Translation воркеры работают параллельно с OCR ✅
- Больше 2-3 translation воркеров не даёт преимущества (GIL в Python)

**Конфигурация:**
```javascript
streaming_config: {
  send_region_preview: true  // Отправлять ли координаты регионов
}
// Воркеры: OCR=1, Translation=2 (зафиксировано на сервере)
```

### Threshold уверенности

```javascript
min_confidence_threshold: 0.1  // 0.0 - 1.0
```

- `0.0` - Переводить всё, даже с низкой уверенностью
- `0.5` - Средняя уверенность (рекомендуется)
- `0.8` - Высокая уверенность (может пропустить текст)

---

## 🌍 Поддерживаемые языки

| Код | Язык |
|-----|------|
| `zh` | Китайский (中文) |
| `en` | Английский (English) |
| `ru` | Русский (Русский) |

### Поддерживаемые направления перевода

- ✅ `zh` → `ru` (через английский)
- ✅ `en` → `ru` (прямой)
- ✅ `zh` → `en` (прямой)

---

## 💡 Best Practices

### 1. Обработка отключений

```javascript
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 3;

ws.onclose = (event) => {
  if (event.code !== 1000 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
    console.log(`🔄 Reconnecting... (${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`);
    reconnectAttempts++;
    setTimeout(() => processImage(imageFile), 2000);
  }
};
```

### 2. Timeout на ожидание

```javascript
const TIMEOUT_MS = 60000; // 60 секунд

const timeoutId = setTimeout(() => {
  console.log('⏱️ Processing timeout');
  ws.close();
  handleError('Processing timeout');
}, TIMEOUT_MS);

ws.onmessage = (event) => {
  clearTimeout(timeoutId); // Сбрасываем при каждом сообщении
  // ... обработка сообщения
};
```

### 3. Валидация изображения перед отправкой

```javascript
const validateImage = (file: File): string | null => {
  // Проверка типа
  if (!['image/jpeg', 'image/png', 'image/jpg'].includes(file.type)) {
    return 'Unsupported image format. Use JPG or PNG.';
  }
  
  // Проверка размера (10MB)
  if (file.size > 10 * 1024 * 1024) {
    return 'Image too large. Maximum size is 10MB.';
  }
  
  return null; // OK
};
```

### 4. Кэширование результатов

```javascript
const resultsCache = new Map<string, TranslationResult[]>();

const getCacheKey = (file: File, fromLang: string, toLang: string) => {
  return `${file.name}_${file.size}_${fromLang}_${toLang}`;
};

// Перед обработкой проверяем кэш
const cacheKey = getCacheKey(imageFile, 'zh', 'ru');
const cached = resultsCache.get(cacheKey);
if (cached) {
  console.log('✅ Using cached results');
  return cached;
}

// После завершения сохраняем в кэш
resultsCache.set(cacheKey, results);
```

---

## 🐛 Troubleshooting

### Проблема: Долгое ожидание первого результата

**Причина:** Детекция текстовых областей занимает 20-25 секунд  
**Решение:** Показывайте индикатор прогресса после события `detection_started`

### Проблема: События приходят батчами

**Причина:** Сетевая буферизация  
**Решение:** Уже исправлено на сервере, события отправляются немедленно

### Проблема: WebSocket закрывается через ~20 секунд

**Причина:** Timeout на ping/pong  
**Решение:** Отключено на клиенте, проблема решена

---

## 📈 Производительность

### Типичные показатели

| Метрика | Значение |
|---------|----------|
| Детекция областей | 3-5 секунд |
| Первый OCR результат | 3.5 секунд |
| OCR одной области | 0.2-0.5 секунд |
| Перевод одного текста | 0.1-0.3 секунд |
| **Общее время (14 регионов)** | **12-15 секунд** |
| Throughput | 1.0-1.2 regions/sec |

### Сравнение с Batch режимом

| Режим | Время обработки | Время до первого результата | UX |
|-------|----------------|----------------------------|-----|
| **Batch** | 45+ секунд | 45+ секунд | ❌ Плохо |
| **Streaming** | 12-15 секунд | 3.5 секунд | ✅ Отлично |

---

## 📚 Дополнительные ресурсы

- [WebSocket API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Полный пример кода](./STREAMING_API.md)
- [Тестовый скрипт](./test_streaming_websocket.py)

---

## 🎯 Краткий чек-лист

- [ ] Установить WebSocket соединение
- [ ] Отправить метаданные с `action` и `streaming_config`
- [ ] Дождаться `status: ready`
- [ ] Отправить изображение как binary data
- [ ] Обработать все `progress` события
- [ ] Показать результаты пользователю по мере готовности
- [ ] Обработать `completed` или `error` события
- [ ] Закрыть соединение

---

**Готово! 🚀 Приятного использования Streaming API!**

