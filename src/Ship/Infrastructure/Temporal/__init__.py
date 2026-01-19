"""Temporal.io Infrastructure — Durable Execution Engine.

Temporal обеспечивает:
- **Durability**: Workflows переживают перезапуски, сбои инфраструктуры
- **Saga Pattern**: Компенсирующие транзакции с гарантированным выполнением
- **Long-running**: Процессы на часы/дни/недели с сохранением состояния
- **Observability**: Полная история выполнения, retry, debugging

КОГДА ИСПОЛЬЗОВАТЬ Temporal vs TaskIQ:

┌─────────────────────────────────────────────────────────────────────────┐
│  TEMPORAL (durable execution)                                           │
│  ✓ Критичные бизнес-процессы (заказы, платежи, подписки)               │
│  ✓ Saga с компенсациями (отмена при ошибках)                           │
│  ✓ Долгие процессы (часы, дни — approval workflows)                    │
│  ✓ Требуется история выполнения и debugging                            │
│  ✓ Нужна гарантия exactly-once                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  TASKIQ (fire-and-forget)                                               │
│  ✓ Отправка email, SMS, push-уведомлений                               │
│  ✓ Очистка временных файлов, кэшей                                     │
│  ✓ Фоновая индексация, синхронизация                                   │
│  ✓ Простые задачи без зависимостей                                     │
│  ✓ Best-effort доставка достаточна                                     │
└─────────────────────────────────────────────────────────────────────────┘

Структура:

    src/Ship/Infrastructure/Temporal/
    ├── __init__.py          # Этот файл — экспорты
    ├── Client.py            # Temporal Client factory
    ├── Worker.py            # Temporal Worker setup
    ├── Decorators.py        # Helpers для @workflow.defn, @activity.defn
    ├── Providers.py         # Dishka DI providers
    ├── Errors.py            # Temporal-specific errors
    └── Saga/                # Saga compensation patterns
        ├── __init__.py
        ├── Compensations.py # SagaCompensations класс
        ├── Steps.py         # SagaStep, execute_saga()
        └── Errors.py        # Saga errors

Интеграция с Porto:

    - Activities = Porto Tasks (атомарные операции)
    - Workflows = Сложные Porto Actions с Saga
    - Result[T, E] возвращается из Workflow

Пример использования:

    from src.Ship.Infrastructure.Temporal import (
        get_temporal_client,
        SagaCompensations,
        SagaStep,
        execute_saga,
    )
    
    @workflow.defn
    class CreateOrderWorkflow:
        @workflow.run
        async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
            comp = SagaCompensations()
            
            try:
                order = await workflow.execute_activity(
                    create_order_activity, data,
                    start_to_close_timeout=timedelta(seconds=30),
                )
                comp.add(cancel_order_activity, order.id)
                
                payment = await workflow.execute_activity(
                    charge_payment_activity, order.id,
                    start_to_close_timeout=timedelta(seconds=60),
                )
                comp.add(refund_payment_activity, payment.id, payment.amount)
                
                return Success(OrderResult(...))
                
            except Exception as ex:
                await comp.run_all()
                return Failure(OrderCreationFailed(reason=str(ex)))

Документация:
- docs/15-saga-patterns.md — паттерны компенсаций
- docs/21-integration-patterns-guide.md — когда Temporal vs TaskIQ
"""

# Client
from src.Ship.Infrastructure.Temporal.Client import (
    get_temporal_client,
    create_temporal_client,
    TemporalClientConfig,
)

# Worker
from src.Ship.Infrastructure.Temporal.Worker import (
    create_temporal_worker,
    run_temporal_worker,
    TemporalWorkerConfig,
)

# Decorators & Helpers
from src.Ship.Infrastructure.Temporal.Decorators import (
    temporal_activity,
    temporal_workflow,
    with_saga_compensations,
    activity_options,
    default_retry_policy,
)

# Saga Patterns
from src.Ship.Infrastructure.Temporal.Saga import (
    # Pattern 2: SagaCompensations class
    SagaCompensations,
    ParallelCompensations,
    # Pattern 3: Declarative
    SagaStep,
    SagaResult,
    SagaBuilder,
    execute_saga,
)

# Errors
from src.Ship.Infrastructure.Temporal.Errors import (
    TemporalError,
    TemporalConnectionError,
    TemporalWorkflowError,
    TemporalActivityError,
    TemporalTimeoutError,
    WorkflowNotFoundError,
    WorkflowAlreadyExistsError,
)

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
    # Client
    "get_temporal_client",
    "create_temporal_client",
    "TemporalClientConfig",
    # Worker
    "create_temporal_worker",
    "run_temporal_worker",
    "TemporalWorkerConfig",
    # Decorators
    "temporal_activity",
    "temporal_workflow",
    "with_saga_compensations",
    "activity_options",
    "default_retry_policy",
    # Saga Pattern 2
    "SagaCompensations",
    "ParallelCompensations",
    # Saga Pattern 3
    "SagaStep",
    "SagaResult",
    "SagaBuilder",
    "execute_saga",
    # Temporal Errors
    "TemporalError",
    "TemporalConnectionError",
    "TemporalWorkflowError",
    "TemporalActivityError",
    "TemporalTimeoutError",
    "WorkflowNotFoundError",
    "WorkflowAlreadyExistsError",
    # Saga Errors
    "SagaError",
    "SagaStepFailedError",
    "CompensationFailedError",
    "SagaTimeoutError",
    "SagaCancellationError",
    "SagaValidationError",
    "SagaRetryExhaustedError",
]
