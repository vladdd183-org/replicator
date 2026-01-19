# 🏛️ Architecture Decision Records (ADRs)

> Почему выбраны именно эти технологии и подходы. Детали: [`docs/08-libraries.md`](../../../docs/08-libraries.md)

---

## ADR-001: Litestar вместо FastAPI

### Контекст
Нужен современный ASGI фреймворк для REST API, GraphQL, WebSocket, CLI.

### Решение
**Litestar** (не FastAPI)

### Причины

| Аспект | FastAPI | Litestar |
|--------|---------|----------|
| DTO | Pydantic-only | Pydantic, dataclass, msgspec |
| Dependency Injection | Depends() | Лучше интеграция с Dishka |
| WebSocket | Базовый | Channels Plugin (pub/sub) |
| CLI | Нет | CLIPlugin (Click) |
| OpenAPI | Swagger UI | Scalar + Swagger + ReDoc |
| Events | Нет | Встроенный EventEmitter |
| Background Tasks | BackgroundTasks | TaskIQ интеграция |

### Последствия
- ✅ Единый фреймворк для HTTP, WebSocket, CLI, GraphQL
- ✅ Встроенные Events для Domain Events
- ✅ Лучшая интеграция с Dishka DI
- ⚠️ Меньше community, меньше примеров

---

## ADR-002: Piccolo вместо SQLAlchemy

### Контекст
Нужен async ORM с миграциями и хорошей типизацией.

### Решение
**Piccolo ORM** (не SQLAlchemy)

### Причины

| Аспект | SQLAlchemy | Piccolo |
|--------|------------|---------|
| Async | Добавлено в 2.0, сложно | Native async |
| Миграции | Alembic (отдельно) | Встроенные |
| Типизация | Сложная | Простая, mypy-friendly |
| Query API | Verbose | Pythonic |
| Litestar | Через плагин | Нативная интеграция (DTO) |
| Learning curve | Высокая | Низкая |

### Последствия
- ✅ Простой async API
- ✅ Встроенные миграции
- ✅ Лучшая типизация
- ⚠️ Меньше фич чем SQLAlchemy
- ⚠️ Меньше community

---

## ADR-003: Dishka вместо dependency-injector

### Контекст
Нужен DI фреймворк с поддержкой async и scopes.

### Решение
**Dishka** (не dependency-injector, не FastAPI Depends)

### Причины

| Аспект | dependency-injector | Dishka |
|--------|---------------------|--------|
| Async | Добавлено, но awkward | Native |
| Scopes | Есть | APP, REQUEST, SESSION |
| Type hints | Частично | Полная поддержка |
| Litestar | Нет интеграции | Официальная интеграция |
| Auto-wiring | Manual | По type hints |

### Последствия
- ✅ Чистый DI через type hints
- ✅ Scoped providers (APP vs REQUEST)
- ✅ Официальная интеграция с Litestar
- ⚠️ Молодая библиотека

---

## ADR-004: returns вместо собственного Result

### Контекст
Нужен Result type для Railway-Oriented Programming.

### Решение
**returns** библиотека (не свой Result класс)

### Причины

| Аспект | Свой Result | returns |
|--------|-------------|---------|
| Функционал | Базовый | Result, Maybe, IO, Future |
| Композиция | Нет | flow, bind, pipe |
| mypy | Ручная типизация | mypy plugin |
| Тестирование | Ручное | pytest plugin |
| Документация | Нет | Обширная |

### Последствия
- ✅ Проверенная реализация
- ✅ mypy plugin для type inference
- ✅ Композиция через flow/bind
- ✅ Не изобретаем велосипед

---

## ADR-005: anyio вместо чистого asyncio

### Контекст
Нужен async runtime с Structured Concurrency.

### Решение
**anyio** (не чистый asyncio)

### Причины

| Аспект | asyncio | anyio |
|--------|---------|-------|
| TaskGroups | Python 3.11+ | Любая версия |
| Cancellation | Manual | Автоматическая |
| Fire-and-forget | create_task() | Запрещено by design |
| Backend | asyncio only | asyncio + trio |
| Thread offload | run_in_executor | to_thread.run_sync |

### Последствия
- ✅ Structured Concurrency из коробки
- ✅ Безопасная отмена задач
- ✅ Нет "забытых" задач
- ⚠️ Дополнительная зависимость

---

## ADR-006: Pydantic для ВСЕХ DTO

### Контекст
Нужен единый способ определения DTO (Request, Response, Errors).

### Решение
**Pydantic BaseModel** везде (не dataclass, не TypedDict)

### Причины

| Аспект | dataclass | Pydantic |
|--------|-----------|----------|
| Валидация | Нет | Встроенная |
| Serialization | Ручная | Встроенная |
| Coercion | Нет | Автоматическая |
| Nested | Сложно | Просто |
| Litestar | Поддержка | Первоклассная |
| OpenAPI | Manual | Автоматическая |

### Последствия
- ✅ Валидация из коробки
- ✅ Автоматический OpenAPI
- ✅ Единообразие кода
- ⚠️ Runtime overhead (минимальный)

---

## ADR-007: litestar.events вместо своего EventBus

### Контекст
Нужен механизм публикации Domain Events.

### Решение
**litestar.events** + UnitOfWork (не свой EventBus/MessageBus)

### Причины

| Аспект | Свой EventBus | litestar.events |
|--------|---------------|-----------------|
| Реализация | Нужно писать | Встроено |
| Async | Нужно писать | Есть |
| Integration | Manual | Нативная |
| Listeners | Manual | @listener декоратор |

### Последствия
- ✅ Нет своего кода для EventBus
- ✅ Нативная интеграция
- ✅ @listener декоратор
- ⚠️ Привязка к Litestar (но мы и так на нём)

---

## ADR-008: TaskIQ вместо Celery

### Контекст
Нужна очередь задач для background processing.

### Решение
**TaskIQ** (не Celery)

### Причины

| Аспект | Celery | TaskIQ |
|--------|--------|--------|
| Async | Gevent/eventlet | Native asyncio |
| Setup | Сложный | Простой |
| Litestar | Нет интеграции | taskiq-litestar |
| Type hints | Нет | Полные |
| Broker | RabbitMQ, Redis | Redis, in-memory |

### Последствия
- ✅ Native async
- ✅ Простая интеграция с Litestar
- ✅ Type hints
- ⚠️ Меньше фич чем Celery
- ⚠️ Меньше production опыта

---

## ADR-009: Strawberry вместо Graphene

### Контекст
Нужен GraphQL фреймворк с хорошей типизацией.

### Решение
**Strawberry** (не Graphene, не Ariadne)

### Причины

| Аспект | Graphene | Strawberry |
|--------|----------|------------|
| Типизация | Слабая | dataclass-based |
| Litestar | Плагин | Нативная интеграция |
| Code-first | Да | Да |
| Federation | Сложно | Встроено |
| Async | Добавлено | Native |

### Последствия
- ✅ Type-safe resolvers
- ✅ Нативная интеграция с Litestar
- ✅ Modern API
- ⚠️ Меньше community чем Graphene

---

## 📊 Сводная таблица решений

| Категория | Выбор | Альтернативы | Причина |
|-----------|-------|--------------|---------|
| Web Framework | **Litestar** | FastAPI, Starlette | Events, CLI, DI |
| ORM | **Piccolo** | SQLAlchemy, Tortoise | Native async, migrations |
| DI | **Dishka** | dependency-injector | Scopes, type hints |
| Result | **returns** | Свой Result | Проверенная реализация |
| Async | **anyio** | asyncio | Structured Concurrency |
| Validation | **Pydantic** | dataclass, attrs | Валидация, OpenAPI |
| Events | **litestar.events** | Свой EventBus | Нативная интеграция |
| Tasks | **TaskIQ** | Celery, Dramatiq | Native async, Litestar |
| GraphQL | **Strawberry** | Graphene, Ariadne | Type safety, Litestar |

---

## 📚 Дополнительно

- **Библиотеки:** [`docs/08-libraries.md`](../../../docs/08-libraries.md)
- **Tech Stack:** [`standards/global/tech-stack.md`](../global/tech-stack.md)
- **Философия:** [`docs/00-philosophy.md`](../../../docs/00-philosophy.md)



