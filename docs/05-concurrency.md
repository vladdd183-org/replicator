# ⚡ Structured Concurrency с anyio

> **Версия:** 4.1 | **Дата:** Январь 2026  
> Безопасная конкурентность: TaskGroups, отмена, таймауты

---

## 🎯 Почему anyio, а не asyncio?

| Аспект | asyncio | anyio |
|--------|---------|-------|
| Backend | Только asyncio | asyncio + trio |
| TaskGroup | Python 3.11+ | Всегда доступен |
| Отмена | Сложная, флаги | Structured, автоматическая |
| Таймауты | `wait_for` | `move_on_after`, `fail_after` |
| Синхронизация | Примитивы asyncio | Унифицированные |
| Cancellation Scopes | Нет | Есть |
| Offload CPU-bound | `run_in_executor` | `to_thread.run_sync` |

---

## 🧵 Task Groups

### Базовое использование

```python
import anyio

async def fetch_all(urls: list[str]) -> list[dict]:
    results: list[dict] = []
    
    async with anyio.create_task_group() as tg:
        async def fetch_one(url: str) -> None:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                results.append(response.json())
        
        for url in urls:
            tg.start_soon(fetch_one, url)
    
    # Сюда дойдём только когда ВСЕ задачи завершены
    return results
```

### Ключевые гарантии

1. **Все задачи завершаются** — блок `async with` не завершится, пока все задачи не закончат
2. **Ошибка в одной → отмена всех** — если одна задача кидает exception, остальные отменяются
3. **Нет "runaway tasks"** — нельзя "забыть" про задачу

---

## 🚀 Реальные примеры из проекта

### CPU-bound offload в Action

```python
# src/Containers/AppSection/UserModule/Actions/CreateUserAction.py

async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
    # Check email exists...
    
    # Hash password — CPU-bound, offload to thread!
    password_hash = await anyio.to_thread.run_sync(
        self.hash_password.run, data.password
    )
    
    # Create user...
```

### WebSocket с TaskGroup

```python
# src/Containers/AppSection/UserModule/UI/WebSocket/Handlers.py

async def _handle_websocket_session(
    socket: WebSocket,
    user_id: UUID,
    channels: ChannelsPlugin,
    query: GetUserQuery,
) -> None:
    """WebSocket session with Structured Concurrency."""
    
    async with channels.start_subscription([f"user:{user_id}"]) as subscriber:
        
        async def handle_commands() -> None:
            """Handle incoming commands from client."""
            while True:
                try:
                    message = await socket.receive_json()
                except Exception:
                    return
                
                match message.get("command"):
                    case "refresh":
                        user = await query.execute(GetUserQueryInput(user_id=user_id))
                        if user:
                            await socket.send_json({
                                "event": "user_data",
                                "user": UserResponse.from_entity(user).model_dump(mode="json"),
                            })
                    case "ping":
                        await socket.send_json({"event": "pong"})
        
        async def handle_channel_messages() -> None:
            """Forward channel messages to WebSocket."""
            async for message in subscriber.iter_events():
                data = _decode_channel_message(message)
                await socket.send_json(data)
        
        # Structured Concurrency: обе задачи под контролем
        async with anyio.create_task_group() as tg:
            tg.start_soon(handle_commands)
            tg.start_soon(handle_channel_messages)
```

### Утилиты для конкурентности

```python
# src/Ship/Infrastructure/Concurrency/TaskGroup.py

async def run_concurrent(*tasks: Callable[[], Awaitable[T]]) -> list[T]:
    """Run multiple async tasks concurrently.
    
    All tasks will complete or cancel together.
    Results are returned in the same order as input tasks.
    
    Example:
        results = await run_concurrent(
            lambda: fetch_user(1),
            lambda: fetch_user(2),
            lambda: fetch_user(3),
        )
    """
    results: list[T | None] = [None] * len(tasks)
    
    async def run_indexed(index: int, task: Callable[[], Awaitable[T]]) -> None:
        results[index] = await task()
    
    async with anyio.create_task_group() as tg:
        for i, task in enumerate(tasks):
            tg.start_soon(run_indexed, i, task)
    
    return results


async def map_concurrent(
    func: Callable[[T], Awaitable[R]],
    items: Sequence[T],
    *,
    max_concurrent: int | None = None,
) -> list[R]:
    """Map an async function over items concurrently.
    
    Args:
        func: Async function to apply to each item
        items: Items to process
        max_concurrent: Maximum concurrent tasks (None = unlimited)
        
    Example:
        users = await map_concurrent(
            fetch_user,
            [1, 2, 3, 4, 5],
            max_concurrent=3,
        )
    """
    results: list[R | None] = [None] * len(items)
    
    if max_concurrent is not None:
        limiter = anyio.Semaphore(max_concurrent)
    else:
        limiter = None
    
    async def process(index: int, item: T) -> None:
        if limiter is not None:
            async with limiter:
                results[index] = await func(item)
        else:
            results[index] = await func(item)
    
    async with anyio.create_task_group() as tg:
        for i, item in enumerate(items):
            tg.start_soon(process, i, item)
    
    return results
```

---

## 🛑 Отмена и Cancellation Scopes

### Таймауты с `fail_after`

```python
import anyio

async def fetch_with_timeout(url: str) -> dict | None:
    """Запрос с таймаутом — кидает TimeoutError."""
    with anyio.fail_after(5.0):  # 5 секунд
        return await fetch_data(url)


async def fetch_with_fallback(url: str) -> dict:
    """Запрос с таймаутом — возвращает дефолт."""
    with anyio.move_on_after(5.0) as scope:
        return await fetch_data(url)
    
    # Если таймаут — продолжаем выполнение
    if scope.cancelled_caught:
        return {"error": "timeout", "url": url}
```

### Вложенные scopes

```python
async def complex_operation(urls: list[str]):
    # Внешний таймаут — 30 секунд на всё
    with anyio.fail_after(30.0):
        
        # Внутренний — 5 секунд на каждый запрос
        async with anyio.create_task_group() as tg:
            for url in urls:
                tg.start_soon(fetch_with_timeout, url)
```

### Shield от отмены

```python
async def save_important_data(data: dict):
    """Операция, которую нельзя прерывать."""
    
    # CancelScope.shield=True — игнорирует внешнюю отмену
    with anyio.CancelScope(shield=True):
        await db.save(data)
        await audit_log.write(f"Saved: {data['id']}")
```

---

## 🔄 Паттерны использования

### 1. Параллельные Tasks в Action

```python
class ProcessOrderAction(Action[OrderRequest, Order, OrderError]):
    """Обработка заказа с параллельными операциями."""
    
    async def run(self, data: OrderRequest) -> Result[Order, OrderError]:
        validation_results: list[tuple[str, Result]] = []
        
        async with anyio.create_task_group() as tg:
            async def validate_stock():
                result = await self.check_stock_task.run(data.items)
                validation_results.append(("stock", result))
            
            async def validate_user():
                result = await self.verify_user_task.run(data.user_id)
                validation_results.append(("user", result))
            
            async def validate_payment():
                result = await self.check_payment_task.run(data.payment_info)
                validation_results.append(("payment", result))
            
            tg.start_soon(validate_stock)
            tg.start_soon(validate_user)
            tg.start_soon(validate_payment)
        
        # Проверяем результаты
        for name, result in validation_results:
            match result:
                case Failure(error):
                    return Failure(OrderError.from_validation(name, error))
        
        return await self._create_order(data)
```

### 2. Graceful Degradation

```python
class SmartCache:
    """Кэш с fallback на source при таймауте."""
    
    async def get_or_fetch(
        self,
        key: str,
        fetcher: Callable[[], Awaitable[T]],
        cache_timeout: float = 0.1,  # 100ms на кэш
    ) -> T:
        # Пробуем кэш с коротким таймаутом
        with anyio.move_on_after(cache_timeout) as scope:
            cached = await self.redis.get(key)
            if cached:
                return deserialize(cached)
        
        # Таймаут или промах — идём в source
        if scope.cancelled_caught:
            logger.debug(f"Cache timeout for {key}")
        
        return await fetcher()
```

### 3. Batch Processing с лимитами

```python
class SendBatchNotificationsTask(Task[list[Notification], BatchResult]):
    """Отправка уведомлений с ограничением параллелизма."""
    
    def __init__(self, sender: NotificationSender, max_concurrent: int = 10):
        self.sender = sender
        self.limiter = anyio.CapacityLimiter(max_concurrent)
    
    async def run(self, notifications: list[Notification]) -> BatchResult:
        results: list[SendResult] = []
        
        async with anyio.create_task_group() as tg:
            async def send_one(notification: Notification):
                async with self.limiter:  # Ограничение параллелизма
                    result = await self.sender.send(notification)
                    results.append(result)
            
            for notification in notifications:
                tg.start_soon(send_one, notification)
        
        return BatchResult(
            total=len(notifications),
            successful=sum(1 for r in results if r.success),
            failed=sum(1 for r in results if not r.success),
        )
```

---

## 🔒 Синхронизация

### Lock

```python
import anyio

class CachedResourceManager:
    def __init__(self):
        self._lock = anyio.Lock()
        self._cache: dict[str, Resource] = {}
    
    async def get_or_create(self, key: str) -> Resource:
        # Быстрый путь без блокировки
        if key in self._cache:
            return self._cache[key]
        
        # Медленный путь с блокировкой
        async with self._lock:
            # Double-check после получения лока
            if key in self._cache:
                return self._cache[key]
            
            resource = await create_resource(key)
            self._cache[key] = resource
            return resource
```

### Semaphore (для rate limiting)

```python
import anyio

class RateLimitedClient:
    def __init__(self, max_requests_per_second: int = 10):
        self._semaphore = anyio.Semaphore(max_requests_per_second)
    
    async def request(self, url: str) -> Response:
        async with self._semaphore:
            try:
                return await self._do_request(url)
            finally:
                await anyio.sleep(1.0)  # Освобождаем слот через секунду
```

### Event (для координации)

```python
import anyio

class ServiceManager:
    def __init__(self):
        self._ready = anyio.Event()
    
    async def start(self):
        await self._initialize()
        self._ready.set()  # Сигнализируем о готовности
    
    async def wait_ready(self):
        await self._ready.wait()
```

---

## ⚠️ Обработка ExceptionGroup

### Python 3.11+ except*

```python
async def process_with_handlers():
    try:
        async with anyio.create_task_group() as tg:
            tg.start_soon(task_that_might_fail_validation)
            tg.start_soon(task_that_might_fail_network)
    except* ValidationError as exc_group:
        for exc in exc_group.exceptions:
            logger.warning(f"Validation: {exc}")
    except* NetworkError as exc_group:
        for exc in exc_group.exceptions:
            logger.error(f"Network: {exc}")
```

### С exceptiongroup.catch

```python
from exceptiongroup import catch, ExceptionGroup

async def process_with_error_handling():
    def handle_validation_errors(exc_group: ExceptionGroup) -> None:
        for exc in exc_group.exceptions:
            if isinstance(exc, ValidationError):
                logger.warning(f"Validation failed: {exc}")
    
    def handle_network_errors(exc_group: ExceptionGroup) -> None:
        for exc in exc_group.exceptions:
            if isinstance(exc, NetworkError):
                logger.error(f"Network error: {exc}")
    
    with catch({
        ValidationError: handle_validation_errors,
        NetworkError: handle_network_errors,
    }):
        async with anyio.create_task_group() as tg:
            tg.start_soon(task1)
            tg.start_soon(task2)
```

---

## 🛠️ Result + anyio

### Используй `returns.iterables.Fold.collect`

```python
from returns.iterables import Fold
from returns.result import Result, Success, Failure

# Собрать все успешные результаты или вернуть первую ошибку
results: list[Result[int, str]] = [Success(1), Success(2), Success(3)]
collected: Result[tuple[int, ...], str] = Fold.collect(results, Success(()))
# => Success((1, 2, 3))

# Если есть ошибка — вернётся первая
results_with_error = [Success(1), Failure("error"), Success(3)]
collected = Fold.collect(results_with_error, Success(()))
# => Failure("error")
```

### Параллельное выполнение с Result

```python
import anyio
from returns.result import Result, Success
from returns.iterables import Fold

async def parallel_with_results(
    tasks: list[Callable[[], Awaitable[Result[T, E]]]]
) -> Result[tuple[T, ...], E]:
    """Параллельное выполнение с Fold.collect."""
    results: list[Result[T, E]] = []
    
    async with anyio.create_task_group() as tg:
        async def run_and_store(task):
            results.append(await task())
        
        for task in tasks:
            tg.start_soon(run_and_store, task)
    
    return Fold.collect(results, Success(()))
```

---

## 📋 Чеклист

### Когда использовать TaskGroup

- ✅ Несколько независимых async операций
- ✅ Нужна гарантия завершения всех задач
- ✅ Ошибка в одной должна отменить остальные

### Когда использовать CapacityLimiter/Semaphore

- ✅ Ограничение параллелизма (API rate limits)
- ✅ Защита ресурсов (connections, memory)

### Когда использовать CancelScope

- ✅ Таймауты на операции
- ✅ Graceful degradation
- ✅ Shield критических операций

### Когда offload в thread

- ✅ CPU-bound операции (bcrypt, json parsing)
- ✅ Блокирующий синхронный код

```python
# CPU-bound → anyio.to_thread.run_sync
hash = await anyio.to_thread.run_sync(bcrypt.hashpw, password, salt)
```

---

<div align="center">

**Следующий раздел:** [06-metaprogramming.md](06-metaprogramming.md) — Сокращение бойлерплейта

</div>
