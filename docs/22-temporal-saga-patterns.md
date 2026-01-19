# 🎭 Temporal Saga Patterns

> **Версия:** 1.0 | **Дата:** Январь 2026  
> Паттерны компенсаций для Temporal.io с интеграцией Railway-Oriented Programming

---

## 🎯 Проблема

Классический подход к Saga в Temporal создаёт "лестницу вложенности":

```python
# ❌ Антипаттерн — вложенные try/except
@workflow.defn
class CreateOrderWorkflow:
    @workflow.run
    async def run(self, data):
        order_id = await execute_activity(create_order, ...)
        try:
            reservation_id = await execute_activity(reserve_inventory, ...)
            try:
                payment_id = await execute_activity(charge_payment, ...)
                try:
                    delivery_id = await execute_activity(schedule_delivery, ...)
                    return Success(...)
                except:
                    await execute_activity(refund_payment, payment_id)
                    raise
            except:
                await execute_activity(cancel_reservation, reservation_id)
                raise
        except:
            await execute_activity(cancel_order, order_id)
            return Failure(...)
```

**Проблемы:**
- Каждый новый шаг добавляет уровень вложенности
- Сложно читать и поддерживать
- Легко ошибиться с порядком компенсаций

---

## 📦 Официальный паттерн Temporal

### Что есть из коробки

| SDK | Встроенная абстракция |
|-----|----------------------|
| **Java** | ✅ `io.temporal.workflow.Saga` — полноценный класс |
| **Python** | ❌ Нет класса, но есть **официальный паттерн** |
| **Go** | ❌ Используют `defer` |
| **TypeScript** | ❌ Простой массив |

### Официальный Python паттерн

Из [temporal-compensating-transactions](https://github.com/temporalio/temporal-compensating-transactions):

```python
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

@workflow.defn
class BookingWorkflow:
    
    @workflow.run
    async def run(self, data: BookVacationInput) -> dict:
        compensations: list[Callable] = []  # Просто список!
        
        try:
            # Регистрируем компенсацию ПЕРЕД выполнением
            compensations.append(undo_book_car)
            car_result = await workflow.execute_activity(
                book_car, data,
                start_to_close_timeout=timedelta(seconds=10),
            )
            
            compensations.append(undo_book_hotel)
            hotel_result = await workflow.execute_activity(
                book_hotel, data,
                start_to_close_timeout=timedelta(seconds=10),
            )
            
            compensations.append(undo_book_flight)
            flight_result = await workflow.execute_activity(
                book_flight, data,
                start_to_close_timeout=timedelta(seconds=10),
            )
            
            return {"status": "success", "results": {...}}
            
        except Exception as ex:
            # Компенсации в ОБРАТНОМ порядке (LIFO)
            for compensation in reversed(compensations):
                await workflow.execute_activity(
                    compensation, data,
                    start_to_close_timeout=timedelta(seconds=10),
                )
            return {"status": "failure", "message": str(ex)}
```

**Ключевые моменты:**
1. `compensations.append()` **ДО** выполнения activity
2. `reversed(compensations)` — LIFO порядок
3. Минималистично и идиоматично для Python

---

## 🚂 Интеграция с Porto (Railway + Temporal)

### Базовый паттерн с Result

```python
from temporalio import workflow
from temporalio.common import RetryPolicy
from returns.result import Result, Success, Failure
from datetime import timedelta
from typing import Callable

@workflow.defn
class CreateOrderWorkflow:
    """Saga с Railway-Oriented Programming."""
    
    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        compensations: list[Callable] = []
        
        try:
            # Step 1: Create order
            compensations.append(cancel_order)
            order_id = await workflow.execute_activity(
                create_order, data,
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            # Step 2: Reserve inventory
            compensations.append(cancel_reservation)
            reservation_id = await workflow.execute_activity(
                reserve_inventory, order_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            # Step 3: Charge payment
            compensations.append(refund_payment)
            payment_id = await workflow.execute_activity(
                charge_payment, order_id,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            
            # Step 4: Schedule delivery (no compensation)
            delivery_id = await workflow.execute_activity(
                schedule_delivery, order_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            # ✅ Success — Railway Success track
            return Success(OrderResult(
                order_id=order_id,
                reservation_id=reservation_id,
                payment_id=payment_id,
                delivery_id=delivery_id,
            ))
            
        except Exception as ex:
            # Run compensations in reverse
            for comp in reversed(compensations):
                await workflow.execute_activity(
                    comp, data,
                    start_to_close_timeout=timedelta(seconds=30),
                )
            # ❌ Failure — Railway Failure track
            return Failure(OrderCreationFailed(reason=str(ex)))
```

---

## 🔧 Расширенный паттерн с Compensations класом

Когда нужно больше контроля (аргументы для компенсаций, параллельное выполнение):

```python
from temporalio import workflow
from dataclasses import dataclass, field
from typing import Callable, Any
from datetime import timedelta
import asyncio

@dataclass
class SagaCompensations:
    """
    Compensation tracker с поддержкой:
    - Аргументов для каждой компенсации
    - Параллельного выполнения
    - Graceful error handling
    """
    _stack: list[tuple[Callable, tuple[Any, ...]]] = field(default_factory=list)
    parallel: bool = False
    timeout: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    
    def add(self, func: Callable, *args: Any) -> None:
        """Добавить компенсацию с аргументами."""
        self._stack.append((func, args))
    
    def __iadd__(self, func: Callable) -> "SagaCompensations":
        """Синтаксический сахар: comp += cancel_order"""
        self.add(func)
        return self
    
    async def run_all(self) -> None:
        """Выполнить все компенсации."""
        if not self._stack:
            return
            
        if self.parallel:
            await self._run_parallel()
        else:
            await self._run_sequential()
    
    async def _run_sequential(self) -> None:
        """LIFO — последовательно в обратном порядке."""
        for func, args in reversed(self._stack):
            await self._execute_one(func, args)
    
    async def _run_parallel(self) -> None:
        """Все компенсации параллельно."""
        tasks = [
            self._execute_one(func, args)
            for func, args in self._stack
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_one(self, func: Callable, args: tuple) -> None:
        """Выполнить одну компенсацию с error handling."""
        try:
            await workflow.execute_activity(
                func, *args,
                start_to_close_timeout=self.timeout,
            )
        except Exception:
            workflow.logger.exception(
                f"Compensation {func.__name__} failed, continuing..."
            )
```

### Использование

```python
@workflow.defn
class CreateOrderWorkflow:
    
    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        comp = SagaCompensations()
        
        try:
            # С аргументами
            order = await workflow.execute_activity(create_order, data, ...)
            comp.add(cancel_order, order.id)  # передаём order.id
            
            reservation = await workflow.execute_activity(reserve_inventory, order.id, ...)
            comp.add(cancel_reservation, reservation.id)
            
            payment = await workflow.execute_activity(charge_payment, order.id, ...)
            comp.add(refund_payment, payment.id, payment.amount)  # несколько аргументов
            
            delivery = await workflow.execute_activity(schedule_delivery, order.id, ...)
            
            return Success(OrderResult(...))
            
        except Exception as ex:
            await comp.run_all()
            return Failure(OrderCreationFailed(reason=str(ex)))
```

---

## 🎨 Декларативный паттерн (для сложных workflows)

Когда Saga имеет сложные зависимости между шагами:

```python
from dataclasses import dataclass
from typing import Callable, Any
from datetime import timedelta

@dataclass(frozen=True)
class SagaStep:
    """Декларативное описание шага Saga."""
    name: str
    action: Callable
    compensate: Callable | None = None
    timeout: timedelta = timedelta(seconds=30)
    retry_policy: RetryPolicy | None = None


async def execute_saga(
    steps: list[SagaStep],
    initial_data: Any,
) -> Result[dict[str, Any], SagaError]:
    """
    Выполнить Saga декларативно.
    
    Returns:
        Success с dict результатов {step.name: result}
        Failure с информацией об ошибке
    """
    results: dict[str, Any] = {"_input": initial_data}
    executed: list[tuple[SagaStep, Any]] = []
    
    for step in steps:
        try:
            result = await workflow.execute_activity(
                step.action,
                results,  # передаём все предыдущие результаты
                start_to_close_timeout=step.timeout,
                retry_policy=step.retry_policy,
            )
            results[step.name] = result
            if step.compensate:
                executed.append((step, result))
                
        except Exception as e:
            # Compensate in reverse order
            for comp_step, comp_result in reversed(executed):
                if comp_step.compensate:
                    try:
                        await workflow.execute_activity(
                            comp_step.compensate,
                            comp_result,
                            start_to_close_timeout=comp_step.timeout,
                        )
                    except Exception:
                        workflow.logger.exception(
                            f"Compensation for {comp_step.name} failed"
                        )
            
            return Failure(SagaError(
                failed_step=step.name,
                cause=str(e),
                completed_steps=list(results.keys()),
            ))
    
    return Success(results)
```

### Использование

```python
@workflow.defn
class CreateOrderWorkflow:
    
    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        
        saga_steps = [
            SagaStep(
                name="order",
                action=create_order,
                compensate=cancel_order,
            ),
            SagaStep(
                name="reservation",
                action=reserve_inventory,
                compensate=cancel_reservation,
            ),
            SagaStep(
                name="payment",
                action=charge_payment,
                compensate=refund_payment,
                timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=3),
            ),
            SagaStep(
                name="delivery",
                action=schedule_delivery,
                compensate=None,  # Нет компенсации
            ),
        ]
        
        result = await execute_saga(saga_steps, data)
        
        match result:
            case Success(results):
                return Success(OrderResult(
                    order_id=results["order"],
                    reservation_id=results["reservation"],
                    payment_id=results["payment"],
                    delivery_id=results["delivery"],
                ))
            case Failure(error):
                return Failure(OrderCreationFailed(
                    reason=error.cause,
                    failed_step=error.failed_step,
                ))
```

---

## 📊 Сравнение подходов

| Подход | Сложность | Когда использовать |
|--------|-----------|-------------------|
| **Простой `list`** | ⭐ | 2-4 шага, одинаковые аргументы |
| **`SagaCompensations`** | ⭐⭐ | 5+ шагов, разные аргументы |
| **Декларативный** | ⭐⭐⭐ | Сложные зависимости, динамические шаги |

### Рекомендация

```
┌─────────────────────────────────────────────────────┐
│ Начни с простого list (официальный паттерн)        │
│ → Если нужны аргументы → SagaCompensations         │
│ → Если сложные зависимости → Декларативный         │
└─────────────────────────────────────────────────────┘
```

---

## ⚠️ Важные нюансы Temporal

### 1. Регистрируй компенсацию ДО выполнения

```python
# ✅ Правильно — компенсация зарегистрирована до возможного timeout
compensations.append(undo_action)
await workflow.execute_activity(action, ...)

# ❌ Неправильно — если activity timeout, компенсация не зарегистрирована
result = await workflow.execute_activity(action, ...)
compensations.append(undo_action)  # Может не выполниться!
```

### 2. Компенсации должны быть идемпотентными

```python
@activity.defn
async def cancel_reservation(reservation_id: str) -> None:
    """Идемпотентная компенсация."""
    reservation = await db.get_reservation(reservation_id)
    
    # Проверяем текущее состояние
    if reservation is None or reservation.status == "cancelled":
        return  # Уже отменено — ничего не делаем
    
    await db.update_reservation(reservation_id, status="cancelled")
```

### 3. Используй asyncio.shield для гарантии выполнения

```python
except Exception:
    # Гарантируем выполнение компенсаций даже при cancellation
    task = asyncio.create_task(run_compensations())
    await asyncio.shield(task)
    raise
```

### 4. Не устанавливай Workflow timeout если нужны компенсации

```python
# ⚠️ Осторожно — если workflow timeout, компенсации не выполнятся
handle = await client.start_workflow(
    CreateOrderWorkflow.run,
    data,
    id="order-123",
    task_queue="orders",
    # execution_timeout=timedelta(minutes=5),  # НЕ устанавливай!
)
```

---

## 🔗 Интеграция с Porto архитектурой

### Activities как Tasks

```python
# src/Containers/AppSection/OrderModule/Tasks/CreateOrderTask.py

from temporalio import activity
from src.Ship.Parents.Task import Task

@activity.defn
class CreateOrderTask(Task[CreateOrderInput, Order]):
    """Temporal Activity = Porto Task."""
    
    async def run(self, data: CreateOrderInput) -> Order:
        async with self.uow:
            order = Order(...)
            await self.uow.orders.add(order)
            await self.uow.commit()
        return order


@activity.defn
class CancelOrderTask(Task[str, None]):
    """Компенсация для CreateOrderTask."""
    
    async def run(self, order_id: str) -> None:
        async with self.uow:
            order = await self.uow.orders.get(order_id)
            if order and order.status != "cancelled":
                order.status = "cancelled"
                await self.uow.commit()
```

### Workflow как сложный Action

```python
# src/Containers/AppSection/OrderModule/Workflows/CreateOrderWorkflow.py

from temporalio import workflow
from returns.result import Result, Success, Failure

@workflow.defn
class CreateOrderWorkflow:
    """
    Temporal Workflow = Сложный Porto Action с Saga.
    
    Используется когда:
    - Нужна durability (переживает перезапуски)
    - Длительные операции (часы/дни)
    - Критичные бизнес-процессы
    """
    
    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        compensations: list = []
        
        try:
            compensations.append(cancel_order_task)
            order = await workflow.execute_activity(
                create_order_task, data, ...
            )
            
            compensations.append(cancel_reservation_task)
            reservation = await workflow.execute_activity(
                reserve_inventory_task, order.id, ...
            )
            
            # ... остальные шаги
            
            return Success(OrderResult(...))
            
        except Exception as ex:
            for comp in reversed(compensations):
                await workflow.execute_activity(comp, ...)
            return Failure(OrderCreationFailed(reason=str(ex)))
```

---

## 📚 Ресурсы

- [Temporal Saga Pattern Blog](https://temporal.io/blog/saga-pattern-made-easy)
- [Compensating Actions Blog](https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas)
- [Python Trip Booking Tutorial](https://learn.temporal.io/tutorials/python/trip-booking-app/)
- [Official Python Saga Example](https://github.com/temporalio/temporal-compensating-transactions/tree/main/python)

---

<div align="center">

**Связанные документы:**
- [21-integration-patterns-guide.md](21-integration-patterns-guide.md) — Когда использовать Temporal vs TaskIQ
- [04-result-railway.md](04-result-railway.md) — Railway-Oriented Programming

</div>

