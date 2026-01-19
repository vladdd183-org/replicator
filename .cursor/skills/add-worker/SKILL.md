---
name: add-worker
description: Create TaskIQ background worker task for Hyper-Porto. Use when the user wants to add worker, background task, taskiq, добавить воркер, фоновая задача, очередь задач.
---

# Add Background Worker Task

Создание TaskIQ background task.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Инструкция** | `agent-os/commands/add-worker.md` |
| **Template** | `agent-os/templates/background-task.py.template` |
| **Docs** | `docs/09-transports.md` (Background Tasks секция) |
| **Library** | <https://taskiq-python.github.io/taskiq-litestar/> |

## Быстрая справка

| Правило | Описание |
|---------|----------|
| **Library** | TaskIQ |
| **Location** | `UI/Workers/Tasks.py` |
| **Broker** | Redis (production) / InMemory (dev) |
| **Scheduling** | Через `task.kiq()` или scheduler |
| **DI** | Через Dishka integration |

## Действие

1. **Загрузи** полную инструкцию из `agent-os/commands/add-worker.md`
2. **Создай** task в `UI/Workers/Tasks.py`
3. **Используй** `@broker.task` декоратор
4. **Настрой** `max_retries`, `timeout` по необходимости
5. **Добавь** в scheduler если periodic task

## Базовая структура

```python
from src.Ship.Infrastructure.Workers.Broker import broker

@broker.task(max_retries=3)
async def send_email_task(to: str, subject: str, body: str) -> bool:
    """Send email asynchronously."""
    # Implementation
    return True
```

## Вызов из Action/Listener

```python
# Enqueue task
await send_email_task.kiq(to="user@example.com", subject="Hi", body="...")

# With delay
await send_email_task.kiq(...).with_delay(hours=1)
```

## Scheduled tasks

```python
from src.Ship.Infrastructure.Workers.Broker import scheduler

scheduler.schedule(
    cleanup_task.kiq(days=90),
    cron="0 3 * * *",  # Daily at 3 AM
)
```

## Запуск workers

```bash
uv run taskiq worker src.Ship.Infrastructure.Workers.Broker:broker
uv run taskiq scheduler src.Ship.Infrastructure.Workers.Broker:scheduler
```
