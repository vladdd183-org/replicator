# Ошибки категории: Асинхронный код

## Описание

Здесь собраны типичные ошибки связанные с асинхронным программированием: async/await, anyio, TaskGroups, блокирующие вызовы.

## Частые ошибки

### 1. Блокирующий вызов в async функции

**Симптом:** Приложение "зависает", низкая производительность, один запрос блокирует другие.
**Причина:** Вызов синхронной блокирующей функции (time.sleep, requests.get, bcrypt) в async коде.
**Решение:** Использовать anyio.to_thread.run_sync() для CPU-bound операций.

```python
# ❌ Плохо — блокирует event loop
async def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# ✅ Хорошо — выносим в thread pool
async def hash_password(password: str) -> str:
    return await anyio.to_thread.run_sync(
        lambda: bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    )
```

### 2. Использование asyncio вместо anyio

**Симптом:** Код привязан к asyncio, не работает с другими event loops.
**Причина:** Прямое использование asyncio.create_task(), asyncio.gather().
**Решение:** Использовать anyio для портабельности.

```python
# ❌ Плохо
import asyncio
await asyncio.gather(task1(), task2())

# ✅ Хорошо
import anyio
async with anyio.create_task_group() as tg:
    tg.start_soon(task1)
    tg.start_soon(task2)
```

### 3. Забытый await

**Симптом:** Функция возвращает coroutine object вместо результата.
**Причина:** Пропущен await перед async вызовом.
**Решение:** Всегда использовать await для async функций.

```python
# ❌ Плохо — result будет coroutine
result = fetch_data()

# ✅ Хорошо
result = await fetch_data()
```

### 4. Неправильная обработка отмены задач

**Симптом:** Ресурсы не освобождаются при отмене, утечки.
**Причина:** Не обрабатывается CancelledError.
**Решение:** Использовать try/finally или context managers.

```python
# ✅ Правильная обработка
async def process():
    try:
        await long_operation()
    finally:
        await cleanup()  # Выполнится даже при отмене
```

### 5. Race condition при shared state

**Симптом:** Непредсказуемое поведение, данные повреждаются.
**Причина:** Несколько корутин модифицируют общее состояние без синхронизации.
**Решение:** Использовать Lock или избегать shared mutable state.

```python
# ✅ Использование Lock
lock = anyio.Lock()
async with lock:
    shared_data.append(item)
```

---

*Файл будет дополняться по мере обнаружения новых паттернов ошибок.*
