---
name: setup-tests
description: Setup and configure pytest tests for Hyper-Porto modules. Use when the user wants to настроить тесты, test setup, pytest, добавить тесты, тестирование модуля.
---

# Setup Tests for Hyper-Porto

Настройка и создание тестов с pytest.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Standard** | `agent-os/standards/testing/test-writing.md` |
| **Docs** | `docs/03-components.md` (тестирование) |

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   └── Containers/
│       └── AppSection/
│           └── UserModule/
│               ├── test_actions.py
│               ├── test_tasks.py
│               └── test_queries.py
├── integration/             # Integration tests
└── e2e/                     # End-to-end tests
```

## Quick Reference

| Tool | Purpose |
|------|---------|
| **pytest** | Test runner |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Coverage reports |
| **Dishka** | DI in tests |

## Действие

1. **Загрузи** полный гайд из `agent-os/standards/testing/test-writing.md`
2. **Создай** структуру папок tests/
3. **Настрой** conftest.py с fixtures
4. **Создай** unit tests для Actions, Tasks, Queries
5. **Запусти** `pytest` для проверки

## Key Fixtures (conftest.py)

```python
@pytest_asyncio.fixture
async def container() -> AsyncContainer:
    """Dishka container for tests."""
    return create_test_container()

@pytest_asyncio.fixture
async def request_container(container):
    """Request-scoped container."""
    async with container() as rc:
        yield rc
```

## Test Pattern: Action

```python
@pytest.mark.asyncio
async def test_create_user_success(action: CreateUserAction):
    request = CreateUserRequest(email="test@test.com", password="pass123", name="Test")
    result = await action.run(request)
    
    assert isinstance(result, Success)
    user = result.unwrap()
    assert user.email == "test@test.com"
```

## Commands

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific module
pytest tests/unit/Containers/AppSection/UserModule/

# Verbose
pytest -v
```

## pytest.ini

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
addopts = -v --tb=short
```
