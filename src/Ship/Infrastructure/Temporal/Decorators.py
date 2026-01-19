"""Temporal Decorators & Helpers — утилиты для работы с Temporal.

Предоставляет:
- Упрощённые декораторы для activities и workflows
- Стандартные RetryPolicy конфигурации
- Helpers для common patterns

Использование:

    from src.Ship.Infrastructure.Temporal.Decorators import (
        temporal_activity,
        temporal_workflow,
        default_retry_policy,
        activity_options,
    )
    
    # Activity с стандартными настройками
    @temporal_activity
    async def create_order(data: CreateOrderInput) -> Order:
        ...
    
    # Workflow с Result
    @temporal_workflow
    class CreateOrderWorkflow:
        @workflow.run
        async def run(self, data: CreateOrderInput) -> Result[Order, OrderError]:
            ...
    
    # В workflow — вызов activity с опциями
    result = await workflow.execute_activity(
        create_order,
        data,
        **activity_options(timeout_seconds=60, max_retries=3),
    )

Интеграция с Porto:

    Activities = Porto Tasks (атомарные операции)
    - Используй @temporal_activity для Tasks, которые нужны в workflows
    - Обычные Tasks (без Temporal) используют @activity.defn напрямую
    
    Workflows = Сложные Porto Actions с Saga
    - Используй @temporal_workflow для Saga workflows
    - Возвращай Result[T, E] для Railway-Oriented Programming
"""

from datetime import timedelta
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from src.Ship.Configs.Settings import get_settings


# Type variables
P = ParamSpec("P")
T = TypeVar("T")


# =============================================================================
# Standard Retry Policies
# =============================================================================

def default_retry_policy(
    maximum_attempts: int = 3,
    initial_interval_seconds: float = 1.0,
    maximum_interval_seconds: float = 60.0,
    backoff_coefficient: float = 2.0,
) -> RetryPolicy:
    """Create a standard retry policy for activities.
    
    Default configuration suitable for most activities:
    - 3 attempts max
    - Exponential backoff starting at 1s
    - Max interval 60s
    
    Args:
        maximum_attempts: Max retry attempts (0 = unlimited)
        initial_interval_seconds: Initial retry delay
        maximum_interval_seconds: Max retry delay
        backoff_coefficient: Multiplier for each retry
        
    Returns:
        RetryPolicy instance
        
    Example:
        await workflow.execute_activity(
            my_activity,
            data,
            retry_policy=default_retry_policy(maximum_attempts=5),
        )
    """
    return RetryPolicy(
        maximum_attempts=maximum_attempts,
        initial_interval=timedelta(seconds=initial_interval_seconds),
        maximum_interval=timedelta(seconds=maximum_interval_seconds),
        backoff_coefficient=backoff_coefficient,
    )


def payment_retry_policy() -> RetryPolicy:
    """Retry policy for payment operations.
    
    More conservative: fewer attempts, longer intervals.
    Suitable for idempotent payment APIs.
    
    Returns:
        RetryPolicy for payments
    """
    return RetryPolicy(
        maximum_attempts=3,
        initial_interval=timedelta(seconds=5),
        maximum_interval=timedelta(seconds=120),
        backoff_coefficient=3.0,
        non_retryable_error_types=["PaymentDeclinedError", "InsufficientFundsError"],
    )


def external_api_retry_policy() -> RetryPolicy:
    """Retry policy for external API calls.
    
    Handles transient failures (rate limits, timeouts).
    More aggressive retries with exponential backoff.
    
    Returns:
        RetryPolicy for external APIs
    """
    return RetryPolicy(
        maximum_attempts=5,
        initial_interval=timedelta(seconds=2),
        maximum_interval=timedelta(seconds=300),
        backoff_coefficient=2.0,
    )


def notification_retry_policy() -> RetryPolicy:
    """Retry policy for notifications (email, SMS, push).
    
    Best-effort delivery: many attempts over long period.
    
    Returns:
        RetryPolicy for notifications
    """
    return RetryPolicy(
        maximum_attempts=10,
        initial_interval=timedelta(seconds=10),
        maximum_interval=timedelta(seconds=3600),  # 1 hour max
        backoff_coefficient=2.0,
    )


# =============================================================================
# Activity Options Helper
# =============================================================================

def activity_options(
    timeout_seconds: float = 30.0,
    max_retries: int = 3,
    schedule_to_close_timeout_seconds: float | None = None,
    heartbeat_timeout_seconds: float | None = None,
    retry_policy: RetryPolicy | None = None,
) -> dict[str, Any]:
    """Create standard activity options dict.
    
    Helper to reduce boilerplate when calling execute_activity.
    
    Args:
        timeout_seconds: Start-to-close timeout (default 30s)
        max_retries: Maximum retry attempts (default 3)
        schedule_to_close_timeout_seconds: Total time from scheduling
        heartbeat_timeout_seconds: Heartbeat timeout for long activities
        retry_policy: Custom retry policy (overrides max_retries)
        
    Returns:
        Dict of activity options for **kwargs
        
    Example:
        await workflow.execute_activity(
            my_activity,
            data,
            **activity_options(timeout_seconds=60, max_retries=5),
        )
    """
    options: dict[str, Any] = {
        "start_to_close_timeout": timedelta(seconds=timeout_seconds),
    }
    
    if schedule_to_close_timeout_seconds:
        options["schedule_to_close_timeout"] = timedelta(
            seconds=schedule_to_close_timeout_seconds
        )
    
    if heartbeat_timeout_seconds:
        options["heartbeat_timeout"] = timedelta(seconds=heartbeat_timeout_seconds)
    
    if retry_policy:
        options["retry_policy"] = retry_policy
    elif max_retries > 0:
        options["retry_policy"] = default_retry_policy(maximum_attempts=max_retries)
    
    return options


def long_running_activity_options(
    timeout_minutes: float = 10.0,
    heartbeat_interval_seconds: float = 30.0,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Activity options for long-running operations.
    
    Includes heartbeat configuration for activities that take minutes.
    Activity should call activity.heartbeat() periodically.
    
    Args:
        timeout_minutes: Start-to-close timeout in minutes
        heartbeat_interval_seconds: Heartbeat interval
        max_retries: Maximum retry attempts
        
    Returns:
        Dict of activity options
        
    Example:
        @activity.defn
        async def process_large_file(file_path: str) -> str:
            for chunk in read_chunks(file_path):
                process(chunk)
                activity.heartbeat()  # Keep alive!
            return "done"
        
        await workflow.execute_activity(
            process_large_file,
            path,
            **long_running_activity_options(timeout_minutes=30),
        )
    """
    return {
        "start_to_close_timeout": timedelta(minutes=timeout_minutes),
        "heartbeat_timeout": timedelta(seconds=heartbeat_interval_seconds * 3),
        "retry_policy": default_retry_policy(maximum_attempts=max_retries),
    }


# =============================================================================
# Decorators
# =============================================================================

def temporal_activity(
    func: Callable[P, T] | None = None,
    *,
    name: str | None = None,
) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to mark a function as Temporal activity.
    
    Wrapper around @activity.defn with Porto conventions.
    
    Args:
        func: Function to decorate (or None for parameterized decorator)
        name: Activity name (defaults to function name)
        
    Returns:
        Decorated function
        
    Example:
        @temporal_activity
        async def create_order(data: CreateOrderInput) -> Order:
            async with uow:
                order = Order(...)
                await uow.orders.add(order)
                await uow.commit()
            return order
        
        # With custom name
        @temporal_activity(name="order.create")
        async def create_order(data: CreateOrderInput) -> Order:
            ...
    """
    def decorator(fn: Callable[P, T]) -> Callable[P, T]:
        # Apply Temporal's activity.defn
        decorated = activity.defn(name=name)(fn)
        return decorated
    
    if func is not None:
        return decorator(func)
    return decorator


def temporal_workflow(
    cls: type | None = None,
    *,
    name: str | None = None,
    sandboxed: bool = True,
) -> type | Callable[[type], type]:
    """Decorator to mark a class as Temporal workflow.
    
    Wrapper around @workflow.defn with Porto conventions.
    
    Args:
        cls: Class to decorate (or None for parameterized decorator)
        name: Workflow name (defaults to class name)
        sandboxed: Enable sandbox for determinism (default True)
        
    Returns:
        Decorated class
        
    Example:
        @temporal_workflow
        class CreateOrderWorkflow:
            @workflow.run
            async def run(self, data: CreateOrderInput) -> Result[Order, OrderError]:
                ...
        
        # With custom name
        @temporal_workflow(name="order.create")
        class CreateOrderWorkflow:
            ...
    """
    def decorator(workflow_cls: type) -> type:
        # Apply Temporal's workflow.defn
        decorated = workflow.defn(name=name, sandboxed=sandboxed)(workflow_cls)
        return decorated
    
    if cls is not None:
        return decorator(cls)
    return decorator


def with_saga_compensations(
    func: Callable[P, T],
) -> Callable[P, T]:
    """Decorator to inject SagaCompensations into workflow run method.
    
    Automatically creates SagaCompensations instance and handles cleanup.
    
    NOTE: This is a pattern suggestion. For complex sagas, 
    prefer explicit SagaCompensations management.
    
    Example:
        @workflow.defn
        class CreateOrderWorkflow:
            
            @workflow.run
            @with_saga_compensations
            async def run(
                self, 
                data: CreateOrderInput,
                compensations: SagaCompensations,  # Injected!
            ) -> Result[Order, OrderError]:
                ...
    """
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        from src.Ship.Infrastructure.Temporal.Saga import SagaCompensations
        
        compensations = SagaCompensations()
        kwargs["compensations"] = compensations
        
        try:
            return await func(*args, **kwargs)
        except Exception:
            await compensations.run_all()
            raise
    
    return wrapper


# =============================================================================
# Workflow Helpers
# =============================================================================

def get_workflow_id_prefix() -> str:
    """Get standard workflow ID prefix from settings.
    
    Returns:
        Workflow ID prefix
    """
    settings = get_settings()
    return settings.temporal_task_queue


def generate_workflow_id(entity_type: str, entity_id: str) -> str:
    """Generate a deterministic workflow ID.
    
    Format: {prefix}-{entity_type}-{entity_id}
    
    Args:
        entity_type: Type of entity (order, payment, etc.)
        entity_id: Entity identifier
        
    Returns:
        Workflow ID string
        
    Example:
        workflow_id = generate_workflow_id("order", "12345")
        # "hyper-porto-order-12345"
    """
    prefix = get_workflow_id_prefix()
    return f"{prefix}-{entity_type}-{entity_id}"


__all__ = [
    # Retry Policies
    "default_retry_policy",
    "payment_retry_policy",
    "external_api_retry_policy",
    "notification_retry_policy",
    # Activity Options
    "activity_options",
    "long_running_activity_options",
    # Decorators
    "temporal_activity",
    "temporal_workflow",
    "with_saga_compensations",
    # Helpers
    "get_workflow_id_prefix",
    "generate_workflow_id",
]
