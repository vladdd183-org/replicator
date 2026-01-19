# /add-graphql — Создание GraphQL Resolvers

Создание GraphQL Types и Resolvers с использованием Strawberry.

## Источники

- **Инструкция:** `agent-os/commands/add-graphql.md`
- Skill: `.cursor/skills/add-graphql/SKILL.md`
- Docs: `docs/09-transports.md`

## Синтаксис

```
/add-graphql <Entity> [в <Module>] [--type query|mutation|both]
```

## Примеры

```
/add-graphql User в UserModule --type both
/add-graphql Order в OrderModule --type query
/add-graphql Payment в PaymentModule --type mutation
```

## Параметры

- `<Entity>` — Название сущности (PascalCase)
- `[в <Module>]` — Модуль для размещения
- `[--type]` — Тип resolvers (query, mutation, both)

## Действие

1. Загрузи skill из `.cursor/skills/add-graphql/SKILL.md`
2. Создай `UI/GraphQL/Types.py` с `@strawberry.type`
3. Создай `UI/GraphQL/Resolvers.py` с Query/Mutation
4. Добавь в корневой Schema (`Ship/GraphQL/Schema.py`)

## Структура файлов

```
UI/GraphQL/
├── __init__.py
├── Types.py          # @strawberry.type, @strawberry.input
└── Resolvers.py      # Query и Mutation классы
```

## DI в GraphQL

```python
from src.Ship.GraphQL.Helpers import get_dependency

@strawberry.field
async def user(self, info: Info, id: UUID) -> UserType:
    query = await get_dependency(info, GetUserQuery)
    return await query.execute(...)
```
