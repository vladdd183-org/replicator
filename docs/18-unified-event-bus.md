# 🔌 Unified Event Bus: Единая система событий

> **Версия:** 1.0  
> **Дата:** Январь 2026  
> **Назначение:** Архитектура унифицированной событийной системы с подменяемыми бэкендами

---

## 📋 Содержание

1. [Проблема](#1-проблема)
2. [Решение: Unified Event Bus](#2-решение-unified-event-bus)
3. [Архитектура](#3-архитектура)
4. [Доступные бэкенды](#4-доступные-бэкенды)
5. [Реализация](#5-реализация)
6. [Интеграция с UnitOfWork](#6-интеграция-с-unitofwork)
7. [Декоратор @subscribe](#7-декоратор-subscribe)
8. [Конфигурация](#8-конфигурация)
9. [Transactional Outbox](#9-transactional-outbox)
10. [Примеры использования](#10-примеры-использования)
11. [Миграция с litestar.events](#11-миграция-с-litestarevents)
12. [FAQ](#12-faq)

---

## 1. Проблема

### 1.1 Текущая ситуация

В Hyper-Porto события работают через `litestar.events`:

```python
# Публикация (в UoW)
self._emit("UserCreated", **event.model_dump())

# Подписка
@listener("UserCreated")
async def on_user_created(user_id: str, **kwargs):
    ...
```

### 1.2 Ограничения litestar.events

| Ограничение | Проблема |
|-------------|----------|
| **In-memory** | Работает только в одном процессе |
| **Синхронная доставка** | Listener блокирует HTTP-ответ |
| **Нет персистентности** | При падении — события теряются |
| **Жёсткая привязка** | Нельзя заменить на Redis/RabbitMQ |

### 1.3 Что хотим

```
✅ Единый интерфейс для всех окружений
✅ Код не меняется при смене бэкенда
✅ Переключение через конфиг (env variable)
✅ Поддержка: In-Memory → Redis → RabbitMQ → Kafka
✅ Готовность к микросервисам из коробки
```

---

## 2. Решение: Unified Event Bus

### 2.1 Концепция

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Бизнес-код                                   │
│                                                                     │
│   @subscribe("UserCreated")           ← Единый декоратор           │
│   async def handle(user_id, **kw):                                 │
│       ...                                                           │
│                                                                     │
│   event_bus.publish(UserCreated(...)) ← Единый метод               │
│                                                                     │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     EventBus Protocol                               │
│                                                                     │
│   publish(event) → отправить событие                               │
│   subscribe(name, handler) → подписаться                           │
│   start() → запустить consumer                                     │
│   stop() → остановить consumer                                     │
│                                                                     │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
   ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
   │ InMemoryBus   │        │ RedisStreams  │        │ RabbitMQBus   │
   │               │        │ Bus           │        │               │
   │ • Монолит     │        │ • Distributed │        │ • Production  │
   │ • Разработка  │        │ • Staging     │        │ • Микросервисы│
   │ • Тесты       │        │ • Multi-inst  │        │ • Надёжность  │
   └───────────────┘        └───────────────┘        └───────────────┘
```

### 2.2 Принцип работы

```python
# Конфиг определяет бэкенд
EVENT_BUS_BACKEND=memory   # Разработка
EVENT_BUS_BACKEND=redis    # Staging / Distributed
EVENT_BUS_BACKEND=rabbitmq # Production

# Код остаётся ОДИНАКОВЫМ везде!
@subscribe("UserCreated")
async def on_user_created(user_id: str, **kwargs):
    await index_user(user_id)
```

---

## 3. Архитектура

### 3.1 Компоненты системы

```
src/Ship/Infrastructure/Events/
├── __init__.py
├── Protocol.py           # EventBus Protocol (интерфейс)
├── Factory.py            # Создание бэкенда по конфигу
├── Decorators.py         # @subscribe декоратор
├── Outbox.py             # Transactional Outbox (опционально)
│
└── Backends/
    ├── __init__.py
    ├── InMemory.py       # In-memory (dev/test)
    ├── RedisStreams.py   # Redis Streams
    ├── RedisPubSub.py    # Redis Pub/Sub (fire-and-forget)
    └── RabbitMQ.py       # RabbitMQ (production)
```

### 3.2 Поток событий

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. ПУБЛИКАЦИЯ                                                       │
│                                                                     │
│   Action                                                            │
│      │                                                              │
│      ▼                                                              │
│   async with uow:                                                   │
│       await uow.users.add(user)                                    │
│       uow.add_event(UserCreated(...))                              │
│       await uow.commit()                                            │
│      │                                                              │
│      ▼                                                              │
│   UoW.__aexit__() → event_bus.publish(event)                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. ТРАНСПОРТ (зависит от бэкенда)                                   │
│                                                                     │
│   InMemory:   handlers[event_name] → handler(**payload)            │
│   Redis:      XADD events:UserCreated {...}                        │
│   RabbitMQ:   exchange.publish(message, routing_key)               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. ДОСТАВКА                                                         │
│                                                                     │
│   InMemory:   Сразу вызывает handler                               │
│   Redis:      Consumer читает XREADGROUP → handler                 │
│   RabbitMQ:   Queue consumer → handler                             │
│                                                                     │
│   @subscribe("UserCreated")                                        │
│   async def on_user_created(**kwargs):                             │
│       ...                                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Доступные бэкенды

### 4.1 Сравнительная таблица

| Бэкенд | Надёжность | Персистентность | Сложность | Когда использовать |
|--------|------------|-----------------|-----------|-------------------|
| **InMemory** | ⭐ | ❌ Нет | ⭐ Простой | Разработка, тесты |
| **Redis Pub/Sub** | ⭐⭐ | ❌ Нет | ⭐⭐ | Fire-and-forget события |
| **Redis Streams** | ⭐⭐⭐ | ✅ Да | ⭐⭐ | Distributed monolith |
| **RabbitMQ** | ⭐⭐⭐⭐ | ✅ Да | ⭐⭐⭐ | Production, микросервисы |
| **Kafka** | ⭐⭐⭐⭐⭐ | ✅ Да | ⭐⭐⭐⭐ | Event Sourcing, Big Data |

### 4.2 InMemory (для разработки)

```
Плюсы:
  ✅ Нулевая задержка
  ✅ Не нужна инфраструктура
  ✅ Простая отладка
  
Минусы:
  ❌ Только один процесс
  ❌ События теряются при падении
  ❌ Listener блокирует ответ
```

### 4.3 Redis Streams (рекомендуется для старта)

```
Плюсы:
  ✅ Redis уже есть (для кэша/TaskIQ)
  ✅ Consumer Groups (несколько инстансов)
  ✅ Персистентность (XADD хранит историю)
  ✅ ACK механизм (гарантия обработки)
  
Минусы:
  ❌ Нет DLQ из коробки (нужно руками)
  ❌ Нет сложного роутинга
```

### 4.4 RabbitMQ (для production)

```
Плюсы:
  ✅ Dead Letter Queues (для failed messages)
  ✅ Routing (topic, fanout, headers)
  ✅ Приоритеты сообщений
  ✅ Management UI
  ✅ Plugins (delayed messages и т.д.)
  
Минусы:
  ❌ Отдельный сервис
  ❌ Сложнее настройка
```

---

## 5. Реализация

### 5.1 Protocol (интерфейс)

```python
# src/Ship/Infrastructure/Events/Protocol.py
"""EventBus Protocol — единый интерфейс для всех бэкендов."""

from typing import Protocol, Callable, Awaitable, Any, runtime_checkable

from src.Ship.Parents.Event import DomainEvent


# Тип для обработчика событий
EventHandler = Callable[..., Awaitable[None]]


@runtime_checkable
class EventBus(Protocol):
    """Unified Event Bus interface.
    
    Все бэкенды реализуют этот протокол, что позволяет
    переключаться между ними через конфигурацию.
    
    Example:
        event_bus = create_event_bus()  # Создаёт по конфигу
        
        # Публикация
        await event_bus.publish(UserCreated(user_id=..., email=...))
        
        # Подписка
        event_bus.subscribe("UserCreated", handle_user_created)
    """
    
    async def publish(self, event: DomainEvent) -> None:
        """Опубликовать событие.
        
        Args:
            event: Доменное событие для публикации
        """
        ...
    
    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Подписаться на тип события.
        
        Args:
            event_name: Имя события (например, "UserCreated")
            handler: Async функция-обработчик
        """
        ...
    
    async def start(self) -> None:
        """Запустить consumer (для внешних брокеров).
        
        Для InMemory — no-op.
        Для Redis/RabbitMQ — запускает consumer loop.
        """
        ...
    
    async def stop(self) -> None:
        """Остановить consumer и освободить ресурсы."""
        ...
```

### 5.2 InMemory Backend

```python
# src/Ship/Infrastructure/Events/Backends/InMemory.py
"""In-memory event bus для разработки и тестов."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Awaitable

import logfire

from src.Ship.Parents.Event import DomainEvent


EventHandler = Callable[..., Awaitable[None]]


@dataclass
class InMemoryEventBus:
    """In-memory event bus.
    
    Простейшая реализация для монолита и разработки.
    События доставляются синхронно в том же процессе.
    
    Characteristics:
        - ✅ Zero latency
        - ✅ No infrastructure needed
        - ❌ Single process only
        - ❌ Events lost on crash
    """
    
    _handlers: dict[str, list[EventHandler]] = field(
        default_factory=lambda: defaultdict(list)
    )
    
    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Подписать handler на событие."""
        self._handlers[event_name].append(handler)
        logfire.debug(f"📌 Subscribed to {event_name}", handler=handler.__name__)
    
    async def publish(self, event: DomainEvent) -> None:
        """Опубликовать событие всем подписчикам."""
        handlers = self._handlers.get(event.event_name, [])
        
        if not handlers:
            logfire.debug(f"📭 No handlers for {event.event_name}")
            return
        
        logfire.info(
            f"📤 Publishing {event.event_name}",
            handlers_count=len(handlers),
        )
        
        for handler in handlers:
            try:
                # Передаём данные события как kwargs
                await handler(**event.model_dump(mode="json"))
            except Exception as e:
                logfire.error(
                    f"❌ Handler failed for {event.event_name}",
                    handler=handler.__name__,
                    error=str(e),
                )
                # Не прерываем — продолжаем другие handlers
    
    async def start(self) -> None:
        """No-op для in-memory bus."""
        logfire.info("🟢 InMemory EventBus started")
    
    async def stop(self) -> None:
        """No-op для in-memory bus."""
        logfire.info("🔴 InMemory EventBus stopped")
```

### 5.3 Redis Streams Backend

```python
# src/Ship/Infrastructure/Events/Backends/RedisStreams.py
"""Redis Streams event bus для distributed систем."""

import asyncio
import json
import socket
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Awaitable

import logfire
from redis.asyncio import Redis

from src.Ship.Parents.Event import DomainEvent


EventHandler = Callable[..., Awaitable[None]]


@dataclass
class RedisStreamsEventBus:
    """Redis Streams event bus.
    
    Использует Redis Streams для надёжной доставки событий
    между несколькими инстансами/процессами.
    
    Features:
        - Consumer Groups: несколько consumers читают из одного стрима
        - ACK: событие удаляется только после подтверждения обработки
        - Persistence: события сохраняются в Redis
        - Replay: можно перечитать необработанные события
    
    Characteristics:
        - ✅ Multiple processes/instances
        - ✅ Persistence (configurable)
        - ✅ Consumer groups
        - ❌ No built-in DLQ (needs manual handling)
    """
    
    redis_url: str
    consumer_group: str = "default-group"
    consumer_name: str = field(default_factory=lambda: f"consumer-{socket.gethostname()}")
    stream_max_len: int = 10000  # Максимум событий в стриме
    
    _handlers: dict[str, list[EventHandler]] = field(
        default_factory=lambda: defaultdict(list)
    )
    _redis: Redis | None = field(default=None, init=False)
    _running: bool = field(default=False, init=False)
    _consumer_task: asyncio.Task | None = field(default=None, init=False)
    
    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Подписать handler на событие."""
        self._handlers[event_name].append(handler)
        logfire.debug(
            f"📌 Subscribed to {event_name}",
            handler=handler.__name__,
            consumer_group=self.consumer_group,
        )
    
    async def publish(self, event: DomainEvent) -> None:
        """Опубликовать событие в Redis Stream."""
        if self._redis is None:
            self._redis = Redis.from_url(self.redis_url)
        
        stream_name = f"events:{event.event_name}"
        
        # Добавляем в стрим с ограничением размера
        message_id = await self._redis.xadd(
            stream_name,
            {
                "payload": event.model_dump_json(),
                "event_name": event.event_name,
                "occurred_at": event.occurred_at.isoformat(),
            },
            maxlen=self.stream_max_len,
        )
        
        logfire.info(
            f"📤 Published {event.event_name} to Redis",
            stream=stream_name,
            message_id=message_id.decode() if message_id else None,
        )
    
    async def start(self) -> None:
        """Запустить consumer loop."""
        self._redis = Redis.from_url(self.redis_url)
        self._running = True
        
        # Создаём consumer groups для каждого типа события
        for event_name in self._handlers.keys():
            stream_name = f"events:{event_name}"
            try:
                await self._redis.xgroup_create(
                    stream_name,
                    self.consumer_group,
                    id="0",      # Читать с начала
                    mkstream=True,  # Создать стрим если нет
                )
                logfire.debug(f"Created consumer group for {stream_name}")
            except Exception as e:
                # Группа уже существует — это ок
                if "BUSYGROUP" not in str(e):
                    logfire.warning(f"Failed to create group: {e}")
        
        # Запускаем consumer в фоне
        self._consumer_task = asyncio.create_task(
            self._consume_loop(),
            name="redis-event-consumer",
        )
        
        logfire.info(
            "🟢 Redis Streams EventBus started",
            consumer_group=self.consumer_group,
            consumer_name=self.consumer_name,
            subscriptions=list(self._handlers.keys()),
        )
    
    async def stop(self) -> None:
        """Остановить consumer и закрыть соединение."""
        self._running = False
        
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        
        if self._redis:
            await self._redis.close()
        
        logfire.info("🔴 Redis Streams EventBus stopped")
    
    async def _consume_loop(self) -> None:
        """Основной цикл чтения событий."""
        while self._running:
            try:
                await self._consume_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logfire.error("Consumer loop error", error=str(e))
                await asyncio.sleep(1)  # Backoff при ошибках
    
    async def _consume_batch(self) -> None:
        """Прочитать и обработать batch событий."""
        if not self._handlers:
            await asyncio.sleep(1)
            return
        
        # Формируем список стримов для чтения
        streams = {
            f"events:{event_name}": ">"  # ">" = новые сообщения
            for event_name in self._handlers.keys()
        }
        
        # Читаем события с блокировкой
        results = await self._redis.xreadgroup(
            groupname=self.consumer_group,
            consumername=self.consumer_name,
            streams=streams,
            count=10,        # Batch size
            block=5000,      # Блокировать 5 секунд если нет событий
        )
        
        # Обрабатываем полученные события
        for stream_name, messages in results:
            event_name = stream_name.decode().replace("events:", "")
            
            for message_id, data in messages:
                await self._process_message(
                    stream_name=stream_name,
                    message_id=message_id,
                    data=data,
                    event_name=event_name,
                )
    
    async def _process_message(
        self,
        stream_name: bytes,
        message_id: bytes,
        data: dict[bytes, bytes],
        event_name: str,
    ) -> None:
        """Обработать одно сообщение."""
        try:
            # Декодируем payload
            payload_raw = data.get(b"payload", b"{}")
            payload = json.loads(payload_raw.decode())
            
            logfire.info(
                f"📥 Processing {event_name}",
                message_id=message_id.decode(),
            )
            
            # Вызываем все handlers для этого события
            handlers = self._handlers.get(event_name, [])
            for handler in handlers:
                try:
                    await handler(**payload)
                except Exception as e:
                    logfire.error(
                        f"Handler failed: {handler.__name__}",
                        event=event_name,
                        error=str(e),
                    )
            
            # ACK сообщения (удаляем из pending)
            await self._redis.xack(
                stream_name,
                self.consumer_group,
                message_id,
            )
            
        except Exception as e:
            logfire.error(
                f"Failed to process message",
                event=event_name,
                message_id=message_id.decode(),
                error=str(e),
            )
            # Не делаем ACK — сообщение останется в pending
            # и будет переобработано или попадёт в claim
```

### 5.4 RabbitMQ Backend

```python
# src/Ship/Infrastructure/Events/Backends/RabbitMQ.py
"""RabbitMQ event bus для production систем."""

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Awaitable

import logfire

try:
    import aio_pika
    from aio_pika import ExchangeType, Message, IncomingMessage
    HAS_RABBITMQ = True
except ImportError:
    HAS_RABBITMQ = False

from src.Ship.Parents.Event import DomainEvent


EventHandler = Callable[..., Awaitable[None]]


@dataclass
class RabbitMQEventBus:
    """RabbitMQ event bus.
    
    Production-grade брокер с полной поддержкой:
    - Dead Letter Queues
    - Message routing
    - Delivery guarantees
    - Management UI
    
    Requires: aio-pika (`uv add aio-pika`)
    
    Characteristics:
        - ✅ Full reliability
        - ✅ Dead Letter Queues
        - ✅ Complex routing
        - ✅ Message priorities
        - ❌ Additional infrastructure
    """
    
    amqp_url: str
    exchange_name: str = "domain_events"
    queue_prefix: str = "q"
    
    _handlers: dict[str, list[EventHandler]] = field(
        default_factory=lambda: defaultdict(list)
    )
    _connection: "aio_pika.Connection | None" = field(default=None, init=False)
    _channel: "aio_pika.Channel | None" = field(default=None, init=False)
    _exchange: "aio_pika.Exchange | None" = field(default=None, init=False)
    
    def __post_init__(self):
        if not HAS_RABBITMQ:
            raise ImportError(
                "aio-pika is required for RabbitMQ backend. "
                "Install with: uv add aio-pika"
            )
    
    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Подписать handler на событие."""
        self._handlers[event_name].append(handler)
        logfire.debug(f"📌 Subscribed to {event_name}", handler=handler.__name__)
    
    async def publish(self, event: DomainEvent) -> None:
        """Опубликовать событие в RabbitMQ."""
        if self._exchange is None:
            await self._ensure_connected()
        
        message = Message(
            body=event.model_dump_json().encode(),
            content_type="application/json",
            headers={
                "event_name": event.event_name,
                "occurred_at": event.occurred_at.isoformat(),
            },
        )
        
        await self._exchange.publish(
            message,
            routing_key=event.event_name,
        )
        
        logfire.info(
            f"📤 Published {event.event_name} to RabbitMQ",
            exchange=self.exchange_name,
            routing_key=event.event_name,
        )
    
    async def start(self) -> None:
        """Запустить consumers для всех подписок."""
        await self._ensure_connected()
        
        for event_name, handlers in self._handlers.items():
            queue_name = f"{self.queue_prefix}.{event_name}"
            
            # Создаём очередь
            queue = await self._channel.declare_queue(
                queue_name,
                durable=True,  # Очередь переживает рестарт
            )
            
            # Привязываем к exchange
            await queue.bind(
                self._exchange,
                routing_key=event_name,
            )
            
            # Создаём consumer
            async def make_consumer(handlers_list: list[EventHandler]):
                async def on_message(message: IncomingMessage):
                    async with message.process():  # Auto-ACK on success
                        payload = json.loads(message.body.decode())
                        for handler in handlers_list:
                            try:
                                await handler(**payload)
                            except Exception as e:
                                logfire.error(
                                    f"Handler failed",
                                    handler=handler.__name__,
                                    error=str(e),
                                )
                return on_message
            
            await queue.consume(await make_consumer(handlers))
            logfire.debug(f"Started consumer for {queue_name}")
        
        logfire.info(
            "🟢 RabbitMQ EventBus started",
            exchange=self.exchange_name,
            subscriptions=list(self._handlers.keys()),
        )
    
    async def stop(self) -> None:
        """Закрыть соединение."""
        if self._connection:
            await self._connection.close()
        logfire.info("🔴 RabbitMQ EventBus stopped")
    
    async def _ensure_connected(self) -> None:
        """Убедиться, что соединение установлено."""
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self.amqp_url)
            self._channel = await self._connection.channel()
            
            # Создаём exchange типа TOPIC для routing
            self._exchange = await self._channel.declare_exchange(
                self.exchange_name,
                ExchangeType.TOPIC,
                durable=True,
            )
            
            logfire.debug("Connected to RabbitMQ")
```

### 5.5 Factory

```python
# src/Ship/Infrastructure/Events/Factory.py
"""Factory для создания EventBus по конфигурации."""

from typing import Literal

from src.Ship.Configs import get_settings
from src.Ship.Infrastructure.Events.Protocol import EventBus


EventBusBackend = Literal["memory", "redis", "redis-pubsub", "rabbitmq"]


def create_event_bus(backend: EventBusBackend | None = None) -> EventBus:
    """Создать EventBus на основе конфигурации.
    
    Args:
        backend: Явное указание бэкенда. Если None — берётся из Settings.
    
    Returns:
        Реализация EventBus
    
    Example:
        # Автоматически по конфигу
        event_bus = create_event_bus()
        
        # Явно указать бэкенд
        event_bus = create_event_bus("redis")
    """
    settings = get_settings()
    
    # Определяем бэкенд
    backend = backend or getattr(settings, "event_bus_backend", "memory")
    
    match backend:
        case "memory":
            from src.Ship.Infrastructure.Events.Backends.InMemory import (
                InMemoryEventBus
            )
            return InMemoryEventBus()
        
        case "redis":
            from src.Ship.Infrastructure.Events.Backends.RedisStreams import (
                RedisStreamsEventBus
            )
            return RedisStreamsEventBus(
                redis_url=settings.redis_url,
                consumer_group=f"{settings.app_name}-events",
            )
        
        case "rabbitmq":
            from src.Ship.Infrastructure.Events.Backends.RabbitMQ import (
                RabbitMQEventBus
            )
            return RabbitMQEventBus(
                amqp_url=getattr(settings, "amqp_url", "amqp://guest:guest@localhost/"),
            )
        
        case _:
            # Fallback на in-memory
            from src.Ship.Infrastructure.Events.Backends.InMemory import (
                InMemoryEventBus
            )
            return InMemoryEventBus()
```

---

## 6. Интеграция с UnitOfWork

### 6.1 Модифицированный UoW

```python
# В BaseUnitOfWork добавляем поддержку EventBus

@dataclass
class BaseUnitOfWork:
    """Unit of Work с поддержкой Unified EventBus."""
    
    # Новое: EventBus вместо _emit
    _event_bus: "EventBus | None" = field(default=None, repr=False)
    
    # Старое: для совместимости с litestar.events
    _emit: "EventEmitterFunc | None" = field(default=None, repr=False)
    
    # Остальные поля без изменений
    _events: list["DomainEvent"] = field(default_factory=list, init=False)
    _committed: bool = field(default=False, init=False)
    _transaction: object | None = field(default=None, init=False)
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # ... существующая логика транзакции ...
        
        # После успешного коммита публикуем события
        if exc_type is None and self._committed:
            await self._publish_events()
        
        self._events.clear()
        self._committed = False
    
    async def _publish_events(self) -> None:
        """Опубликовать накопленные события."""
        for event in self._events:
            # Приоритет: EventBus → litestar.events → log only
            if self._event_bus is not None:
                await self._event_bus.publish(event)
            elif self._emit is not None:
                self._emit(event.event_name, **event.model_dump(mode="json"))
            else:
                import logfire
                logfire.info(
                    f"📤 Event (no bus): {event.event_name}",
                    event_data=event.model_dump(mode="json"),
                )
```

### 6.2 Provider для EventBus

```python
# src/Ship/Providers/AppProvider.py

from dishka import Provider, Scope, provide
from litestar import Request

from src.Ship.Infrastructure.Events.Protocol import EventBus


class AppProvider(Provider):
    """Application-level providers."""
    
    @provide(scope=Scope.APP)
    def provide_event_bus(self) -> EventBus:
        """Создать EventBus (singleton на уровне приложения)."""
        from src.Ship.Infrastructure.Events.Factory import create_event_bus
        return create_event_bus()
```

---

## 7. Декоратор @subscribe

### 7.1 Реализация

```python
# src/Ship/Infrastructure/Events/Decorators.py
"""Декоратор @subscribe для подписки на события."""

from functools import wraps
from typing import Callable, Awaitable

import logfire


# Глобальный реестр подписок
# Заполняется при импорте модулей с handlers
_SUBSCRIPTIONS: list[tuple[str, Callable[..., Awaitable[None]]]] = []


def subscribe(event_name: str):
    """Декоратор для подписки функции на событие.
    
    Альтернатива litestar @listener с поддержкой Unified EventBus.
    
    Example:
        @subscribe("UserCreated")
        async def handle_user_created(user_id: str, email: str, **kwargs):
            await index_user(user_id, email)
        
        @subscribe("UserDeleted")
        async def handle_user_deleted(user_id: str, **kwargs):
            await remove_from_index(user_id)
    
    Note:
        Декоратор регистрирует handler в глобальном реестре.
        Реестр используется при инициализации EventBus в lifespan.
    """
    def decorator(func: Callable[..., Awaitable[None]]):
        # Регистрируем в глобальном реестре
        _SUBSCRIPTIONS.append((event_name, func))
        
        logfire.debug(
            f"Registered subscription",
            event=event_name,
            handler=func.__name__,
        )
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Сохраняем метаданные
        wrapper._event_name = event_name
        wrapper._is_event_handler = True
        
        return wrapper
    
    return decorator


def get_all_subscriptions() -> list[tuple[str, Callable[..., Awaitable[None]]]]:
    """Получить все зарегистрированные подписки.
    
    Используется в lifespan для регистрации handlers в EventBus.
    
    Returns:
        Список кортежей (event_name, handler_function)
    """
    return _SUBSCRIPTIONS.copy()


def clear_subscriptions() -> None:
    """Очистить реестр подписок (для тестов)."""
    _SUBSCRIPTIONS.clear()
```

### 7.2 Использование в Listeners

```python
# src/Containers/AppSection/SearchModule/Listeners.py
"""SearchModule event handlers."""

import logfire
from src.Ship.Infrastructure.Events.Decorators import subscribe
from src.Containers.AppSection.SearchModule.Tasks.IndexEntityTask import (
    IndexEntityTask,
    IndexableEntity,
    RemoveFromIndexTask,
)


@subscribe("UserCreated")
async def on_user_created_index(
    user_id: str,
    email: str,
    name: str,
    **kwargs,  # Всегда принимаем **kwargs для совместимости
) -> None:
    """Индексировать нового пользователя."""
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


@subscribe("UserUpdated")
async def on_user_updated_index(user_id: str, **kwargs) -> None:
    """Переиндексировать обновлённого пользователя."""
    logfire.info("🔄 Re-indexing user", user_id=user_id)
    # В реальности: загрузить и переиндексировать


@subscribe("UserDeleted")
async def on_user_deleted_index(user_id: str, **kwargs) -> None:
    """Удалить пользователя из индекса."""
    logfire.info("🗑️ Removing user from index", user_id=user_id)
    
    task = RemoveFromIndexTask()
    await task.run(("User", user_id))
```

---

## 8. Конфигурация

### 8.1 Settings

```python
# src/Ship/Configs/Settings.py (добавить поля)

from typing import Literal


class Settings(BaseSettings):
    # ... existing fields ...
    
    # ═══════════════════════════════════════════════════════════════
    # Event Bus Configuration
    # ═══════════════════════════════════════════════════════════════
    
    event_bus_backend: Literal["memory", "redis", "rabbitmq"] = Field(
        default="memory",
        description="Event bus backend: memory (dev), redis (distributed), rabbitmq (prod)",
    )
    
    # RabbitMQ (если используется)
    amqp_url: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        description="RabbitMQ AMQP URL",
    )
```

### 8.2 Примеры конфигурации

```bash
# .env для разработки
EVENT_BUS_BACKEND=memory

# .env для staging (несколько инстансов)
EVENT_BUS_BACKEND=redis
REDIS_URL=redis://redis:6379/0

# .env для production
EVENT_BUS_BACKEND=rabbitmq
AMQP_URL=amqp://user:password@rabbitmq:5672/events
```

### 8.3 docker-compose для разных окружений

```yaml
# docker-compose.dev.yml (memory, ничего не нужно)
services:
  app:
    environment:
      - EVENT_BUS_BACKEND=memory

# docker-compose.staging.yml (redis)
services:
  app:
    environment:
      - EVENT_BUS_BACKEND=redis
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine

# docker-compose.prod.yml (rabbitmq)
services:
  app:
    environment:
      - EVENT_BUS_BACKEND=rabbitmq
      - AMQP_URL=amqp://user:pass@rabbitmq:5672/
    depends_on:
      - rabbitmq
  
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "15672:15672"  # Management UI
```

---

## 9. Transactional Outbox

### 9.1 Проблема Dual Write

```
┌─────────────────────────────────────────────────────────────────────┐
│ ❌ ПРОБЛЕМА: Dual Write                                              │
│                                                                     │
│   async with uow:                                                   │
│       await uow.users.add(user)                                    │
│       await uow.commit()         # 1. Коммит в БД ✅               │
│                                                                     │
│   # --- ПРОЦЕСС УПАЛ ЗДЕСЬ ---                                     │
│                                                                     │
│   await event_bus.publish(...)   # 2. Публикация ❌ НЕ ПРОИЗОШЛА   │
│                                                                     │
│   Результат:                                                        │
│   • Пользователь создан в БД                                       │
│   • Событие НЕ отправлено                                          │
│   • SearchService НЕ проиндексировал                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Решение: Outbox Pattern

```
┌─────────────────────────────────────────────────────────────────────┐
│ ✅ РЕШЕНИЕ: Transactional Outbox                                     │
│                                                                     │
│   ОДНА ТРАНЗАКЦИЯ:                                                  │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ async with uow:                                               │ │
│   │     await uow.users.add(user)           # Данные             │ │
│   │     await uow.outbox.add(UserCreated)   # Событие в outbox   │ │
│   │     await uow.commit()                  # ОБА атомарно       │ │
│   └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│   ОТДЕЛЬНЫЙ WORKER:                                                 │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ while True:                                                   │ │
│   │     events = SELECT * FROM outbox WHERE published = false   │ │
│   │     for event in events:                                      │ │
│   │         await event_bus.publish(event)                       │ │
│   │         UPDATE outbox SET published = true                   │ │
│   │     await sleep(1)                                            │ │
│   └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│   Гарантия: Если данные есть → событие БУДЕТ доставлено           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.3 Модель Outbox

```python
# src/Ship/Infrastructure/Events/Outbox.py
"""Transactional Outbox для надёжной доставки событий."""

from datetime import datetime
from uuid import UUID

from piccolo.table import Table
from piccolo.columns import UUID as UUIDColumn, Varchar, Text, Timestamptz, Boolean
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.defaults.timestamptz import TimestamptzNow


class OutboxEvent(Table, tablename="outbox_events"):
    """Таблица Outbox для событий.
    
    События записываются сюда в той же транзакции, что и бизнес-данные.
    Отдельный worker читает и публикует в брокер.
    
    Schema:
        id: UUID события (используется для идемпотентности)
        event_name: Имя события (UserCreated, OrderCompleted)
        event_version: Версия схемы события
        payload: JSON с данными события
        occurred_at: Когда событие произошло
        published: Опубликовано ли в брокер
        published_at: Когда опубликовано
        retries: Количество попыток публикации
    """
    
    id = UUIDColumn(primary_key=True, default=UUID4())
    event_name = Varchar(length=255, index=True)
    event_version = Varchar(length=10, default="v1")
    payload = Text()  # JSON
    occurred_at = Timestamptz(default=TimestamptzNow())
    published = Boolean(default=False, index=True)
    published_at = Timestamptz(null=True, default=None)
    retries = Integer(default=0)
    last_error = Text(null=True, default=None)
```

### 9.4 Outbox Publisher Worker

```python
# src/Ship/Infrastructure/Events/OutboxPublisher.py
"""Worker для публикации событий из Outbox."""

import asyncio
import json
from datetime import datetime

import logfire

from src.Ship.Infrastructure.Events.Outbox import OutboxEvent
from src.Ship.Infrastructure.Events.Protocol import EventBus
from src.Ship.Parents.Event import DomainEvent


class OutboxPublisher:
    """Публикует события из Outbox в EventBus.
    
    Запускается как фоновый процесс или TaskIQ task.
    Гарантирует at-least-once доставку.
    
    Example:
        publisher = OutboxPublisher(event_bus, batch_size=100)
        await publisher.run()  # Бесконечный цикл
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        batch_size: int = 100,
        poll_interval: float = 1.0,
        max_retries: int = 5,
    ):
        self.event_bus = event_bus
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self._running = False
    
    async def run(self) -> None:
        """Основной цикл публикации."""
        self._running = True
        logfire.info("📤 Outbox Publisher started")
        
        while self._running:
            try:
                published = await self._publish_batch()
                if published == 0:
                    await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logfire.error("Outbox Publisher error", error=str(e))
                await asyncio.sleep(self.poll_interval)
    
    async def stop(self) -> None:
        """Остановить publisher."""
        self._running = False
    
    async def _publish_batch(self) -> int:
        """Опубликовать batch событий.
        
        Returns:
            Количество опубликованных событий
        """
        # Получаем неопубликованные события
        events = await OutboxEvent.select().where(
            (OutboxEvent.published == False) &
            (OutboxEvent.retries < self.max_retries)
        ).order_by(
            OutboxEvent.occurred_at
        ).limit(
            self.batch_size
        ).run()
        
        if not events:
            return 0
        
        published_count = 0
        
        for event_row in events:
            try:
                # Восстанавливаем событие
                payload = json.loads(event_row["payload"])
                
                # Публикуем через EventBus
                # Создаём временный DomainEvent для публикации
                event = type(
                    event_row["event_name"],
                    (DomainEvent,),
                    {
                        "event_name": event_row["event_name"],
                        **payload,
                    }
                )()
                
                await self.event_bus.publish(event)
                
                # Помечаем как опубликованное
                await OutboxEvent.update({
                    OutboxEvent.published: True,
                    OutboxEvent.published_at: datetime.utcnow(),
                }).where(
                    OutboxEvent.id == event_row["id"]
                ).run()
                
                published_count += 1
                
            except Exception as e:
                logfire.error(
                    "Failed to publish outbox event",
                    event_id=str(event_row["id"]),
                    error=str(e),
                )
                
                # Увеличиваем счётчик retries
                await OutboxEvent.update({
                    OutboxEvent.retries: OutboxEvent.retries + 1,
                    OutboxEvent.last_error: str(e),
                }).where(
                    OutboxEvent.id == event_row["id"]
                ).run()
        
        if published_count > 0:
            logfire.info(f"Published {published_count} outbox events")
        
        return published_count
```

---

## 10. Примеры использования

### 10.1 Полный пример: Action → Event → Handler

```python
# 1. Action публикует событие
# src/Containers/AppSection/UserModule/Actions/CreateUserAction.py

@dataclass
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    uow: UserUnitOfWork
    hash_password: HashPasswordTask
    
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        # Проверки...
        
        async with self.uow:
            user = AppUser(
                email=data.email,
                password_hash=await self._hash(data.password),
                name=data.name,
            )
            await self.uow.users.add(user)
            
            # Добавляем событие — будет опубликовано после commit
            self.uow.add_event(UserCreated(
                user_id=str(user.id),
                email=user.email,
                name=user.name,
            ))
            
            await self.uow.commit()
        
        return Success(user)


# 2. Handler обрабатывает событие
# src/Containers/AppSection/SearchModule/Listeners.py

@subscribe("UserCreated")
async def on_user_created_index(
    user_id: str,
    email: str,
    name: str,
    **kwargs,
) -> None:
    """Индексировать нового пользователя."""
    task = IndexEntityTask()
    await task.run(IndexableEntity(
        entity_type="User",
        entity_id=user_id,
        title=name,
        content=f"{name} ({email})",
    ))


# 3. App.py инициализирует EventBus
# src/App.py

@asynccontextmanager
async def lifespan(app: Litestar):
    # Создаём EventBus
    event_bus = create_event_bus()
    
    # Регистрируем подписки
    for event_name, handler in get_all_subscriptions():
        event_bus.subscribe(event_name, handler)
    
    # Запускаем consumer
    await event_bus.start()
    app.state.event_bus = event_bus
    
    yield
    
    await event_bus.stop()
```

### 10.2 Тестирование с InMemory

```python
# tests/unit/test_user_events.py

import pytest
from src.Ship.Infrastructure.Events.Backends.InMemory import InMemoryEventBus
from src.Containers.AppSection.UserModule.Events import UserCreated


@pytest.fixture
def event_bus():
    return InMemoryEventBus()


async def test_user_created_triggers_indexing(event_bus):
    """Проверить, что UserCreated вызывает индексацию."""
    indexed_users = []
    
    @event_bus.subscribe("UserCreated")
    async def mock_handler(user_id: str, **kwargs):
        indexed_users.append(user_id)
    
    # Публикуем событие
    await event_bus.publish(UserCreated(
        user_id="123",
        email="test@example.com",
        name="Test User",
    ))
    
    # Проверяем
    assert "123" in indexed_users
```

---

## 11. Миграция с litestar.events

### 11.1 Пошаговая миграция

```markdown
## Checklist миграции на Unified EventBus

### Шаг 1: Добавить инфраструктуру
- [ ] Создать `src/Ship/Infrastructure/Events/`
- [ ] Добавить Protocol, Factory, Decorators
- [ ] Добавить InMemory backend

### Шаг 2: Обновить Settings
- [ ] Добавить `event_bus_backend` в Settings
- [ ] Добавить `amqp_url` (если нужен RabbitMQ)

### Шаг 3: Обновить UnitOfWork
- [ ] Добавить поле `_event_bus: EventBus | None`
- [ ] Обновить `_publish_events()` для поддержки EventBus

### Шаг 4: Обновить App.py
- [ ] Добавить инициализацию EventBus в lifespan
- [ ] Зарегистрировать подписки

### Шаг 5: Мигрировать Listeners
- [ ] Заменить `@listener` на `@subscribe`
- [ ] Убедиться, что все handlers принимают `**kwargs`

### Шаг 6: Обновить Providers
- [ ] Добавить EventBus в UserUnitOfWork и др.

### Шаг 7: Тестирование
- [ ] Проверить с `EVENT_BUS_BACKEND=memory`
- [ ] Проверить с `EVENT_BUS_BACKEND=redis`
```

### 11.2 Совместимость

На переходный период можно поддерживать оба варианта:

```python
# UoW поддерживает и старый, и новый способ
async def _publish_events(self) -> None:
    for event in self._events:
        # Новый способ: EventBus
        if self._event_bus is not None:
            await self._event_bus.publish(event)
        
        # Старый способ: litestar.events (для совместимости)
        elif self._emit is not None:
            self._emit(event.event_name, **event.model_dump(mode="json"))
```

---

## 12. FAQ

### Q: Можно ли использовать и litestar.events, и EventBus одновременно?

**A:** Да, на переходный период. UoW проверяет наличие `_event_bus` первым, затем `_emit`. Это позволяет мигрировать постепенно.

---

### Q: Что выбрать: Redis Streams или RabbitMQ?

**A:** 
- **Redis Streams** — если Redis уже есть и достаточно at-least-once с ручным DLQ
- **RabbitMQ** — если нужны DLQ, сложный routing, приоритеты, management UI

---

### Q: Как гарантировать exactly-once обработку?

**A:** EventBus гарантирует at-least-once. Для exactly-once нужна **идемпотентность handlers**:

```python
@subscribe("PaymentCreated")
async def handle_payment(payment_id: str, **kwargs):
    # Проверяем, обрабатывали ли уже
    if await redis.get(f"processed:payment:{payment_id}"):
        return  # Уже обработали
    
    await process_payment(payment_id)
    
    # Помечаем как обработанное
    await redis.set(f"processed:payment:{payment_id}", "1", ex=86400 * 7)
```

---

### Q: Нужен ли Outbox для InMemory?

**A:** Нет. Outbox нужен только при использовании внешнего брокера (Redis/RabbitMQ) для гарантии доставки.

---

### Q: Как мониторить события?

**A:** 
1. **Logfire** автоматически логирует publish/consume
2. **Redis**: `XINFO STREAM events:UserCreated`
3. **RabbitMQ**: Management UI на порту 15672

---

## 📚 Связанная документация

- [13-cross-module-communication.md](13-cross-module-communication.md) — Event-Driven архитектура
- [14-future-roadmap-and-patterns.md](14-future-roadmap-and-patterns.md) — Outbox, Idempotency
- [17-microservice-extraction-guide.md](17-microservice-extraction-guide.md) — Вынос в микросервисы

---

<div align="center">

**Hyper-Porto v4.3**

*Unified Event Bus — один интерфейс, любой бэкенд*

🔌 Memory → Redis → RabbitMQ → Kafka

</div>


