---
name: debug-di
description: Debug Dishka Dependency Injection issues in Hyper-Porto. Use when the user mentions ошибка dishka, di не работает, not provided, dependency error, зависимость не найдена, container error.
---

# Debug Dishka DI Issues

Отладка проблем с Dependency Injection (Dishka).

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Troubleshooting** | `agent-os/troubleshooting/di-errors.md` |
| **Standard** | `agent-os/standards/backend/dependency-injection.md` |
| **Library docs** | <https://dishka.dev/> |

## Quick Diagnostic

| Симптом | Причина | Решение |
|---------|---------|---------|
| `NoFactoryError` | Не зарегистрировано | Добавить в Providers.py |
| `ScopeMismatch` | Неправильный scope | Проверить REQUEST vs APP |
| `CyclicDependency` | Circular import | Рефакторить зависимости |
| `CannotProvide` | Missing sub-dependency | Зарегистрировать все deps |
| Работает в тестах, падает в runtime | Container не передан | Проверить middleware |

## Действие

1. **Загрузи** полный гайд из `agent-os/troubleshooting/di-errors.md`
2. **Определи** тип ошибки по симптому
3. **Проверь** регистрацию в Providers.py
4. **Проверь** scope (APP vs REQUEST)
5. **Проверь** что все sub-dependencies зарегистрированы
6. **Проверь** нет circular imports

## Scope Reference

| Scope | Lifetime | Use For |
|-------|----------|---------|
| `Scope.APP` | Singleton | Tasks, Settings, Clients |
| `Scope.REQUEST` | Per request | Actions, Queries, UoW, Repos |

**Direction:** `APP ← REQUEST` (REQUEST может зависеть от APP)

## Common Fixes

```python
# Fix: NoFactoryError
class ModuleRequestProvider(Provider):
    scope = Scope.REQUEST
    my_action = provide(MyAction)  # Add this!

# Fix: Scope mismatch - move to REQUEST
class ModuleRequestProvider(Provider):
    scope = Scope.REQUEST  # Not APP!
    uow = provide(ModuleUnitOfWork)

# Fix: Missing FromDishka
async def endpoint(action: FromDishka[MyAction]):  # Add FromDishka!
```
