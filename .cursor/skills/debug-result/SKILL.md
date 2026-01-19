---
name: debug-result
description: Debug issues with returns.Result in Hyper-Porto architecture. Use when the user mentions "не работает result", "ошибка failure", "debug result", "result не возвращает", Result pattern matching errors, Failure handling issues, or railway-oriented programming problems.
---

# Debug Result Issues

Отладка проблем с `Result[T, E]` из библиотеки returns.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Troubleshooting** | `agent-os/troubleshooting/result-errors.md` |
| **Patterns** | `agent-os/snippets/result-patterns.md` |
| **Standard** | `agent-os/standards/global/error-handling.md` |
| **Docs** | `docs/04-result-railway.md` |
| **Library** | <https://returns.readthedocs.io/> |

## Quick Diagnostic

| Симптом | Причина | Решение |
|---------|---------|---------|
| `AttributeError: 'Failure' has no unwrap` | `unwrap()` на Failure | Используй pattern matching |
| Action возвращает `None` | Забыл `return Success()` | Добавить return на всех ветках |
| 500 вместо 404 | Error без `http_status` | Добавить `http_status` в Error |
| Type mismatch | Забыл `Success()` wrapper | Обернуть в `Success(value)` |
| Event loop зависает | CPU-bound код | `anyio.to_thread.run_sync()` |

## Действие

1. **Загрузи** полный гайд из `agent-os/troubleshooting/result-errors.md`
2. **Определи** тип проблемы по симптому
3. **Проверь** что все ветки возвращают `Success()`/`Failure()`
4. **Проверь** что Error классы имеют `http_status`
5. **Проверь** что Controller использует `@result_handler`

## Pattern Matching (правильно)

```python
match result:
    case Success(user):
        return UserResponse.from_entity(user)
    case Failure(UserNotFoundError(user_id=uid)):
        raise DomainException(UserNotFoundError(user_id=uid))
    case Failure(error):
        raise DomainException(error)
```

## Error с http_status (обязательно!)

```python
class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User {user_id} not found"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404  # ОБЯЗАТЕЛЬНО!
    user_id: UUID
```

## Checklist

```
- [ ] Все ветки Action возвращают Success/Failure?
- [ ] Error классы имеют http_status?
- [ ] Controller использует @result_handler?
- [ ] Pattern matching exhaustive?
- [ ] CPU-bound код в anyio.to_thread?
- [ ] Нет raise в бизнес-логике?
```
