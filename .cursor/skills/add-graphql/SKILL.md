---
name: add-graphql
description: Create GraphQL Types and Resolvers using Strawberry for Hyper-Porto. Use when the user wants to add graphql, create resolver, strawberry, добавить graphql, graphql type, мутация graphql.
---

# Add GraphQL Types & Resolvers

Создание GraphQL схемы с использованием Strawberry.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Инструкция** | `agent-os/commands/add-graphql.md` |
| **Template** | `agent-os/templates/graphql-resolver.py.template` |
| **Docs** | `docs/09-transports.md` (GraphQL секция) |
| **Library** | `foxdocs/strawberry-main/docs/` |

## Быстрая справка

| Правило | Описание |
|---------|----------|
| **Library** | Strawberry GraphQL |
| **Types** | В `UI/GraphQL/Types.py` |
| **Resolvers** | В `UI/GraphQL/Resolvers.py` |
| **DI** | Через `get_dependency()` helper |
| **Auth** | Через `Info` context |

## Действие

1. **Загрузи** полную инструкцию из `agent-os/commands/add-graphql.md`
2. **Создай** Types в `UI/GraphQL/Types.py`:
   - `@strawberry.type` для entities
   - `@strawberry.input` для inputs
   - `from_entity()` classmethod
3. **Создай** Resolvers в `UI/GraphQL/Resolvers.py`:
   - Query class для read операций
   - Mutation class для write операций
4. **Добавь** в root Schema в `Ship/GraphQL/Schema.py`

## Структура

```
UI/GraphQL/
├── Types.py      # @strawberry.type, @strawberry.input
└── Resolvers.py  # Query, Mutation classes

Ship/GraphQL/
├── Schema.py     # Root schema assembly
└── Helpers.py    # get_dependency(), get_current_user()
```

## DI в Resolvers

```python
from src.Ship.GraphQL.Helpers import get_dependency

@strawberry.field
async def user(self, info: Info, id: UUID) -> UserType | None:
    query = await get_dependency(info, GetUserQuery)
    result = await query.execute(GetUserQueryInput(user_id=id))
    return UserType.from_entity(result) if result else None
```
