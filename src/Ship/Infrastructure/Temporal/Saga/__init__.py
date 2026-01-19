"""Temporal Saga Infrastructure — паттерны компенсаций для Temporal.io.

Saga обеспечивает консистентность данных в распределенных транзакциях
через последовательное выполнение шагов с автоматической компенсацией
при ошибках.

ВАЖНО: Saga реализованы на Temporal для durability и long-running workflows.
TaskIQ используется ТОЛЬКО для простых фоновых задач (email, notifications).

Три уровня сложности паттернов:
┌─────────────────────────────────────────────────────────────────────────┐
│  1. ПРОСТОЙ LIST (⭐) — официальный паттерн Temporal                    │
│     - 2-4 шага, одинаковые аргументы компенсаций                       │
│     - compensations.append(func) ДО activity                            │
│     - reversed(compensations) — LIFO                                    │
│                                                                         │
│  2. SagaCompensations (⭐⭐) — улучшенный паттерн                        │
│     - 5+ шагов, разные аргументы для компенсаций                       │
│     - comp.add(func, *args) ПОСЛЕ activity                             │
│     - await comp.run_all() — автоматический LIFO                       │
│                                                                         │
│  3. ДЕКЛАРАТИВНЫЙ (⭐⭐⭐) — для сложных workflows                       │
│     - Сложные зависимости между шагами                                 │
│     - SagaStep dataclass + execute_saga()                              │
│     - Полная информация о выполнении                                   │
└─────────────────────────────────────────────────────────────────────────┘

Примеры использования:

1. Простой list (официальный паттерн):
    
    @workflow.defn
    class BookingWorkflow:
        @workflow.run
        async def run(self, data: BookingInput) -> Result[Booking, BookingError]:
            compensations: list[Callable] = []
            
            try:
                compensations.append(undo_book_car)
                car = await workflow.execute_activity(book_car, data, ...)
                
                compensations.append(undo_book_hotel)
                hotel = await workflow.execute_activity(book_hotel, data, ...)
                
                return Success(Booking(car=car, hotel=hotel))
                
            except Exception as ex:
                for comp in reversed(compensations):
                    await workflow.execute_activity(comp, data, ...)
                return Failure(BookingError(reason=str(ex)))

2. SagaCompensations класс:

    from src.Ship.Infrastructure.Temporal.Saga import SagaCompensations
    
    @workflow.defn
    class OrderWorkflow:
        @workflow.run
        async def run(self, data: OrderInput) -> Result[Order, OrderError]:
            comp = SagaCompensations()
            
            try:
                order = await workflow.execute_activity(create_order, data, ...)
                comp.add(cancel_order, order.id)  # С аргументом!
                
                payment = await workflow.execute_activity(charge, order.id, ...)
                comp.add(refund, payment.id, payment.amount)  # Несколько args!
                
                return Success(order)
                
            except Exception as ex:
                await comp.run_all()
                return Failure(OrderError(reason=str(ex)))

3. Декларативный паттерн:

    from src.Ship.Infrastructure.Temporal.Saga import SagaStep, execute_saga
    
    @workflow.defn
    class ComplexWorkflow:
        @workflow.run
        async def run(self, data: Input) -> Result[Output, Error]:
            steps = [
                SagaStep("order", create_order, cancel_order),
                SagaStep("payment", charge, refund, timeout=timedelta(seconds=60)),
                SagaStep("notify", send_notification),  # без компенсации
            ]
            
            result = await execute_saga(steps, data)
            
            match result:
                case Success(saga_result):
                    return Success(Output(
                        order_id=saga_result["order"]["id"],
                        payment_id=saga_result["payment"]["id"],
                    ))
                case Failure(error):
                    return Failure(Error(reason=error.cause))

Документация:
- docs/22-temporal-saga-patterns.md — полное описание паттернов
- docs/21-integration-patterns-guide.md — когда Temporal vs TaskIQ
"""

# SagaCompensations — улучшенный паттерн (Pattern 2)
from src.Ship.Infrastructure.Temporal.Saga.Compensations import (
    SagaCompensations,
    ParallelCompensations,
)

# Декларативный паттерн (Pattern 3)
from src.Ship.Infrastructure.Temporal.Saga.Steps import (
    SagaStep,
    SagaResult,
    SagaBuilder,
    execute_saga,
)

# Ошибки
from src.Ship.Infrastructure.Temporal.Saga.Errors import (
    SagaError,
    SagaStepFailedError,
    CompensationFailedError,
    SagaTimeoutError,
    SagaCancellationError,
    SagaValidationError,
    SagaRetryExhaustedError,
)


__all__ = [
    # Pattern 2: SagaCompensations class
    "SagaCompensations",
    "ParallelCompensations",
    # Pattern 3: Declarative
    "SagaStep",
    "SagaResult",
    "SagaBuilder",
    "execute_saga",
    # Errors
    "SagaError",
    "SagaStepFailedError",
    "CompensationFailedError",
    "SagaTimeoutError",
    "SagaCancellationError",
    "SagaValidationError",
    "SagaRetryExhaustedError",
]
