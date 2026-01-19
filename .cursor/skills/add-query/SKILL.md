---
name: add-query
description: Create new Query (CQRS Read operation) for Hyper-Porto architecture. Queries read data without side effects. Use when the user wants to add query, create query, cqrs read, добавить query, получить данные.
---

# Add Query (CQRS Read Operation)

Создание Query по архитектуре Hyper-Porto CQRS.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Инструкция** | `agent-os/commands/add-query.md` |
| **Template** | `agent-os/templates/query.py.template` |
| **Standard** | `agent-os/standards/backend/queries.md` |
| **Snippets** | `agent-os/snippets/query-patterns.md` |

## Быстрая справка

| Правило | Описание |
|---------|----------|
| **Purpose** | Read-only получение данных |
| **Returns** | Прямое значение (НЕ `Result[T, E]`) |
| **Side effects** | НИКАКИХ — никогда не модифицирует данные |
| **Method** | `execute()`, не `run()` |
| **DI** | Регистрация в `Providers.py` (REQUEST scope) |

## Query vs Action (CQRS)

| Аспект | Query (Read) | Action (Write) |
|--------|--------------|----------------|
| **Returns** | `T` или `None` | `Result[T, E]` |
| **UoW** | НЕ использует | Использует |
| **Events** | НЕ эмитит | Эмитит |
| **Controller** | Без `@result_handler` | С `@result_handler` |

## Действие

1. **Загрузи** полную инструкцию из `agent-os/commands/add-query.md`
2. **Используй** template из `agent-os/templates/query.py.template`
3. **Создай** Query файл в `Queries/[QueryName].py`
4. **Создай** `@dataclass(frozen=True)` для Input
5. **Зарегистрируй** в `Providers.py` (REQUEST scope)

## Именование

| Операция | Паттерн | Пример |
|----------|---------|--------|
| Get single | `Get{Entity}Query` | `GetUserQuery` |
| List | `List{Entity}sQuery` | `ListUsersQuery` |
| Search | `Search{Entity}sQuery` | `SearchUsersQuery` |
| Stats | `Get{Entity}StatsQuery` | `GetUserStatsQuery` |
