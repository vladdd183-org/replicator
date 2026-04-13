# 🎨 Метапрограммирование без велосипедов

> **Версия:** 4.3 | **Дата:** Январь 2026  
> Используем мощь экосистемы Python: Tenacity, Cashews, Pydantic, Logfire

---

## 🎯 Философия

```
Не пиши то, что уже написали и протестировали тысячи разработчиков.
```

Вместо создания собственных декораторов для кэширования, ретраев и валидации, мы используем промышленные стандарты.

---

## 🛡️ Resilience & Retries: Tenacity

Вместо самописного `@retryable` используем **Tenacity**.

```bash
uv add tenacity
```

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
)
import logfire
import httpx


class ExternalService:
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        before=before_log(logfire, "info"),
    )
    async def fetch_data(self, url: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
```

---

## ⚡ Caching: Cashews

### Когда что использовать

| Сценарий | Решение | Пример |
|----------|---------|--------|
| Кэширование HTTP ответов | Litestar `ResponseCache` | GET /api/users (список) |
| Кэширование бизнес-логики | Cashews | Repository queries |
| Кэширование внешних API | Cashews | ExternalService.fetch_data() |
| Инвалидация кэша | `invalidate_cache()` | Repository lifecycle hooks |

### Настройка Cashews

```python
# src/Ship/Infrastructure/Cache/Cashews.py
from cashews import cache

cache.setup("redis://localhost:6379/1")  # Или "mem://" для development
```

### Использование в Repository

```python
from cashews import cache

class UserRepository:
    
    # Кэширование результата на 10 минут
    @cache(ttl="10m", key="user:{user_id}")
    async def get_profile(self, user_id: UUID) -> UserProfile:
        return await self.db.fetch_one(...)
```

### Инвалидация кэша (реальный код)

```python
# src/Ship/Decorators/cache_utils.py

async def invalidate_cache(*patterns: str) -> None:
    """Invalidate cache entries matching patterns.
    
    Single source of truth for cache invalidation.
    Supports wildcards via cashews delete_match.
    
    Args:
        patterns: Cache key patterns to delete (supports * wildcards)
        
    Example:
        await invalidate_cache("user:123", "users:list:*", "users:count")
    """
    ensure_cache_initialized()
    
    for pattern in patterns:
        if "*" in pattern:
            await cache.delete_match(pattern)
        else:
            await cache.delete(pattern)
```

### Использование в Repository (реальный код)

```python
# src/Containers/AppSection/UserModule/Data/Repositories/UserRepository.py

class UserRepository(Repository[AppUser]):
    
    # Lifecycle hooks для cache invalidation
    
    async def _on_add(self, entity: AppUser) -> None:
        """Invalidate cache after adding user."""
        await invalidate_cache("users:list:*", "users:count")
    
    async def _on_update(self, entity: AppUser) -> None:
        """Invalidate cache after updating user."""
        await invalidate_cache(
            f"user:{entity.id}",
            "user:email:*",
            "users:list:*",
            "users:count",
        )
    
    async def _on_delete(self, entity: AppUser) -> None:
        """Invalidate cache after deleting user."""
        await invalidate_cache(
            f"user:{entity.id}",
            "user:email:*",
            "users:list:*",
            "users:count",
        )
```

### Litestar ResponseCache для HTTP

```python
from litestar import get
from litestar.config.response_cache import ResponseCacheConfig

@get("/users", cache=60)  # Кэширование HTTP ответа на 60 секунд
async def list_users() -> list[UserResponse]:
    ...
```

---

## ✅ Validation: Pydantic

### В Schemas (Request DTOs)

```python
# src/Containers/AppSection/UserModule/Data/Schemas/Requests.py

from pydantic import BaseModel, EmailStr, Field, field_validator


class CreateUserRequest(BaseModel):
    """Request to create a new user."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=2, max_length=100)
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class LoginRequest(BaseModel):
    """Request for user authentication."""
    
    email: EmailStr
    password: str = Field(..., min_length=1)
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()
```

### Pydantic validate_call

```python
from pydantic import validate_call, Field, EmailStr


class UserService:

    @validate_call
    async def register(
        self,
        name: str = Field(min_length=2),
        email: EmailStr,
        age: int = Field(gt=18),
    ) -> User:
        # Аргументы уже провалидированы!
        # Если email невалиден — pydantic.ValidationError
        ...
```

---

## 🔍 Tracing: Logfire

### Настройка

```python
# src/Ship/Infrastructure/Telemetry/Logfire.py

import logfire

def setup_logfire(app) -> None:
    """Setup Logfire telemetry."""
    settings = get_settings()
    
    if settings.logfire_token:
        logfire.configure(token=settings.logfire_token)
    else:
        logfire.configure(send_to_logfire=False)
    
    # Auto-instrument Litestar
    logfire.instrument_litestar(app)
```

### Logging в коде

```python
# src/Containers/AppSection/UserModule/Listeners.py

import logfire
from litestar.events import listener


@listener("UserCreated")
async def on_user_created(user_id: str, email: str, **kwargs):
    logfire.info(
        "🎉 User created event received",
        user_id=user_id,
        email=email,
    )


@listener("UserDeleted")
async def on_user_deleted(user_id: str, email: str, **kwargs):
    logfire.info(
        "🗑️ User deleted event received",
        user_id=user_id,
        email=email,
    )
```

### Ручная трассировка

```python
import logfire


@logfire.instrument("processing_order")
async def process_order(order_id: str):
    with logfire.span("validating_items"):
        # ...
        pass
    
    with logfire.span("charging_payment"):
        # ...
        pass
```

---

## 🧬 Протоколы (Interfaces)

`typing.Protocol` — стандарт языка, замена абстрактным базовым классам.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class FileStorage(Protocol):
    async def save(self, path: str, content: bytes) -> str: ...
    async def get(self, path: str) -> bytes: ...
    async def delete(self, path: str) -> None: ...


# Реализация
class S3Storage:
    async def save(self, path: str, content: bytes) -> str:
        # Upload to S3
        ...
    
    async def get(self, path: str) -> bytes:
        # Download from S3
        ...
    
    async def delete(self, path: str) -> None:
        # Delete from S3
        ...


# Проверка
storage = S3Storage()
assert isinstance(storage, FileStorage)  # True!
```

---

## 📋 Итоговый стек

| Задача | Библиотека | Почему |
|--------|------------|--------|
| **Retries** | `tenacity` | Стандарт де-факто, гибкая настройка стратегий |
| **Cache** | `cashews` | Async-first, типизация, теги, wildcards |
| **Cache invalidation** | `invalidate_cache()` | Единая точка, wildcards через cashews |
| **Validation** | `pydantic` | Встроенный `validate_call` в v2, Field constraints |
| **Tracing** | `logfire` | Zero-config инструментация, Litestar интеграция |
| **Protocols** | `typing.Protocol` | Стандарт Python, runtime_checkable |

---

## ❌ НЕ создавай свои:

| Задача | ❌ НЕ пиши | ✅ Используй |
|--------|-----------|-------------|
| Retry логика | `@retryable` | `tenacity.retry` |
| Кэширование | `@cached` | `cashews.cache` |
| Валидация | `@validated` | `pydantic.validate_call` |
| Трассировка | `@traced` | `logfire.instrument` |
| HTTP кэш | Custom middleware | `litestar.ResponseCache` |

---

<div align="center">

**Следующий раздел:** [07-spec-driven.md](07-spec-driven.md) — Spec-Driven Development

</div>
