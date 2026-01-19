# /add-query — Создание Query

Создание нового Query для CQRS Read операций.

## Источники

- **Инструкция:** `agent-os/commands/add-query.md`
- Skill: `.cursor/skills/add-query/SKILL.md`
- Template: `agent-os/templates/query.py.template`

## Синтаксис

```
/add-query <QueryName> [в <Module>] [--paginated]
```

## Примеры

```
/add-query GetUser в UserModule
/add-query ListUsers в UserModule --paginated
/add-query SearchOrders в OrderModule
/add-query GetUserStats в UserModule
```

## Параметры

- `<QueryName>` — Название Query (PascalCase, заканчивается на Query)
- `[в <Module>]` — Модуль для размещения (опционально)
- `[--paginated]` — Добавить пагинацию (page, per_page, total)

## Действие

1. Загрузи skill из `.cursor/skills/add-query/SKILL.md`
2. Создай `@dataclass(frozen=True)` для Input
3. Создай файл `Queries/<QueryName>.py`
4. Зарегистрируй в `Providers.py` (REQUEST scope)
5. Добавь в `Queries/__init__.py`

## Query vs Action (CQRS)

| Query (Read) | Action (Write) |
|--------------|----------------|
| Возвращает данные | Модифицирует данные |
| Без side effects | Создаёт/изменяет/удаляет |
| Прямое значение | `Result[T, E]` |
| Без UoW | Через UoW |
