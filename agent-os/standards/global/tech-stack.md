# Tech Stack — Hyper-Porto v4.0

> Технический стек проекта. Все компоненты выбраны для функциональной архитектуры с Railway-Oriented Programming.

---

## Framework & Runtime

| Категория | Технология | Версия | Документация |
|-----------|------------|--------|--------------|
| **Application Framework** | Litestar | >=2.12.0 | `foxdocs/litestar-main/docs/` |
| **Language** | Python | >=3.12 | — |
| **Package Manager** | uv | latest | — |
| **Build System** | hatchling | latest | — |

---

## Backend Core

| Категория | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **ORM** | Piccolo | >=1.0 | Async ORM + миграции |
| **DI Framework** | Dishka | >=1.4.0 | Dependency Injection |
| **Result Type** | returns | >=0.23 | Railway-oriented programming |
| **Validation** | Pydantic | >=2.0 | DTOs, Settings, Errors |
| **Async** | anyio | >=4.0 | Structured Concurrency |

---

## API Layer

| Категория | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **REST API** | Litestar Controllers | — | HTTP endpoints |
| **GraphQL** | Strawberry | >=0.230 | GraphQL API |
| **WebSocket** | Litestar Channels | — | Real-time updates |
| **CLI** | Litestar CLIPlugin + Click | — | Command line |
| **Background Tasks** | TaskIQ | >=0.11 | Async task queue |

---

## Infrastructure

| Категория | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Database** | SQLite/PostgreSQL | — | Через Piccolo |
| **Caching** | cashews | >=7.0 | @cached декоратор |
| **Retry** | tenacity | >=8.2 | @retry с backoff |
| **HTTP Client** | httpx | >=0.27 | Async HTTP |

---

## Observability

| Категория | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Tracing** | Logfire | >=0.50 | OpenTelemetry tracing |
| **Logging** | structlog | >=24.0 | Structured logging |
| **Error Format** | RFC 9457 | — | Problem Details |

---

## Security

| Категория | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Password Hashing** | bcrypt | >=4.0 | Secure hashing |
| **JWT** | PyJWT | >=2.0 | Token auth |
| **Auth Middleware** | Custom | — | `Ship/Auth/` |

---

## Testing & Quality

| Категория | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Test Framework** | pytest | >=8.0 | Testing |
| **Async Tests** | pytest-asyncio | >=0.23 | Async support |
| **Property Testing** | Hypothesis | >=6.0 | Property-based |
| **Coverage** | pytest-cov | >=4.0 | Code coverage |
| **Linting** | ruff | >=0.4 | Linting + formatting |
| **Type Checking** | mypy | >=1.10 | Static types |

---

## Deployment

| Категория | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **ASGI Server** | uvicorn | >=0.32.0 | Production server |
| **Container** | Docker | — | Containerization |
| **Compose** | docker-compose | — | Local dev |

---

## ⚠️ НЕ используем (принципиально)

| Библиотека | Причина | Альтернатива |
|------------|---------|--------------|
| FastAPI | Архитектурные причины | Litestar |
| SQLAlchemy | Сложность async | Piccolo |
| dependency-injector | Устаревший подход | Dishka |
| Celery | Не async-native | TaskIQ |
| dataclasses (для DTO) | Нет валидации | Pydantic |
| asyncio напрямую | Fire-and-forget | anyio TaskGroups |

---

## 📚 Документация библиотек

Локальная документация находится в `foxdocs/`:

```
foxdocs/
├── litestar-main/docs/         # Litestar
├── piccolo-master/docs/        # Piccolo ORM
├── dishka-develop/docs/        # Dishka DI
├── returns-master/docs/        # Returns
├── anyio-master/docs/          # anyio
├── strawberry-main/docs/       # Strawberry GraphQL
├── taskiq-litestar-develop/    # TaskIQ
├── Porto-master/docs/          # Porto SAP
├── cosmic/                     # Cosmic Python
└── LitestarPortoShowcase-main/ # Пример проекта
```

---

## Entry Points

```toml
# pyproject.toml
[project.scripts]
porto = "src.Ship.CLI.Main:cli"

[project.entry-points."litestar.commands"]
users = "src.Containers.AppSection.UserModule.UI.CLI.Commands:users_group"
db = "src.Ship.CLI.MigrationCommands:db_group"
```
