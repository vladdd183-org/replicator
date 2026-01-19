# /add-worker — Создание Background Worker

Создание TaskIQ background task.

## Источники

- **Инструкция:** `agent-os/commands/add-worker.md`
- Skill: `.cursor/skills/add-worker/SKILL.md`
- Docs: `docs/09-transports.md`

## Синтаксис

```
/add-worker <TaskName> [в <Module>] [--scheduled <cron>]
```

## Примеры

```
/add-worker SendEmail в EmailModule
/add-worker CleanupLogs в AuditModule --scheduled "0 3 * * *"
/add-worker ProcessImport в UserModule
/add-worker GenerateReport в SettingsModule --scheduled "0 6 * * *"
```

## Параметры

- `<TaskName>` — Название task (PascalCase)
- `[в <Module>]` — Модуль для размещения
- `[--scheduled]` — Cron expression для периодических задач

## Действие

1. Загрузи инструкцию из `agent-os/commands/add-worker.md`
2. Создай `UI/Workers/Tasks.py`
3. Используй `@broker.task` декоратор
4. Настрой `max_retries`, `timeout`
5. Добавь в scheduler если periodic

## Worker Template

```python
from src.Ship.Infrastructure.Workers.Broker import broker

@broker.task(max_retries=3)
async def my_task(param: str) -> bool:
    """Background task description."""
    # Implementation
    return True
```

## Вызов из Action/Listener

```python
await my_task.kiq(param="value")

# С задержкой
await my_task.kiq(param="value").with_delay(hours=1)
```

## Запуск workers

```bash
taskiq worker src.Ship.Infrastructure.Workers.Broker:broker
taskiq scheduler src.Ship.Infrastructure.Workers.Broker:scheduler
```
