# /generate-crud — Генерация полного CRUD

Генерация полного CRUD для сущности.

## Источники

- Инструкция: `agent-os/commands/generate-crud.md`
- Templates: `agent-os/templates/` (все)
- Workflow: `agent-os/workflows/create-module.md`

## Синтаксис

```
/generate-crud <Entity> [в <Module>] [поля: <fields>]
```

## Примеры

```
/generate-crud Product в ShopModule
/generate-crud Product в ShopModule поля: name:str, price:Decimal, stock:int
/generate-crud Category
```

## Действие

1. Загрузи инструкцию из `agent-os/commands/generate-crud.md`
2. Создай: Model, Errors, Events, Schemas, Repository, UoW, Queries, Actions, Controller, Listeners, Providers
3. Используй все templates из `agent-os/templates/`
4. Выведи список действий после генерации

