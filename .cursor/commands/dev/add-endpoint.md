# /add-endpoint — Добавление REST endpoint

Добавление нового REST API endpoint.

## Источники

- Инструкция: `agent-os/commands/add-endpoint.md`
- Workflow: `agent-os/workflows/add-api-endpoint.md`
- Templates: `agent-os/templates/controller.py.template`, `agent-os/templates/action.py.template`

## Синтаксис

```
/add-endpoint <METHOD> <path> [для <ActionName>] [в <Module>]
```

## Примеры

```
/add-endpoint POST /orders для CreateOrderAction в OrderModule
/add-endpoint GET /users/active в UserModule
/add-endpoint PATCH /users/{id}/status для UpdateUserStatusAction
/add-endpoint DELETE /orders/{id} для DeleteOrderAction
```

## Действие

1. Загрузи инструкцию из `agent-os/commands/add-endpoint.md`
2. Определи тип операции (read/write)
3. Создай Action/Query + DTO + Endpoint
4. Зарегистрируй в Providers.py

