# /explain — Объяснение концепций

Объяснение концепций и паттернов Hyper-Porto архитектуры.

## Синтаксис

```
/explain <topic>
```

## Темы

### Архитектура

```
/explain porto           # Porto pattern
/explain container       # Что такое Container
/explain ship           # Что такое Ship
/explain cqrs           # Command Query Responsibility Segregation
```

### Компоненты

```
/explain action         # Actions и Result[T, E]
/explain task           # Tasks vs Actions
/explain query          # Queries для чтения
/explain repository     # Repository pattern
/explain uow            # Unit of Work
```

### Паттерны

```
/explain result         # Result[T, E] и Railway
/explain events         # Domain Events
/explain di             # Dependency Injection с Dishka
/explain structured-concurrency  # anyio TaskGroups
```

### Транспорты

```
/explain http           # HTTP API с Litestar
/explain graphql        # GraphQL с Strawberry
/explain websocket      # WebSocket и Channels
/explain cli            # CLI с Click
/explain workers        # Background tasks с TaskIQ
```

## Примеры

```
/explain result
```

Вывод:
```markdown
# Result[T, E] — Railway-Oriented Programming

## Концепция

Result[T, E] представляет результат операции, который может быть:
- `Success(value)` — успешный результат с данными
- `Failure(error)` — ошибка с информацией

## Использование

```python
from returns.result import Result, Success, Failure

async def run(self, data) -> Result[User, UserError]:
    if error:
        return Failure(UserNotFoundError(...))
    return Success(user)
```

## Pattern Matching

```python
match result:
    case Success(user):
        return UserResponse.from_entity(user)
    case Failure(UserNotFoundError()):
        raise NotFoundException()
```

## Преимущества

1. Явная обработка ошибок
2. Типобезопасность
3. Композиция через `bind`, `map`
4. Нет exceptions в бизнес-логике
```

## Связанная документация

Каждый `/explain` ссылается на:
- Соответствующий документ в `docs/`
- Пример в `foxdocs/LitestarPortoShowcase-main/`
