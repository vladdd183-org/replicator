# Knowledge — Поиск знаний

Поиск и получение знаний из внутренних и внешних источников.

## Когда использовать

- Для вопросов о библиотеках (Litestar, Piccolo, etc.)
- Для поиска best practices
- Для исследования тем
- Для разрешения ошибок
- Для сравнения подходов

## Синтаксис

```
/agent-os/knowledge [действие] "[запрос]"
```

## Доступные действия

| Действие | Описание |
|----------|----------|
| `search "query"` | Поиск по всем источникам |
| `litestar "topic"` | Документация Litestar |
| `piccolo "topic"` | Документация Piccolo |
| `dishka "topic"` | Документация Dishka |
| `returns "topic"` | Документация Returns |
| `anyio "topic"` | Документация anyio |
| `strawberry "topic"` | Документация Strawberry GraphQL |
| `research "topic"` | Глубокое исследование темы |
| `compare "X" "Y"` | Сравнение двух подходов |
| `cache stats` | Статистика кэша |
| `cache clear` | Очистить кэш |

## Примеры использования

### Общий поиск

```
/agent-os/knowledge search "как обрабатывать ошибки в Result"
```

Ищет по иерархии:
1. Внутренняя документация (docs/, agent-os/)
2. Память проекта (memory/)
3. Документация библиотек (Context7)
4. Внешние источники (Web)

### Документация Litestar

```
/agent-os/knowledge litestar "middleware"
```

Использует Context7 MCP для получения актуальной документации Litestar по теме middleware.

### Документация Piccolo

```
/agent-os/knowledge piccolo "migrations add column"
```

Получит документацию по добавлению колонок в миграциях Piccolo.

### Глубокое исследование

```
/agent-os/knowledge research "saga pattern в Python"
```

Проведёт комплексное исследование:
1. Внутренние документы
2. Научные статьи (arXiv)
3. Документация библиотек
4. Community best practices

### Сравнение

```
/agent-os/knowledge compare "TaskIQ" "Temporal"
```

Создаст сравнительный анализ с рекомендациями.

## Процесс

Делегируется агенту **knowledge-retriever**:

```
@.cursor/agents/knowledge-retriever.md

Найди информацию по запросу:

1. Классифицируй тип запроса
2. Используй иерархию источников
3. Синтезируй ответ из нескольких источников
4. Приоритет: Internal > Library > External

Конфигурация: @agent-os/knowledge/config.yml
Источники: @agent-os/knowledge/sources/
```

## Иерархия источников

```
┌────────────────────────────────────────────────┐
│  Priority 1: INTERNAL (Высший приоритет)       │
│  docs/, agent-os/, CLAUDE.md                   │
├────────────────────────────────────────────────┤
│  Priority 2: PROJECT DECISIONS                 │
│  memory/knowledge/                             │
├────────────────────────────────────────────────┤
│  Priority 3: LIBRARY DOCS                      │
│  Context7 MCP (Litestar, Piccolo, etc.)        │
├────────────────────────────────────────────────┤
│  Priority 4: EXTERNAL (Низший приоритет)       │
│  Web search, arXiv                             │
└────────────────────────────────────────────────┘
```

> При конфликте между источниками — внутренняя документация проекта всегда побеждает!

## Поддерживаемые библиотеки

| Библиотека | Команда | Примеры тем |
|------------|---------|-------------|
| Litestar | `litestar` | routing, middleware, events, channels |
| Piccolo | `piccolo` | tables, queries, migrations, transactions |
| Dishka | `dishka` | providers, scopes, integrations |
| Returns | `returns` | result, maybe, io, railway |
| anyio | `anyio` | task groups, cancellation, sync |
| Strawberry | `strawberry` | types, resolvers, subscriptions |
| Pydantic | `pydantic` | models, validation, settings |
| TaskIQ | `taskiq` | tasks, brokers, middlewares |

## Формат вывода

### Standard Answer

```markdown
## Ответ: Как обрабатывать ошибки в Result

### Из документации проекта

> Используйте pattern matching для обработки Result:
> 
> ```python
> match result:
>     case Success(user):
>         return UserResponse.from_entity(user)
>     case Failure(UserNotFoundError()):
>         return Response(status_code=404)
> ```
> 
> — docs/04-result-railway.md

### Из документации библиотеки

Returns library предоставляет несколько способов обработки:
- `match` — pattern matching (рекомендуется)
- `bind` — композиция операций
- `map` — трансформация значения

### Дополнительно

[Если использовались внешние источники]

---
**Источники:**
- docs/04-result-railway.md (internal)
- agent-os/snippets/result-patterns.md (internal)
- Returns Documentation (Context7)
```

### Comparison

```markdown
## Сравнение: TaskIQ vs Temporal

| Аспект | TaskIQ | Temporal |
|--------|--------|----------|
| Сложность | Низкая | Высокая |
| Durability | Redis/RabbitMQ | Event Sourcing |
| Saga Support | Ручной | Встроенный |
| Learning Curve | 1-2 дня | 2-4 недели |

### Рекомендация

**TaskIQ** — для простых background tasks, не-критичных процессов.
**Temporal** — для mission-critical workflows, сложных Saga.

---
**Источники:**
- docs/22-temporal-saga-patterns.md (internal)
- Temporal Python SDK (Context7)
- TaskIQ Documentation (Context7)
```

## MCP Интеграции

| MCP Server | Использование |
|------------|---------------|
| `user-context7` | Документация библиотек |
| `user-arxiv-mcp-server` | Научные статьи |
| `user-parrallel` | Web search, fetch |

## Кэширование

| Тип | TTL |
|-----|-----|
| Library docs | 7 дней |
| Web searches | 24 часа |
| arXiv papers | 30 дней |
| Internal | Без кэша (всегда актуально) |

## Связанные системы

| Система | Интеграция |
|---------|------------|
| **Memory** | Сохраняет synthesis в knowledge |
| **Standards** | Обогащает примерами |
| **Training** | Использует для обучающих материалов |

## Справка

Полная документация: `agent-os/knowledge/README.md`
