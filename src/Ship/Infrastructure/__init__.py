"""Infrastructure module - Database, Cache, Telemetry, Events, Temporal.

This module provides core infrastructure components:

- Cache: Caching utilities with cashews
- Channels: Litestar channels integration
- Concurrency: Rate limiting and task groups
- Database: Database connections
- Events: Unified Event Bus (InMemory, Redis, RabbitMQ)
- MessageBus: Legacy event handlers (deprecated)
- Telemetry: Logging and tracing with Logfire
- Temporal: Durable Execution, Saga patterns (Temporal.io)
- Workers: TaskIQ background task broker (simple fire-and-forget jobs)

Temporal vs TaskIQ:
┌─────────────────────────────────────────────────────────────────────────┐
│  TEMPORAL (durable execution)                                           │
│  ✓ Критичные бизнес-процессы (заказы, платежи, подписки)               │
│  ✓ Saga с компенсациями (отмена при ошибках)                           │
│  ✓ Долгие процессы (часы, дни — approval workflows)                    │
│  ✓ Требуется история выполнения и debugging                            │
├─────────────────────────────────────────────────────────────────────────┤
│  TASKIQ (fire-and-forget)                                               │
│  ✓ Отправка email, SMS, push-уведомлений                               │
│  ✓ Очистка временных файлов, кэшей                                     │
│  ✓ Фоновая индексация, синхронизация                                   │
└─────────────────────────────────────────────────────────────────────────┘
"""

from src.Ship.Infrastructure.Events import (
    EventBusProtocol,
    create_event_bus,
    subscribe,
)

# Temporal.io - Durable Execution & Saga
from src.Ship.Infrastructure.Temporal import (
    # Client
    get_temporal_client,
    create_temporal_client,
    TemporalClientConfig,
    # Worker
    create_temporal_worker,
    run_temporal_worker,
    TemporalWorkerConfig,
    # Decorators
    temporal_activity,
    temporal_workflow,
    activity_options,
    default_retry_policy,
    # Saga Patterns
    SagaCompensations,
    ParallelCompensations,
    SagaStep,
    SagaResult,
    SagaBuilder,
    execute_saga,
    # Errors
    TemporalError,
    SagaError,
    SagaStepFailedError,
)

__all__ = [
    # Events
    "EventBusProtocol",
    "create_event_bus",
    "subscribe",
    # Temporal Client
    "get_temporal_client",
    "create_temporal_client",
    "TemporalClientConfig",
    # Temporal Worker
    "create_temporal_worker",
    "run_temporal_worker",
    "TemporalWorkerConfig",
    # Temporal Decorators
    "temporal_activity",
    "temporal_workflow",
    "activity_options",
    "default_retry_policy",
    # Saga Patterns
    "SagaCompensations",
    "ParallelCompensations",
    "SagaStep",
    "SagaResult",
    "SagaBuilder",
    "execute_saga",
    # Errors
    "TemporalError",
    "SagaError",
    "SagaStepFailedError",
]

