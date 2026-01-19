# 🚀 Практическое руководство: Вынос Container в микросервис

> **Версия:** 1.0  
> **Дата:** Январь 2026  
> **Назначение:** Полное пошаговое руководство по выделению модуля (Container) из Hyper-Porto монолита в самостоятельный микросервис

---

## 📋 Содержание

1. [Философия и ключевые принципы](#1-философия-и-ключевые-принципы)
2. [Оценка готовности модуля](#2-оценка-готовности-модуля)
3. [Три уровня архитектурной зрелости](#3-три-уровня-архитектурной-зрелости)
4. [Подготовка модуля к выносу](#4-подготовка-модуля-к-выносу)
5. [Структура нового микросервиса](#5-структура-нового-микросервиса)
6. [Пошаговый процесс выноса](#6-пошаговый-процесс-выноса)
7. [Событийная система: от litestar.events к брокеру](#7-событийная-система-от-litestarevents-к-брокеру)
8. [Конфигурация и инфраструктура](#8-конфигурация-и-инфраструктура)
9. [Миграция данных](#9-миграция-данных)
10. [Module Gateway: синхронные зависимости](#10-module-gateway-синхронные-зависимости)
11. [Практический пример: SearchModule → SearchService](#11-практический-пример-searchmodule--searchservice)
12. [Типичные ошибки и как их избежать](#12-типичные-ошибки-и-как-их-избежать)
13. [Чеклисты](#13-чеклисты)
14. [Шаблоны файлов](#14-шаблоны-файлов)

---

## 1. Философия и ключевые принципы

### Почему вынос в Hyper-Porto — это просто

В Hyper-Porto **Container уже является границей будущего сервиса**. Архитектура изначально спроектирована так, что:

| Аспект | Как реализовано | Что это даёт при выносе |
|--------|-----------------|-------------------------|
| **Явная сборка** | `src/App.py` вручную подключает роутеры/listeners | Просто убрать из списка |
| **Явная DI-регистрация** | `AppProvider.py` перечисляет провайдеры | Просто убрать импорт |
| **Модульные миграции** | `PiccoloApp.py` в каждом модуле | Просто перенести |
| **События через UoW** | `uow.add_event()` + `litestar.events` | Заменить на брокер |
| **Изоляция данных** | Каждый модуль владеет своими таблицами | Просто вынести БД |

### Ключевой принцип

```
Вынос модуля = Перенос папки + Создание точки входа + Замена транспорта событий
                                                       
Бизнес-логика (Actions, Tasks, Repositories) остаётся БЕЗ ИЗМЕНЕНИЙ
```

---

## 2. Оценка готовности модуля

### 2.1 Матрица готовности

Оцените модуль по следующим критериям (0-3 балла за каждый):

| Критерий | 0 | 1 | 2 | 3 |
|----------|---|---|---|---|
| **Изоляция кода** | Много импортов из других Containers | Есть импорты, но можно заменить | Минимум импортов, через Events | Полная изоляция |
| **Изоляция данных** | Читает/пишет чужие таблицы | Только читает чужие | Только через Events/API | Полная изоляция |
| **Событийный контракт** | События не определены | Частично определены | Определены, но не версионированы | Полный контракт + версии |
| **Идемпотентность** | Нет | Частичная | Для критичных операций | Полная |

**Интерпретация:**
- **10-12**: Готов к выносу немедленно
- **7-9**: Требуется небольшая подготовка
- **4-6**: Требуется серьёзная подготовка
- **0-3**: Не готов, нужен рефакторинг

### 2.2 Хорошие кандидаты для выноса

Из текущего проекта:

| Модуль | Оценка | Причина |
|--------|--------|---------|
| **SearchModule** | ⭐⭐⭐ | Только слушает события, своя таблица, независим |
| **WebhookModule** | ⭐⭐⭐ | Fire-and-forget, внешние доставки |
| **AuditModule** | ⭐⭐ | Слушает события, но зависит от Ship декоратора |
| **NotificationModule** | ⭐⭐ | Может потребовать Gateway для чтения |
| **UserModule** | ⭐ | Центральный, много зависимостей от него |

---

## 3. Три уровня архитектурной зрелости

### Уровень 1: Модульный монолит (текущее состояние)

```
┌─────────────────────────────────────────────────────────────┐
│                    Единый процесс                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  App.py                                              │    │
│  │  ├── UserModule (роутер + listeners)                │    │
│  │  ├── SearchModule (роутер + listeners)              │    │
│  │  └── WebhookModule (роутер + listeners)             │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                    litestar.events                           │
│                      (in-process)                            │
└─────────────────────────────────────────────────────────────┘
```

### Уровень 2: Distributed Monolith (промежуточный)

```
┌─────────────────────────────────────────────────────────────┐
│                    Один репозиторий                          │
│                                                              │
│  ┌────────────────────┐     ┌────────────────────┐          │
│  │  Process 1         │     │  Process 2         │          │
│  │  App.py (Main)     │     │  SearchApp.py      │          │
│  │  ├── UserModule    │     │  └── SearchModule  │          │
│  │  └── WebhookModule │     │                    │          │
│  └─────────┬──────────┘     └────────┬───────────┘          │
│            │                         │                       │
│            └───────── Redis ─────────┘                       │
│                   (Pub/Sub или Streams)                      │
└─────────────────────────────────────────────────────────────┘
```

### Уровень 3: Микросервисы (целевое состояние)

```
┌────────────────────┐     ┌────────────────────┐
│  user-service      │     │  search-service    │
│  Repo: user-svc    │     │  Repo: search-svc  │
│  DB: PostgreSQL    │     │  DB: Elasticsearch │
└─────────┬──────────┘     └────────┬───────────┘
          │                         │
          └───── Kafka/RabbitMQ ────┘
                   + Outbox
```

---

## 4. Подготовка модуля к выносу

### 4.1 Устранение прямых импортов

**Проверка:**

```bash
# Найти прямые импорты между контейнерами
grep -r "from src.Containers.AppSection" src/Containers/AppSection/SearchModule/ | \
  grep -v "SearchModule"
```

**Если найдены — заменить на:**

```python
# ❌ БЫЛО: прямой импорт
from src.Containers.AppSection.UserModule.Actions.GetUserAction import GetUserAction

# ✅ СТАЛО: через Gateway
from src.Containers.AppSection.SearchModule.Gateways.UserGateway import UserGateway
```

### 4.2 Определение событийного контракта

Создайте файл `EventContracts.md` в модуле:

```markdown
# SearchModule Event Contracts

## Потребляемые события (Subscribed)

| Событие | Producer | Версия | Обязательные поля | Опциональные |
|---------|----------|--------|-------------------|--------------|
| UserCreated | UserModule | v1 | user_id, email, name | occurred_at |
| UserUpdated | UserModule | v1 | user_id | email, name |
| UserDeleted | UserModule | v1 | user_id | - |
| NotificationCreated | NotificationModule | v1 | notification_id, title | message |
| PaymentCreated | PaymentModule | v1 | payment_id, amount | currency |

## Публикуемые события (Published)

| Событие | Версия | Поля | Consumers |
|---------|--------|------|-----------|
| EntityIndexed | v1 | entity_type, entity_id | AuditModule |

## Гарантии доставки

- **Consumer idempotency**: Обязательно (по entity_type + entity_id)
- **Ordering**: Не требуется
- **At-least-once**: Допускаем дубли
```

### 4.3 Добавление версионирования

```python
# src/Containers/AppSection/SearchModule/Events.py

from src.Ship.Parents.Event import DomainEvent

class EntityIndexed(DomainEvent):
    """Событие успешной индексации сущности."""
    
    event_version: str = "v1"  # <-- Добавить версию
    
    entity_type: str
    entity_id: str
    indexed_at: str  # ISO datetime
```

---

## 5. Структура нового микросервиса

### 5.1 Рекомендуемая структура репозитория

```
hyper-porto-search/                  # Новый репозиторий
├── docs/
│   ├── README.md
│   └── event-contracts.md           # Контракты событий
│
├── src/
│   ├── __init__.py
│   ├── App.py                       # Litestar App (только этот модуль)
│   ├── Main.py                      # uvicorn entry point
│   │
│   ├── Ship/                        # Копия или зависимость
│   │   ├── Parents/
│   │   │   ├── Action.py
│   │   │   ├── Task.py
│   │   │   ├── Query.py
│   │   │   ├── Repository.py
│   │   │   ├── Event.py
│   │   │   └── UnitOfWork.py
│   │   ├── Core/
│   │   │   ├── BaseSchema.py
│   │   │   └── Errors.py
│   │   ├── Configs/
│   │   │   └── Settings.py          # Своя конфигурация
│   │   ├── Decorators/
│   │   │   └── result_handler.py
│   │   └── Infrastructure/
│   │       ├── HealthCheck.py
│   │       └── EventConsumer/       # НОВОЕ: консьюмер событий
│   │           ├── __init__.py
│   │           └── BrokerConsumer.py
│   │
│   └── Containers/
│       └── AppSection/
│           └── SearchModule/        # Переносим модуль целиком
│               ├── __init__.py
│               ├── Actions/
│               ├── Tasks/
│               ├── Queries/
│               ├── Data/
│               ├── Models/
│               │   ├── PiccoloApp.py
│               │   └── migrations/
│               ├── UI/
│               │   └── API/
│               ├── Events.py
│               ├── Errors.py
│               ├── Providers.py
│               └── Listeners.py     # Переделать на BrokerConsumer
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/                    # Consumer-driven contract tests
│
├── piccolo_conf.py                  # Только SearchModule PiccoloApp
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

### 5.2 Зависимости от Ship

**Вариант A: Копирование (для начала)**

```bash
# Копируем только нужные части Ship
mkdir -p new-service/src/Ship/Parents
cp src/Ship/Parents/{Action,Task,Query,Repository,Event,UnitOfWork}.py \
   new-service/src/Ship/Parents/
```

**Вариант B: Общий пакет (для масштабирования)**

```toml
# pyproject.toml нового сервиса
[project]
dependencies = [
    "hyper-porto-ship>=0.1.0",  # Общий пакет Ship
]
```

---

## 6. Пошаговый процесс выноса

### Шаг 1: Создание нового App.py для изолированного запуска

Сначала создаём отдельную точку входа **в том же репозитории**:

```python
# src/SearchApp.py (временно в том же репо)
"""Isolated SearchModule application for testing extraction."""

from litestar import Litestar
from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka

from src.Ship.Configs import get_settings
from src.Ship.Infrastructure.HealthCheck import health_controller
from src.Containers.AppSection.SearchModule import search_router
from src.Containers.AppSection.SearchModule.Providers import (
    SearchModuleProvider,
    SearchRequestProvider,
)
from src.Ship.Providers.AppProvider import AppProvider
from dishka.integrations.litestar import LitestarProvider


def create_search_app() -> Litestar:
    """Create isolated SearchModule application."""
    settings = get_settings()
    
    # Только провайдеры SearchModule
    container = make_async_container(
        AppProvider(),
        LitestarProvider(),
        SearchModuleProvider(),
        SearchRequestProvider(),
    )
    
    app = Litestar(
        route_handlers=[
            health_controller,
            search_router,
        ],
        listeners=[],  # События пойдут через брокер
        debug=settings.app_debug,
    )
    
    setup_dishka(container, app)
    return app


# Для uvicorn
app = create_search_app()
```

### Шаг 2: Тестирование изолированного запуска

```bash
# Запуск изолированного сервиса
uvicorn src.SearchApp:app --port 8001

# Проверка
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/search?q=test
```

### Шаг 3: Создание нового репозитория

```bash
# Создаём новый репозиторий
mkdir hyper-porto-search
cd hyper-porto-search

# Инициализируем проект
uv init
uv add litestar dishka piccolo returns anyio pydantic logfire

# Копируем модуль
cp -r ../new_porto/src/Containers/AppSection/SearchModule src/Containers/AppSection/

# Копируем необходимые части Ship
cp -r ../new_porto/src/Ship/Parents src/Ship/
cp -r ../new_porto/src/Ship/Core src/Ship/
cp -r ../new_porto/src/Ship/Decorators src/Ship/
cp -r ../new_porto/src/Ship/Configs src/Ship/
```

### Шаг 4: Адаптация конфигурации

```python
# src/Ship/Configs/Settings.py (для SearchService)
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """SearchService configuration."""
    
    # Идентификация сервиса
    service_name: str = Field(default="search-service")
    service_version: str = Field(default="1.0.0")
    
    # Основные настройки
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8001)  # Другой порт
    app_debug: bool = Field(default=False)
    
    # База данных (своя!)
    db_url: str = Field(default="postgresql://search:secret@localhost/search_db")
    
    # Брокер сообщений (для событий)
    broker_url: str = Field(default="redis://localhost:6379/0")
    
    # Consumer группа (для идемпотентности)
    consumer_group: str = Field(default="search-service-group")
```

### Шаг 5: Замена Listeners на Consumer

```python
# src/Ship/Infrastructure/EventConsumer/BrokerConsumer.py
"""Event consumer for microservice architecture."""

import asyncio
import json
from typing import Callable, Awaitable
from dataclasses import dataclass, field

import logfire
from redis.asyncio import Redis


@dataclass
class EventHandler:
    """Handler for a specific event type."""
    event_name: str
    handler: Callable[..., Awaitable[None]]
    version: str = "v1"


@dataclass
class BrokerConsumer:
    """Consumes events from Redis Streams."""
    
    redis_url: str
    consumer_group: str
    consumer_name: str
    handlers: list[EventHandler] = field(default_factory=list)
    _redis: Redis | None = field(default=None, init=False)
    
    async def start(self) -> None:
        """Start consuming events."""
        self._redis = Redis.from_url(self.redis_url)
        
        # Создаём consumer group для каждого типа события
        for handler in self.handlers:
            stream_name = f"events:{handler.event_name}"
            try:
                await self._redis.xgroup_create(
                    stream_name, 
                    self.consumer_group, 
                    id="0", 
                    mkstream=True
                )
            except Exception:
                pass  # Группа уже существует
        
        logfire.info(
            "🎧 Event consumer started",
            consumer_group=self.consumer_group,
            events=[h.event_name for h in self.handlers],
        )
        
        while True:
            await self._consume_batch()
    
    async def _consume_batch(self) -> None:
        """Consume a batch of events."""
        streams = {f"events:{h.event_name}": ">" for h in self.handlers}
        
        try:
            results = await self._redis.xreadgroup(
                groupname=self.consumer_group,
                consumername=self.consumer_name,
                streams=streams,
                count=10,
                block=5000,  # 5 секунд
            )
            
            for stream_name, messages in results:
                event_name = stream_name.decode().split(":")[1]
                handler = next(
                    (h for h in self.handlers if h.event_name == event_name),
                    None,
                )
                
                if handler:
                    for message_id, data in messages:
                        await self._process_message(
                            stream_name, message_id, data, handler
                        )
        except Exception as e:
            logfire.error("Failed to consume events", error=str(e))
            await asyncio.sleep(1)
    
    async def _process_message(
        self,
        stream_name: bytes,
        message_id: bytes,
        data: dict,
        handler: EventHandler,
    ) -> None:
        """Process a single message."""
        try:
            # Декодируем данные
            event_data = {
                k.decode(): json.loads(v.decode()) if isinstance(v, bytes) else v
                for k, v in data.items()
            }
            
            logfire.info(
                f"📥 Processing {handler.event_name}",
                message_id=message_id.decode(),
            )
            
            # Вызываем хендлер
            await handler.handler(**event_data)
            
            # ACK сообщения
            await self._redis.xack(stream_name, self.consumer_group, message_id)
            
        except Exception as e:
            logfire.error(
                f"Failed to process {handler.event_name}",
                error=str(e),
                message_id=message_id.decode(),
            )
            # Не делаем ACK — сообщение будет переобработано
```

### Шаг 6: Адаптация Listeners

```python
# src/Containers/AppSection/SearchModule/Consumers.py (новый файл)
"""SearchModule event consumers for microservice mode."""

from src.Ship.Infrastructure.EventConsumer.BrokerConsumer import EventHandler
from src.Containers.AppSection.SearchModule.Tasks.IndexEntityTask import (
    IndexEntityTask,
    IndexableEntity,
    RemoveFromIndexTask,
)
import logfire


async def handle_user_created(
    user_id: str,
    email: str,
    name: str,
    **kwargs,
) -> None:
    """Index newly created user."""
    logfire.info("🔍 Indexing new user", user_id=user_id)
    
    task = IndexEntityTask()
    await task.run(IndexableEntity(
        entity_type="User",
        entity_id=user_id,
        title=name,
        content=f"{name} ({email})",
        tags=["user", "active"],
        metadata={"email": email},
    ))


async def handle_user_deleted(user_id: str, **kwargs) -> None:
    """Remove deleted user from index."""
    logfire.info("🗑️ Removing user from index", user_id=user_id)
    
    task = RemoveFromIndexTask()
    await task.run(("User", user_id))


# Список хендлеров для регистрации
EVENT_HANDLERS = [
    EventHandler(event_name="UserCreated", handler=handle_user_created),
    EventHandler(event_name="UserDeleted", handler=handle_user_deleted),
    # ... другие хендлеры
]
```

### Шаг 7: Обновление App.py нового сервиса

```python
# src/App.py (в новом репозитории)
"""SearchService main application."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import asyncio
import socket

from litestar import Litestar
from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka, LitestarProvider

from src.Ship.Configs import get_settings
from src.Ship.Infrastructure.HealthCheck import health_controller
from src.Ship.Infrastructure.EventConsumer.BrokerConsumer import BrokerConsumer
from src.Containers.AppSection.SearchModule import search_router
from src.Containers.AppSection.SearchModule.Providers import (
    SearchModuleProvider,
    SearchRequestProvider,
)
from src.Containers.AppSection.SearchModule.Consumers import EVENT_HANDLERS


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """Application lifespan with event consumer."""
    settings = get_settings()
    
    # Запускаем consumer в фоне
    consumer = BrokerConsumer(
        redis_url=settings.broker_url,
        consumer_group=settings.consumer_group,
        consumer_name=f"{settings.service_name}-{socket.gethostname()}",
        handlers=EVENT_HANDLERS,
    )
    
    consumer_task = asyncio.create_task(consumer.start())
    
    try:
        yield
    finally:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass


def create_app() -> Litestar:
    """Create SearchService application."""
    settings = get_settings()
    
    container = make_async_container(
        SearchModuleProvider(),
        SearchRequestProvider(),
        LitestarProvider(),
    )
    
    app = Litestar(
        route_handlers=[
            health_controller,
            search_router,
        ],
        lifespan=[lifespan],
        debug=settings.app_debug,
    )
    
    setup_dishka(container, app)
    return app


app = create_app()
```

### Шаг 8: Удаление модуля из монолита

```python
# src/App.py (в монолите) — убрать:

# 1. Убрать импорт роутера
# from src.Containers.AppSection.SearchModule import search_router  # УДАЛИТЬ

# 2. Убрать из route_handlers
route_handlers=[
    # ...
    # search_router,  # УДАЛИТЬ
    # ...
]

# 3. Убрать listeners
# from src.Containers.AppSection.SearchModule.Listeners import (
#     on_user_created_index,
#     ...
# )  # УДАЛИТЬ

listeners=[
    # ...
    # on_user_created_index,  # УДАЛИТЬ
    # ...
]
```

```python
# src/Ship/Providers/AppProvider.py — убрать:

# from src.Containers.AppSection.SearchModule.Providers import (
#     SearchModuleProvider,
#     SearchRequestProvider,
# )  # УДАЛИТЬ

# В get_all_providers():
# SearchModuleProvider(),  # УДАЛИТЬ
# SearchRequestProvider(),  # УДАЛИТЬ
```

```python
# piccolo_conf.py — убрать:

APP_REGISTRY = AppRegistry(
    apps=[
        # ...
        # "src.Containers.AppSection.SearchModule.Models.PiccoloApp",  # УДАЛИТЬ
    ]
)
```

---

## 7. Событийная система: от litestar.events к брокеру

### 7.1 Текущая схема (монолит)

```
Action → uow.add_event() → uow.commit() → __aexit__() → app.emit()
                                                            │
                                                     litestar.events
                                                      (in-process)
                                                            │
                                                      @listener()
```

### 7.2 Целевая схема (микросервисы)

```
┌─ Сервис-продьюсер ─────────────────────────────────────────────────┐
│                                                                     │
│  Action → uow.add_event() → uow.commit()                           │
│                                 │                                   │
│                                 ▼                                   │
│                          Outbox Table (в той же транзакции)        │
│                                 │                                   │
└─────────────────────────────────│───────────────────────────────────┘
                                  │
                           Outbox Worker                               
                                  │
                                  ▼
                         Redis Streams / Kafka
                                  │
                                  ▼
┌─ Сервис-консьюмер ─────────────────────────────────────────────────┐
│                                                                     │
│                          BrokerConsumer                            │
│                                 │                                   │
│                                 ▼                                   │
│                          Event Handlers                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Публикация событий в брокер (продьюсер)

Добавляем публикацию в Redis Streams:

```python
# src/Ship/Parents/UnitOfWork.py (модифицированный)

from redis.asyncio import Redis

@dataclass
class BaseUnitOfWork:
    _emit: EventEmitterFunc = field(default=None, repr=False)
    _broker_url: str | None = field(default=None, repr=False)  # НОВОЕ
    # ...
    
    async def _publish_to_broker(self, events: list["DomainEvent"]) -> None:
        """Publish events to message broker."""
        if not self._broker_url:
            return
        
        redis = Redis.from_url(self._broker_url)
        try:
            for event in events:
                stream_name = f"events:{event.event_name}"
                await redis.xadd(
                    stream_name,
                    {
                        "payload": event.model_dump_json(),
                        "version": getattr(event, "event_version", "v1"),
                        "occurred_at": event.occurred_at.isoformat(),
                    },
                )
        finally:
            await redis.close()
    
    async def __aexit__(self, ...):
        # ... существующий код ...
        
        # После локального emit добавляем публикацию в брокер
        if self._broker_url:
            await self._publish_to_broker(self._events)
```

### 7.4 Transactional Outbox (рекомендуется)

Для гарантированной доставки используйте Outbox:

```python
# src/Ship/Core/OutboxEvent.py
from piccolo.table import Table
from piccolo.columns import UUID, Varchar, Text, Timestamptz, Boolean
from piccolo.columns.defaults import UUID4, TimestamptzNow


class OutboxEvent(Table, tablename="outbox_events"):
    """Transactional Outbox for reliable event publishing."""
    
    id = UUID(primary_key=True, default=UUID4())
    event_name = Varchar(length=255, index=True)
    event_version = Varchar(length=10, default="v1")
    payload = Text()  # JSON
    occurred_at = Timestamptz(default=TimestamptzNow())
    published = Boolean(default=False, index=True)
    published_at = Timestamptz(null=True, default=None)
```

```python
# src/Ship/Infrastructure/Workers/OutboxPublisher.py
"""Background worker that publishes Outbox events to broker."""

import asyncio
import json
from redis.asyncio import Redis
from piccolo.engine import engine_finder

from src.Ship.Core.OutboxEvent import OutboxEvent


async def publish_outbox_events(redis_url: str, batch_size: int = 100) -> None:
    """Publish pending outbox events to broker."""
    redis = Redis.from_url(redis_url)
    
    while True:
        # Получаем неопубликованные события
        events = await OutboxEvent.select().where(
            OutboxEvent.published == False
        ).limit(batch_size).run()
        
        for event in events:
            try:
                stream_name = f"events:{event['event_name']}"
                await redis.xadd(
                    stream_name,
                    {
                        "payload": event["payload"],
                        "version": event["event_version"],
                        "event_id": str(event["id"]),
                    },
                )
                
                # Помечаем как опубликованное
                await OutboxEvent.update({
                    OutboxEvent.published: True,
                    OutboxEvent.published_at: datetime.utcnow(),
                }).where(
                    OutboxEvent.id == event["id"]
                ).run()
                
            except Exception as e:
                logfire.error(
                    "Failed to publish outbox event",
                    event_id=str(event["id"]),
                    error=str(e),
                )
        
        # Пауза между итерациями
        await asyncio.sleep(1)
```

---

## 8. Конфигурация и инфраструктура

### 8.1 Dockerfile для нового сервиса

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

# Run the service
CMD ["uv", "run", "uvicorn", "src.App:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 8.2 docker-compose.yml

```yaml
version: '3.8'

services:
  search-service:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: search-service
    ports:
      - "8001:8001"
    environment:
      - SERVICE_NAME=search-service
      - APP_DEBUG=false
      - DB_URL=postgresql://search:secret@postgres:5432/search_db
      - BROKER_URL=redis://redis:6379/0
      - CONSUMER_GROUP=search-service-group
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - microservices-network

  postgres:
    image: postgres:16-alpine
    container_name: search-postgres
    environment:
      POSTGRES_USER: search
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: search_db
    volumes:
      - search-postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U search -d search_db"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - microservices-network

  redis:
    image: redis:7-alpine
    container_name: shared-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - microservices-network

volumes:
  search-postgres-data:

networks:
  microservices-network:
    driver: bridge
```

### 8.3 piccolo_conf.py для нового сервиса

```python
# piccolo_conf.py
from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine
import os

DB = PostgresEngine(
    config={
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USER", "search"),
        "password": os.getenv("DB_PASSWORD", "secret"),
        "database": os.getenv("DB_NAME", "search_db"),
    }
)

APP_REGISTRY = AppRegistry(
    apps=[
        # Только SearchModule
        "src.Containers.AppSection.SearchModule.Models.PiccoloApp",
    ]
)
```

---

## 9. Миграция данных

### 9.1 Стратегии миграции

| Стратегия | Даунтайм | Сложность | Когда использовать |
|-----------|----------|-----------|-------------------|
| **Freeze & Move** | Есть | Низкая | Небольшой объём, допустим даунтайм |
| **Dual Write** | Нет | Высокая | Критичные данные, нужен zero-downtime |
| **Event Replay** | Нет | Средняя | Read-модели (SearchModule) |

### 9.2 Freeze & Move (для SearchModule)

```bash
# 1. Остановить запись (feature flag или maintenance mode)
curl -X POST http://api/admin/maintenance/enable

# 2. Экспорт таблицы
piccolo migrations forwards search_module
pg_dump -t search_index old_db > search_index.sql

# 3. Импорт в новую БД
psql -d search_db < search_index.sql

# 4. Запустить новый сервис
docker-compose up -d search-service

# 5. Переключить трафик (nginx/ingress)
# 6. Включить запись обратно
```

### 9.3 Event Replay (рекомендуется для SearchModule)

```python
# scripts/replay_events.py
"""Replay historical events to rebuild search index."""

import asyncio
from datetime import datetime, timedelta

from src.Containers.AppSection.SearchModule.Consumers import EVENT_HANDLERS


async def replay_from_main_db():
    """Replay all entities from main database."""
    # Подключаемся к БД монолита (read-only)
    from piccolo.engine.postgres import PostgresEngine
    
    main_db = PostgresEngine(config={...})
    
    # Получаем всех пользователей
    users = await main_db.run(
        "SELECT id, email, name, created_at FROM app_users"
    )
    
    # Эмулируем события
    handler = next(h for h in EVENT_HANDLERS if h.event_name == "UserCreated")
    
    for user in users:
        await handler.handler(
            user_id=str(user["id"]),
            email=user["email"],
            name=user["name"],
        )
        print(f"Indexed user {user['id']}")


if __name__ == "__main__":
    asyncio.run(replay_from_main_db())
```

---

## 10. Module Gateway: синхронные зависимости

Если вашему модулю нужны **синхронные** данные от другого сервиса:

### 10.1 Создание Gateway Interface

```python
# src/Containers/AppSection/SearchModule/Gateways/UserGateway.py
from typing import Protocol
from dataclasses import dataclass
from returns.result import Result


@dataclass
class UserInfo:
    """Minimal user info needed by SearchModule."""
    user_id: str
    email: str
    name: str
    is_active: bool


class UserGateway(Protocol):
    """Port for getting user information."""
    
    async def get_user(self, user_id: str) -> Result[UserInfo, Exception]:
        """Get user by ID."""
        ...
    
    async def get_users_batch(
        self, user_ids: list[str]
    ) -> dict[str, UserInfo | None]:
        """Get multiple users by IDs."""
        ...
```

### 10.2 HTTP Adapter (для микросервиса)

```python
# src/Containers/AppSection/SearchModule/Gateways/Adapters/HttpUserAdapter.py
from dataclasses import dataclass
import httpx
from returns.result import Result, Success, Failure

from src.Containers.AppSection.SearchModule.Gateways.UserGateway import (
    UserGateway, UserInfo
)


@dataclass
class HttpUserAdapter:
    """HTTP adapter for UserService."""
    
    base_url: str
    timeout: float = 5.0
    
    async def get_user(self, user_id: str) -> Result[UserInfo, Exception]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/users/{user_id}")
                response.raise_for_status()
                
                data = response.json()
                return Success(UserInfo(
                    user_id=data["id"],
                    email=data["email"],
                    name=data["name"],
                    is_active=data["is_active"],
                ))
        except Exception as e:
            return Failure(e)
    
    async def get_users_batch(
        self, user_ids: list[str]
    ) -> dict[str, UserInfo | None]:
        result = {}
        # В реальности — batch endpoint или параллельные запросы
        for user_id in user_ids:
            user_result = await self.get_user(user_id)
            result[user_id] = user_result.value_or(None)
        return result
```

### 10.3 Регистрация в DI

```python
# src/Containers/AppSection/SearchModule/Providers.py
from dishka import Provider, Scope, provide

from src.Ship.Configs import get_settings
from src.Containers.AppSection.SearchModule.Gateways.UserGateway import UserGateway
from src.Containers.AppSection.SearchModule.Gateways.Adapters.HttpUserAdapter import (
    HttpUserAdapter
)


class SearchMicroserviceProvider(Provider):
    """Provider for microservice mode."""
    
    scope = Scope.APP
    
    @provide
    def user_gateway(self) -> UserGateway:
        settings = get_settings()
        return HttpUserAdapter(base_url=settings.user_service_url)
```

---

## 11. Практический пример: SearchModule → SearchService

### 11.1 Что переносим

| Компонент | Действие |
|-----------|----------|
| `SearchModule/Actions/` | Переносим без изменений |
| `SearchModule/Tasks/` | Переносим без изменений |
| `SearchModule/Queries/` | Переносим без изменений |
| `SearchModule/Data/` | Переносим без изменений |
| `SearchModule/Models/` | Переносим + новый piccolo_conf.py |
| `SearchModule/UI/API/` | Переносим без изменений |
| `SearchModule/Listeners.py` | **Переделываем** в Consumers.py |
| `SearchModule/Events.py` | Переносим + добавляем версии |
| `SearchModule/Providers.py` | **Адаптируем** под микросервис |

### 11.2 Что меняем

**До (Listeners.py):**

```python
@listener("UserCreated")
async def on_user_created_index(user_id: str, email: str, name: str, **kwargs):
    task = IndexEntityTask()
    await task.run(...)
```

**После (Consumers.py):**

```python
async def handle_user_created(user_id: str, email: str, name: str, **kwargs):
    task = IndexEntityTask()
    await task.run(...)

EVENT_HANDLERS = [
    EventHandler(event_name="UserCreated", handler=handle_user_created),
]
```

### 11.3 Что НЕ меняем

```python
# Actions остаются без изменений
class IndexEntityAction(Action[IndexRequest, IndexResult, SearchError]):
    async def run(self, data: IndexRequest) -> Result[IndexResult, SearchError]:
        # Та же логика
        ...

# Tasks остаются без изменений
class IndexEntityTask(Task[IndexableEntity, None]):
    async def run(self, entity: IndexableEntity) -> None:
        # Та же логика
        ...

# Queries остаются без изменений
class FullTextSearchQuery(Query[SearchParams, list[SearchResult]]):
    async def execute(self, params: SearchParams) -> list[SearchResult]:
        # Та же логика
        ...
```

---

## 12. Типичные ошибки и как их избежать

### 12.1 Потеря событий (Dual Write Problem)

**❌ Проблема:**

```python
# Событие отправляется ДО коммита
async with uow:
    await uow.users.add(user)
    await publish_to_broker(UserCreated(...))  # ← Опасно!
    await uow.commit()  # Может упасть
```

**✅ Решение: Outbox**

```python
# Событие записывается в ту же транзакцию
async with uow:
    await uow.users.add(user)
    await uow.outbox.add(UserCreated(...))  # В ту же БД
    await uow.commit()
# Отдельный worker публикует из Outbox
```

### 12.2 Отсутствие идемпотентности

**❌ Проблема:**

```python
async def handle_payment_created(payment_id: str, amount: float, **kwargs):
    # При повторной доставке — дублирование
    await create_invoice(payment_id, amount)
```

**✅ Решение:**

```python
async def handle_payment_created(payment_id: str, amount: float, **kwargs):
    # Проверяем, обрабатывали ли уже
    if await redis.get(f"processed:payment:{payment_id}"):
        return  # Уже обработали
    
    await create_invoice(payment_id, amount)
    
    # Помечаем как обработанное
    await redis.set(f"processed:payment:{payment_id}", "1", ex=86400 * 7)
```

### 12.3 Нет версионирования событий

**❌ Проблема:**

```python
# Продьюсер добавил новое поле
class UserCreated(DomainEvent):
    user_id: str
    email: str
    name: str
    phone: str  # НОВОЕ — сломает старых консьюмеров
```

**✅ Решение:**

```python
class UserCreatedV2(DomainEvent):
    event_name: str = "UserCreated"
    event_version: str = "v2"  # Версия!
    
    user_id: str
    email: str
    name: str
    phone: str | None = None  # Optional для совместимости
```

### 12.4 Циклические зависимости

**❌ Проблема:**

```
SearchService → UserService (для получения данных)
UserService → SearchService (для поиска)
```

**✅ Решение: Event-Carried State Transfer**

```python
# SearchService хранит копию нужных данных
class UserReplica(Table):
    user_id = UUID(primary_key=True)
    email = Varchar()
    name = Varchar()

# Обновляется по событиям UserUpdated
```

---

## 13. Чеклисты

### 13.1 Чеклист подготовки модуля

```markdown
## Подготовка к выносу: [ModuleName]

### Изоляция кода
- [ ] Нет прямых импортов из других Containers
- [ ] Зависимости через Events или Gateway
- [ ] Ship-компоненты выделены или копируемы

### Изоляция данных
- [ ] Модуль владеет своими таблицами
- [ ] Нет чужих write-операций в наши таблицы
- [ ] Нет наших write-операций в чужие таблицы

### Событийный контракт
- [ ] Все потребляемые события задокументированы
- [ ] Все публикуемые события задокументированы
- [ ] События имеют версии (event_version)
- [ ] Обязательные и опциональные поля определены

### Идемпотентность
- [ ] Consumer handlers идемпотентны
- [ ] Критичные операции имеют idempotency keys
- [ ] Логика устойчива к дублированию сообщений
```

### 13.2 Чеклист выноса

```markdown
## Вынос модуля: [ModuleName]

### Шаг 1: Изолированный запуск (в том же репо)
- [ ] Создан отдельный App.py для модуля
- [ ] Модуль запускается на отдельном порту
- [ ] HTTP endpoints работают
- [ ] Health check проходит

### Шаг 2: Новый репозиторий
- [ ] Создан репозиторий
- [ ] Скопирован код модуля
- [ ] Скопированы/добавлены зависимости Ship
- [ ] pyproject.toml настроен
- [ ] piccolo_conf.py настроен

### Шаг 3: Событийная система
- [ ] Listeners переделаны в Consumers
- [ ] BrokerConsumer настроен
- [ ] События читаются из брокера
- [ ] Продьюсер публикует в брокер

### Шаг 4: Инфраструктура
- [ ] Dockerfile создан
- [ ] docker-compose.yml создан
- [ ] CI/CD настроен
- [ ] Мониторинг настроен

### Шаг 5: Миграция данных
- [ ] Стратегия миграции выбрана
- [ ] Данные мигрированы
- [ ] Данные верифицированы

### Шаг 6: Переключение
- [ ] Трафик переключён на новый сервис
- [ ] Модуль удалён из монолита
- [ ] Старые listeners удалены
- [ ] Старые providers удалены
- [ ] PiccoloApp удалён из piccolo_conf.py

### Шаг 7: Верификация
- [ ] Все endpoints работают
- [ ] События обрабатываются
- [ ] Логи и метрики собираются
- [ ] Алерты настроены
```

---

## 14. Шаблоны файлов

### 14.1 Шаблон Settings для микросервиса

```python
# src/Ship/Configs/Settings.py
"""${ServiceName} configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """${ServiceName} settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Service identity
    service_name: str = Field(default="${service-name}")
    service_version: str = Field(default="1.0.0")
    
    # Server
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8001)
    app_debug: bool = Field(default=False)
    
    # Database (own database!)
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_user: str = Field(default="${service}")
    db_password: str = Field(default="secret")
    db_name: str = Field(default="${service}_db")
    
    # Message broker
    broker_url: str = Field(default="redis://localhost:6379/0")
    consumer_group: str = Field(default="${service-name}-group")
    
    # External services (if needed)
    user_service_url: str = Field(default="http://user-service:8000")
    
    # Observability
    logfire_token: str | None = Field(default=None)
    
    @property
    def db_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
```

### 14.2 Шаблон App.py для микросервиса

```python
# src/App.py
"""${ServiceName} main application."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import asyncio
import socket

from litestar import Litestar
from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka, LitestarProvider

from src.Ship.Configs import get_settings
from src.Ship.Infrastructure.HealthCheck import health_controller
from src.Ship.Infrastructure.EventConsumer.BrokerConsumer import BrokerConsumer
from src.Containers.AppSection.${ModuleName} import ${module}_router
from src.Containers.AppSection.${ModuleName}.Providers import (
    ${ModuleName}Provider,
    ${ModuleName}RequestProvider,
)
from src.Containers.AppSection.${ModuleName}.Consumers import EVENT_HANDLERS


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """Application lifespan with event consumer."""
    settings = get_settings()
    
    consumer = BrokerConsumer(
        redis_url=settings.broker_url,
        consumer_group=settings.consumer_group,
        consumer_name=f"{settings.service_name}-{socket.gethostname()}",
        handlers=EVENT_HANDLERS,
    )
    
    consumer_task = asyncio.create_task(consumer.start())
    
    try:
        yield
    finally:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass


def create_app() -> Litestar:
    """Create ${ServiceName} application."""
    settings = get_settings()
    
    container = make_async_container(
        ${ModuleName}Provider(),
        ${ModuleName}RequestProvider(),
        LitestarProvider(),
    )
    
    app = Litestar(
        route_handlers=[
            health_controller,
            ${module}_router,
        ],
        lifespan=[lifespan],
        debug=settings.app_debug,
    )
    
    setup_dishka(container, app)
    return app


app = create_app()
```

### 14.3 Шаблон Consumers.py

```python
# src/Containers/AppSection/${ModuleName}/Consumers.py
"""${ModuleName} event consumers for microservice mode."""

import logfire
from src.Ship.Infrastructure.EventConsumer.BrokerConsumer import EventHandler

# Import tasks/actions needed for handling events
# from src.Containers.AppSection.${ModuleName}.Tasks.SomeTask import SomeTask


async def handle_some_event(
    entity_id: str,
    **kwargs,
) -> None:
    """Handle SomeEvent."""
    logfire.info("📥 Processing SomeEvent", entity_id=entity_id)
    
    # Your handling logic here
    # task = SomeTask()
    # await task.run(...)


# Register all event handlers
EVENT_HANDLERS = [
    EventHandler(event_name="SomeEvent", handler=handle_some_event),
    # Add more handlers as needed
]
```

---

## 📚 Связанная документация

- [00-philosophy.md](00-philosophy.md) — Философия архитектуры
- [01-architecture.md](01-architecture.md) — Архитектурные слои
- [10-registration.md](10-registration.md) — Явная регистрация компонентов
- [13-cross-module-communication.md](13-cross-module-communication.md) — Межмодульное взаимодействие
- [14-future-roadmap-and-patterns.md](14-future-roadmap-and-patterns.md) — Outbox, Idempotency, SAGA
- [15-module-gateway-pattern.md](15-module-gateway-pattern.md) — Gateway Pattern
- [16-extract-module-to-microservice.md](16-extract-module-to-microservice.md) — Предыдущая версия документа

---

<div align="center">

**Hyper-Porto v4.3**

*От модульного монолита к микросервисам — шаг за шагом*

🚢 Container → 🔀 Distributed → 🚀 Microservice

</div>


