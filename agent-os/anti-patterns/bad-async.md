# 🚫 Anti-patterns: Bad Async

> Ошибки асинхронного кода и как их исправить.

---

## 1. ❌ asyncio вместо anyio

### Плохо
```python
import asyncio

async def process_items(items):
    tasks = [asyncio.create_task(process(item)) for item in items]  # ❌
    await asyncio.gather(*tasks)
```

### Хорошо
```python
import anyio

async def process_items(items):
    async with anyio.create_task_group() as tg:  # ✅
        for item in items:
            tg.start_soon(process, item)
```

---

## 2. ❌ Fire-and-forget

### Плохо
```python
async def run(self, data):
    asyncio.create_task(send_notification(user.id))  # ❌ Забудется!
    return Success(user)
# Задача может не выполниться при shutdown
```

### Хорошо
```python
# Вариант 1: TaskGroup
async def run(self, data):
    async with anyio.create_task_group() as tg:
        tg.start_soon(send_notification, user.id)
    return Success(user)  # ✅ Дождёмся завершения

# Вариант 2: Events (рекомендуется)
async def run(self, data):
    self.uow.add_event(NotificationRequested(user_id=user.id))  # ✅
    return Success(user)
```

---

## 3. ❌ Блокирующий код в async

### Плохо
```python
async def run(self, data):
    # ❌ Блокирует event loop!
    password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt())
    return Success(user)
```

### Хорошо
```python
import anyio

async def run(self, data):
    # ✅ Выносим в thread pool
    password_hash = await anyio.to_thread.run_sync(
        self.hash_password.run, data.password
    )
    return Success(user)
```

---

## 4. ❌ sleep для polling

### Плохо
```python
async def wait_for_completion(job_id):
    while True:
        status = await get_status(job_id)
        if status == "done":
            return
        await asyncio.sleep(1)  # ❌ Бесконечный polling
```

### Хорошо
```python
# Вариант 1: Timeout
async def wait_for_completion(job_id):
    with anyio.fail_after(60):  # ✅ Timeout
        while True:
            status = await get_status(job_id)
            if status == "done":
                return
            await anyio.sleep(1)

# Вариант 2: Events/Channels (лучше)
async def wait_for_completion(job_id):
    async with channels.start_subscription([f"job:{job_id}"]) as sub:
        async for message in sub.iter_events():
            if message["status"] == "done":
                return
```

---

## 5. ❌ Игнорирование CancelledError

### Плохо
```python
async def process():
    try:
        await some_operation()
    except Exception:  # ❌ Ловит CancelledError!
        pass
```

### Хорошо
```python
import anyio

async def process():
    try:
        await some_operation()
    except anyio.get_cancelled_exc_class():
        raise  # ✅ Пробрасываем CancelledError
    except Exception:
        pass
```

---

## 6. ❌ Неправильная отмена

### Плохо
```python
async def run(self, data):
    task = asyncio.create_task(long_operation())
    
    if timeout_exceeded:
        task.cancel()  # ❌ Задача может не отмениться корректно
```

### Хорошо
```python
async def run(self, data):
    with anyio.move_on_after(30) as scope:  # ✅ Корректная отмена
        await long_operation()
    
    if scope.cancelled_caught:
        return Failure(TimeoutError())
```

---

## 7. ❌ async def без await

### Плохо
```python
async def get_config():  # ❌ Зачем async?
    return {"key": "value"}
```

### Хорошо
```python
def get_config():  # ✅ Обычная функция
    return {"key": "value"}

# Или если реально нужен async:
async def get_config():
    config = await load_from_db()  # ✅ Есть await
    return config
```

---

## 8. ❌ Shared mutable state

### Плохо
```python
results = []  # ❌ Shared state!

async def process_items(items):
    async with anyio.create_task_group() as tg:
        for item in items:
            tg.start_soon(process_and_append, item, results)
```

### Хорошо
```python
async def process_items(items):
    results = []
    lock = anyio.Lock()  # ✅ Защита через lock
    
    async def process_and_append(item):
        result = await process(item)
        async with lock:
            results.append(result)
    
    async with anyio.create_task_group() as tg:
        for item in items:
            tg.start_soon(process_and_append, item)
    
    return results
```

---

## 9. ❌ Неограниченный parallelism

### Плохо
```python
async def process_all(items):
    async with anyio.create_task_group() as tg:
        for item in items:  # ❌ 10000 параллельных задач!
            tg.start_soon(call_api, item)
```

### Хорошо
```python
from anyio import CapacityLimiter

async def process_all(items):
    limiter = CapacityLimiter(10)  # ✅ Максимум 10 параллельных
    
    async def limited_call(item):
        async with limiter:
            return await call_api(item)
    
    async with anyio.create_task_group() as tg:
        for item in items:
            tg.start_soon(limited_call, item)
```

---

## 📊 Сводка

| ❌ Ошибка | ✅ Решение |
|----------|-----------|
| `asyncio.create_task()` | `anyio.create_task_group()` |
| Fire-and-forget | TaskGroup или Events |
| Blocking в async | `anyio.to_thread.run_sync()` |
| Бесконечный polling | `anyio.fail_after()` |
| Catch all exceptions | Пробрасывать `CancelledError` |
| `task.cancel()` | `anyio.move_on_after()` |
| Shared mutable state | `anyio.Lock()` |
| Unlimited parallelism | `anyio.CapacityLimiter()` |



