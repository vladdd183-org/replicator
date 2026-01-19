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

В Hyper-Porto **Activities** маппятся на **Tasks**, а **Workflows** — на сложные **Actions**.

#### Activities = Porto Tasks

```python
# src/Containers/AppSection/OrderModule/Tasks/CreateOrderTask.py

from temporalio import activity
from dataclasses import dataclass
from src.Ship.Parents.Task import Task

@activity.defn
@dataclass
class CreateOrderTask(Task[CreateOrderInput, Order]):
    """
    Temporal Activity = Porto Task.
    
    Атомарная операция создания заказа.
    """
    uow: OrderUnitOfWork
    
    async def run(self, data: CreateOrderInput) -> Order:
        async with self.uow:
            order = Order(
                user_id=data.user_id,
                items=data.items,
                status=OrderStatus.PENDING,
            )
            await self.uow.orders.add(order)
            await self.uow.commit()
        return order


@activity.defn
@dataclass  
class CancelOrderTask(Task[str, None]):
    """
    Компенсация для CreateOrderTask.
    
    ⚠️ ВАЖНО: Должна быть идемпотентной!
    """
    uow: OrderUnitOfWork
    
    async def run(self, order_id: str) -> None:
        async with self.uow:
            order = await self.uow.orders.get(order_id)
            # Идемпотентность: проверяем текущее состояние
            if order and order.status != OrderStatus.CANCELLED:
                order.status = OrderStatus.CANCELLED
                await self.uow.commit()
```

#### Workflow = Сложный Porto Action

```python
# src/Containers/AppSection/OrderModule/Workflows/CreateOrderWorkflow.py

from temporalio import workflow
from returns.result import Result, Success, Failure
from datetime import timedelta

@workflow.defn
class CreateOrderWorkflow:
    """
    Temporal Workflow = Сложный Porto Action с Saga.
    
    Используется когда:
    - Нужна durability (переживает перезапуски)
    - Длительные операции (часы/дни)
    - Критичные бизнес-процессы с деньгами
    """
    
    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        compensations: list = []
        
        try:
            # Шаг 1: Создать заказ
            compensations.append(cancel_order_task)
            order = await workflow.execute_activity(
                create_order_task, data,
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            # Шаг 2: Зарезервировать товар
            compensations.append(cancel_reservation_task)
            reservation = await workflow.execute_activity(
                reserve_inventory_task, order.id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            # Шаг 3: Списать оплату
            compensations.append(refund_payment_task)
            payment = await workflow.execute_activity(
                charge_payment_task, order.id,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            
            # Шаг 4: Назначить доставку
            delivery = await workflow.execute_activity(
                schedule_delivery_task, order.id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            return Success(OrderResult(
                order_id=order.id,
                reservation_id=reservation.id,
                payment_id=payment.id,
                delivery_id=delivery.id,
            ))
            
        except Exception as ex:
            # ROLLBACK: компенсации в обратном порядке
            for comp in reversed(compensations):
                await workflow.execute_activity(
                    comp, order.id if 'order' in locals() else data,
                    start_to_close_timeout=timedelta(seconds=30),
                )
            return Failure(OrderCreationFailed(reason=str(ex)))
```

#### Структура папок для Workflows

```
OrderModule/
├── Workflows/                    # Temporal Workflows (= сложные Actions)
│   ├── CreateOrderWorkflow.py
│   └── CancelOrderWorkflow.py
├── Tasks/                        # Temporal Activities (= Porto Tasks)
│   ├── CreateOrderTask.py
│   ├── CancelOrderTask.py
│   ├── ReserveInventoryTask.py
│   └── ChargePaymentTask.py
└── Actions/                      # Обычные Porto Actions (простые use cases)
    └── GetOrderAction.py
```

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

Комплексный пример Saga для оформления заказа с Temporal:

### Activities (Tasks)

```python
# src/Containers/AppSection/OrderModule/Tasks/OrderTasks.py

from temporalio import activity
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# STEP 1: CREATE ORDER
# ═══════════════════════════════════════════════════════════════

@dataclass
class CreateOrderInput:
    user_id: UUID
    items: list[OrderItem]
    total_amount: Decimal


@dataclass
class OrderCreated:
    order_id: UUID
    created_at: datetime


@activity.defn
async def create_order(data: CreateOrderInput) -> OrderCreated:
    """Создать заказ в статусе PENDING."""
    order = Order(
        user_id=data.user_id,
        items=data.items,
        total_amount=data.total_amount,
        status=OrderStatus.PENDING,
    )
    await order_repository.add(order)
    return OrderCreated(order_id=order.id, created_at=order.created_at)


@activity.defn
async def cancel_order(order_id: UUID) -> None:
    """Компенсация: отменить заказ."""
    order = await order_repository.get(order_id)
    if order and order.status != OrderStatus.CANCELLED:
        order.status = OrderStatus.CANCELLED
        await order_repository.update(order)


# ═══════════════════════════════════════════════════════════════
# STEP 2: RESERVE INVENTORY
# ═══════════════════════════════════════════════════════════════

@dataclass
class ReservationCreated:
    reservation_id: UUID
    items_reserved: list[str]


@activity.defn
async def reserve_inventory(order_id: UUID) -> ReservationCreated:
    """Зарезервировать товары на складе."""
    order = await order_repository.get(order_id)
    reservation = await inventory_service.reserve(order.items)
    return ReservationCreated(
        reservation_id=reservation.id,
        items_reserved=[item.sku for item in order.items],
    )


@activity.defn
async def cancel_reservation(reservation_id: UUID) -> None:
    """Компенсация: отменить резервацию."""
    reservation = await inventory_service.get_reservation(reservation_id)
    if reservation and reservation.status != "cancelled":
        await inventory_service.cancel_reservation(reservation_id)


# ═══════════════════════════════════════════════════════════════
# STEP 3: CHARGE PAYMENT
# ═══════════════════════════════════════════════════════════════

@dataclass
class PaymentCharged:
    payment_id: UUID
    amount: Decimal
    transaction_id: str


@activity.defn
async def charge_payment(order_id: UUID) -> PaymentCharged:
    """Списать оплату."""
    order = await order_repository.get(order_id)
    payment = await payment_service.charge(
        user_id=order.user_id,
        amount=order.total_amount,
        order_id=order_id,
    )
    return PaymentCharged(
        payment_id=payment.id,
        amount=payment.amount,
        transaction_id=payment.transaction_id,
    )


@activity.defn
async def refund_payment(payment_id: UUID) -> None:
    """Компенсация: вернуть деньги."""
    payment = await payment_service.get_payment(payment_id)
    if payment and payment.status != "refunded":
        await payment_service.refund(payment_id)


# ═══════════════════════════════════════════════════════════════
# STEP 4: SCHEDULE DELIVERY
# ═══════════════════════════════════════════════════════════════

@dataclass
class DeliveryScheduled:
    delivery_id: UUID
    estimated_date: datetime


@activity.defn
async def schedule_delivery(order_id: UUID) -> DeliveryScheduled:
    """Назначить доставку."""
    order = await order_repository.get(order_id)
    delivery = await delivery_service.schedule(
        order_id=order_id,
        address=order.delivery_address,
    )
    return DeliveryScheduled(
        delivery_id=delivery.id,
        estimated_date=delivery.estimated_date,
    )

# Нет компенсации для delivery — последний шаг
```

### Workflow (Action)

```python
# src/Containers/AppSection/OrderModule/Workflows/CreateOrderWorkflow.py

from temporalio import workflow
from temporalio.common import RetryPolicy
from returns.result import Result, Success, Failure
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID
from decimal import Decimal

@dataclass
class CreateOrderInput:
    user_id: UUID
    items: list[OrderItem]
    total_amount: Decimal


@dataclass
class OrderResult:
    order_id: UUID
    reservation_id: UUID
    payment_id: UUID
    delivery_id: UUID
    estimated_delivery: datetime


@dataclass
class OrderCreationFailed:
    reason: str
    failed_step: str | None = None


@workflow.defn
class CreateOrderWorkflow:
    """
    Saga для создания заказа.
    
    Шаги:
    1. Create Order (PENDING) → cancel_order
    2. Reserve Inventory → cancel_reservation  
    3. Charge Payment → refund_payment
    4. Schedule Delivery (no compensation)
    """
    
    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderCreationFailed]:
        compensations: list[tuple] = []
        
        try:
            # ═══════════════════════════════════════════════════════
            # STEP 1: CREATE ORDER
            # ═══════════════════════════════════════════════════════
            workflow.logger.info(f"Step 1: Creating order for user {data.user_id}")
            
            compensations.append((cancel_order, ()))  # Регистрируем ДО!
            order = await workflow.execute_activity(
                create_order, data,
                start_to_close_timeout=timedelta(seconds=30),
            )
            # Обновляем аргументы компенсации
            compensations[-1] = (cancel_order, (order.order_id,))
            
            workflow.logger.info(f"Order {order.order_id} created")
            
            # ═══════════════════════════════════════════════════════
            # STEP 2: RESERVE INVENTORY
            # ═══════════════════════════════════════════════════════
            workflow.logger.info(f"Step 2: Reserving inventory")
            
            compensations.append((cancel_reservation, ()))
            reservation = await workflow.execute_activity(
                reserve_inventory, order.order_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            compensations[-1] = (cancel_reservation, (reservation.reservation_id,))
            
            workflow.logger.info(f"Reservation {reservation.reservation_id} created")
            
            # ═══════════════════════════════════════════════════════
            # STEP 3: CHARGE PAYMENT
            # ═══════════════════════════════════════════════════════
            workflow.logger.info(f"Step 3: Charging payment")
            
            compensations.append((refund_payment, ()))
            payment = await workflow.execute_activity(
                charge_payment, order.order_id,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                ),
            )
            compensations[-1] = (refund_payment, (payment.payment_id,))
            
            workflow.logger.info(f"Payment {payment.payment_id} charged: {payment.amount}")
            
            # ═══════════════════════════════════════════════════════
            # STEP 4: SCHEDULE DELIVERY (no compensation)
            # ═══════════════════════════════════════════════════════
            workflow.logger.info(f"Step 4: Scheduling delivery")
            
            # Без регистрации компенсации — последний шаг
            delivery = await workflow.execute_activity(
                schedule_delivery, order.order_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            workflow.logger.info(f"Delivery {delivery.delivery_id} scheduled")
            
            # ═══════════════════════════════════════════════════════
            # SUCCESS
            # ═══════════════════════════════════════════════════════
            return Success(OrderResult(
                order_id=order.order_id,
                reservation_id=reservation.reservation_id,
                payment_id=payment.payment_id,
                delivery_id=delivery.delivery_id,
                estimated_delivery=delivery.estimated_date,
            ))
            
        except Exception as ex:
            # ═══════════════════════════════════════════════════════
            # ROLLBACK
            # ═══════════════════════════════════════════════════════
            workflow.logger.error(f"Saga failed: {ex}. Starting rollback...")
            
            for comp_func, comp_args in reversed(compensations):
                if comp_args:  # Есть аргументы — шаг был выполнен
                    try:
                        await workflow.execute_activity(
                            comp_func, *comp_args,
                            start_to_close_timeout=timedelta(seconds=30),
                        )
                        workflow.logger.info(f"Compensation {comp_func.__name__} completed")
                    except Exception as comp_ex:
                        workflow.logger.exception(
                            f"Compensation {comp_func.__name__} failed: {comp_ex}"
                        )
            
            return Failure(OrderCreationFailed(reason=str(ex)))
```

### Запуск Workflow

```python
# src/Containers/AppSection/OrderModule/Actions/CreateOrderAction.py

from temporalio.client import Client
from returns.result import Result, Success, Failure
from dataclasses import dataclass
from uuid import uuid4

@dataclass
class CreateOrderAction(Action[CreateOrderRequest, OrderResponse, OrderError]):
    """Action для создания заказа через Temporal."""
    
    temporal_client: Client
    
    async def run(self, data: CreateOrderRequest) -> Result[OrderResponse, OrderError]:
        # Запускаем Workflow
        workflow_id = f"order-{uuid4()}"
        
        handle = await self.temporal_client.start_workflow(
            CreateOrderWorkflow.run,
            CreateOrderInput(
                user_id=data.user_id,
                items=data.items,
                total_amount=data.total_amount,
            ),
            id=workflow_id,
            task_queue="orders",
        )
        
        # Ждём результат (или можно вернуть workflow_id для polling)
        result = await handle.result()
        
        match result:
            case Success(order_result):
                return Success(OrderResponse.from_result(order_result))
            case Failure(error):
                return Failure(OrderCreationError(
                    message=error.reason,
                    workflow_id=workflow_id,
                ))
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
