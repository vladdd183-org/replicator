# 📚 Библиотеки и зависимости

> **Версия:** 4.3 | **Дата:** Январь 2026  
> Полный стек технологий Hyper-Porto с обоснованием выбора

---

## 🎯 Принцип выбора

```
Используй проверенные библиотеки вместо изобретения велосипедов.
Каждая зависимость должна решать конкретную проблему.
```

---

## 📦 Основные зависимости

### Web Framework

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **litestar[standard]** | ≥2.12.0 | ASGI фреймворк |
| **uvicorn[standard]** | ≥0.32.0 | ASGI сервер |

**Почему Litestar:**
- Современный ASGI фреймворк с отличной производительностью
- Встроенные: OpenAPI, CORS, Middleware, Guards
- Channels для WebSocket Pub/Sub
- CLIPlugin для команд
- Problem Details (RFC 9457) из коробки

### GraphQL

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **strawberry-graphql[litestar]** | ≥0.230 | GraphQL сервер |

**Почему Strawberry:**
- Code-first подход (Python типы → GraphQL схема)
- Нативная интеграция с Litestar
- Pydantic совместимость

### Background Tasks

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **taskiq** | ≥0.11 | Task queue |
| **taskiq-redis** | ≥1.0 | Redis backend |
| **taskiq-litestar** | ≥0.2 | Litestar интеграция |
| **temporalio** | ≥1.9.0 | Durable Execution, Saga Workflows |

**Почему TaskIQ:**
- Современный async task queue
- Dishka интеграция (DI в воркерах)
- Redis backend для распределённых задач

### Functional Programming

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **returns** | ≥0.23 | Result, Maybe, flow, bind |

**Почему Returns:**
- Railway-oriented programming
- Типизированные контейнеры (Result[T, E])
- mypy плагин для статической проверки

### Async & Resilience

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **anyio** | ≥4.0 | Structured concurrency |
| **tenacity** | ≥8.2 | Retry логика |
| **cashews** | ≥7.0 | Async кэширование |

**Почему anyio:**
- TaskGroups для structured concurrency
- CancelScope для таймаутов
- `to_thread.run_sync` для CPU-bound

**Почему Tenacity:**
- Стандарт де-факто для retry
- Гибкие стратегии (exponential backoff, jitter)

**Почему Cashews:**
- Async-first кэширование
- Wildcards для инвалидации
- Early refresh для защиты от stampede

### Dependency Injection

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **dishka** | ≥1.4.0 | DI контейнер |

**Почему Dishka:**
- Scoped контейнеры (APP, REQUEST)
- Интеграции: Litestar, TaskIQ, Click
- Автоматический резолвинг по type hints

### ORM

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **piccolo[all]** | ≥1.0 | Async ORM + миграции |

**Почему Piccolo:**
- Async-first ORM
- Встроенные миграции
- Type-safe запросы
- Litestar DTO интеграция

### Validation

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **pydantic** | ≥2.0 | DTO валидация |
| **pydantic-settings** | ≥2.0 | Settings из env |

**Почему Pydantic v2:**
- Быстрая валидация (Rust-core)
- `from_attributes` для ORM
- `validate_call` декоратор

### Observability

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **logfire[asgi]** | ≥0.50 | Tracing + logging |
| **structlog** | ≥24.0 | Structured logging |

**Почему Logfire:**
- Zero-config инструментация
- Litestar интеграция
- OpenTelemetry совместимость

### Security

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **bcrypt** | ≥4.0 | Password hashing |
| **PyJWT** | ≥2.0 | JWT tokens |

### Utils

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| **httpx** | ≥0.27 | HTTP client |
| **python-dotenv** | ≥1.0.0 | .env loading |
| **rich** | ≥13.0 | CLI formatting |

---

## 🔧 pyproject.toml

```toml
[project]
name = "hyper-porto-app"
version = "0.1.0"
description = "Hyper-Porto v4.3 - Functional architecture for Python backends"
requires-python = ">=3.12"

dependencies = [
    # Web Framework
    "litestar[standard]>=2.12.0",
    # GraphQL
    "strawberry-graphql[litestar]>=0.230",
    # Background Tasks
    "taskiq>=0.11",
    "taskiq-redis>=1.0",
    "taskiq-litestar>=0.2",
    # Functional Programming
    "returns>=0.23",
    # Async & Resilience
    "anyio>=4.0",
    "tenacity>=8.2",
    "cashews>=7.0",
    # DI
    "dishka>=1.4.0",
    # ORM
    "piccolo[all]>=1.0",
    # Validation
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    # Observability
    "logfire[asgi]>=0.50",
    "structlog>=24.0",
    # Security
    "bcrypt>=4.0",
    "PyJWT>=2.0",
    # Utils
    "httpx>=0.27",
    "python-dotenv>=1.0.0",
    "rich>=13.0",
    # Server
    "uvicorn[standard]>=0.32.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "hypothesis>=6.0",
    "ruff>=0.4",
    "mypy>=1.10",
    "pre-commit>=3.0",
]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = [
    "returns.contrib.mypy.returns_plugin",
    "pydantic.mypy",
]
```

---

## 📊 Сравнение альтернатив

### Web Framework

| Фреймворк | Преимущества | Недостатки |
|-----------|-------------|------------|
| **Litestar** ✅ | Channels, CLIPlugin, Guards | Меньше сообщество |
| FastAPI | Большое сообщество | Нет Channels из коробки |
| Starlette | Минималистичный | Много писать вручную |

### ORM

| ORM | Преимущества | Недостатки |
|-----|-------------|------------|
| **Piccolo** ✅ | Async, миграции, type-safe | Меньше фич чем SQLAlchemy |
| SQLAlchemy 2.0 | Зрелый, много фич | Сложнее, больше boilerplate |
| Tortoise | Простой | Менее активная разработка |

### DI

| DI | Преимущества | Недостатки |
|----|-------------|------------|
| **Dishka** ✅ | Scopes, интеграции | Новее |
| dependency-injector | Зрелый | Сложнее, меньше интеграций |

### Task Queue

| Queue | Преимущества | Недостатки |
|-------|-------------|------------|
| **TaskIQ** ✅ | Async, Dishka DI | Моложе |
| Celery | Зрелый, много фич | Sync-first, тяжелый |
| arq | Простой | Меньше фич |

### Result type

| Библиотека | Преимущества | Недостатки |
|------------|-------------|------------|
| **returns** ✅ | Полный набор, mypy plugin | Кривая обучения |
| result | Проще | Меньше фич |
| custom | Контроль | Надо поддерживать |

---

## 🔌 Интеграции

### Dishka интеграции

| Интеграция | Использование |
|------------|---------------|
| `dishka.integrations.litestar` | HTTP Controllers |
| `dishka.integrations.taskiq` | Background Workers |
| `dishka.integrations.click` | CLI Commands |

### Litestar плагины

| Плагин | Использование |
|--------|---------------|
| `ChannelsPlugin` | WebSocket Pub/Sub |
| `ProblemDetailsPlugin` | RFC 9457 errors |
| `CLIPlugin` | CLI commands |

### Strawberry интеграции

| Интеграция | Использование |
|------------|---------------|
| `strawberry.litestar` | GraphQL Controller |
| Pydantic types | Input/Output conversion |

---

## ⚠️ Известные ограничения

### dishka-strawberry + Litestar

```python
# ❌ dishka-strawberry требует FastAPI, не работает с Litestar
# from dishka.integrations.strawberry import FromDishka

# ✅ Используй get_dependency() helper
from src.Ship.GraphQL.Helpers import get_dependency

@strawberry.mutation
async def create_user(self, input: CreateUserInput, info: strawberry.Info):
    action = await get_dependency(info, CreateUserAction)
    return await action.run(input.to_pydantic())
```

### Piccolo + SQLite

```python
# ⚠️ SQLite не поддерживает auto_update для Timestamptz
# Используй override update() в Repository для ручного updated_at

async def update(self, user: AppUser) -> AppUser:
    await AppUser.update({
        AppUser.updated_at: datetime.now(timezone.utc),
        # ... other fields
    }).where(AppUser.id == user.id)
```

---

## 📁 Где искать документацию

| Библиотека | Официальная документация |
|------------|-----------------|
| Litestar | <https://docs.litestar.dev/> |
| Piccolo | <https://piccolo-orm.com/docs/> |
| Dishka | <https://dishka.dev/> |
| Returns | <https://returns.readthedocs.io/> |
| anyio | <https://anyio.readthedocs.io/> |
| Strawberry | <https://strawberry.rocks/docs/> |
| TaskIQ | <https://taskiq-python.github.io/taskiq-litestar/> |

---

<div align="center">

**Следующий раздел:** [09-transports.md](09-transports.md) — HTTP, GraphQL, CLI, WebSocket

</div>
