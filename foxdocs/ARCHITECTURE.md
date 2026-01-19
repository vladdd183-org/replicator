# 🏗️ Hyper-Porto Stack: Ультимативная Python Архитектура

> **Версия:** 3.0 | **Дата:** Январь 2026  
> **Назначение:** Микросервисы, модульные монолиты, ML-проекты  
> **Оптимизировано для:** AI-Driven Development (Cursor, Claude, GPT)

---

## 📋 Содержание

- [Философия](#-философия)
- [Сравнение архитектур](#-сравнение-архитектур)
- [Основа: Porto Architecture](#-основа-porto-architecture)
- [Усиление: Cosmic Python](#-усиление-cosmic-python)
- [Изоляция: Modular Slice](#-изоляция-modular-slice)
- [Структура проекта](#-структура-проекта)
- [Компоненты системы](#-компоненты-системы)
- [Паттерны надёжности](#-паттерны-надёжности)
- [Продвинутые паттерны](#-продвинутые-паттерны)
- [AI-Driven Development паттерны](#-ai-driven-development-паттерны)
- [Observability & Resilience](#-observability--resilience)
- [AI-Friendly правила](#-ai-friendly-правила)
- [Примеры кода](#-примеры-кода)
- [Рекомендуемый стек](#-рекомендуемый-стек)
- [Исследование: Современные паттерны 2026](#-исследование-современные-паттерны-2026)

---

## 🎯 Философия

**Hyper-Porto Stack** — это синтез трёх мощных архитектурных подходов, усиленных современными паттернами 2026 года:

| Концепция | Что даёт |
|-----------|----------|
| **Porto** | Жёсткий порядок в структуре папок и файлов |
| **Cosmic Python** | Чистота кода через паттерны (Repository, UoW, DI) |
| **Modular Slice** | Полная автономность бизнес-модулей |
| **AI-First Patterns** | Типизация и структуры для работы с нейросетями |

### Ключевые принципы

1. **Детерминизм** — каждый файл имеет своё чёткое место
2. **Локальность контекста** — весь код фичи в одной папке
3. **Изоляция модулей** — модули не знают о внутренностях друг друга
4. **AI-First** — структура оптимизирована для работы с нейросетями
5. **Надёжность** — паттерны гарантируют консистентность данных
6. **Наблюдаемость** — встроенная телеметрия и трассировка

---

## 📊 Сравнение архитектур

### Обзор подходов

| Архитектура | Основной упор | Сложность | Удобство для AI |
|-------------|---------------|-----------|-----------------|
| **Clean Architecture** | Слои (горизонтальное деление) | Высокая | Среднее |
| **Porto** | Структура папок (иерархия) | Высокая | Хорошее |
| **Cosmic Python** | Чистота логики (абстракции) | Высокая | Среднее |
| **Vertical Slice** | Автономия фич (границы) | Низкая/Средняя | Идеальное |
| **Hyper-Porto** | Всё вместе | Высокая | Идеальное |

### Когда что использовать

```
Clean Architecture  → Крупные enterprise-проекты с частой сменой БД/UI
Porto              → Системы с огромным количеством переиспользуемых задач
Vertical Slices    → Быстрая разработка, частые изменения фич
Functional Core    → Сложные расчёты, финтех, алгоритмы
Hyper-Porto        → Когда нужно ВСЁ и сразу 🚀
```

---

## 🚢 Основа: Porto Architecture

Porto пришла из мира PHP (Laravel/Apiato), но идеально адаптируется под Python.

### Ключевые концепции

```
┌─────────────────────────────────────────────────────────┐
│                         SHIP                            │
│  (Общий код: базовые классы, утилиты, инфраструктура)  │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  CONTAINER A  │   │  CONTAINER B  │   │  CONTAINER C  │
│   (Vision)    │   │   (Billing)   │   │    (Users)    │
│               │   │               │   │               │
│ ├── Actions   │   │ ├── Actions   │   │ ├── Actions   │
│ ├── Tasks     │   │ ├── Tasks     │   │ ├── Tasks     │
│ ├── Models    │   │ ├── Models    │   │ ├── Models    │
│ ├── Data      │   │ ├── Data      │   │ ├── Data      │
│ └── UI        │   │ └── UI        │   │ └── UI        │
└───────────────┘   └───────────────┘   └───────────────┘
```

### Терминология Porto

| Термин | Описание | Пример |
|--------|----------|--------|
| **Ship** | Глобальный код, общие компоненты | Базовые классы, конфиги |
| **Container** | Изолированный бизнес-модуль | VisionModule, BillingModule |
| **Action** | Высокоуровневый сценарий | RegisterUserAction |
| **Task** | Атомарная переиспользуемая операция | HashPasswordTask |
| **Model** | Доменная сущность | User, Invoice |

---

## 🐍 Усиление: Cosmic Python

**Cosmic Python** (книга "Architecture Patterns with Python") добавляет инженерную мощь.

### Ключевые паттерны

#### Repository Pattern
```python
# Абстракция доступа к данным
class AbstractRepository(ABC):
    @abstractmethod
    async def add(self, entity: Entity) -> None: ...
    
    @abstractmethod
    async def get(self, id: UUID) -> Entity | None: ...
```

#### Unit of Work
```python
# Атомарность операций
class UnitOfWork:
    async def __aenter__(self):
        self.session = await create_session()
        return self
    
    async def commit(self):
        await self.session.commit()
    
    async def rollback(self):
        await self.session.rollback()
```

#### Dependency Injection
```python
# Инверсия зависимостей
class DetectObjectsAction:
    def __init__(
        self, 
        uow: UnitOfWork,           # Инъекция
        inference: InferenceTask   # Инъекция
    ):
        self.uow = uow
        self.inference = inference
```

### Преимущества

- ✅ Лёгкая замена БД или ML-движка
- ✅ Простое тестирование через моки
- ✅ Чистое разделение бизнес-логики и инфраструктуры

---

## 🍕 Изоляция: Modular Slice

**Modular Slice** — это не папка, это **принцип изоляции**.

### Вертикальное vs Горизонтальное деление

```
❌ Горизонтальное (Clean Architecture):
├── controllers/
│   ├── user_controller.py
│   ├── billing_controller.py
│   └── vision_controller.py
├── services/
│   ├── user_service.py
│   ├── billing_service.py
│   └── vision_service.py
└── repositories/
    ├── user_repo.py
    ├── billing_repo.py
    └── vision_repo.py

✅ Вертикальное (Modular Slice):
├── user/
│   ├── controller.py
│   ├── service.py
│   └── repository.py
├── billing/
│   ├── controller.py
│   ├── service.py
│   └── repository.py
└── vision/
    ├── controller.py
    ├── service.py
    └── repository.py
```

### Правила изоляции

1. **Контейнеры не импортируют друг друга напрямую**
2. **Общение только через Events или интерфейсы в Ship**
3. **Каждый контейнер владеет своими данными**

---

## 📁 Структура проекта

### Полная структура Hyper-Porto

```
src/
├── Ship/                        # 🚢 "Материнский корабль" (Ядро)
│   ├── Parents/                 # Базовые абстрактные классы
│   │   ├── Action.py            # class Action(ABC) + Result Object
│   │   ├── Task.py              # class Task(ABC)
│   │   ├── Query.py             # class Query(ABC)
│   │   ├── Model.py             # class Model(BaseModel)
│   │   ├── Repository.py        # class AbstractRepository(ABC)
│   │   └── Specification.py     # class Specification(ABC)
│   │
│   ├── Core/                    # Общие типы и результаты
│   │   ├── Result.py            # Result[T, E] — Success/Failure
│   │   ├── Types.py             # Discriminated Unions
│   │   └── Protocols.py         # typing.Protocol интерфейсы
│   │
│   ├── Infrastructure/          # Глобальная инфраструктура
│   │   ├── Database/            # Настройка SQLAlchemy/MongoDB
│   │   ├── Cache/               # Redis конфигурация
│   │   ├── MessageBus/          # Kafka/RabbitMQ + Outbox/Inbox
│   │   ├── Telemetry/           # OpenTelemetry трассировка
│   │   ├── FeatureFlags/        # Feature Toggles
│   │   └── Logging/             # Структурированное логирование
│   │
│   ├── Decorators/              # Sidecar-паттерны
│   │   ├── traceable.py         # @traceable — автотрассировка
│   │   ├── cached.py            # @cached — кэширование
│   │   ├── retry.py             # @retry — повторные попытки
│   │   └── idempotent.py        # @idempotent — идемпотентность
│   │
│   ├── ServiceProviders/        # Глобальная регистрация DI
│   │   └── AppServiceProvider.py
│   │
│   └── Transporters/            # Общие DTO и ответы
│       ├── ApiResponse.py       # Стандартный формат ответа
│       └── Exceptions.py        # Базовые исключения
│
└── Containers/                  # 📦 Модульные слайсы
    │
    ├── VisionModule/            # Пример: ML-модуль
    │   ├── UI/                  # 🖥️ Слой адаптеров
    │   │   ├── API/
    │   │   │   ├── Routes.py    # FastAPI router
    │   │   │   └── Controllers.py
    │   │   └── CLI/
    │   │       └── Commands.py  # Typer commands
    │   │
    │   ├── Actions/             # 🎬 Оркестраторы (Porto)
    │   │   ├── DetectObjectsAction.py
    │   │   └── ProcessImageAction.py
    │   │
    │   ├── Tasks/               # ⚙️ Атомарная логика (Porto)
    │   │   ├── PreprocessImageTask.py
    │   │   ├── RunInferenceTask.py
    │   │   └── PostprocessResultsTask.py
    │   │
    │   ├── Queries/             # 📖 Чтение данных (CQRS)
    │   │   ├── GetDetectionResultQuery.py
    │   │   └── ListDetectionsQuery.py
    │   │
    │   ├── Specifications/      # 🔍 Условия поиска
    │   │   ├── ActiveDetectionsSpec.py
    │   │   └── ByUserIdSpec.py
    │   │
    │   ├── Data/                # 💾 Слой данных (Cosmic Python)
    │   │   ├── Repositories/
    │   │   │   ├── DetectionRepository.py
    │   │   │   └── ImageRepository.py
    │   │   ├── Outbox/          # Transactional Outbox
    │   │   ├── Inbox/           # Inbox для входящих событий
    │   │   ├── Migrations/
    │   │   └── UoW.py           # Unit of Work
    │   │
    │   ├── Models/              # 📋 Domain Models
    │   │   ├── Detection.py
    │   │   └── Image.py
    │   │
    │   ├── Engines/             # 🔧 Тяжёлые вычисления
    │   │   ├── OnnxEngine.py
    │   │   └── TensorRTEngine.py
    │   │
    │   ├── Validators/          # ✅ Chain of Responsibility
    │   │   ├── ImageFormatValidator.py
    │   │   ├── ImageSizeValidator.py
    │   │   └── ValidationPipeline.py
    │   │
    │   ├── Events/              # 📨 Domain Events
    │   │   ├── ImageProcessed.py
    │   │   └── ObjectDetected.py
    │   │
    │   ├── Providers/           # 💉 DI-контейнер модуля
    │   │   └── MainServiceProvider.py
    │   │
    │   └── Schemas/             # 📝 Pydantic DTOs
    │       ├── Requests.py
    │       └── Responses.py
    │
    ├── UserModule/              # Пример: CRUD-модуль
    │   └── ... (аналогичная структура)
    │
    └── BillingModule/           # Пример: Бизнес-модуль
        └── ... (аналогичная структура)
```

---

## 🧩 Компоненты системы

### Таблица компонентов (Расширенная)

| Компонент | Источник | Роль | Паттерн |
|-----------|----------|------|---------|
| **Action** | Porto | Оркестратор сценария | Command + Result Object |
| **Task** | Porto | Атомарная операция | Strategy / Chain of Responsibility |
| **Query** | CQRS | Чтение данных | Query Object |
| **Repository** | Cosmic | Абстракция данных | Repository + Specification |
| **UoW** | Cosmic | Транзакции | Unit of Work + Outbox |
| **Engine** | Custom | Тяжёлые вычисления | Adapter / Facade |
| **Event** | DDD | Уведомления | Domain Event |
| **Validator** | Custom | Валидация данных | Chain of Responsibility |
| **Specification** | DDD | Условия поиска | Specification |
| **Provider** | Porto/DI | Сборка модуля | Service Locator |

### Поток данных

```
Request → Controller → Action → [Tasks, Repositories, Engines]
              ↓                         ↓
         Validation              Result<T, Error>
         Pipeline                      ↓
                                   Events → Outbox → Other Modules
                                       ↓
                                  Response ← Query (для чтения)
```

---

## 🔒 Паттерны надёжности

### 1. Transactional Outbox + Inbox Pattern

**Проблема:** Данные сохранились, но событие не отправилось (сеть моргнула).

**Решение:** 
- **Outbox:** Сохраняем событие в ту же транзакцию БД
- **Inbox:** Принимающая сторона сначала записывает событие, потом обрабатывает

```python
# Data/UoW.py
class UnitOfWork:
    def __init__(self):
        self.outbox: list[DomainEvent] = []
    
    def add_event(self, event: DomainEvent):
        self.outbox.append(event)
    
    async def commit(self):
        # Сохраняем бизнес-данные + события в одной транзакции
        for event in self.outbox:
            await self.session.execute(
                insert(outbox_table).values(
                    event_type=type(event).__name__,
                    payload=event.model_dump_json(),
                    status="pending"
                )
            )
        await self.session.commit()
        # Relay-процесс подхватит и отправит
```

```
┌─────────────────────────────────────────────────────────┐
│                    ОТПРАВИТЕЛЬ                          │
│  ┌─────────────┐  ┌─────────────────┐                   │
│  │   Orders    │  │   outbox_events │ ← Одна транзакция │
│  └─────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────┘
                        ↓ Relay Process
              ┌─────────────────┐
              │  Message Broker │ (Kafka/RabbitMQ)
              └─────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                    ПОЛУЧАТЕЛЬ                           │
│  ┌─────────────────┐  ┌─────────────┐                   │
│  │   inbox_events  │→ │   Handler   │ ← Идемпотентность │
│  └─────────────────┘  └─────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

**Крутость:** Гарантированная доставка (Exactly-once delivery) без распределённых транзакций.

### 2. CQRS (Command Query Responsibility Segregation)

**Идея:** Разделяем операции записи и чтения.

```
Commands (Actions)          Queries
    ↓                          ↓
Write Model               Read Model
    ↓                          ↓
 База данных              Оптимизированные
 (нормализованная)        представления
```

### 3. Event Sourcing (Продвинутый)

**Идея:** Храним не состояние, а цепочку событий.

```python
# Вместо: status = "processed"
# Храним:
events = [
    ImageUploaded(timestamp="..."),
    PreprocessingStarted(timestamp="..."),
    InferenceCompleted(result="..."),
    ObjectDetected(class="car", confidence=0.95)
]
```

**Преимущество для ML:** Можно "отмотать" историю и прогнать данные через новую модель.

---

## 🧠 Продвинутые паттерны

### 1. Result Object Pattern

**Забудь про try-except во всей бизнес-логике.** Action возвращает типизированный результат.

```python
# Ship/Core/Result.py
from typing import TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Success(Generic[T]):
    value: T
    
    def is_success(self) -> bool:
        return True
    
    def is_failure(self) -> bool:
        return False

@dataclass(frozen=True)  
class Failure(Generic[E]):
    error: E
    
    def is_success(self) -> bool:
        return False
    
    def is_failure(self) -> bool:
        return True

Result = Success[T] | Failure[E]
```

**Использование в Action:**

```python
# Actions/CreateOrderAction.py
from Ship.Core.Result import Result, Success, Failure

class CreateOrderAction(Action[Result[Order, OrderError]]):
    async def run(self, data: CreateOrderDTO) -> Result[Order, OrderError]:
        # Валидация
        if data.amount <= 0:
            return Failure(OrderError.INVALID_AMOUNT)
        
        # Бизнес-логика
        order = Order(amount=data.amount)
        await self.uow.orders.add(order)
        await self.uow.commit()
        
        return Success(order)
```

**В контроллере:**

```python
# UI/API/Controllers.py
@router.post("/orders")
async def create_order(data: CreateOrderDTO, action: CreateOrderAction):
    result = await action.execute(data)
    
    match result:
        case Success(order):
            return {"id": order.id}
        case Failure(error):
            raise HTTPException(400, detail=error.value)
```

**Крутость:** Код линейный и предсказуемый. AI видит: если `Failure` — надо вернуть 400.

---

### 2. Specification Pattern

**Не пиши `find_by_id_and_status`.** Условия поиска — это отдельные объекты.

```python
# Ship/Parents/Specification.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class Specification(ABC, Generic[T]):
    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        """Проверка в памяти."""
        ...
    
    @abstractmethod
    def to_expression(self):
        """SQLAlchemy выражение для БД."""
        ...
    
    def __and__(self, other: "Specification[T]") -> "AndSpecification[T]":
        return AndSpecification(self, other)
    
    def __or__(self, other: "Specification[T]") -> "OrSpecification[T]":
        return OrSpecification(self, other)

class AndSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)
    
    def to_expression(self):
        return and_(self.left.to_expression(), self.right.to_expression())
```

**Пример спецификаций:**

```python
# Containers/UserModule/Specifications/ActiveUsersSpec.py
class ActiveUsersSpec(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.is_active
    
    def to_expression(self):
        return User.is_active == True

class ByRoleSpec(Specification[User]):
    def __init__(self, role: str):
        self.role = role
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.role == self.role
    
    def to_expression(self):
        return User.role == self.role
```

**Использование:**

```python
# Комбинируем спецификации
active_admins = ActiveUsersSpec() & ByRoleSpec("admin")

# В репозитории
users = await repo.find_by_spec(active_admins)
```

**Для AI:** Ты можешь сказать: "Создай спецификацию для активных пользователей", и AI переиспользует её везде.

---

### 3. Sidecar Pattern (Декораторы)

**Для логирования, телеметрии или кэширования.** Вместо `log.info()` в каждом экшене — декораторы.

```python
# Ship/Decorators/traceable.py
from functools import wraps
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def traceable(name: str = None):
    """Автоматическая трассировка через OpenTelemetry."""
    def decorator(func):
        span_name = name or func.__qualname__
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("args", str(args)[:100])
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.StatusCode.OK)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.StatusCode.ERROR)
                    raise
        return wrapper
    return decorator
```

```python
# Ship/Decorators/cached.py
from functools import wraps
import hashlib
import json

def cached(ttl: int = 300, key_prefix: str = ""):
    """Кэширование результата в Redis."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(json.dumps(args).encode()).hexdigest()}"
            
            # Проверяем кэш
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Выполняем функцию
            result = await func(self, *args, **kwargs)
            
            # Сохраняем в кэш
            await self.cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
```

```python
# Ship/Decorators/idempotent.py
def idempotent(key_extractor):
    """Гарантирует, что операция выполнится только один раз."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            idempotency_key = key_extractor(*args, **kwargs)
            
            # Проверяем, была ли уже обработка
            existing = await self.idempotency_store.get(idempotency_key)
            if existing:
                return existing
            
            # Выполняем
            result = await func(self, *args, **kwargs)
            
            # Сохраняем результат
            await self.idempotency_store.set(idempotency_key, result)
            return result
        return wrapper
    return decorator
```

**Использование:**

```python
# Actions/ProcessPaymentAction.py
class ProcessPaymentAction(Action):
    
    @traceable("payment.process")
    @idempotent(lambda dto: dto.idempotency_key)
    async def run(self, dto: PaymentDTO) -> Result[Payment, PaymentError]:
        # Логика — чистая, без обвязки
        ...
```

**Для AI:** Ты просто вешаешь декоратор, и AI понимает, что "под капотом" происходит магия.

---

### 4. Validation Pipeline (Chain of Responsibility)

**Каждый шаг валидации — отдельный класс.**

```python
# Ship/Parents/Validator.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class Validator(ABC, Generic[T]):
    def __init__(self):
        self._next: Validator[T] | None = None
    
    def set_next(self, validator: "Validator[T]") -> "Validator[T]":
        self._next = validator
        return validator
    
    async def validate(self, data: T) -> Result[T, ValidationError]:
        result = await self._validate(data)
        
        if result.is_failure():
            return result
        
        if self._next:
            return await self._next.validate(data)
        
        return Success(data)
    
    @abstractmethod
    async def _validate(self, data: T) -> Result[T, ValidationError]:
        ...
```

**Пример валидаторов:**

```python
# Containers/VisionModule/Validators/
class ImageFormatValidator(Validator[ImageUploadDTO]):
    ALLOWED_FORMATS = {"jpg", "jpeg", "png", "webp"}
    
    async def _validate(self, data: ImageUploadDTO) -> Result:
        if data.format.lower() not in self.ALLOWED_FORMATS:
            return Failure(ValidationError.INVALID_FORMAT)
        return Success(data)

class ImageSizeValidator(Validator[ImageUploadDTO]):
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    
    async def _validate(self, data: ImageUploadDTO) -> Result:
        if data.size > self.MAX_SIZE:
            return Failure(ValidationError.FILE_TOO_LARGE)
        return Success(data)

class UserQuotaValidator(Validator[ImageUploadDTO]):
    async def _validate(self, data: ImageUploadDTO) -> Result:
        quota = await self.quota_service.get_remaining(data.user_id)
        if quota <= 0:
            return Failure(ValidationError.QUOTA_EXCEEDED)
        return Success(data)
```

**Сборка пайплайна:**

```python
# Containers/VisionModule/Validators/ValidationPipeline.py
class ImageValidationPipeline:
    def __init__(
        self,
        format_validator: ImageFormatValidator,
        size_validator: ImageSizeValidator,
        quota_validator: UserQuotaValidator
    ):
        # Собираем цепочку
        format_validator.set_next(size_validator).set_next(quota_validator)
        self.head = format_validator
    
    async def validate(self, data: ImageUploadDTO) -> Result:
        return await self.head.validate(data)
```

---

### 5. Feature Flags / Toggles

**Переключение фич на лету без деплоя.**

```python
# Ship/Infrastructure/FeatureFlags/FeatureService.py
from enum import Enum

class Feature(str, Enum):
    NEW_ML_MODEL = "new_ml_model"
    BETA_UI = "beta_ui"
    EXPERIMENTAL_PRICING = "experimental_pricing"

class FeatureFlagService:
    def __init__(self, config_source: ConfigSource):
        self.config = config_source
    
    async def is_enabled(self, feature: Feature, user_id: str = None) -> bool:
        flag = await self.config.get(feature.value)
        
        if not flag:
            return False
        
        # Глобально включено
        if flag.enabled_for_all:
            return True
        
        # Процент пользователей
        if user_id and flag.percentage:
            return hash(user_id) % 100 < flag.percentage
        
        # Список конкретных пользователей
        if user_id and user_id in flag.allowed_users:
            return True
        
        return False
```

**Использование в Action:**

```python
class DetectObjectsAction(Action):
    async def run(self, data: DetectDTO) -> Result:
        # Выбираем модель по флагу
        if await self.features.is_enabled(Feature.NEW_ML_MODEL, data.user_id):
            engine = self.new_engine  # YOLOv9
        else:
            engine = self.legacy_engine  # YOLOv5
        
        return await self.inference_task.run(engine, data.image)
```

**Зачем:** Выкатить новую нейронку только для 5% пользователей, не трогая код.

---

## 🤖 AI-Driven Development паттерны

### Type Hinting & Pydantic V2

**Используй `Annotated` и `Strict` типы.** Это даёт AI 100% понимание данных.

```python
from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints

class CreateUserDTO(BaseModel):
    email: Annotated[str, StringConstraints(
        pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$'
    )]
    username: Annotated[str, StringConstraints(
        min_length=3, 
        max_length=50,
        pattern=r'^[a-zA-Z0-9_]+$'
    )]
    age: Annotated[int, Field(ge=18, le=120)]
```

### Discriminated Unions (Размеченные объединения)

**Когда ответ может принимать разные формы.**

```python
from typing import Literal
from pydantic import BaseModel

class SuccessResponse(BaseModel):
    status: Literal["success"] = "success"
    data: dict

class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    code: str
    message: str

class RetryResponse(BaseModel):
    status: Literal["retry"] = "retry"
    retry_after: int

# Размеченное объединение
APIResponse = SuccessResponse | ErrorResponse | RetryResponse
```

**Зачем:** AI не забудет обработать ошибку, потому что тип данных заставит его это сделать.

### Protocol-based Interfaces

**"Утиная типизация" на стероидах.**

```python
# Ship/Core/Protocols.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class MLEngine(Protocol):
    """Любой класс с этими методами — это MLEngine."""
    
    def load(self, path: str) -> None: ...
    def predict(self, data: np.ndarray) -> np.ndarray: ...
    def unload(self) -> None: ...

# Использование — не нужно наследование!
class OnnxEngine:
    def load(self, path: str) -> None:
        self.session = onnx.InferenceSession(path)
    
    def predict(self, data: np.ndarray) -> np.ndarray:
        return self.session.run(None, {"input": data})[0]
    
    def unload(self) -> None:
        del self.session

# Проверка типа
def run_inference(engine: MLEngine, data: np.ndarray):
    return engine.predict(data)

# OnnxEngine автоматически совместим с MLEngine!
```

**Зачем:** AI не нужно импортировать базовые классы из других модулей, что снижает связность кода.

---

## 📡 Observability & Resilience

### 1. OpenTelemetry (Трассировка)

**Как встроить трассировку, чтобы видеть путь запроса через все контейнеры.**

```python
# Ship/Infrastructure/Telemetry/setup.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def setup_telemetry(service_name: str):
    provider = TracerProvider()
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer(service_name)
```

**Автотрассировка Action:**

```python
# Ship/Parents/Action.py (обновлённый)
class Action(ABC, Generic[T]):
    def __init__(self):
        self.tracer = trace.get_tracer(self.__class__.__module__)
    
    async def execute(self, *args, **kwargs) -> T:
        with self.tracer.start_as_current_span(
            f"{self.__class__.__name__}.execute",
            attributes={"args": str(args)[:200]}
        ) as span:
            try:
                result = await self.run(*args, **kwargs)
                span.set_status(trace.StatusCode.OK)
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                raise
```

### 2. Idempotency Key

**Гарантирует, что повторный запрос не выполнится дважды.**

```python
# Ship/Infrastructure/Idempotency/IdempotencyService.py
class IdempotencyService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.ttl = 86400  # 24 часа
    
    async def check_and_set(self, key: str) -> tuple[bool, Any]:
        """
        Returns:
            (is_duplicate, cached_result)
        """
        cached = await self.redis.get(f"idempotency:{key}")
        if cached:
            return True, json.loads(cached)
        return False, None
    
    async def store_result(self, key: str, result: Any):
        await self.redis.setex(
            f"idempotency:{key}",
            self.ttl,
            json.dumps(result)
        )
```

**Использование:**

```python
@router.post("/payments")
async def create_payment(
    data: PaymentDTO,
    idempotency_key: str = Header(..., alias="X-Idempotency-Key"),
    idempotency: IdempotencyService = Depends()
):
    # Проверяем дубликат
    is_duplicate, cached = await idempotency.check_and_set(idempotency_key)
    if is_duplicate:
        return cached
    
    # Выполняем платёж
    result = await payment_action.execute(data)
    
    # Сохраняем результат
    await idempotency.store_result(idempotency_key, result)
    return result
```

### 3. Graceful Degradation

**Как заставить систему работать, если упал сервис нейронок.**

```python
# Ship/Decorators/fallback.py
def fallback(fallback_func):
    """Если основная функция падает — вызываем запасную."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Fallback activated: {e}")
                return await fallback_func(*args, **kwargs)
        return wrapper
    return decorator
```

**Пример использования:**

```python
class DetectObjectsAction(Action):
    
    async def _fallback_detection(self, image: Image) -> DetectionResult:
        """Упрощённая детекция без нейронки."""
        return DetectionResult(
            objects=[],
            confidence=0.0,
            message="ML service unavailable, please retry later"
        )
    
    @fallback(_fallback_detection)
    async def run(self, image: Image) -> DetectionResult:
        # Основная логика с нейронкой
        return await self.ml_engine.detect(image)
```

### 4. Circuit Breaker

**Защита от каскадных сбоев.**

```python
# Ship/Infrastructure/CircuitBreaker/CircuitBreaker.py
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"      # Всё работает
    OPEN = "open"          # Сервис недоступен, отказываем сразу
    HALF_OPEN = "half_open"  # Пробуем восстановиться

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        success_threshold: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time = 0
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpen()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.successes += 1
            if self.successes >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failures = 0
    
    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

---

## 🎯 AI-Friendly правила

### Правила для AI (.cursorrules)

Создайте файл `.cursorrules` в корне проекта:

```markdown
# Правила архитектуры Hyper-Porto

## Структура
- Все изменения данных только через Actions
- Чтение данных только через Queries
- Модули общаются через Events в Ship
- Каждый Action возвращает Result[T, Error]

## Запрещено
- Импортировать Tasks/Actions из других Containers
- Обращаться к БД напрямую (только через Repository)
- Менять данные в Queries
- Использовать try-except в бизнес-логике (используй Result)

## Обязательно
- Все входные/выходные данные через Pydantic Schemas
- Использовать Unit of Work для транзакций
- Декорировать Actions с @traceable
- Типизировать всё через Annotated и Protocol

## Именование
- Actions: {Verb}{Noun}Action (CreateUserAction)
- Tasks: {Verb}{Noun}Task (HashPasswordTask)
- Queries: {Get|List}{Noun}Query (GetUserQuery)
- Specifications: {Condition}Spec (ActiveUsersSpec)
- Validators: {What}Validator (ImageFormatValidator)

## Паттерны
- Валидация: Chain of Responsibility через ValidationPipeline
- Поиск: Specification Pattern, комбинируй через & и |
- Ошибки: Result Object, не бросай исключения
- Cross-cutting: Используй декораторы (@traceable, @cached, @idempotent)
```

### Пример промптов для AI

```
✅ Хороший промпт:
"Создай новый Action в VisionModule для обработки видео.
- Используй существующие Tasks для извлечения кадров
- Валидируй через ValidationPipeline
- Возвращай Result[VideoResult, VideoError]
- Сохрани результат через UoW
- Добавь декоратор @traceable"

❌ Плохой промпт:
"Добавь обработку видео"
```

---

## 💻 Примеры кода

### Базовый класс Action с Result (Ship/Parents/Action.py)

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from datetime import datetime
from opentelemetry import trace
import structlog

from Ship.Core.Result import Result

T = TypeVar('T')
E = TypeVar('E')

class Action(ABC, Generic[T, E]):
    """
    Базовый класс для всех Actions в Porto.
    
    Особенности:
    - Возвращает Result[T, E] вместо исключений
    - Автоматическая трассировка через OpenTelemetry
    - Структурированное логирование
    """
    
    def __init__(self):
        self.logger = structlog.get_logger(self.__class__.__name__)
        self.tracer = trace.get_tracer(self.__class__.__module__)
        self._started_at: datetime | None = None
    
    async def execute(self, *args, **kwargs) -> Result[T, E]:
        """Выполняет action с логированием и трассировкой."""
        self._started_at = datetime.now()
        
        with self.tracer.start_as_current_span(
            f"{self.__class__.__name__}.execute"
        ) as span:
            span.set_attribute("action.args", str(args)[:200])
            self.logger.info("action_started")
            
            try:
                result = await self.run(*args, **kwargs)
                duration = (datetime.now() - self._started_at).total_seconds()
                
                if result.is_success():
                    span.set_status(trace.StatusCode.OK)
                    self.logger.info("action_completed", duration=duration)
                else:
                    span.set_status(trace.StatusCode.ERROR)
                    span.set_attribute("error", str(result.error))
                    self.logger.warning("action_failed", error=str(result.error))
                
                return result
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                self.logger.error("action_exception", error=str(e))
                raise
    
    @abstractmethod
    async def run(self, *args, **kwargs) -> Result[T, E]:
        """Реализация логики action."""
        ...
```

### Базовый класс Task (Ship/Parents/Task.py)

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class Task(ABC, Generic[T]):
    """
    Базовый класс для атомарных задач.
    
    Правила:
    - Одна задача = одна операция
    - Синхронный (если не требуется I/O)
    - Переиспользуемый между Actions
    """
    
    @abstractmethod
    def run(self, *args, **kwargs) -> T:
        """Выполняет одну атомарную операцию."""
        ...
```

### Unit of Work с Outbox (Data/UoW.py)

```python
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from Ship.Core.DomainEvent import DomainEvent

class UnitOfWork:
    """
    Unit of Work с поддержкой Outbox Pattern.
    
    Гарантирует:
    - Атомарность операций
    - Надёжную доставку событий
    """
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session: AsyncSession | None = None
        self._outbox: list[DomainEvent] = []
    
    async def __aenter__(self):
        self._session = self.session_factory()
        self._outbox = []
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        await self._session.close()
    
    def add_event(self, event: DomainEvent):
        """Добавляет событие в outbox."""
        self._outbox.append(event)
    
    async def commit(self):
        """Сохраняет данные + события в одной транзакции."""
        # Сохраняем события в outbox таблицу
        for event in self._outbox:
            await self._session.execute(
                insert(outbox_table).values(
                    id=str(uuid4()),
                    event_type=type(event).__name__,
                    payload=event.model_dump_json(),
                    created_at=datetime.utcnow(),
                    status="pending"
                )
            )
        
        await self._session.commit()
        self._outbox.clear()
    
    async def rollback(self):
        await self._session.rollback()
        self._outbox.clear()
```

### Полный пример Action (Containers/VisionModule/Actions/)

```python
# DetectObjectsAction.py
from typing import Annotated
from Ship.Parents.Action import Action
from Ship.Core.Result import Result, Success, Failure
from Ship.Decorators.traceable import traceable
from Ship.Decorators.idempotent import idempotent

from ..Tasks.PreprocessImageTask import PreprocessImageTask
from ..Tasks.RunInferenceTask import RunInferenceTask
from ..Data.UoW import VisionUnitOfWork
from ..Events.ObjectDetected import ObjectDetected
from ..Validators.ValidationPipeline import ImageValidationPipeline
from ..Schemas.Requests import DetectRequest
from ..Schemas.Responses import DetectionResult
from ..Errors import DetectionError

class DetectObjectsAction(Action[DetectionResult, DetectionError]):
    """
    Определяет объекты на изображении и сохраняет результат.
    
    Шаги:
    1. Валидация входных данных
    2. Препроцессинг изображения
    3. Инференс ML-модели
    4. Сохранение результата
    5. Публикация события
    """
    
    def __init__(
        self,
        uow: VisionUnitOfWork,
        validation_pipeline: ImageValidationPipeline,
        preprocess_task: PreprocessImageTask,
        inference_task: RunInferenceTask,
    ):
        super().__init__()
        self.uow = uow
        self.validation_pipeline = validation_pipeline
        self.preprocess_task = preprocess_task
        self.inference_task = inference_task
    
    async def run(self, request: DetectRequest) -> Result[DetectionResult, DetectionError]:
        # 1. Валидация
        validation_result = await self.validation_pipeline.validate(request)
        if validation_result.is_failure():
            return Failure(DetectionError.from_validation(validation_result.error))
        
        async with self.uow:
            # 2. Препроцессинг
            image_data = self.preprocess_task.run(request.image_url)
            
            # 3. Инференс
            detections = self.inference_task.run(image_data)
            
            # 4. Сохранение
            detection_record = Detection(
                user_id=request.user_id,
                image_url=request.image_url,
                results=detections,
                model_version=self.inference_task.model_version
            )
            await self.uow.detections.add(detection_record)
            
            # 5. Публикация события (через Outbox)
            self.uow.add_event(
                ObjectDetected(
                    detection_id=detection_record.id,
                    user_id=request.user_id,
                    object_count=len(detections)
                )
            )
            
            await self.uow.commit()
            
            return Success(DetectionResult.from_entity(detection_record))
```

### DI Provider (Containers/VisionModule/Providers/)

```python
# MainServiceProvider.py
from punq import Container
from Ship.Infrastructure.Database import get_session_factory
from Ship.Infrastructure.FeatureFlags import FeatureFlagService

from ..Actions.DetectObjectsAction import DetectObjectsAction
from ..Tasks.PreprocessImageTask import PreprocessImageTask
from ..Tasks.RunInferenceTask import RunInferenceTask
from ..Queries.GetDetectionQuery import GetDetectionQuery
from ..Queries.ListDetectionsQuery import ListDetectionsQuery
from ..Data.Repositories.DetectionRepository import SQLDetectionRepository
from ..Data.UoW import VisionUnitOfWork
from ..Engines.OnnxEngine import OnnxEngine
from ..Validators.ImageFormatValidator import ImageFormatValidator
from ..Validators.ImageSizeValidator import ImageSizeValidator
from ..Validators.ValidationPipeline import ImageValidationPipeline

def register_vision_module(container: Container) -> None:
    """Регистрирует все зависимости VisionModule."""
    
    # === Engines ===
    container.register(OnnxEngine, scope="singleton")
    
    # === Tasks ===
    container.register(PreprocessImageTask)
    container.register(RunInferenceTask)
    
    # === Validators ===
    container.register(ImageFormatValidator)
    container.register(ImageSizeValidator)
    container.register(ImageValidationPipeline)
    
    # === Repositories ===
    container.register(DetectionRepository, SQLDetectionRepository)
    
    # === UoW ===
    container.register(VisionUnitOfWork)
    
    # === Queries ===
    container.register(GetDetectionQuery)
    container.register(ListDetectionsQuery)
    
    # === Actions ===
    container.register(DetectObjectsAction)
```

---

## 🛠️ Рекомендуемый стек

### Фреймворки и библиотеки

| Категория | Рекомендация | Альтернатива |
|-----------|--------------|--------------|
| **Web** | FastAPI | Litestar |
| **ORM** | SQLAlchemy 2.0 | Tortoise ORM |
| **Validation** | Pydantic v2 | — |
| **DI** | punq | dependency-injector |
| **Async** | anyio | asyncio |
| **CLI** | Typer | Click |
| **Logging** | structlog | loguru |
| **Tracing** | OpenTelemetry | — |
| **Testing** | pytest + pytest-asyncio | — |
| **ML** | ONNX Runtime | TensorRT |
| **Queue** | Celery / ARQ | Dramatiq |
| **Events** | Kafka | RabbitMQ |
| **Cache** | Redis | — |
| **Feature Flags** | Unleash | LaunchDarkly |

### Инструменты разработки

| Категория | Рекомендация |
|-----------|--------------|
| **Type Checking** | mypy / pyright |
| **Linting** | ruff |
| **Formatting** | ruff format |
| **Pre-commit** | pre-commit |
| **AI Coding** | Cursor, Claude |
| **API Docs** | Swagger UI (встроен в FastAPI) |

---

## 📊 Итоговый стек паттернов

| Слой Porto | Паттерн | Что это даёт |
|------------|---------|--------------|
| **Actions** | Command + Result Object | Предсказуемый вход и выход для AI |
| **Tasks** | Strategy / Chain of Responsibility | Лёгкая замена алгоритмов (моделей) |
| **Queries** | Query Object + Specification | Гибкий поиск с комбинируемыми условиями |
| **Data** | Unit of Work + Outbox/Inbox | Надёжность данных и событий |
| **Infrastructure** | Adapter / Facade | Изоляция от внешних библиотек |
| **Validators** | Chain of Responsibility | Расширяемая валидация |
| **Cross-cutting** | Decorator (Sidecar) | Логирование, кэш, трассировка без бойлерплейта |

---

## 📚 Источники и материалы

### Книги
- **"Architecture Patterns with Python"** (Harry Percival, Bob Gregory) — Cosmic Python
- **"Domain-Driven Design"** (Eric Evans) — Основы DDD
- **"Release It!"** (Michael Nygard) — Паттерны надёжности

### Документация
- [Porto SAP](https://github.com/Mahmoudz/Porto) — Оригинальная спецификация
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)

### Видео
- Vertical Slice Architecture Explained — Milan Jovanović
- Modular Monoliths in Python
- Transactional Outbox за 10 минут

---

## 🚀 Быстрый старт

### 1. Создание нового Container

```bash
# Структура нового модуля
mkdir -p src/Containers/NewModule/{UI/API,Actions,Tasks,Queries,Specifications,Data/Repositories,Data/Outbox,Models,Events,Validators,Engines,Providers,Schemas}
touch src/Containers/NewModule/__init__.py
touch src/Containers/NewModule/Providers/MainServiceProvider.py
```

### 2. Чеклист нового Action

- [ ] Создать файл в `Actions/`
- [ ] Наследоваться от `Ship.Parents.Action`
- [ ] Определить `Result[SuccessType, ErrorType]`
- [ ] Определить зависимости в конструкторе
- [ ] Реализовать метод `run()` → `Result`
- [ ] Добавить валидацию через `ValidationPipeline`
- [ ] Зарегистрировать в `Providers/MainServiceProvider.py`
- [ ] Создать эндпоинт в `UI/API/Controllers.py`
- [ ] Добавить декоратор `@traceable` если нужна трассировка

### 3. Чеклист нового Task

- [ ] Создать файл в `Tasks/`
- [ ] Наследоваться от `Ship.Parents.Task`
- [ ] Реализовать метод `run()` (синхронный, атомарный)
- [ ] Зарегистрировать в Provider

### 4. Чеклист новой Specification

- [ ] Создать файл в `Specifications/`
- [ ] Наследоваться от `Ship.Parents.Specification`
- [ ] Реализовать `is_satisfied_by()` и `to_expression()`
- [ ] Использовать в Repository через `find_by_spec()`

---

---

## 🔬 Исследование: Современные паттерны 2026

> Результаты исследования arXiv и современных источников по архитектурным паттернам Python.

### 📚 Научные статьи (arXiv)

#### 1. Domain-Driven Design + Microservices для Big Data
**Источник:** arXiv:2511.05880v1 (Ноябрь 2025)

Исследование показывает, что DDD в сочетании с микросервисами значительно улучшает:
- Масштабируемость систем обработки данных
- Качество данных через изоляцию доменов
- Эффективность сбора данных через динамическое планирование

```
DDD + Microservices = Независимая разработка, деплой и масштабирование каждого модуля
```

#### 2. Hexagonal Architecture для ML-систем
**Источник:** arXiv:2512.08657v1 (Декабрь 2025)

**Ports and Adapters** паттерн активно применяется для ML-Enabled Systems (MLES):
- Позволяет строить множество микросервисов из единой кодовой базы
- Обеспечивает переиспользуемость ML-компонентов
- Интегрируется с MLOps практиками

#### 3. LLMs в Software Architecture
**Источник:** arXiv:2505.16697v1 (Май 2025)

Systematic Literature Review показал:
- LLM применяются для классификации архитектурных решений
- Детекция паттернов проектирования
- Генерация архитектуры из требований
- **Важно:** Открытые модели (Llama) показывают 80% нарушений архитектуры vs 0% у GPT

#### 4. Microservices для Multi-Agent Systems
**Источник:** arXiv:2505.07838v1 (Май 2025)

Переход от монолита к микросервисам для AI-агентов:
- **Model Context Protocol (MCP)** — новый стандарт коммуникации
- **A2A Protocol** — Application-to-Application для агентов
- Agent Communication Languages (ACLs)

---

### 🌐 Современные архитектурные тренды 2025-2026

#### Топ-10 архитектур по популярности

| # | Архитектура | Применение | Python-инструменты |
|---|-------------|------------|-------------------|
| 1 | **Microservices** | Масштабируемые системы | FastAPI, Litestar |
| 2 | **Event-Driven (EDA)** | Real-time обработка | Kafka, RabbitMQ |
| 3 | **Serverless** | Sporadic workloads | AWS Lambda, Azure Functions |
| 4 | **Service Mesh** | Service-to-service | Istio, Linkerd |
| 5 | **Hexagonal** | Testability & DDD | Порты и адаптеры |
| 6 | **Data Mesh** | Distributed data | Databricks, Snowflake |
| 7 | **Edge Computing** | Low-latency IoT | AWS Greengrass |
| 8 | **CQRS + Event Sourcing** | Audit & replay | eventsourcing lib |
| 9 | **AI/ML-Centric** | MLOps pipelines | MLflow, Kubeflow |
| 10 | **Multi-Cloud/Hybrid** | Vendor independence | Kubernetes |

---

### 🐍 Современные Python-паттерны

#### 1. Structured Concurrency (Python 3.11+)

**TaskGroups** — новый стандарт для конкурентного кода:

```python
import asyncio

async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_data("api1"))
        task2 = tg.create_task(fetch_data("api2"))
        task3 = tg.create_task(fetch_data("api3"))
    # Все таски завершены или отменены при ошибке
    return task1.result(), task2.result(), task3.result()
```

**Преимущества:**
- Гарантированное завершение всех задач
- Автоматическая отмена при ошибке
- Нет "runaway tasks"
- Exception Groups для обработки множественных ошибок

#### 2. Pattern Matching (match-case)

```python
def handle_response(response: APIResponse) -> str:
    match response:
        case SuccessResponse(data=data):
            return process_data(data)
        case ErrorResponse(code="404"):
            return "Not found"
        case ErrorResponse(code=code, message=msg):
            return f"Error {code}: {msg}"
        case RetryResponse(retry_after=seconds):
            return f"Retry in {seconds}s"
        case _:
            return "Unknown response"
```

#### 3. Model Context Protocol (MCP) для AI-агентов

Новый стандарт для интеграции LLM с инструментами:

```python
# MCP Server
from mcp import MCPServer

server = MCPServer()

@server.tool("search_database")
async def search_db(query: str) -> list[dict]:
    """Search the database for records."""
    return await db.search(query)

@server.resource("user/{user_id}")
async def get_user(user_id: str) -> dict:
    """Get user by ID."""
    return await db.get_user(user_id)
```

**Зачем:** "Write once, run anywhere" для AI интеграций.

#### 4. AI Systems Engineering Patterns

30+ техник из статьи Alex Ewerlöf (Ноябрь 2025):

| Слой | Паттерны |
|------|----------|
| **Interface** | Templated Prompting, Structured Outputs, Function Calling, MCP |
| **Context** | CAG, RAG, Context Caching, Skills |
| **Control Flow** | Router, Model Cascading, Agentic Loops |
| **Cognitive** | Chain of Thought, Self-Reflection, Multi-Agent |

#### 5. Python Design Patterns for AI

**GitHub:** `arunpshankar/Python-Design-Patterns-for-AI`

| Паттерн | Применение в AI |
|---------|-----------------|
| **Singleton** | Model Registry, Config |
| **Factory** | Model/Pipeline Creation |
| **Observer** | Model Monitoring |
| **Strategy** | Interchangeable Algorithms |
| **Adapter** | Legacy System Integration |
| **Builder** | Complex Pipeline Construction |
| **Command** | Task Scheduling, Undo/Redo |
| **Mediator** | Agent Orchestration |
| **State** | Model Lifecycle Management |
| **Chain of Responsibility** | Data Validation Pipeline |
| **Visitor** | Cross-cutting Concerns |

---

### 🔮 Emerging Patterns

#### 1. Workflow Engines (Temporal.io)

Для сложных, долгоживущих процессов:

```python
from temporalio import workflow, activity

@activity.defn
async def process_image(image_url: str) -> dict:
    # Даже если сервер упадёт — Temporal восстановит состояние
    return await ml_engine.process(image_url)

@workflow.defn
class ImageProcessingWorkflow:
    @workflow.run
    async def run(self, images: list[str]) -> list[dict]:
        results = []
        for image in images:
            result = await workflow.execute_activity(
                process_image,
                image,
                start_to_close_timeout=timedelta(minutes=5)
            )
            results.append(result)
        return results
```

#### 2. Effect Systems (Returns library)

Функциональная обработка ошибок:

```python
from returns.result import Result, Success, Failure
from returns.pipeline import pipe
from returns.pointfree import bind

def validate(data: dict) -> Result[dict, str]:
    if not data.get("email"):
        return Failure("Email required")
    return Success(data)

def save(data: dict) -> Result[int, str]:
    try:
        return Success(db.save(data))
    except Exception as e:
        return Failure(str(e))

# Композиция без исключений
result = pipe(
    input_data,
    validate,
    bind(save),
)
```

#### 3. Reactive Streams (RxPY)

Для event-driven систем:

```python
from reactivex import operators as ops
from reactivex import create

# Реактивный поток событий
events.pipe(
    ops.filter(lambda e: e.type == "order_created"),
    ops.map(lambda e: process_order(e)),
    ops.buffer_with_time(1.0),  # Batch every second
    ops.flat_map(lambda batch: save_batch(batch)),
).subscribe(on_next=lambda x: print(f"Saved: {x}"))
```

---

### 📊 Сравнение: Какой паттерн когда использовать?

| Сценарий | Рекомендуемый паттерн | Почему |
|----------|----------------------|--------|
| Простой CRUD API | FastAPI + Repository | Минимум бойлерплейта |
| Сложная бизнес-логика | DDD + Porto Actions/Tasks | Чёткое разделение |
| ML-сервис | Hexagonal + Adapters | Лёгкая замена моделей |
| Real-time обработка | Event-Driven + Outbox | Гарантированная доставка |
| Аудит и compliance | Event Sourcing | Полная история |
| Долгие процессы | Temporal Workflows | Устойчивость к сбоям |
| AI-агенты | MCP + Function Calling | Стандартизация |
| Высокая конкурентность | Structured Concurrency | Безопасность |

---

### 📖 Источники исследования

#### Научные статьи (arXiv)
- `2511.05880v1` - DDD + Microservices for Big Data
- `2512.08657v1` - Hexagonal Architecture for MLOps
- `2505.16697v1` - LLMs in Software Architecture
- `2505.07838v1` - Microservices for Multi-Agent Systems
- `2310.01905v4` - Domain-Driven Design SLR

#### Книги и документация
- **"Architecture Patterns with Python"** (Cosmic Python) — Harry Percival, Bob Gregory
- **"Python Event Sourcing"** — eventsourcing.readthedocs.io
- **Python Design Patterns** — python-patterns.guide

#### Статьи и блоги
- "AI Systems Engineering Patterns" — Alex Ewerlöf (Nov 2025)
- "Modern FastAPI Architecture Patterns" — Medium (Jul 2025)
- "Python Structured Concurrency" — Applifting (Nov 2025)
- "10 Microservices Design Patterns" — Capital One

#### Репозитории
- `arunpshankar/Python-Design-Patterns-for-AI`
- `betaacid/FastAPI-Reference-App`
- `pyeventsourcing/eventsourcing`

---

## 📝 Заключение

**Hyper-Porto Stack v3.0** объединяет лучшее из трёх миров + продвинутые паттерны 2026:

### Базовые слои
- 🚢 **Porto** → Порядок и предсказуемость структуры
- 🐍 **Cosmic Python** → Чистота кода и тестируемость  
- 🍕 **Modular Slice** → Автономность и масштабируемость

### Паттерны надёжности
- 🔒 **Reliability** → Outbox/Inbox, Idempotency, Circuit Breaker
- 📊 **CQRS + Event Sourcing** → Аудит и replay истории
- ⚡ **Structured Concurrency** → TaskGroups для безопасного async

### AI-First паттерны
- 🤖 **Result Object** → Типизированные результаты без исключений
- 🎯 **Discriminated Unions** → Безопасная обработка вариантов
- 🔌 **Protocols** → Утиная типизация без связности
- 🌐 **MCP** → Model Context Protocol для AI-агентов

### Observability
- 📡 **OpenTelemetry** → Распределённая трассировка
- 📝 **structlog** → Структурированное логирование
- 🎚️ **Feature Flags** → Постепенный rollout

---

### Почему это работает для AI-разработки?

| Аспект | Как это помогает нейронке |
|--------|--------------------------|
| **Детерминизм** | Чёткие правила = меньше галлюцинаций |
| **Локальность** | Весь контекст в одной папке = точный код |
| **Типизация** | Pydantic + Protocols = валидация на этапе генерации |
| **Паттерны** | Стандартные решения = предсказуемый результат |

---

### Что изучать дальше?

1. **Для микросервисов:** Service Mesh (Istio), Temporal.io
2. **Для ML:** MLOps, Feature Stores, Model Registry
3. **Для AI-агентов:** MCP, Function Calling, Agentic Loops
4. **Для масштаба:** Event Sourcing, Data Mesh, Reactive Streams

---

> *"Хорошая архитектура 2026 года — это когда нейронка понимает, куда класть код, с первого промпта, не забывает обработать ошибку (потому что тип данных заставляет), и может объяснить своё решение через трассировку."*

---

<div align="center">

**Hyper-Porto Stack v3.0**

*Built for Humans & AI*

🚢 Porto + 🐍 Cosmic + 🍕 Slice + 🤖 AI-First = 🚀 Production-Ready

---

**Исследование проведено:** Январь 2026  
**Источники:** arXiv, Medium, GitHub, Real Python, O'Reilly

</div>
