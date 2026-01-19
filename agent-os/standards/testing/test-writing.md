# Test Writing — pytest + Hypothesis

> Стандарты написания тестов для Hyper-Porto проектов.

---

## 🧪 Tech Stack

| Инструмент | Версия | Назначение |
|------------|--------|------------|
| pytest | >=8.0 | Test framework |
| pytest-asyncio | >=0.23 | Async tests |
| pytest-cov | >=4.0 | Coverage |
| hypothesis | >=6.0 | Property-based testing |

---

## 📁 Структура тестов

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests
│   └── test_hash_password_task.py
├── integration/         # API integration tests
│   └── test_user_api.py
├── e2e/                 # End-to-end flows
│   └── test_user_flow.py
└── property/            # Property-based tests
    └── test_user_properties.py
```

---

## ⚙️ Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"
```

---

## 📋 Test Types

### Unit Tests — Tasks и чистые функции

```python
# tests/unit/test_hash_password_task.py
import pytest
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask


def test_hash_password_produces_valid_hash():
    """Test that HashPasswordTask produces valid bcrypt hash."""
    task = HashPasswordTask()
    
    result = task.run("password123")
    
    assert result.startswith("$2b$")
    assert len(result) == 60


def test_hash_password_different_for_same_input():
    """Test that same password produces different hashes (salt)."""
    task = HashPasswordTask()
    
    hash1 = task.run("password123")
    hash2 = task.run("password123")
    
    assert hash1 != hash2  # Different salts
```

### Integration Tests — API endpoints

```python
# tests/integration/test_user_api.py
import pytest
from litestar.testing import AsyncTestClient

from src.App import create_app


@pytest.fixture
async def client():
    app = create_app()
    async with AsyncTestClient(app=app) as client:
        yield client


@pytest.mark.asyncio
async def test_create_user_success(client):
    """Test creating a new user via API."""
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client):
    """Test that duplicate email returns 409 Conflict."""
    # Create first user
    await client.post(
        "/api/v1/users",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "name": "User 1",
        },
    )
    
    # Try to create duplicate
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "duplicate@example.com",
            "password": "password456",
            "name": "User 2",
        },
    )
    
    assert response.status_code == 409
    assert response.json()["code"] == "USER_ALREADY_EXISTS"
```

### E2E Tests — Full user flows

```python
# tests/e2e/test_user_flow.py
import pytest
from litestar.testing import AsyncTestClient


@pytest.mark.asyncio
async def test_complete_user_registration_flow(client):
    """Test complete user flow: register → login → get profile."""
    # 1. Register
    register_response = await client.post(
        "/api/v1/users",
        json={
            "email": "newuser@example.com",
            "password": "securepass123",
            "name": "New User",
        },
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]
    
    # 2. Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "newuser@example.com",
            "password": "securepass123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # 3. Get profile
    profile_response = await client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "newuser@example.com"
```

### Property Tests — Hypothesis

```python
# tests/property/test_user_properties.py
import pytest
from hypothesis import given, strategies as st

from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask
from src.Containers.AppSection.UserModule.Tasks.VerifyPasswordTask import VerifyPasswordTask


@given(password=st.text(min_size=1, max_size=100))
def test_hash_verify_roundtrip(password):
    """Property: any password can be hashed and verified."""
    hash_task = HashPasswordTask()
    verify_task = VerifyPasswordTask()
    
    hashed = hash_task.run(password)
    result = verify_task.run(password, hashed)
    
    assert result is True


@given(
    password=st.text(min_size=8, max_size=50),
    wrong_password=st.text(min_size=8, max_size=50),
)
def test_wrong_password_fails_verification(password, wrong_password):
    """Property: wrong password never verifies (unless equal)."""
    from hypothesis import assume
    assume(password != wrong_password)
    
    hash_task = HashPasswordTask()
    verify_task = VerifyPasswordTask()
    
    hashed = hash_task.run(password)
    result = verify_task.run(wrong_password, hashed)
    
    assert result is False
```

---

## 🎯 Testing Priorities

### ✅ Тестируй обязательно

1. **Actions** — core business logic
2. **Tasks** — CPU-bound operations
3. **API endpoints** — critical paths
4. **Authentication** — security-critical

### ⏭️ Тестируй по необходимости

1. Edge cases — только если бизнес-критичны
2. Queries — простые read operations
3. DTOs — Pydantic валидирует автоматически

### ❌ НЕ тестируй

1. Boilerplate код (Controllers без логики)
2. Pydantic модели (валидация встроена)
3. Piccolo миграции

---

## 📐 Naming Conventions

```python
# test_{what}_{expected_behavior}
def test_hash_password_produces_valid_hash():
    ...

def test_create_user_with_duplicate_email_returns_409():
    ...

def test_login_with_invalid_credentials_fails():
    ...
```

---

## 🔧 Fixtures

### conftest.py

```python
# tests/conftest.py
import pytest
import os

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["DB_URL"] = "sqlite:///data/test.db"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Setup test database."""
    yield
    # Cleanup
    if os.path.exists("data/test.db"):
        os.remove("data/test.db")


@pytest.fixture
async def client():
    """Async test client."""
    from litestar.testing import AsyncTestClient
    from src.App import create_app
    
    app = create_app()
    async with AsyncTestClient(app=app) as client:
        yield client
```

---

## 📊 Coverage

```bash
# Run with coverage
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

### Минимальные требования

| Категория | Coverage |
|-----------|----------|
| Actions | 80%+ |
| Tasks | 90%+ |
| Overall | 70%+ |

---

## ⚠️ Чего НЕ делать

```python
# ❌ Тесты без assertions
def test_create_user():
    action.run(data)  # Нет assert!

# ❌ Тесты implementation details
def test_uses_bcrypt_internally():
    assert "bcrypt" in hash_task.run.__code__.co_names  # Нет!

# ❌ Медленные тесты в unit/
def test_with_real_database():
    ...  # Это integration test!
```

---

## 📚 Дополнительно

- `tests/conftest.py` — shared fixtures
- `foxdocs/hypothesis-master/` — Hypothesis docs
- `docs/07-spec-driven.md` — Spec-Driven Development
