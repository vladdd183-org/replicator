# Development Conventions — Hyper-Porto

> Общие конвенции разработки для Hyper-Porto проектов.

---

## 📁 Project Structure

### Porto Pattern: Ship + Containers

```
src/
├── Ship/               # Инфраструктура (общий код)
│   ├── Auth/           # Аутентификация
│   ├── CLI/            # CLI команды
│   ├── Configs/        # Settings
│   ├── Core/           # BaseSchema, Errors, Protocols
│   ├── Decorators/     # @audited, @result_handler
│   ├── Events/         # Ship-level events
│   ├── Exceptions/     # RFC 9457 Problem Details
│   ├── GraphQL/        # Strawberry schema
│   ├── Infrastructure/ # Cache, Telemetry, Workers
│   ├── Parents/        # Abstract: Action, Task, Query, Repository, UoW
│   └── Providers/      # Dishka providers (общие)
│
└── Containers/         # Бизнес-модули
    ├── AppSection/     # Основные модули
    │   └── UserModule/
    └── VendorSection/  # Внешние интеграции
        └── EmailModule/
```

### Container Structure

```
{Module}/
├── Actions/           # Use Cases (CQRS Commands)
├── Tasks/             # Атомарные операции
├── Queries/           # CQRS Read operations
├── Data/
│   ├── Repositories/  # Repository Pattern
│   ├── Schemas/       # DTOs (Requests/Responses)
│   └── UnitOfWork.py  # Transaction + Events
├── Models/            # Piccolo Tables + migrations
├── UI/
│   ├── API/           # HTTP REST Controllers
│   ├── CLI/           # Click commands
│   ├── GraphQL/       # Strawberry resolvers
│   ├── WebSocket/     # Litestar Channels
│   └── Workers/       # TaskIQ background tasks
├── Errors.py          # Module errors (Pydantic frozen)
├── Events.py          # Domain Events
├── Listeners.py       # @listener event handlers
└── Providers.py       # Dishka DI registration
```

---

## 🔗 Dependency Rules

### Разрешённые зависимости

```
Controller → Action, Query
Action → Task, Repository, UoW, SubAction
Query → Repository
Task → (опционально) Repository
Repository → Model
Любой компонент → Ship/*
```

### Запрещённые зависимости

```
Controller → Repository (напрямую)
Container A → Container B (напрямую, используй Events)
Action → HTTP/GraphQL/CLI specifics
```

---

## 📋 Explicit Configuration

### ❌ НЕТ автосканированию

```python
# ПЛОХО
discover_and_register_everything("src/Containers")
```

### ✅ ДА явной регистрации

```python
# ХОРОШО — App.py
from src.Containers.AppSection.UserModule import user_router

app = Litestar(
    route_handlers=[user_router],
    listeners=[on_user_created, on_user_updated],
)

container = make_async_container(*get_all_providers())
setup_dishka(container, app)
```

---

## 🌿 Git Conventions

### Branch Names

```
feature/user-authentication
fix/password-validation
refactor/user-module-cleanup
docs/api-documentation
```

### Commit Messages

```
feat(user): add password reset functionality
fix(auth): correct JWT token expiration
refactor(user): extract password hashing to Task
docs(api): update OpenAPI descriptions
test(user): add integration tests for CreateUserAction
```

### PR Description

```markdown
## Summary
Brief description of changes

## Changes
- Added CreateUserAction
- Updated UserRepository with find_by_email
- Added UserCreated event

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
```

---

## ⚙️ Environment Configuration

### .env файл

```bash
# App
APP_NAME="Hyper-Porto"
APP_ENV=development
APP_DEBUG=true

# Database
DB_URL=sqlite:///data/app.db

# Auth
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# External Services
REDIS_URL=redis://localhost:6379
```

### Pydantic Settings

```python
# src/Ship/Configs/Settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Hyper-Porto"
    app_env: str = "development"
    app_debug: bool = False
    
    db_url: str = "sqlite:///data/app.db"
    
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
```

---

## 📦 Dependency Management

### pyproject.toml

```toml
[project]
name = "hyper-porto-app"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    "litestar[standard]>=2.12.0",
    "piccolo[all]>=1.0",
    "dishka>=1.4.0",
    "returns>=0.23",
    "pydantic>=2.0",
    # ...
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "ruff>=0.4",
    "mypy>=1.10",
]
```

### uv для управления зависимостями

```bash
# Установка зависимостей
uv sync

# Добавление пакета
uv add package-name

# Dev зависимость
uv add --dev pytest
```

---

## 🧪 Testing Requirements

| Тип теста | Когда писать | Папка |
|-----------|--------------|-------|
| Unit | Critical business logic | `tests/unit/` |
| Integration | API endpoints, DB | `tests/integration/` |
| E2E | Full user flows | `tests/e2e/` |
| Property | Data-driven validation | `tests/property/` |

### Запуск тестов

```bash
# Все тесты
pytest

# С coverage
pytest --cov=src

# Только unit
pytest tests/unit/
```

---

## 📚 Documentation

### Обязательная документация

1. `README.md` — setup instructions
2. `docs/` — архитектурная документация
3. Docstrings в коде
4. OpenAPI (автогенерация)

### Где искать документацию

```
docs/               # Архитектура Hyper-Porto
foxdocs/            # Документация библиотек
/api/docs           # OpenAPI (Scalar UI)
/graphql            # GraphQL Playground
```

---

## 🔄 Changelog

### Формат

```markdown
# Changelog

## [Unreleased]

### Added
- New CreateUserAction with Result pattern

### Changed
- Updated UserRepository to use Piccolo

### Fixed
- Fixed password validation in ChangePasswordAction

### Removed
- Removed deprecated UserService
```

---

## 📚 Дополнительно

- `docs/00-philosophy.md` — философия архитектуры
- `docs/02-project-structure.md` — детальная структура
- `docs/10-registration.md` — явная регистрация
