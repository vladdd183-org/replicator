"""Temporal Saga Compensations — улучшенный паттерн для компенсаций.

Предоставляет класс SagaCompensations для:
- Хранения компенсаций с аргументами
- LIFO выполнения (последовательного или параллельного)
- Graceful error handling

Это второй уровень сложности паттернов компенсаций (после простого list).
Используй когда:
- Нужно передавать аргументы в компенсации
- 5+ шагов в Saga
- Нужен контроль над порядком выполнения (parallel/sequential)

Пример:
    @workflow.defn
    class CreateOrderWorkflow:
        @workflow.run
        async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
            comp = SagaCompensations()
            
            try:
                order = await workflow.execute_activity(
                    create_order, data,
                    start_to_close_timeout=timedelta(seconds=30),
                )
                comp.add(cancel_order, order.id)  # Аргументы!
                
                reservation = await workflow.execute_activity(
                    reserve_inventory, order.id,
                    start_to_close_timeout=timedelta(seconds=30),
                )
                comp.add(cancel_reservation, reservation.id)
                
                payment = await workflow.execute_activity(
                    charge_payment, order.id,
                    start_to_close_timeout=timedelta(seconds=60),
                )
                comp.add(refund_payment, payment.id, payment.amount)  # Несколько аргументов
                
                return Success(OrderResult(...))
                
            except Exception as ex:
                await comp.run_all()  # Автоматически в обратном порядке
                return Failure(OrderCreationFailed(reason=str(ex)))
"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable

import anyio
from temporalio import workflow
from temporalio.common import RetryPolicy


@dataclass
class SagaCompensations:
    """Compensation tracker с поддержкой аргументов и режимов выполнения.
    
    Преимущества над простым list:
    - Аргументы для каждой компенсации
    - Параллельное или последовательное выполнение
    - Graceful error handling (продолжает при ошибках)
    - Настраиваемый timeout
    
    Attributes:
        parallel: Если True, выполнять все компенсации параллельно.
                  Если False (default), выполнять LIFO последовательно.
        timeout: Timeout для каждой activity компенсации.
        continue_on_error: Если True, продолжать при ошибках компенсации.
        retry_policy: Политика повторов для компенсаций.
    
    Example:
        comp = SagaCompensations()
        
        # С одним аргументом
        comp.add(cancel_order, order_id)
        
        # С несколькими аргументами  
        comp.add(refund_payment, payment_id, amount)
        
        # Синтаксический сахар (без аргументов)
        comp += cancel_notification
        
        # Выполнить все в обратном порядке
        await comp.run_all()
    """
    
    _stack: list[tuple[Callable[..., Any], tuple[Any, ...]]] = field(default_factory=list)
    parallel: bool = False
    timeout: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    continue_on_error: bool = True
    retry_policy: RetryPolicy | None = None
    
    def add(self, func: Callable[..., Any], *args: Any) -> None:
        """Добавить компенсацию с аргументами.
        
        ВАЖНО: Регистрируй компенсацию ПОСЛЕ успешного выполнения activity,
        чтобы компенсировать только реально выполненные действия.
        
        Args:
            func: Activity function для компенсации (должна быть @activity.defn)
            *args: Аргументы для передачи в activity
        
        Example:
            # После успешного создания заказа
            order = await workflow.execute_activity(create_order, ...)
            comp.add(cancel_order, order.id)  # Теперь можно компенсировать
        """
        self._stack.append((func, args))
    
    def add_before(self, func: Callable[..., Any], *args: Any) -> None:
        """Добавить компенсацию ДО выполнения activity.
        
        Используется для официального паттерна Temporal, когда компенсация
        регистрируется перед возможным timeout.
        
        Args:
            func: Activity function для компенсации
            *args: Аргументы для передачи в activity
        
        Example:
            # Регистрируем компенсацию ДО activity (для protection от timeout)
            comp.add_before(cancel_order, data.order_id)
            order = await workflow.execute_activity(create_order, data, ...)
        """
        self._stack.append((func, args))
    
    def __iadd__(self, func: Callable[..., Any]) -> "SagaCompensations":
        """Синтаксический сахар: comp += cancel_order.
        
        Используй когда компенсация не требует аргументов.
        
        Args:
            func: Activity function для компенсации
            
        Returns:
            Self для цепочки вызовов
        """
        self.add(func)
        return self
    
    def __len__(self) -> int:
        """Количество зарегистрированных компенсаций."""
        return len(self._stack)
    
    @property
    def is_empty(self) -> bool:
        """Проверить, есть ли зарегистрированные компенсации."""
        return len(self._stack) == 0
    
    async def run_all(self) -> list[Exception | None]:
        """Выполнить все компенсации.
        
        Порядок выполнения:
        - parallel=False: LIFO (последовательно, с конца)
        - parallel=True: Все одновременно
        
        Returns:
            Список ошибок (None если успешно) для каждой компенсации
        """
        if not self._stack:
            return []
        
        workflow.logger.info(
            f"🔙 Running {len(self._stack)} compensations "
            f"({'parallel' if self.parallel else 'sequential LIFO'})"
        )
        
        if self.parallel:
            return await self._run_parallel()
        else:
            return await self._run_sequential()
    
    async def _run_sequential(self) -> list[Exception | None]:
        """LIFO — последовательно в обратном порядке.
        
        Каждая компенсация ждёт завершения предыдущей.
        Ошибки логируются, но не прерывают выполнение остальных.
        
        Returns:
            Список ошибок в порядке выполнения
        """
        errors: list[Exception | None] = []
        
        for func, args in reversed(self._stack):
            error = await self._execute_one(func, args)
            errors.append(error)
        
        return errors
    
    async def _run_parallel(self) -> list[Exception | None]:
        """Все компенсации параллельно.
        
        Используй когда компенсации независимы друг от друга
        и важна скорость.
        
        Returns:
            Список ошибок (порядок не гарантирован)
        """
        results: list[Exception | None] = [None] * len(self._stack)
        
        async def _run_one(index: int, func: Callable[..., Any], args: tuple[Any, ...]) -> None:
            results[index] = await self._execute_one(func, args)
        
        async with anyio.create_task_group() as tg:
            for index, (func, args) in enumerate(self._stack):
                tg.start_soon(_run_one, index, func, args)
        
        return results
    
    async def _execute_one(
        self,
        func: Callable[..., Any],
        args: tuple[Any, ...],
    ) -> Exception | None:
        """Выполнить одну компенсацию с error handling.
        
        Args:
            func: Activity function
            args: Аргументы для activity
            
        Returns:
            Exception если ошибка, None если успешно
        """
        func_name = getattr(func, "__name__", str(func))
        
        try:
            workflow.logger.info(f"🔹 Compensating: {func_name}")
            
            # Build activity options
            activity_kwargs: dict[str, Any] = {
                "start_to_close_timeout": self.timeout,
            }
            if self.retry_policy:
                activity_kwargs["retry_policy"] = self.retry_policy
            
            await workflow.execute_activity(
                func,
                *args,
                **activity_kwargs,
            )
            
            workflow.logger.info(f"✅ Compensation completed: {func_name}")
            return None
            
        except Exception as e:
            workflow.logger.exception(
                f"❌ Compensation {func_name} failed: {e}"
            )
            
            if not self.continue_on_error:
                raise
            
            return e
    
    def clear(self) -> None:
        """Очистить все зарегистрированные компенсации.
        
        Используй после успешного завершения всех шагов,
        когда компенсации больше не нужны.
        """
        self._stack.clear()
    
    def pop(self) -> tuple[Callable[..., Any], tuple[Any, ...]] | None:
        """Извлечь последнюю компенсацию (LIFO).
        
        Полезно для ручного управления компенсациями.
        
        Returns:
            Tuple (func, args) или None если стек пуст
        """
        if self._stack:
            return self._stack.pop()
        return None


@dataclass
class ParallelCompensations(SagaCompensations):
    """Специализированный класс для параллельных компенсаций.
    
    Просто SagaCompensations с parallel=True по умолчанию.
    Для удобства и явности намерения.
    
    Example:
        comp = ParallelCompensations()
        comp.add(cancel_order, order_id)
        comp.add(cancel_reservation, reservation_id)
        await comp.run_all()  # Обе выполнятся параллельно
    """
    
    parallel: bool = True


# Export all
__all__ = [
    "SagaCompensations",
    "ParallelCompensations",
]
