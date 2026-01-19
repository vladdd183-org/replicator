# 🎮 Command: /add-task

> Создание нового Task (атомарная операция).

---

## Синтаксис

```
/add-task <TaskName> [в <Module>] [sync]
```

## Параметры

| Параметр | Обязательный | Пример |
|----------|--------------|--------|
| TaskName | ✅ | `HashPassword`, `GenerateToken`, `SendEmail` |
| Module | ❌ | `UserModule` |
| sync | ❌ | Флаг для CPU-bound операций (SyncTask) |

---

## Типы Task

| Тип | Класс | Когда использовать |
|-----|-------|-------------------|
| **Async Task** | `Task[I, O]` | I/O операции (сеть, БД) |
| **Sync Task** | `SyncTask[I, O]` | CPU-bound (хеширование, парсинг) |

---

## Примеры

### Базовый async
```
/add-task GenerateToken в UserModule
```
→ Создаст `GenerateTokenTask` наследник `Task[I, O]`

### CPU-bound sync
```
/add-task HashPassword в UserModule sync
```
→ Создаст `HashPasswordTask` наследник `SyncTask[I, O]`

---

## Что создаётся

### 1. Async Task файл

`Tasks/GenerateTokenTask.py`:

```python
"""GenerateTokenTask - Generates JWT access and refresh tokens."""

from dataclasses import dataclass
from datetime import datetime, timedelta, UTC

import jwt

from src.Ship.Parents.Task import Task
from src.Ship.Configs.Settings import Settings


@dataclass
class GenerateTokenInput:
    user_id: str
    email: str


@dataclass
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_at: datetime


class GenerateTokenTask(Task[GenerateTokenInput, AuthTokens]):
    """Generate JWT access and refresh tokens.
    
    Used by:
    - AuthenticateAction
    - RefreshTokenAction
    """
    
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
    
    async def run(self, data: GenerateTokenInput) -> AuthTokens:
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self.settings.jwt_expire_minutes)
        
        payload = {
            "sub": str(data.user_id),
            "email": data.email,
            "exp": expires_at,
            "iat": now,
        }
        
        access_token = jwt.encode(
            payload,
            self.settings.jwt_secret,
            algorithm="HS256"
        )
        
        refresh_payload = {
            "sub": str(data.user_id),
            "type": "refresh",
            "exp": now + timedelta(days=7),
        }
        
        refresh_token = jwt.encode(
            refresh_payload,
            self.settings.jwt_secret,
            algorithm="HS256"
        )
        
        return AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
```

### 2. Sync Task файл

`Tasks/HashPasswordTask.py`:

```python
"""HashPasswordTask - Hashes passwords using bcrypt."""

import bcrypt

from src.Ship.Parents.Task import SyncTask


class HashPasswordTask(SyncTask[str, str]):
    """CPU-bound: Hash password with bcrypt.
    
    Used by: CreateUserAction, ChangePasswordAction
    
    Note: Call via anyio.to_thread.run_sync() in async context.
    """
    
    def run(self, password: str) -> str:
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")
```

**Использование SyncTask в Action:**

```python
import anyio

# В async Action.run()
password_hash = await anyio.to_thread.run_sync(
    self.hash_password.run, data.password
)
```

### 3. Регистрация в Providers

Tasks регистрируются в **APP scope** (stateless):

```python
class ModuleAppProvider(Provider):
    scope = Scope.APP
    
    hash_password = provide(HashPasswordTask)
    generate_token = provide(GenerateTokenTask)
```

---

## Task vs Action

| Аспект | Task | Action |
|--------|------|--------|
| **Purpose** | Атомарная операция | Orchestrates бизнес-логику |
| **Returns** | Прямое значение | `Result[T, E]` |
| **State** | Stateless | Может держать UoW |
| **Reusability** | Высокая (много Actions) | Низкая (конкретный use case) |
| **Errors** | Raises exceptions | Returns `Failure()` |
| **DI Scope** | APP | REQUEST |

---

## Именование

| Операция | Паттерн | Пример |
|----------|---------|--------|
| Transform | `{Verb}{Noun}Task` | `HashPasswordTask` |
| Generate | `Generate{Noun}Task` | `GenerateTokenTask` |
| Send | `Send{Noun}Task` | `SendEmailTask` |
| Validate | `Validate{Noun}Task` | `ValidateAddressTask` |
| Parse | `Parse{Noun}Task` | `ParseCSVTask` |
| Calculate | `Calculate{Noun}Task` | `CalculateTaxTask` |

---

## Действия после создания

1. ✅ Зарегистрировать в `Providers.py` (APP scope)
2. ✅ Добавить в `Tasks/__init__.py` exports
3. ✅ Для SyncTask: документировать `anyio.to_thread` usage
4. ✅ Написать unit тест

---

## Типичные ошибки

| ❌ Неправильно | ✅ Правильно |
|----------------|-------------|
| Держать state в Task | Tasks stateless |
| `Task` для CPU-bound | `SyncTask` + `anyio.to_thread` |
| Возвращать `Result[T, E]` | Tasks возвращают прямые значения |
| Бизнес-логика в Task | Бизнес-логика в Action |
| REQUEST scope | APP scope (stateless) |

---

## Связанные ресурсы

- **Template:** `../templates/task.py.template`
- **Standard:** `../standards/backend/actions-tasks.md`
- **Docs:** `docs/03-components.md`
