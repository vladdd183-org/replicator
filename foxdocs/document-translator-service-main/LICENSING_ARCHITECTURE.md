# Архитектура лицензирования

## Проблема

Изначально проверка лицензии была реализована через:
1. **Middleware** для HTTP запросов — работает корректно, проверяет каждый запрос ✅
2. **Декораторы** `@require_license` для WebSocket — проверяют лицензию **только при подключении**, а не при каждом сообщении ❌
3. **Ручные вызовы** `self._check_license()` в методах Actions — дублирование кода, нет унификации ❌

## Решение: Проверка лицензии в базовом классе Action

### Принцип

**Один Action = Один Use Case** (Porto Architecture)

Все запросы (HTTP и WebSocket) в итоге вызывают `Action.execute()` — это и есть единая точка входа для бизнес-логики.

### Архитектура

```
HTTP Request  ──→  Controller  ──→  Action.execute()  ──→  Task
                   (маршрутизация)   (лицензия + бизнес)
                                            │
                                            ├─► ✅ Успех
                                            │
                                            └─► ❌ NotAuthorizedException
                                                      │
                                                ┌─────▼──────────────┐
                                                │ Exception Handler  │ ──► HTTP 403
                                                └────────────────────┘

WebSocket     ──→  Handler     ──→  execute_with_license_check()  ──→  Task
                   (подключение)         (helper функция)
                                                │
                                                ├─► ✅ Успех
                                                │
                                                └─► ❌ NotAuthorizedException
                                                          │
                                                    ┌─────▼───────────┐
                                                    │ Helper catches  │ ──► WS error + close
                                                    └─────────────────┘
```

### Реализация

#### 1. Базовый класс Action (`src/Ship/Parents/Action.py`)

```python
class Action(ABC, Generic[InputT, OutputT]):
    # Флаг для отключения проверки лицензии (публичные endpoints)
    require_license: bool = True
    
    async def execute(self, data: InputT) -> OutputT:
        """
        Выполнить Action с автоматической проверкой лицензии.
        
        1. Проверка лицензии (если require_license = True)
        2. Вызов run() с бизнес-логикой
        3. Логирование и обработка ошибок
        """
        if self.require_license:
            await self._check_license()  # 🔐 Проверка лицензии
        
        return await self.run(data)
    
    @abstractmethod
    async def run(self, data: InputT) -> OutputT:
        """Бизнес-логика Action (переопределяется в наследниках)"""
        raise NotImplementedError
```

#### 2. Гранулярные Actions (один Use Case = один Action)

**До (неправильно):**
```python
class ProcessDocumentAction:
    async def process_full_image(...)  # Метод вызывается напрямую
    async def process_regions(...)      # Метод вызывается напрямую
    async def get_status(...)           # Метод вызывается напрямую
```

**После (правильно):**
```python
class ProcessFullImageAction(Action):
    """Use Case: обработка полного изображения"""
    async def run(self, data): ...

class ProcessRegionsAction(Action):
    """Use Case: обработка областей изображения"""
    async def run(self, data): ...

class GetStatusAction(Action):
    """Use Case: получение статуса (публичный)"""
    require_license = False  # 🔓 Отключаем проверку
    async def run(self, data): ...
```

#### 3. Обработка ошибок лицензии

**HTTP: Exception Handler** (`src/Ship/Exceptions/Handlers.py`)
```python
def license_exception_handler(request: Request, exc: Exception) -> Response:
    """Автоматически ловит NotAuthorizedException и возвращает HTTP 403"""
    if isinstance(exc, NotAuthorizedException):
        return Response(
            content={
                "status": "error",
                "error": "license_invalid",
                "message": str(exc)
            },
            status_code=403
        )
    raise exc

# В App.py:
app = Litestar(
    exception_handlers={
        Exception: license_exception_handler,  # Глобальный обработчик
    }
)
```

**WebSocket: Helper функция** (`src/Ship/Licensing/helpers.py`)
```python
async def execute_with_license_check(
    action: Action,
    data: Any,
    websocket: WebSocket
) -> T:
    """
    Выполняет action.execute() с автоматической обработкой ошибок лицензии.
    Если лицензия невалидна:
    1. Отправляет error message в WebSocket
    2. Закрывает соединение с кодом 1008 (Policy Violation)
    3. Пробрасывает исключение дальше
    """
    try:
        return await action.execute(data)
    except NotAuthorizedException as e:
        await websocket.send_json({
            "status": "error",
            "error": "license_invalid",
            "message": str(e),
            "code": 1008
        })
        await websocket.close(code=1008, reason="License validation failed")
        raise
```

#### 4. Использование в контроллерах

**HTTP Controller:**
```python
@inject
async def process_image(
    self,
    request: Request,
    action: FromDishka[ProcessFullImageAction],
) -> ProcessAndTranslateImageResponse:
    # Парсинг запроса...
    
    # Вызываем execute() — проверка лицензии произойдет автоматически
    # Если ошибка — Exception Handler вернет HTTP 403 автоматически
    return await action.execute((image_data, process_request))
```

**WebSocket Handler:**
```python
@websocket("/ws/docs-translate/process")
async def process_image_websocket_handler(socket: WebSocket) -> None:
    await socket.accept()
    
    # Получаем Action через DI
    async with socket.app.state.di_container() as container:
        action = await container.get(ProcessFullImageAction)
        
        # Используем helper для автоматической обработки ошибок лицензии
        result = await execute_with_license_check(
            action,
            (image_data, request),
            socket  # Helper отправит error и закроет соединение при ошибке
        )
```

## Преимущества решения

### ✅ Унификация
- **Один способ** проверки лицензии: `Action.execute()`
- **Нет дублирования** кода проверки лицензии
- **Централизованная обработка ошибок**:
  - HTTP → Exception Handler (автоматически)
  - WebSocket → `execute_with_license_check()` helper

### ✅ Правильная архитектура Porto
- Один Action = Один Use Case
- Четкое разделение ответственности
- Легко тестировать и поддерживать

### ✅ Проверка на каждый запрос
- **HTTP**: `Action.execute()` → Exception Handler → HTTP 403
- **WebSocket**: `execute_with_license_check()` → WS error + close
- Лицензия проверяется при **выполнении бизнес-логики**, а не только при подключении

### ✅ Автоматическая обработка ошибок
- **HTTP**: Exception Handler ловит и возвращает HTTP 403 автоматически
- **WebSocket**: Helper отправляет error message и закрывает соединение
- **Нет try-catch** в каждом контроллере

### ✅ Гибкость
- Публичные endpoints: `require_license = False`
- Легко добавить кастомную логику проверки
- Можно отключить проверку для конкретного вызова: `execute(data, skip_license_check=True)`

## Структура проекта

```
src/Containers/AppSection/
├── DocsTranslate/
│   ├── Actions/
│   │   ├── ProcessFullImageAction.py    # Use Case: обработка изображения
│   │   ├── ProcessRegionsAction.py      # Use Case: обработка областей
│   │   ├── GetStatusAction.py           # Use Case: статус (публичный)
│   │   └── ProcessDocumentAction.py     # @deprecated (старый, толстый Action)
│   ├── Tasks/                            # Атомарные операции
│   ├── Providers.py                      # DI конфигурация
│   └── UI/API/Controllers/
│       ├── DocsTranslateController.py           # HTTP endpoints
│       └── DocsTranslateWebSocketController.py  # WebSocket handlers
│
├── Translation/
│   └── Actions/
│       └── TranslateAction.py            # TODO: разбить на гранулярные Actions
│
├── OCR/
│   └── Actions/
│       ├── ProcessImageAction.py         # ✅ Уже гранулярный
│       └── ProcessPolygonsAction.py      # ✅ Уже гранулярный
│
src/Ship/
├── Parents/Action.py                     # Базовый класс с проверкой лицензии
└── Licensing/
    ├── Middleware.py                     # HTTP middleware + check_license()
    └── decorators.py                     # @deprecated WebSocket decorators
```

## Миграция

### Для DocsTranslate ✅ Завершено
- [x] Созданы гранулярные Actions
- [x] Обновлены контроллеры на `action.execute()`
- [x] Обновлены WebSocket handlers
- [x] Настроены DI провайдеры
- [x] Убраны ручные проверки лицензии
- [x] Старый ProcessDocumentAction помечен как @deprecated

### Для Translation 🔄 TODO
- [ ] Создать `TranslateTextAction`
- [ ] Создать `BatchTranslateAction`
- [ ] Создать `GetTranslationStatusAction`
- [ ] Обновить контроллеры
- [ ] Обновить WebSocket handlers

### Для OCR ✅ Уже готово
- [x] `ProcessImageAction` — уже гранулярный
- [x] `ProcessPolygonsAction` — уже гранулярный
- [ ] Проверить, что используется `execute()` везде

## Примеры использования

### Публичный endpoint (без лицензии)
```python
class GetStatusAction(Action[None, StatusResponse]):
    require_license = False  # Отключаем проверку лицензии
    
    async def run(self, data: None) -> StatusResponse:
        return await self.status_task.run()
```

### Защищенный endpoint
```python
class ProcessImageAction(Action[ImageData, ProcessedImage]):
    # require_license = True по умолчанию
    
    async def run(self, data: ImageData) -> ProcessedImage:
        # Лицензия уже проверена в execute()
        return await self.process_task.run(data)
```

### Временное отключение проверки
```python
# Если по какой-то причине нужно пропустить проверку
result = await action.execute(data, skip_license_check=True)
```

## Обработка ошибок лицензии

### HTTP запросы
Все **автоматически**! Не нужно оборачивать в try-catch:

```python
# Контроллер - просто вызываем action.execute()
@post("/process-image")
@inject
async def process_image(
    self,
    request: Request,
    action: FromDishka[ProcessFullImageAction],
) -> ProcessAndTranslateImageResponse:
    # Если лицензия невалидна - Exception Handler вернет HTTP 403 автоматически
    return await action.execute((image_data, process_request))
```

**Что происходит при ошибке:**
1. `action.execute()` бросает `NotAuthorizedException`
2. `license_exception_handler` ловит исключение
3. Возвращается HTTP 403 с JSON:
   ```json
   {
     "status": "error",
     "error": "license_invalid",
     "message": "❌ Лицензия не найдена...",
     "status_code": 403
   }
   ```

### WebSocket сообщения
Используйте `execute_with_license_check()` вместо `action.execute()`:

```python
# Вместо:
result = await action.execute((data, request))

# Используйте:
result = await execute_with_license_check(
    action,
    (data, request),
    socket
)
```

**Что происходит при ошибке:**
1. `action.execute()` бросает `NotAuthorizedException`
2. Helper ловит исключение
3. Отправляет WS сообщение:
   ```json
   {
     "status": "error",
     "error": "license_invalid",
     "message": "❌ Лицензия не найдена...",
     "code": 1008
   }
   ```
4. Закрывает соединение с кодом 1008 (Policy Violation)
5. Прерывает обработку (исключение пробрасывается дальше)

## Заключение

Теперь **проверка лицензии унифицирована** и происходит в **одном месте** — в базовом классе `Action.execute()`.

**Обработка ошибок централизована:**
- ✅ HTTP: Exception Handler (автоматически)
- ✅ WebSocket: `execute_with_license_check()` helper
- ✅ Нет дублирования кода
- ✅ Нет try-catch в контроллерах

**Архитектура:**
- ✅ Проверка на каждый запрос (HTTP и WebSocket)
- ✅ Соответствует Porto Architecture
- ✅ Легко поддерживать и расширять
- ✅ Единообразный код во всех контроллерах

