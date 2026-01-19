# /add-action — Создание Action

Создание нового Action (Use Case).

## Источники

- Инструкция: `agent-os/commands/add-action.md`
- Template: `agent-os/templates/action.py.template`
- Checklist: `agent-os/checklists/action-implementation.md`

## Синтаксис

```
/add-action <ActionName> [в <Module>] [с событием <EventName>]
```

## Примеры

```
/add-action ActivateUser в UserModule
/add-action ApproveOrder в OrderModule с событием OrderApproved
/add-action ResetPassword
```

## Действие

1. Загрузи инструкцию из `agent-os/commands/add-action.md`
2. Используй template из `agent-os/templates/action.py.template`
3. Создай Action, Event (если указан), Listener
4. Зарегистрируй в Providers.py

