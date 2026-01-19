# 🔧 Troubleshooting: DI Errors (Dishka)

> Частые ошибки Dependency Injection и их решения.

---

## ❌ Error: `NoFactoryError`

### Симптом
```
dishka.exceptions.NoFactoryError: Cannot find factory for <class 'CreateUserAction'>
```

### Причина
Action/Query/Task не зарегистрирован в Provider.

### Решение
```python
# Providers.py
class ModuleRequestProvider(Provider):
    scope = Scope.REQUEST
    create_user_action = provide(CreateUserAction)  # Добавить!
```

---

## ❌ Error: `NoFactoryError` для Request

### Симптом
```
dishka.exceptions.NoFactoryError: Cannot find factory for <class 'litestar.connection.Request'>
```

### Причина
`LitestarProvider` не добавлен в контейнер.

### Решение
```python
# Ship/Providers/__init__.py
from dishka.integrations.litestar import LitestarProvider

def get_all_providers() -> list[Provider]:
    return [
        LitestarProvider(),  # Обязательно!
        AppProvider(),
        # ...
    ]
```

---

## ❌ Error: Circular Dependency

### Симптом
```
dishka.exceptions.CycleDependenciesError: Cycle dependencies detected
```

### Причина
A зависит от B, B зависит от A.

### Решение
1. Разбить на более мелкие компоненты
2. Использовать Events вместо прямой зависимости
3. Вынести общую логику в Task

```python
# ❌ Плохо: ActionA → ActionB → ActionA
class ActionA:
    def __init__(self, action_b: ActionB): ...

class ActionB:
    def __init__(self, action_a: ActionA): ...

# ✅ Хорошо: Использовать Events
class ActionA:
    async def run(self):
        self.uow.add_event(SomethingHappened())

# ActionB реагирует на событие через Listener
```

---

## ❌ Error: Wrong Scope

### Симптом
```
dishka.exceptions.GraphMissingFactoryError: 
Cannot create <Request scope> from <APP scope>
```

### Причина
Пытаешься получить REQUEST-scoped зависимость из APP-scoped.

### Решение
```python
# ❌ Плохо: UoW в APP scope
class ModuleProvider(Provider):
    scope = Scope.APP
    uow = provide(ModuleUnitOfWork)  # Нельзя!

# ✅ Хорошо: UoW в REQUEST scope
class ModuleRequestProvider(Provider):
    scope = Scope.REQUEST
    
    @provide
    def uow(self, request: Request) -> ModuleUnitOfWork:
        return ModuleUnitOfWork(_emit=request.app.emit)
```

---

## ❌ Error: Missing `FromDishka` annotation

### Симптом
```
TypeError: create_user() missing 1 required positional argument: 'action'
```

### Причина
Забыл `FromDishka[]` в Controller.

### Решение
```python
# ❌ Плохо
async def create_user(self, action: CreateUserAction):

# ✅ Хорошо
async def create_user(self, action: FromDishka[CreateUserAction]):
```

---

## ❌ Error: `@inject` не работает

### Симптом
DI не инъектирует зависимости в Controller.

### Причина
С Litestar + Dishka `@inject` не нужен!

### Решение
```python
# ❌ НЕ нужно
from dishka import inject

@inject
async def create_user(action: CreateUserAction): ...

# ✅ Правильно — просто FromDishka
async def create_user(action: FromDishka[CreateUserAction]): ...
```

---

## ❌ Error: CLI не находит зависимости

### Симптом
```
NoFactoryError в CLI команде
```

### Причина
CLI использует другой контейнер без `LitestarProvider`.

### Решение
Создать отдельный `get_cli_providers()`:

```python
# Ship/Providers/__init__.py
def get_cli_providers() -> list[Provider]:
    return [
        AppProvider(),
        UserModuleProvider(),
        UserCLIProvider(),  # Без Request!
    ]

# UserCLIProvider
class UserCLIProvider(Provider):
    scope = Scope.REQUEST
    
    @provide
    def uow(self) -> UserUnitOfWork:
        return UserUnitOfWork(_emit=None)  # Без event emitter
```

---

## ❌ Error: GraphQL не получает зависимости

### Симптом
```
TypeError в GraphQL resolver
```

### Причина
GraphQL resolvers не интегрированы с Dishka напрямую.

### Решение
Использовать `get_dependency()` helper:

```python
# Ship/GraphQL/Helpers.py
from dishka import AsyncContainer

async def get_dependency(info: Info, dependency_type: type[T]) -> T:
    container: AsyncContainer = info.context["dishka_container"]
    return await container.get(dependency_type)

# В resolver:
async def create_user(self, info: Info, input: CreateUserInput) -> User:
    action = await get_dependency(info, CreateUserAction)
    result = await action.run(...)
```

---

## 📐 Диагностика

### Проверить зарегистрированные провайдеры

```python
from src.Ship.Providers import get_all_providers

for provider in get_all_providers():
    print(f"{provider.__class__.__name__}: {provider.scope}")
```

### Проверить что зарегистрировано

```python
container = make_async_container(*get_all_providers())
# Попробовать резолвить вручную
async with container() as request_container:
    action = await request_container.get(CreateUserAction)
```

---

---

## 🧪 Тестирование DI

### Unit Test для зависимостей

```python
import pytest
from dishka import make_async_container

from src.Ship.Providers.AppProvider import create_container
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction


@pytest.mark.asyncio
async def test_can_resolve_action():
    """Test that all dependencies are properly registered."""
    container = create_container()
    
    async with container() as request_container:
        action = await request_container.get(CreateUserAction)
        assert action is not None
        assert action.hash_password is not None
        assert action.uow is not None
```

### Проверить все Actions резолвятся

```python
@pytest.mark.asyncio
async def test_all_actions_resolve():
    """Test all registered actions can be resolved."""
    from src.Containers.AppSection.UserModule.Actions import (
        CreateUserAction,
        UpdateUserAction,
        DeleteUserAction,
    )
    
    actions = [CreateUserAction, UpdateUserAction, DeleteUserAction]
    container = create_container()
    
    async with container() as request_container:
        for action_class in actions:
            action = await request_container.get(action_class)
            assert action is not None, f"Failed to resolve {action_class.__name__}"
```

---

## 📐 Паттерны Provider

### Simple Registration

```python
class UserAppProvider(Provider):
    scope = Scope.APP
    hash_password = provide(HashPasswordTask)
```

### Factory с Dependencies

```python
class UserRequestProvider(Provider):
    scope = Scope.REQUEST
    
    @provide
    def user_uow(
        self,
        users: UserRepository,
        app: Litestar,
    ) -> UserUnitOfWork:
        return UserUnitOfWork(users=users, _emit=app.emit)
```

### Conditional Providing

```python
class InfrastructureProvider(Provider):
    scope = Scope.APP
    
    @provide
    def cache_backend(self, settings: Settings) -> CacheBackend:
        if settings.cache_backend == "redis":
            return RedisCacheBackend(settings.redis_url)
        return MemoryCacheBackend()
```

---

## ✅ Quick Fix Checklist

```
DI Issue Debugging:
- [ ] Error message identifies missing dependency
- [ ] Check dependency is in Providers.py
- [ ] Check scope is correct (APP vs REQUEST)
- [ ] Check all sub-dependencies are registered
- [ ] Check no circular imports
- [ ] Check Provider is added to container
- [ ] Run dependency resolution test
- [ ] Restart server after changes
```

---

## 📊 Scope Reference

| Scope | Lifetime | Use For |
|-------|----------|---------|
| `Scope.APP` | Singleton | Tasks, Settings, Clients |
| `Scope.REQUEST` | Per request | Actions, Queries, UoW, Repos |

**Dependency Direction:**
```
APP ← REQUEST

APP scope can only depend on APP
REQUEST can depend on APP and REQUEST
```

---

## 🔗 Связанные

- **Standards:** `../standards/backend/dependency-injection.md`
- **Docs:** `foxdocs/dishka-develop/docs/`



