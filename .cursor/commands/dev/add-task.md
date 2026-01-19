# /add-task — Создание Task

Создание нового Task (атомарной операции).

## Источники

- **Инструкция:** `agent-os/commands/add-task.md`
- Skill: `.cursor/skills/add-task/SKILL.md`
- Template: `agent-os/templates/task.py.template`

## Синтаксис

```
/add-task <TaskName> [в <Module>] [--sync]
```

## Примеры

```
/add-task HashPassword в UserModule --sync
/add-task GenerateToken в UserModule
/add-task SendEmail в EmailModule
/add-task ValidateAddress в OrderModule
```

## Параметры

- `<TaskName>` — Название Task (PascalCase, заканчивается на Task)
- `[в <Module>]` — Модуль для размещения (опционально)
- `[--sync]` — Создать SyncTask для CPU-bound операций

## Действие

1. Загрузи skill из `.cursor/skills/add-task/SKILL.md`
2. Определи тип: `Task[I, O]` или `SyncTask[I, O]`
3. Создай файл `Tasks/<TaskName>.py`
4. Зарегистрируй в `Providers.py` (APP scope)
5. Добавь в `Tasks/__init__.py`

## Task Types

| Тип | Использование | Вызов |
|-----|---------------|-------|
| `Task[I, O]` | Async I/O операции | `await task.run(data)` |
| `SyncTask[I, O]` | CPU-bound операции | `await anyio.to_thread.run_sync(task.run, data)` |
