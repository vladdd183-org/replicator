"""Temporal Saga Declarative Pattern — декларативное описание шагов Saga.

Предоставляет SagaStep dataclass и execute_saga функцию для
декларативного описания Saga через список шагов.

Это третий (самый продвинутый) уровень сложности паттернов.
Используй когда:
- Сложные зависимости между шагами
- Динамическое построение Saga
- Нужна полная информация о выполнении

Пример:
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
                        order_id=results["order"]["id"],
                        reservation_id=results["reservation"]["id"],
                        ...
                    ))
                case Failure(error):
                    return Failure(OrderCreationFailed(
                        reason=error.cause,
                        failed_step=error.failed_step,
                    ))
"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable

from temporalio import workflow
from temporalio.common import RetryPolicy
from returns.result import Result, Success, Failure

from src.Ship.Infrastructure.Temporal.Saga.Errors import SagaStepFailedError


@dataclass(frozen=True)
class SagaStep:
    """Декларативное описание шага Saga.
    
    Immutable dataclass для описания одного шага.
    Каждый шаг имеет action (обязательно) и compensate (опционально).
    
    Attributes:
        name: Уникальное имя шага (используется как ключ в results)
        action: Activity function для выполнения (обязательно @activity.defn)
        compensate: Activity function для компенсации (None если не нужна)
        timeout: Timeout для activity
        retry_policy: Политика повторов для activity
        description: Человекочитаемое описание для логирования
        
    Example:
        SagaStep(
            name="payment",
            action=charge_payment,
            compensate=refund_payment,
            timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
            description="Process payment for order",
        )
    """
    
    name: str
    action: Callable[..., Any]
    compensate: Callable[..., Any] | None = None
    timeout: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    retry_policy: RetryPolicy | None = None
    description: str = ""
    
    def __post_init__(self) -> None:
        """Валидация полей."""
        if not self.name:
            raise ValueError("SagaStep name cannot be empty")
        if self.action is None:
            raise ValueError(f"SagaStep '{self.name}' must have an action")


@dataclass
class SagaResult:
    """Результат выполнения Saga.
    
    Содержит результаты всех успешно выполненных шагов.
    
    Attributes:
        results: Dict с результатами {step_name: result}
        input: Исходные входные данные
        completed_steps: Список имён завершённых шагов (в порядке выполнения)
    """
    
    results: dict[str, Any]
    input: Any
    completed_steps: list[str] = field(default_factory=list)
    
    def get(self, step_name: str, default: Any = None) -> Any:
        """Получить результат шага по имени."""
        return self.results.get(step_name, default)
    
    def __getitem__(self, step_name: str) -> Any:
        """Доступ через квадратные скобки: result['payment']."""
        return self.results[step_name]
    
    def __contains__(self, step_name: str) -> bool:
        """Проверка наличия результата: 'payment' in result."""
        return step_name in self.results


async def execute_saga(
    steps: list[SagaStep],
    initial_data: Any,
    *,
    pass_all_results: bool = False,
    compensation_timeout: timedelta | None = None,
) -> Result[SagaResult, SagaStepFailedError]:
    """Выполнить Saga декларативно.
    
    Последовательно выполняет все шаги. При ошибке автоматически
    запускает компенсации для всех успешно выполненных шагов
    в обратном порядке (LIFO).
    
    Args:
        steps: Список шагов Saga (в порядке выполнения)
        initial_data: Входные данные для первого шага
        pass_all_results: Если True, передавать dict всех результатов в каждый шаг.
                          Если False (default), передавать только initial_data.
        compensation_timeout: Timeout для компенсаций (default: step.timeout)
    
    Returns:
        Success[SagaResult]: Результаты всех шагов
        Failure[SagaStepFailedError]: Информация об ошибке
    
    Example:
        steps = [
            SagaStep(name="order", action=create_order, compensate=cancel_order),
            SagaStep(name="payment", action=charge_payment, compensate=refund_payment),
        ]
        
        result = await execute_saga(steps, order_data)
        
        match result:
            case Success(saga_result):
                order_id = saga_result["order"]["id"]
                payment_id = saga_result["payment"]["id"]
            case Failure(error):
                logger.error(f"Failed at {error.failed_step}: {error.cause}")
    """
    results: dict[str, Any] = {"_input": initial_data}
    executed: list[tuple[SagaStep, Any]] = []
    completed_steps: list[str] = []
    
    workflow.logger.info(f"🎭 Starting saga with {len(steps)} steps")
    
    for i, step in enumerate(steps):
        step_name = step.name
        
        workflow.logger.info(
            f"🔹 Step {i + 1}/{len(steps)}: {step_name}"
            + (f" - {step.description}" if step.description else "")
        )
        
        try:
            # Определяем что передавать в activity
            activity_input = results if pass_all_results else initial_data
            
            # Выполняем activity
            activity_kwargs: dict[str, Any] = {
                "start_to_close_timeout": step.timeout,
            }
            if step.retry_policy:
                activity_kwargs["retry_policy"] = step.retry_policy
            
            step_result = await workflow.execute_activity(
                step.action,
                activity_input,
                **activity_kwargs,
            )
            
            # Сохраняем результат
            results[step_name] = step_result
            completed_steps.append(step_name)
            
            # Регистрируем для потенциальной компенсации
            if step.compensate:
                executed.append((step, step_result))
            
            workflow.logger.info(f"✅ Step completed: {step_name}")
            
        except Exception as e:
            error_msg = str(e)
            workflow.logger.error(f"❌ Step failed: {step_name} - {error_msg}")
            
            # Запускаем компенсации в обратном порядке
            await _run_compensations(executed, compensation_timeout)
            
            return Failure(SagaStepFailedError(
                failed_step=step_name,
                cause=error_msg,
                completed_steps=completed_steps,
            ))
    
    workflow.logger.info(f"🎉 Saga completed successfully with {len(completed_steps)} steps")
    
    return Success(SagaResult(
        results=results,
        input=initial_data,
        completed_steps=completed_steps,
    ))


async def _run_compensations(
    executed: list[tuple[SagaStep, Any]],
    custom_timeout: timedelta | None = None,
) -> None:
    """Выполнить компенсации для всех executed шагов.
    
    Выполняет в обратном порядке (LIFO).
    Продолжает при ошибках, логируя их.
    
    Args:
        executed: Список (step, result) для компенсации
        custom_timeout: Кастомный timeout (используется step.timeout если None)
    """
    if not executed:
        return
    
    workflow.logger.info(f"🔙 Running {len(executed)} compensations")
    
    for step, step_result in reversed(executed):
        if step.compensate is None:
            continue
        
        try:
            workflow.logger.info(f"🔹 Compensating: {step.name}")
            
            timeout = custom_timeout or step.timeout
            
            await workflow.execute_activity(
                step.compensate,
                step_result,
                start_to_close_timeout=timeout,
            )
            
            workflow.logger.info(f"✅ Compensation completed: {step.name}")
            
        except Exception as e:
            workflow.logger.exception(
                f"❌ Compensation for {step.name} failed: {e}"
            )
            # Продолжаем компенсацию остальных шагов


# Type alias для builder pattern
SagaStepList = list[SagaStep]


class SagaBuilder:
    """Builder для создания списка шагов Saga.
    
    Предоставляет fluent API для построения Saga.
    
    Example:
        saga = (
            SagaBuilder()
            .add_step("order", create_order, cancel_order)
            .add_step("payment", charge_payment, refund_payment,
                      timeout=timedelta(seconds=60))
            .add_step("notification", send_notification)  # без компенсации
            .build()
        )
        
        result = await execute_saga(saga, data)
    """
    
    def __init__(self) -> None:
        self._steps: list[SagaStep] = []
    
    def add_step(
        self,
        name: str,
        action: Callable[..., Any],
        compensate: Callable[..., Any] | None = None,
        *,
        timeout: timedelta | None = None,
        retry_policy: RetryPolicy | None = None,
        description: str = "",
    ) -> "SagaBuilder":
        """Добавить шаг в Saga.
        
        Args:
            name: Уникальное имя шага
            action: Activity для выполнения
            compensate: Activity для компенсации (опционально)
            timeout: Timeout для activity
            retry_policy: Политика повторов
            description: Описание шага
            
        Returns:
            Self для chaining
        """
        step = SagaStep(
            name=name,
            action=action,
            compensate=compensate,
            timeout=timeout or timedelta(seconds=30),
            retry_policy=retry_policy,
            description=description,
        )
        self._steps.append(step)
        return self
    
    def with_retry(
        self,
        maximum_attempts: int = 3,
        initial_interval_seconds: float = 1.0,
    ) -> "SagaBuilder":
        """Установить retry policy для последнего добавленного шага.
        
        Args:
            maximum_attempts: Максимум попыток
            initial_interval_seconds: Начальный интервал
            
        Returns:
            Self для chaining
            
        Example:
            saga = (
                SagaBuilder()
                .add_step("payment", charge, refund)
                .with_retry(maximum_attempts=5)
                .build()
            )
        """
        if self._steps:
            last_step = self._steps[-1]
            # Create new step with retry policy (SagaStep is frozen)
            new_step = SagaStep(
                name=last_step.name,
                action=last_step.action,
                compensate=last_step.compensate,
                timeout=last_step.timeout,
                retry_policy=RetryPolicy(
                    maximum_attempts=maximum_attempts,
                    initial_interval=timedelta(seconds=initial_interval_seconds),
                ),
                description=last_step.description,
            )
            self._steps[-1] = new_step
        return self
    
    def with_timeout(self, seconds: float) -> "SagaBuilder":
        """Установить timeout для последнего добавленного шага.
        
        Args:
            seconds: Timeout в секундах
            
        Returns:
            Self для chaining
        """
        if self._steps:
            last_step = self._steps[-1]
            new_step = SagaStep(
                name=last_step.name,
                action=last_step.action,
                compensate=last_step.compensate,
                timeout=timedelta(seconds=seconds),
                retry_policy=last_step.retry_policy,
                description=last_step.description,
            )
            self._steps[-1] = new_step
        return self
    
    def build(self) -> list[SagaStep]:
        """Построить и вернуть список шагов.
        
        Returns:
            Список SagaStep для передачи в execute_saga
        """
        return list(self._steps)
    
    def __len__(self) -> int:
        """Количество шагов."""
        return len(self._steps)


# Export all
__all__ = [
    "SagaStep",
    "SagaResult",
    "SagaBuilder",
    "SagaStepList",
    "execute_saga",
]
