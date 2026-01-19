# 🎮 Command: /add-worker

> Создание Background Worker Task (TaskIQ).

---

## Синтаксис

```
/add-worker <TaskName> [в <Module>] [scheduled <cron>]
```

## Параметры

| Параметр | Обязательный | Пример |
|----------|--------------|--------|
| TaskName | ✅ | `SendEmail`, `ProcessImport`, `CleanupLogs` |
| Module | ❌ | `EmailModule` |
| scheduled | ❌ | Cron expression для периодического запуска |

---

## Ключевые правила

| Правило | Описание |
|---------|----------|
| **Library** | TaskIQ |
| **Location** | `UI/Workers/Tasks.py` |
| **Broker** | Redis (production) или InMemory (dev) |
| **Scheduling** | Через `task.kiq()` или schedule |
| **DI** | Через Dishka integration |

---

## Примеры

### Обычный task
```
/add-worker SendEmail в EmailModule
```
→ Создаст background task для отправки email

### Scheduled task
```
/add-worker CleanupLogs в AuditModule scheduled "0 3 * * *"
```
→ Создаст task с cron-расписанием (каждый день в 3:00)

---

## Что создаётся

### 1. Email Task

`UI/Workers/Tasks.py`:

```python
"""Background tasks for EmailModule."""

from src.Ship.Infrastructure.Workers.Broker import broker


@broker.task(
    retry_on_error=True,
    max_retries=3,
)
async def send_email_task(
    to: str,
    subject: str,
    body: str,
    template: str | None = None,
) -> bool:
    """Send email asynchronously.
    
    Triggered by:
    - UserCreated event (welcome email)
    - OrderCreated event (confirmation)
    - PasswordReset action
    
    Retries: 3 times with exponential backoff
    """
    from src.Containers.VendorSection.EmailModule.Tasks.SendEmailTask import SendEmailTask
    
    task = SendEmailTask()
    
    if template:
        body = await task.render_template(template, body)
    
    await task.run(EmailPayload(to=to, subject=subject, body=body))
    return True
```

**Использование:**

```python
# In Action or Listener
from src.Containers.VendorSection.EmailModule.UI.Workers.Tasks import send_email_task

# Enqueue task
await send_email_task.kiq(
    to="user@example.com",
    subject="Welcome!",
    body="Hello, welcome to our app!",
)

# With delay
await send_email_task.kiq(
    to="user@example.com",
    subject="Follow up",
    body="How's it going?",
).with_delay(hours=24)
```

### 2. Import Processing Task

```python
"""Background tasks for UserModule."""

from uuid import UUID

from src.Ship.Infrastructure.Workers.Broker import broker


@broker.task(
    timeout=600,  # 10 minutes max
    max_retries=1,
)
async def import_users_task(
    file_path: str,
    import_id: UUID,
    user_id: UUID,
) -> dict:
    """Process bulk user import from CSV/Excel.
    
    Long-running task that:
    1. Reads file from storage
    2. Validates each row
    3. Creates users in batches
    4. Reports progress via WebSocket
    
    Timeout: 10 minutes
    """
    from src.Containers.AppSection.UserModule.Actions.BulkCreateUsersAction import (
        BulkCreateUsersAction,
    )
    
    # Get dependencies
    action = await get_task_dependency(BulkCreateUsersAction)
    channels = await get_task_dependency(ChannelsPlugin)
    
    total = 0
    created = 0
    errors = []
    
    async for batch in read_file_batches(file_path, batch_size=100):
        result = await action.run(batch)
        
        match result:
            case Success(users):
                created += len(users)
            case Failure(error):
                errors.append(str(error))
        
        total += len(batch)
        
        # Report progress
        await channels.publish(
            {
                "type": "import_progress",
                "import_id": str(import_id),
                "total": total,
                "created": created,
                "errors": len(errors),
            },
            channels=[f"import:{user_id}"],
        )
    
    return {
        "import_id": str(import_id),
        "total": total,
        "created": created,
        "errors": errors,
    }
```

### 3. Scheduled Cleanup Task

```python
"""Background tasks for AuditModule."""

from datetime import datetime, timedelta, UTC

from src.Ship.Infrastructure.Workers.Broker import broker


@broker.task
async def cleanup_old_logs_task(days_to_keep: int = 90) -> dict:
    """Clean up audit logs older than specified days.
    
    Scheduled: Daily at 3:00 AM
    """
    from src.Containers.AppSection.AuditModule.Data.Repositories.AuditRepository import (
        AuditRepository,
    )
    
    repo = await get_task_dependency(AuditRepository)
    
    cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)
    deleted_count = await repo.delete_before(cutoff_date)
    
    return {
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat(),
    }


@broker.task
async def generate_daily_report_task() -> str:
    """Generate daily activity report.
    
    Scheduled: Daily at 6:00 AM
    """
    from src.Containers.AppSection.AuditModule.Queries.GetDailyStatsQuery import (
        GetDailyStatsQuery,
    )
    
    query = await get_task_dependency(GetDailyStatsQuery)
    stats = await query.execute(None)
    
    # Generate report
    report_url = await generate_report_pdf(stats)
    
    # Send to admins
    await send_email_task.kiq(
        to="admin@example.com",
        subject=f"Daily Report - {datetime.now(UTC).date()}",
        body=f"Report available at: {report_url}",
    )
    
    return report_url
```

### 4. Event-Driven Task

```python
"""Background tasks for NotificationModule."""

from uuid import UUID

from src.Ship.Infrastructure.Workers.Broker import broker


@broker.task(max_retries=3)
async def send_push_notification_task(
    user_id: UUID,
    title: str,
    body: str,
    data: dict | None = None,
) -> bool:
    """Send push notification to user's devices.
    
    Triggered by domain events:
    - OrderShipped
    - PaymentReceived
    - NewMessage
    """
    from src.Containers.AppSection.NotificationModule.Tasks.SendPushTask import SendPushTask
    from src.Containers.AppSection.UserModule.Data.Repositories.DeviceRepository import (
        DeviceRepository,
    )
    
    device_repo = await get_task_dependency(DeviceRepository)
    push_task = await get_task_dependency(SendPushTask)
    
    devices = await device_repo.get_user_devices(user_id)
    
    for device in devices:
        await push_task.run(PushPayload(
            token=device.push_token,
            title=title,
            body=body,
            data=data or {},
        ))
    
    return True
```

---

## Broker Configuration

```python
# In Ship/Infrastructure/Workers/Broker.py
"""TaskIQ broker configuration."""

from taskiq import TaskiqScheduler
from taskiq_redis import RedisAsyncResultBackend, ListQueueBroker

from src.Ship.Configs.Settings import get_settings


settings = get_settings()

# Redis broker for production
broker = ListQueueBroker(
    url=settings.redis_url,
).with_result_backend(
    RedisAsyncResultBackend(
        redis_url=settings.redis_url,
    )
)

# Scheduler for periodic tasks
scheduler = TaskiqScheduler(
    broker=broker,
    sources=["src.Containers.*.UI.Workers.Tasks"],
)
```

---

## Scheduling Tasks

```python
# In Workers/Tasks.py
from taskiq import TaskiqScheduler

from src.Ship.Infrastructure.Workers.Broker import scheduler


# Schedule cleanup at 3:00 AM daily
scheduler.schedule(
    cleanup_old_logs_task.kiq(days_to_keep=90),
    cron="0 3 * * *",
)

# Schedule report at 6:00 AM daily
scheduler.schedule(
    generate_daily_report_task.kiq(),
    cron="0 6 * * *",
)

# Every hour
scheduler.schedule(
    sync_external_data_task.kiq(),
    cron="0 * * * *",
)
```

---

## Использование из Actions/Listeners

```python
# In Action
from src.Containers.VendorSection.EmailModule.UI.Workers.Tasks import send_email_task


class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        async with self.uow:
            user = AppUser(...)
            await self.uow.users.add(user)
            await self.uow.commit()
        
        # Enqueue background task (non-blocking)
        await send_email_task.kiq(
            to=user.email,
            subject="Welcome!",
            body=f"Hello {user.name}!",
        )
        
        return Success(user)
```

```python
# In Listener
from src.Containers.AppSection.NotificationModule.UI.Workers.Tasks import (
    send_push_notification_task,
)


async def on_order_shipped(event: OrderShipped) -> None:
    """Send push notification when order ships."""
    await send_push_notification_task.kiq(
        user_id=event.user_id,
        title="Order Shipped!",
        body=f"Your order {event.order_id} is on its way!",
        data={"order_id": str(event.order_id)},
    )
```

---

## Task с DI (Dishka Integration)

```python
# In Ship/Infrastructure/Workers/DI.py
"""TaskIQ Dishka integration."""

from dishka import AsyncContainer
from taskiq import TaskiqState

from src.Ship.Providers.AppProvider import create_container


_container: AsyncContainer | None = None


async def get_task_dependency(dependency_type: type[T]) -> T:
    """Get dependency from Dishka container in task context."""
    global _container
    
    if _container is None:
        _container = create_container()
    
    async with _container() as request_container:
        return await request_container.get(dependency_type)
```

---

## Запуск Workers

```bash
# Start worker
taskiq worker src.Ship.Infrastructure.Workers.Broker:broker

# Start scheduler (for periodic tasks)
taskiq scheduler src.Ship.Infrastructure.Workers.Broker:scheduler

# With multiple workers
taskiq worker src.Ship.Infrastructure.Workers.Broker:broker --workers 4
```

---

## Структура файлов

```
src/Containers/[Section]/[Module]/
└── UI/
    └── Workers/
        ├── __init__.py
        └── Tasks.py          # @broker.task functions

src/Ship/Infrastructure/Workers/
├── Broker.py                 # TaskIQ broker config
└── DI.py                     # Dishka integration
```

---

## Действия после создания

1. ✅ Создать `UI/Workers/Tasks.py`
2. ✅ Использовать `@broker.task` декоратор
3. ✅ Установить `max_retries` и `timeout`
4. ✅ Документировать triggers в docstring
5. ✅ Добавить в scheduler если periodic
6. ✅ Протестировать task execution
7. ✅ Протестировать retry behavior

---

## Типичные ошибки

| ❌ Неправильно | ✅ Правильно |
|----------------|-------------|
| Sync blocking код | Только async операции |
| Нет retry config | Установить `max_retries` для unreliable ops |
| Огромные payloads | Передавать IDs, fetch data в task |
| Нет timeout | Установить reasonable `timeout` |
| Прямой DB access | Использовать Repository/Query |

---

## Связанные ресурсы

- **Template:** `../templates/background-task.py.template`
- **Docs:** `docs/09-transports.md` (Background Tasks секция)
- **Library docs:** `foxdocs/taskiq-litestar-develop/`
