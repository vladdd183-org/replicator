# 🎭 Saga Pattern в Hyper-Porto

> **Версия:** 4.3 | **Дата:** Январь 2026  
> Комплексное руководство по распределённым транзакциям с Temporal и TaskIQ

---

## 📖 Содержание

1. [Что такое Saga Pattern](#1-что-такое-saga-pattern)
2. [Когда использовать](#2-когда-использовать-temporal-vs-taskiq)
3. [Temporal Saga (основной способ)](#3-temporal-saga-основной-способ)
   - [Официальный Python паттерн](#31-официальный-python-паттерн-простой-list)
   - [SagaCompensations класс](#32-sagacompensations-расширенный-паттерн)
   - [Декларативный паттерн](#33-декларативный-паттерн-для-сложных-workflows)
   - [Интеграция с Porto](#34-интеграция-с-porto-архитектурой)
4. [TaskIQ Saga (простая альтернатива)](#4-taskiq-saga-простая-альтернатива)
5. [Важные нюансы](#5-важные-нюансы)
6. [Полный пример: CreateOrderWorkflow](#6-полный-пример-createorderworkflow)

---

## 1. Что такое Saga Pattern

### Проблема

В модульном монолите (и микросервисах) каждый модуль имеет свою базу данных или изолированные таблицы. Мы не можем сделать `JOIN` или общую транзакцию `BEGIN...COMMIT` между модулями `OrderModule` и `PaymentModule`.

**Сценарий сбоя:**

```
1. Пользователь нажимает "Оформить заказ"
2. OrderModule создаёт заказ (Status: Pending)     ✅
3. PaymentModule списывает деньги                   ✅
4. DeliveryModule назначает курьера                 ❌ ОШИБКА!
```

**Результат без Saga:** Деньги списаны, заказ завис, пользователь зол 😡

### Решение

**Saga** — паттерн управления распределёнными транзакциями через последовательность локальных транзакций. При сбое на любом шаге автоматически запускаются **компенсирующие действия** (rollback) для всех ранее выполненных шагов.

```
┌─────────────────────────────────────────────────────────────────┐
│                         SAGA EXECUTION                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ✅ Шаг 1: Create Order                                         │
│       └── 📝 Зарегистрирована компенсация: cancel_order          │
│                                                                  │
│   ✅ Шаг 2: Charge Payment                                       │
│       └── 📝 Зарегистрирована компенсация: refund_payment        │
│                                                                  │
│   ❌ Шаг 3: Schedule Delivery                                    │
│       └── 💥 ОШИБКА: нет курьеров                                │
│                                                                  │
│   🔄 ROLLBACK (обратный порядок):                                │
│       1. refund_payment()    ← возврат денег                     │
│       2. cancel_order()      ← отмена заказа                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Типы Saga

| Тип | Координация | Когда использовать |
|-----|-------------|-------------------|
| **Orchestration** | Центральный дирижёр управляет шагами | ✅ Hyper-Porto использует этот подход |
| **Choreography** | Каждый сервис слушает события и реагирует | Микросервисы без центрального контроля |

---

## 2. Когда использовать: Temporal vs TaskIQ

### Сравнительная таблица

| Критерий | **Temporal** | **TaskIQ** |
|----------|--------------|------------|
| **Durability** | ✅ Переживает перезапуски, сохраняет состояние | ⚠️ Требует ручного сохранения состояния |
| **Визуализация** | ✅ Web UI для мониторинга | ❌ Только логи |
| **Replay & Debug** | ✅ Полный replay истории | ❌ Нет |
| **Длительные процессы** | ✅ Часы, дни, недели | ⚠️ Не рекомендуется |
| **Сложность** | ⭐⭐ Требует инфраструктуры | ⭐ Простая настройка |
| **Количество шагов** | 5+ шагов | 2-4 шага |
| **Критичность** | Критичные бизнес-процессы | Некритичные операции |

### Правило выбора

```
┌─────────────────────────────────────────────────────────────────┐
│                    ВЫБОР ИНСТРУМЕНТА ДЛЯ SAGA                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Критичный бизнес-процесс?  ──────► ДА ──────► TEMPORAL         │
│         │                                                       │
│         ▼                                                       │
│        НЕТ                                                      │
│         │                                                       │
│         ▼                                                       │
│  Больше 4 шагов? ─────────────────► ДА ──────► TEMPORAL         │
│         │                                                       │
│         ▼                                                       │
│        НЕТ                                                      │
│         │                                                       │
│         ▼                                                       │
│  Длительность > 5 минут? ─────────► ДА ──────► TEMPORAL         │
│         │                                                       │
│         ▼                                                       │
│        НЕТ ───────────────────────────────────► TaskIQ          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Примеры сценариев

| Сценарий | Инструмент | Причина |
|----------|------------|---------|
| Оформление заказа (order → payment → delivery) | **Temporal** | Критичный процесс, деньги |
| Регистрация (user → email → notification) | TaskIQ | Простой, некритичный |
| Бронирование тура (flight → hotel → car) | **Temporal** | Длительный, много шагов |
| Обновление профиля (user → avatar → cache) | TaskIQ | Быстрый, 3 шага |
| Подписка (payment → subscription → access) | **Temporal** | Деньги, критичный |
| Импорт данных (parse → validate → save) | TaskIQ | Внутренний процесс |

---

## 3. Temporal Saga (основной способ)

> **Temporal** — это workflow engine с гарантированной durability и встроенной поддержкой компенсаций.

### 3.1 Официальный Python паттерн (простой list)

Минималистичный подход из официальной документации Temporal:

```python
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import Callable

@workflow.defn
class BookingWorkflow:
    """Простой паттерн Saga с list компенсаций."""
    
    @workflow.run
    async def run(self, data: BookVacationInput) -> dict:
        compensations: list[Callable] = []  # Просто список!
        
        try:
            # Шаг 1: Бронирование машины
            compensations.append(undo_book_car)  # ⚡ СНАЧАЛА регистрируем
            car_result = await workflow.execute_activity(
                book_car, data,
                start_to_close_timeout=timedelta(seconds=10),
            )
            
            # Шаг 2: Бронирование отеля
            compensations.append(undo_book_hotel)
            hotel_result = await workflow.execute_activity(
                book_hotel, data,
                start_to_close_timeout=timedelta(seconds=10),
            )
            
            # Шаг 3: Бронирование рейса
            compensations.append(undo_book_flight)
            flight_result = await workflow.execute_activity(
                book_flight, data,
                start_to_close_timeout=timedelta(seconds=10),
            )
            
            return {"status": "success", "car": car_result, "hotel": hotel_result, "flight": flight_result}
            
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

### Сравнение с Java SDK

| SDK | Встроенная абстракция |
|-----|----------------------|
| **Java** | ✅ `io.temporal.workflow.Saga` — полноценный класс |
| **Python** | ❌ Нет класса, но есть **официальный паттерн** (выше) |
| **Go** | ❌ Используют `defer` |
| **TypeScript** | ❌ Простой массив |

---

### 3.2 SagaCompensations (расширенный паттерн)

Когда нужно передавать **разные аргументы** в компенсации:

```python
from temporalio import workflow
from dataclasses import dataclass, field
from typing import Callable, Any
from datetime import timedelta

@dataclass
class SagaCompensations:
    """
    Compensation tracker с поддержкой:
    - Аргументов для каждой компенсации
    - Параллельного выполнения (опционально)
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
        """Выполнить все компенсации в обратном порядке."""
        if not self._stack:
            return
            
        for func, args in reversed(self._stack):
            await self._execute_one(func, args)
    
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

**Использование:**

```python
from returns.result import Result, Success, Failure

@workflow.defn
class CreateOrderWorkflow:
    
    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        comp = SagaCompensations()
        
        try:
            # Шаг 1: Создание заказа
            order = await workflow.execute_activity(
                create_order, data,
                start_to_close_timeout=timedelta(seconds=30),
            )
            comp.add(cancel_order, order.id)  # ✅ Передаём order.id
            
            # Шаг 2: Резервирование
            reservation = await workflow.execute_activity(
                reserve_inventory, order.id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            comp.add(cancel_reservation, reservation.id)
            
            # Шаг 3: Оплата
            payment = await workflow.execute_activity(
                charge_payment, order.id,
                start_to_close_timeout=timedelta(seconds=60),
            )
            comp.add(refund_payment, payment.id, payment.amount)  # ✅ Несколько аргументов
            
            # Шаг 4: Доставка (без компенсации)
            delivery = await workflow.execute_activity(
                schedule_delivery, order.id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            return Success(OrderResult(
                order_id=order.id,
                reservation_id=reservation.id,
                payment_id=payment.id,
                delivery_id=delivery.id,
            ))
            
        except Exception as ex:
            await comp.run_all()
            return Failure(OrderCreationFailed(reason=str(ex)))
```

---

### 3.3 Декларативный паттерн (для сложных workflows)

Когда Saga имеет **сложные зависимости** между шагами:

```python
from dataclasses import dataclass
from typing import Callable, Any
from datetime import timedelta
from temporalio.common import RetryPolicy
from returns.result import Result, Success, Failure

@dataclass(frozen=True)
class SagaStep:
    """Декларативное описание шага Saga."""
    name: str
    action: Callable
    compensate: Callable | None = None
    timeout: timedelta = timedelta(seconds=30)
    retry_policy: RetryPolicy | None = None


@dataclass(frozen=True)
class SagaError:
    """Ошибка выполнения Saga."""
    failed_step: str
    cause: str
    completed_steps: list[str]


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
                results,  # Передаём все предыдущие результаты
                start_to_close_timeout=step.timeout,
                retry_policy=step.retry_policy,
            )
            results[step.name] = result
            if step.compensate:
                executed.append((step, result))
                
        except Exception as e:
            # Compensate in reverse order (LIFO)
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

**Использование:**

```python
@workflow.defn
class CreateOrderWorkflow:
    
    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        
        # Декларативное описание Saga
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
                compensate=None,  # Нет компенсации для последнего шага
            ),
        ]
        
        result = await execute_saga(saga_steps, data)
        
        # Pattern matching для Result
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

### 3.4 Интеграция с Porto архитектурой

В Hyper-Porto **Activities** — это функции в отдельной папке `Activities/`, а **Workflows** — сложные оркестраторы в папке `Workflows/`.

> **Почему функции, а не классы?**
> - Temporal Python SDK идиоматичнее работает с функциями
> - `@activity.defn` ожидает функцию, а не класс
> - Меньше boilerplate, проще тестировать
> - Porto Tasks остаются для локальных атомарных операций (не-Temporal)

#### Activities = Функции с @activity.defn

```python
# src/Containers/AppSection/OrderModule/Activities/CreateOrderActivity.py

from temporalio import activity
from pydantic import BaseModel
from uuid import UUID, uuid4

from src.Containers.AppSection.OrderModule.Data.UnitOfWork import OrderUnitOfWork
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderRepository import OrderRepository
from src.Containers.AppSection.OrderModule.Models.Order import Order, OrderStatus


class CreateOrderInput(BaseModel):
    """Input DTO для activity."""
    workflow_id: str
    user_id: UUID
    items: list[OrderItemInput]
    shipping_address: str
    currency: str = "USD"


class CreateOrderOutput(BaseModel):
    """Output DTO от activity."""
    order_id: UUID
    user_id: UUID
    total_amount: str
    status: str


@activity.defn(name="create_order")
async def create_order(data: CreateOrderInput) -> CreateOrderOutput:
    """Temporal Activity: создать заказ в БД.
    
    Это функция (не класс), использующая UoW напрямую.
    Temporal обеспечивает retry и durability.
    """
    activity.logger.info(f"📦 Creating order for user {data.user_id}")
    
    # Создаём UoW внутри activity (не инжектируем)
    uow = OrderUnitOfWork(
        orders=OrderRepository(),
        items=OrderItemRepository(),
    )
    
    async with uow:
        order = Order(
            id=uuid4(),
            user_id=data.user_id,
            status=OrderStatus.PENDING.value,
            total_amount=data.total_amount,
        )
        await uow.orders.add(order)
        await uow.commit()
    
    activity.logger.info(f"✅ Order created: {order.id}")
    
    return CreateOrderOutput(
        order_id=order.id,
        user_id=order.user_id,
        total_amount=str(order.total_amount),
        status=order.status,
    )


@activity.defn(name="cancel_order")
async def cancel_order(order_id: UUID) -> bool:
    """Компенсация: отменить заказ.
    
    ⚠️ ВАЖНО: Идемпотентна — безопасно вызывать несколько раз.
    """
    activity.logger.info(f"🔙 Cancelling order: {order_id}")
    
    uow = OrderUnitOfWork(orders=OrderRepository(), items=OrderItemRepository())
    
    async with uow:
        order = await uow.orders.get(order_id)
        
        # Идемпотентность: проверяем текущее состояние
        if order is None:
            return True  # Уже удалён
            
        if order.status in (OrderStatus.CANCELLED.value, OrderStatus.FAILED.value):
            return True  # Уже отменён
        
        await uow.orders.update_status(order_id, OrderStatus.FAILED)
        await uow.commit()
    
    return True
```

#### Workflow = Оркестратор с SagaCompensations

```python
# src/Containers/AppSection/OrderModule/Workflows/CreateOrderWorkflow.py

from temporalio import workflow
from temporalio.common import RetryPolicy
from returns.result import Result, Success, Failure
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from src.Containers.AppSection.OrderModule.Activities import (
        create_order, cancel_order,
        reserve_inventory, cancel_reservation,
        charge_payment, refund_payment,
        schedule_delivery,
        CreateOrderInput, CreateOrderOutput,
    )
    from src.Ship.Infrastructure.Temporal.Saga import SagaCompensations


@workflow.defn(name="CreateOrderWorkflow")
class CreateOrderWorkflow:
    """
    Temporal Workflow = Оркестратор Saga.
    
    Используется когда:
    - Нужна durability (переживает перезапуски)
    - Длительные операции (часы/дни)
    - Критичные бизнес-процессы с деньгами
    
    Использует SagaCompensations для автоматического rollback.
    """
    
    @workflow.run
    async def run(self, data: CreateOrderWorkflowInput) -> Result[OrderResult, OrderError]:
        # Compensation tracker из Ship/Infrastructure
        comp = SagaCompensations()
        
        try:
            # Шаг 1: Создать заказ
            workflow.logger.info("📦 Step 1: Creating order")
            order: CreateOrderOutput = await workflow.execute_activity(
                create_order,  # Функция, не класс!
                CreateOrderInput(workflow_id=workflow.info().workflow_id, ...),
                start_to_close_timeout=timedelta(seconds=30),
            )
            comp.add(cancel_order, order.order_id)  # Регистрируем компенсацию
            
            # Шаг 2: Зарезервировать товар
            workflow.logger.info("📦 Step 2: Reserving inventory")
            reservation = await workflow.execute_activity(
                reserve_inventory,
                ReserveInventoryInput(order_id=order.order_id, ...),
                start_to_close_timeout=timedelta(seconds=30),
            )
            comp.add(cancel_reservation, reservation.reservation_id)
            
            # Шаг 3: Списать оплату
            workflow.logger.info("💳 Step 3: Processing payment")
            payment = await workflow.execute_activity(
                charge_payment,
                ChargePaymentInput(order_id=order.order_id, amount=order.total_amount, ...),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=5),
            )
            comp.add(refund_payment, payment.payment_id)
            
            # Шаг 4: Назначить доставку (последний шаг)
            workflow.logger.info("🚚 Step 4: Scheduling delivery")
            delivery = await workflow.execute_activity(
                schedule_delivery,
                ScheduleDeliveryInput(order_id=order.order_id, ...),
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            # Успех — очищаем компенсации
            comp.clear()
            
            return Success(OrderResult(
                order_id=order.order_id,
                reservation_id=reservation.reservation_id,
                payment_id=payment.payment_id,
                delivery_id=delivery.delivery_id,
            ))
            
        except Exception as ex:
            # ROLLBACK: запускаем все компенсации в обратном порядке
            workflow.logger.error(f"❌ Saga failed: {ex}. Running compensations...")
            await comp.run_all()
            return Failure(OrderCreationFailed(reason=str(ex)))
```

#### Структура папок для Workflows

```
OrderModule/
├── Activities/                   # Temporal Activities (функции с @activity.defn)
│   ├── __init__.py              # Экспорт всех activities и DTOs
│   ├── CreateOrderActivity.py   # create_order, cancel_order
│   ├── ReserveInventoryActivity.py
│   ├── ChargePaymentActivity.py
│   ├── ScheduleDeliveryActivity.py
│   └── NotificationActivity.py
├── Workflows/                    # Temporal Workflows (классы-оркестраторы)
│   ├── __init__.py
│   └── CreateOrderWorkflow.py
├── Tasks/                        # Porto Tasks (локальные, не-Temporal)
│   ├── ReserveInventoryTask.py  # Для использования вне Temporal
│   └── ProcessPaymentTask.py
├── Actions/                      # Porto Actions (простые use cases)
│   ├── CreateOrderAction.py     # Обычный action (без Temporal)
│   └── StartCreateOrderWorkflowAction.py  # Запуск Workflow
└── Workers/                      # Temporal Worker регистрация
    └── OrderWorker.py
```

#### Различие Activities и Tasks

| Аспект | Activities (`Activities/`) | Tasks (`Tasks/`) |
|--------|---------------------------|------------------|
| **Декоратор** | `@activity.defn` | Нет (обычный класс) |
| **Запуск** | Через Temporal Worker | Напрямую в Action |
| **Retry** | Автоматический (RetryPolicy) | Ручной (tenacity) |
| **Durability** | Да (сохраняется в Temporal) | Нет |
| **DI** | Создаёт UoW внутри | Инжектируется через DI |
| **Use case** | Шаги Saga/Workflow | Локальные операции |

### Сравнение паттернов Temporal

| Подход | Сложность | Когда использовать |
|--------|-----------|-------------------|
| **Простой `list`** | ⭐ | 2-4 шага, одинаковые аргументы для компенсаций |
| **`SagaCompensations`** | ⭐⭐ | 5+ шагов, разные аргументы для компенсаций |
| **Декларативный** | ⭐⭐⭐ | Сложные зависимости, динамические шаги |

**Рекомендация:**

```
Начни с простого list (официальный паттерн)
    ↓
Если нужны разные аргументы → SagaCompensations
    ↓
Если сложные зависимости → Декларативный паттерн
```

---

## 4. TaskIQ Saga (простая альтернатива)

> Используй TaskIQ для **простых, некритичных** саг с 2-4 шагами.

### Когда использовать TaskIQ

| ✅ Подходит | ❌ Не подходит |
|-------------|---------------|
| 2-4 шага | 5+ шагов |
| Быстрые операции (< 5 мин) | Длительные процессы |
| Некритичные процессы | Финансовые операции |
| Внутренние операции | Операции с внешними API |
| Ручной retry допустим | Требуется auto-recovery |

### Архитектура TaskIQ Saga

```python
# src/Ship/Parents/Saga.py

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

class SagaStep(ABC, Generic[InputT, OutputT]):
    """Базовый класс для шага Saga."""
    
    @abstractmethod
    async def execute(self, data: InputT) -> OutputT:
        """Выполнить действие."""
        ...

    @abstractmethod
    async def compensate(self, data: InputT, result: OutputT | None) -> None:
        """Отменить действие (Compensating Transaction)."""
        ...
```

### Пример реализации шагов

```python
# src/Containers/AppSection/UserModule/Sagas/Steps/CreateUserStep.py

from dataclasses import dataclass
from src.Ship.Parents.Saga import SagaStep

@dataclass
class CreateUserStep(SagaStep[CreateUserDto, str]):
    """Шаг создания пользователя."""
    user_repository: UserRepository

    async def execute(self, data: CreateUserDto) -> str:
        user = User(email=data.email, name=data.name)
        await self.user_repository.add(user)
        return str(user.id)

    async def compensate(self, data: CreateUserDto, result: str | None) -> None:
        if result:
            await self.user_repository.delete(UUID(result))


@dataclass
class SendWelcomeEmailStep(SagaStep[EmailDto, str]):
    """Шаг отправки приветственного email."""
    email_service: EmailService

    async def execute(self, data: EmailDto) -> str:
        message_id = await self.email_service.send(data.to, data.subject, data.body)
        return message_id

    async def compensate(self, data: EmailDto, result: str | None) -> None:
        # Email нельзя "отозвать", но можно залогировать
        if result:
            logger.info(f"Email {result} was sent but saga failed")
```

### TaskIQ Orchestrator

```python
# src/Containers/AppSection/UserModule/Sagas/RegisterUserSaga.py

from dataclasses import dataclass
from dishka.integrations.taskiq import FromDishka
from src.Ship.Infrastructure.Workers.Broker import broker

@dataclass
class SagaContext:
    """Контекст для саги регистрации."""
    email: str
    name: str


@broker.task(retry_on_error=True, max_retries=3)
async def register_user_saga(
    context: SagaContext,
    create_user_step: FromDishka[CreateUserStep],
    send_email_step: FromDishka[SendWelcomeEmailStep],
    create_notification_step: FromDishka[CreateNotificationStep],
):
    """
    Простая Saga для регистрации пользователя.
    
    ⚠️ Использовать для некритичных процессов!
    Для критичных — используй Temporal.
    """
    results: dict[str, Any] = {}
    
    try:
        # Шаг 1: Создание пользователя
        results['user'] = await create_user_step.execute(
            CreateUserDto(email=context.email, name=context.name)
        )
        
        # Шаг 2: Отправка email
        results['email'] = await send_email_step.execute(
            EmailDto(to=context.email, subject="Welcome!", body="...")
        )
        
        # Шаг 3: Создание уведомления
        results['notification'] = await create_notification_step.execute(
            NotificationDto(user_id=results['user'], message="Welcome!")
        )
        
        logger.info(f"Saga completed successfully for {context.email}")

    except Exception as e:
        logger.error(f"Saga failed: {e}. Starting rollback.")
        
        # ROLLBACK в обратном порядке
        if 'email' in results:
            await send_email_step.compensate(
                EmailDto(to=context.email, ...), results['email']
            )
            
        if 'user' in results:
            await create_user_step.compensate(
                CreateUserDto(email=context.email, ...), results['user']
            )
        
        raise  # Re-raise для retry
```

### Запуск из Action

```python
# src/Containers/AppSection/UserModule/Actions/RegisterUserAction.py

from returns.result import Result, Success

@dataclass
class RegisterUserAction(Action[RegisterUserRequest, str, UserError]):
    
    async def run(self, data: RegisterUserRequest) -> Result[str, UserError]:
        # Запускаем Saga асинхронно
        context = SagaContext(email=data.email, name=data.name)
        await register_user_saga.kiq(context)
        
        # Возвращаем confirmation (процесс выполняется в фоне)
        return Success(f"Registration started for {data.email}")
```

---

## 5. Важные нюансы

### 5.1 Регистрируй компенсацию ДО выполнения

```python
# ✅ ПРАВИЛЬНО — компенсация зарегистрирована до возможного timeout
compensations.append(undo_action)
await workflow.execute_activity(action, ...)

# ❌ НЕПРАВИЛЬНО — если activity timeout, компенсация не зарегистрирована
result = await workflow.execute_activity(action, ...)
compensations.append(undo_action)  # ⚠️ Может не выполниться!
```

**Почему это важно:**

```
Сценарий без предварительной регистрации:
1. Activity начала выполняться                    ⏳
2. Activity выполнила действие (деньги списаны)   ✅
3. Network timeout при возврате ответа            💥
4. Workflow получает ошибку                       ❌
5. compensations.append() НЕ выполнился           ⚠️
6. Деньги списаны, компенсация не зарегистрирована 😱
```

### 5.2 Компенсации ДОЛЖНЫ быть идемпотентными

```python
@activity.defn
async def cancel_reservation(reservation_id: str) -> None:
    """
    Идемпотентная компенсация.
    
    Может вызываться несколько раз без побочных эффектов.
    """
    reservation = await db.get_reservation(reservation_id)
    
    # ✅ Проверяем текущее состояние ПЕРЕД изменением
    if reservation is None:
        return  # Уже удалена — ничего не делаем
        
    if reservation.status == "cancelled":
        return  # Уже отменена — ничего не делаем
    
    await db.update_reservation(reservation_id, status="cancelled")
```

**Паттерны идемпотентности:**

| Паттерн | Описание |
|---------|----------|
| **Check-then-act** | Проверить состояние перед изменением |
| **Idempotency key** | Сохранять ключ операции, проверять перед выполнением |
| **Upsert** | INSERT ... ON CONFLICT DO UPDATE |
| **Version check** | Проверять версию записи (optimistic locking) |

### 5.3 LIFO порядок компенсаций

Компенсации выполняются в **обратном порядке** (Last In, First Out):

```
Выполнение:        Компенсации:
                   
Step 1 ────────►   ◄──────── Compensate 1 (последний)
    ↓                   ↑
Step 2 ────────►   ◄──────── Compensate 2
    ↓                   ↑
Step 3 ────────►   ◄──────── Compensate 3 (первый)
    ↓
   ❌ FAIL
```

```python
# ✅ ПРАВИЛЬНО — reversed()
for comp in reversed(compensations):
    await execute_compensation(comp)

# ❌ НЕПРАВИЛЬНО — прямой порядок нарушает логику
for comp in compensations:
    await execute_compensation(comp)  # Может сломать данные!
```

### 5.4 Temporal: Не устанавливай Workflow timeout

```python
# ⚠️ ОСТОРОЖНО — если workflow timeout, компенсации НЕ выполнятся
handle = await client.start_workflow(
    CreateOrderWorkflow.run,
    data,
    id="order-123",
    task_queue="orders",
    # execution_timeout=timedelta(minutes=5),  # ❌ НЕ устанавливай!
)
```

**Вместо этого** используй timeouts на уровне Activities:

```python
await workflow.execute_activity(
    action, data,
    start_to_close_timeout=timedelta(minutes=5),  # ✅ OK
)
```

### 5.5 Error handling в компенсациях

```python
async def run_compensations(compensations: list) -> None:
    """Выполнить компенсации с error handling."""
    errors: list[Exception] = []
    
    for comp_func, comp_args in reversed(compensations):
        try:
            await workflow.execute_activity(
                comp_func, *comp_args,
                start_to_close_timeout=timedelta(seconds=30),
            )
        except Exception as e:
            # Логируем, но продолжаем!
            workflow.logger.exception(
                f"Compensation {comp_func.__name__} failed: {e}"
            )
            errors.append(e)
    
    if errors:
        # Можно отправить alert для manual review
        await send_alert(f"Compensations failed: {errors}")
```

---

## 6. Полный пример: CreateOrderWorkflow

Комплексный пример Saga для оформления заказа с Temporal.
Основан на реальной реализации в `src/Containers/AppSection/OrderModule/`.

### Структура файлов

```
OrderModule/
├── Activities/
│   ├── __init__.py              # Экспорт всех activities
│   ├── CreateOrderActivity.py   # create_order, cancel_order
│   ├── ReserveInventoryActivity.py
│   ├── ChargePaymentActivity.py
│   ├── ScheduleDeliveryActivity.py
│   └── NotificationActivity.py
├── Workflows/
│   └── CreateOrderWorkflow.py
├── Workers/
│   └── OrderWorker.py           # Регистрация activities и workflows
└── Actions/
    └── StartCreateOrderWorkflowAction.py
```

### Activities (Функции)

```python
# src/Containers/AppSection/OrderModule/Activities/CreateOrderActivity.py

from temporalio import activity
from pydantic import BaseModel
from uuid import UUID, uuid4

from src.Containers.AppSection.OrderModule.Data.UnitOfWork import OrderUnitOfWork
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderRepository import OrderRepository
from src.Containers.AppSection.OrderModule.Models.Order import Order, OrderStatus


# ═══════════════════════════════════════════════════════════════
# Input/Output DTOs (Pydantic для сериализации)
# ═══════════════════════════════════════════════════════════════

class CreateOrderInput(BaseModel):
    """Input DTO — сериализуется Temporal."""
    workflow_id: str
    user_id: UUID
    items: list[OrderItemInput]
    shipping_address: str
    currency: str = "USD"


class CreateOrderOutput(BaseModel):
    """Output DTO — сериализуется Temporal."""
    order_id: UUID
    user_id: UUID
    total_amount: str  # Decimal как строка
    status: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════════
# STEP 1: CREATE ORDER
# ═══════════════════════════════════════════════════════════════

@activity.defn(name="create_order")
async def create_order(data: CreateOrderInput) -> CreateOrderOutput:
    """Создать заказ в статусе PENDING.
    
    Activity создаёт UoW внутри себя (не через DI),
    так как выполняется в контексте Temporal Worker.
    """
    activity.logger.info(f"📦 Creating order for user {data.user_id}")
    
    # UoW создаётся внутри activity
    uow = OrderUnitOfWork(
        orders=OrderRepository(),
        items=OrderItemRepository(),
    )
    
    async with uow:
        order = Order(
            id=uuid4(),
            user_id=data.user_id,
            status=OrderStatus.PENDING.value,
            total_amount=data.total_amount,
            shipping_address=data.shipping_address,
        )
        await uow.orders.add(order)
        
        # Создаём OrderItems
        for item_data in data.items:
            item = OrderItem(order=order.id, ...)
            await uow.items.add(item)
        
        await uow.commit()
    
    activity.logger.info(f"✅ Order created: {order.id}")
    
    return CreateOrderOutput(
        order_id=order.id,
        user_id=order.user_id,
        total_amount=str(order.total_amount),
        status=order.status,
        created_at=order.created_at,
    )


@activity.defn(name="cancel_order")
async def cancel_order(order_id: UUID) -> bool:
    """Компенсация: отменить заказ.
    
    ⚠️ Идемпотентна — безопасно вызывать несколько раз.
    """
    activity.logger.info(f"🔙 Cancelling order: {order_id}")
    
    uow = OrderUnitOfWork(orders=OrderRepository(), items=OrderItemRepository())
    
    async with uow:
        order = await uow.orders.get(order_id)
        
        if order is None:
            return True  # Уже удалён — идемпотентность
            
        if order.status in (OrderStatus.CANCELLED.value, OrderStatus.FAILED.value):
            return True  # Уже отменён
        
        await uow.orders.update_status(order_id, OrderStatus.FAILED)
        await uow.commit()
    
    activity.logger.info(f"✅ Order {order_id} marked as failed")
    return True
```

```python
# src/Containers/AppSection/OrderModule/Activities/ChargePaymentActivity.py

@activity.defn(name="charge_payment")
async def charge_payment(data: ChargePaymentInput) -> PaymentOutput:
    """Списать оплату.
    
    В production здесь вызов Stripe/PayPal.
    Temporal обеспечивает retry через RetryPolicy.
    """
    activity.logger.info(f"💳 Processing payment: {data.amount} {data.currency}")
    
    # Валидация
    if Decimal(data.amount) > Decimal("10000.00"):
        raise Exception("Payment declined: Amount exceeds limit")
    
    # В production:
    # payment_intent = await stripe.PaymentIntent.create(...)
    
    payment_id = f"PAY-{uuid4().hex[:12].upper()}"
    
    activity.logger.info(f"✅ Payment processed: {payment_id}")
    
    return PaymentOutput(
        payment_id=payment_id,
        order_id=data.order_id,
        amount=data.amount,
        status="completed",
    )


@activity.defn(name="refund_payment")
async def refund_payment(payment_id: str) -> RefundOutput:
    """Компенсация: вернуть деньги.
    
    Идемпотентна — повторный refund игнорируется.
    """
    activity.logger.info(f"💸 Refunding payment: {payment_id}")
    
    # В production:
    # await stripe.Refund.create(payment_intent=payment_id)
    
    return RefundOutput(
        refund_id=f"REF-{uuid4().hex[:12].upper()}",
        payment_id=payment_id,
        status="completed",
    )
```

### Workflow (Оркестратор)

```python
# src/Containers/AppSection/OrderModule/Workflows/CreateOrderWorkflow.py

from temporalio import workflow
from temporalio.common import RetryPolicy
from returns.result import Result, Success, Failure
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from src.Containers.AppSection.OrderModule.Activities import (
        create_order, cancel_order,
        reserve_inventory, cancel_reservation,
        charge_payment, refund_payment,
        schedule_delivery, cancel_delivery,
        CreateOrderInput, ChargePaymentInput,
    )
    from src.Ship.Infrastructure.Temporal.Saga import SagaCompensations


@workflow.defn(name="CreateOrderWorkflow")
class CreateOrderWorkflow:
    """Saga для создания заказа.
    
    Шаги:
    1. Create Order (PENDING) → cancel_order
    2. Reserve Inventory → cancel_reservation  
    3. Charge Payment → refund_payment
    4. Schedule Delivery → cancel_delivery
    5. Send Notification (без компенсации)
    """
    
    def __init__(self) -> None:
        self._status = "pending"
        self._order_id: UUID | None = None
    
    @workflow.query
    def get_status(self) -> str:
        """Query для получения статуса во время выполнения."""
        return self._status
    
    @workflow.run
    async def run(
        self, 
        data: CreateOrderWorkflowInput,
    ) -> Result[OrderWorkflowResult, OrderWorkflowError]:
        workflow.logger.info(f"🎭 Starting CreateOrderWorkflow for user {data.user_id}")
        
        # Compensation tracker
        comp = SagaCompensations()
        workflow_id = workflow.info().workflow_id
        
        # Retry policies
        default_retry = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
        )
        
        payment_retry = RetryPolicy(
            maximum_attempts=5,
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=60),
        )
        
        try:
            # ═══════════════════════════════════════════════════════
            # STEP 1: CREATE ORDER
            # ═══════════════════════════════════════════════════════
            self._status = "creating_order"
            workflow.logger.info("📦 Step 1: Creating order")
            
            order: CreateOrderOutput = await workflow.execute_activity(
                create_order,
                CreateOrderInput(workflow_id=workflow_id, user_id=data.user_id, ...),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry,
            )
            
            self._order_id = order.order_id
            comp.add(cancel_order, order.order_id)  # Регистрируем компенсацию
            
            # ═══════════════════════════════════════════════════════
            # STEP 2: RESERVE INVENTORY
            # ═══════════════════════════════════════════════════════
            self._status = "reserving_inventory"
            workflow.logger.info("📦 Step 2: Reserving inventory")
            
            reservation = await workflow.execute_activity(
                reserve_inventory,
                ReserveInventoryInput(order_id=order.order_id, ...),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry,
            )
            comp.add(cancel_reservation, reservation.reservation_id)
            
            # ═══════════════════════════════════════════════════════
            # STEP 3: CHARGE PAYMENT
            # ═══════════════════════════════════════════════════════
            self._status = "processing_payment"
            workflow.logger.info("💳 Step 3: Processing payment")
            
            payment = await workflow.execute_activity(
                charge_payment,
                ChargePaymentInput(
                    order_id=order.order_id,
                    amount=order.total_amount,
                    ...
                ),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=payment_retry,  # Больше retry для платежей
            )
            comp.add(refund_payment, payment.payment_id)
            
            # ═══════════════════════════════════════════════════════
            # STEP 4: SCHEDULE DELIVERY
            # ═══════════════════════════════════════════════════════
            self._status = "scheduling_delivery"
            workflow.logger.info("🚚 Step 4: Scheduling delivery")
            
            delivery = await workflow.execute_activity(
                schedule_delivery,
                ScheduleDeliveryInput(order_id=order.order_id, ...),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry,
            )
            comp.add(cancel_delivery, delivery.delivery_id)
            
            # ═══════════════════════════════════════════════════════
            # SUCCESS
            # ═══════════════════════════════════════════════════════
            self._status = "completed"
            comp.clear()  # Очищаем — успех!
            
            workflow.logger.info(f"🎉 Order {order.order_id} completed!")
            
            return Success(OrderWorkflowResult(
                order_id=order.order_id,
                reservation_id=reservation.reservation_id,
                payment_id=payment.payment_id,
                delivery_id=delivery.delivery_id,
                tracking_number=delivery.tracking_number,
                status="confirmed",
            ))
            
        except Exception as ex:
            # ═══════════════════════════════════════════════════════
            # ROLLBACK
            # ═══════════════════════════════════════════════════════
            self._status = "compensating"
            workflow.logger.error(f"❌ Saga failed: {ex}. Running compensations...")
            
            # Запускаем все компенсации в обратном порядке
            await comp.run_all()
            
            self._status = "failed"
            
            return Failure(OrderWorkflowError(
                message=f"Order creation failed: {ex}",
                code="ORDER_CREATION_FAILED",
                failed_step=self._status,
            ))
```

### Запуск Workflow из Action

```python
# src/Containers/AppSection/OrderModule/Actions/StartCreateOrderWorkflowAction.py

from temporalio.client import Client as TemporalClient
from returns.result import Result, Success, Failure
from uuid import uuid4

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.OrderModule.Workflows.CreateOrderWorkflow import (
    CreateOrderWorkflow,
    CreateOrderWorkflowInput,
)


class StartCreateOrderWorkflowAction(Action[CreateOrderRequest, WorkflowStarted, OrderError]):
    """Action для запуска Temporal Workflow.
    
    Не ждёт завершения — возвращает workflow_id для polling.
    """
    
    def __init__(self, temporal_client: TemporalClient) -> None:
        self.temporal_client = temporal_client
    
    async def run(self, data: CreateOrderRequest) -> Result[WorkflowStarted, OrderError]:
        workflow_id = f"order-{uuid4()}"
        
        try:
            handle = await self.temporal_client.start_workflow(
                CreateOrderWorkflow.run,
                CreateOrderWorkflowInput(
                    user_id=data.user_id,
                    items=data.items,
                    shipping_address=data.shipping_address,
                    currency=data.currency,
                ),
                id=workflow_id,
                task_queue="orders",
            )
            
            return Success(WorkflowStarted(
                workflow_id=workflow_id,
                run_id=handle.run_id,
                message="Order creation started",
            ))
            
        except Exception as ex:
            return Failure(OrderError(message=f"Failed to start workflow: {ex}"))


class ExecuteCreateOrderWorkflowAction(Action[CreateOrderRequest, OrderResult, OrderError]):
    """Action для запуска и ожидания результата Workflow."""
    
    def __init__(self, temporal_client: TemporalClient) -> None:
        self.temporal_client = temporal_client
    
    async def run(self, data: CreateOrderRequest) -> Result[OrderResult, OrderError]:
        workflow_id = f"order-{uuid4()}"
        
        handle = await self.temporal_client.start_workflow(
            CreateOrderWorkflow.run,
            CreateOrderWorkflowInput(...),
            id=workflow_id,
            task_queue="orders",
        )
        
        # Ждём результат
        result = await handle.result()
        
        match result:
            case Success(order_result):
                return Success(order_result)
            case Failure(error):
                return Failure(OrderError(
                    message=error.message,
                    code=error.code,
                ))
```

### Worker регистрация

```python
# src/Containers/AppSection/OrderModule/Workers/OrderWorker.py

from temporalio.worker import Worker
from temporalio.client import Client

from src.Containers.AppSection.OrderModule.Workflows import ALL_WORKFLOWS
from src.Containers.AppSection.OrderModule.Activities import ALL_ACTIVITIES


async def create_order_worker(client: Client) -> Worker:
    """Создать Temporal Worker для OrderModule."""
    return Worker(
        client,
        task_queue="orders",
        workflows=ALL_WORKFLOWS,
        activities=ALL_ACTIVITIES,
    )
```

---

## 📊 Итоговая таблица

| Аспект | Temporal | TaskIQ |
|--------|----------|--------|
| **Durability** | ✅ Гарантированная | ⚠️ При сбое worker — потеря |
| **Monitoring** | ✅ Web UI | ❌ Только логи |
| **Replay** | ✅ Полный replay | ❌ Нет |
| **Длительность** | Часы → месяцы | Секунды → минуты |
| **Сложность** | ⭐⭐ Инфраструктура | ⭐ Простая настройка |
| **Шаги** | 5+ шагов | 2-4 шага |
| **Use case** | Критичные процессы | Некритичные операции |

---

## 📚 Ресурсы

### Temporal

- [Temporal Saga Pattern Blog](https://temporal.io/blog/saga-pattern-made-easy)
- [Compensating Actions Blog](https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas)
- [Python Trip Booking Tutorial](https://learn.temporal.io/tutorials/python/trip-booking-app/)
- [Official Python Saga Example](https://github.com/temporalio/temporal-compensating-transactions/tree/main/python)

### Связанные документы Hyper-Porto

- [04-result-railway.md](04-result-railway.md) — Railway-Oriented Programming
- [05-concurrency.md](05-concurrency.md) — Structured Concurrency
- [13-cross-module-communication.md](13-cross-module-communication.md) — Интеграция Temporal с Porto

---

<div align="center">

**Hyper-Porto v4.3** — Saga Pattern для распределённых транзакций 🎭

</div>
