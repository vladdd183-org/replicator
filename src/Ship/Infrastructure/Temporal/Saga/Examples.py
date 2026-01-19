"""Примеры использования Temporal Saga паттернов.

Этот файл содержит примеры всех 3-х паттернов компенсаций:
1. Простой list (официальный паттерн Temporal)
2. SagaCompensations класс (улучшенный паттерн)
3. Декларативный паттерн (для сложных workflows)

Когда использовать какой:
┌─────────────────────────────────────────────────────────────────────────┐
│ Начни с простого list (официальный паттерн)                             │
│ → Если нужны аргументы → SagaCompensations                              │
│ → Если сложные зависимости → Декларативный                              │
└─────────────────────────────────────────────────────────────────────────┘

Сравнение:
| Подход            | Сложность | Когда использовать          |
|-------------------|-----------|----------------------------|
| Простой list      | ⭐        | 2-4 шага, одинаковые args  |
| SagaCompensations | ⭐⭐      | 5+ шагов, разные args      |
| Декларативный     | ⭐⭐⭐    | Сложные зависимости        |
"""

from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from returns.result import Failure, Result, Success
from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from src.Ship.Core.Errors import BaseError
from src.Ship.Infrastructure.Temporal.Saga.Compensations import SagaCompensations
from src.Ship.Infrastructure.Temporal.Saga.Steps import SagaBuilder, SagaStep, execute_saga

# ============================================================================
# Example DTOs (для примеров)
# ============================================================================


class CreateOrderInput(BaseModel):
    """Входные данные для создания заказа."""

    user_id: UUID
    items: list[dict[str, Any]]
    shipping_address: str
    total_amount: str


class OrderResult(BaseModel):
    """Результат создания заказа."""

    order_id: str
    reservation_id: str
    payment_id: str
    delivery_id: str | None = None


class OrderError(BaseError):
    """Ошибка заказа."""

    code: str = "ORDER_ERROR"


# ============================================================================
# Паттерн 1: ПРОСТОЙ LIST (Официальный паттерн Temporal)
# ============================================================================


# Пример Activities (функции с @activity.defn)
@activity.defn
async def create_order_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Создать заказ."""
    # В реальности: await uow.orders.add(order)
    return {"order_id": "ORD-123"}


@activity.defn
async def cancel_order_activity(data: dict[str, Any]) -> None:
    """Компенсация: отменить заказ."""
    # В реальности: await uow.orders.cancel(order_id)
    pass


@activity.defn
async def reserve_inventory_activity(order_id: str) -> dict[str, Any]:
    """Зарезервировать инвентарь."""
    return {"reservation_id": "RES-456"}


@activity.defn
async def cancel_reservation_activity(data: dict[str, Any]) -> None:
    """Компенсация: отменить резервацию."""
    pass


@activity.defn
async def charge_payment_activity(order_id: str) -> dict[str, Any]:
    """Провести оплату."""
    return {"payment_id": "PAY-789"}


@activity.defn
async def refund_payment_activity(data: dict[str, Any]) -> None:
    """Компенсация: вернуть платеж."""
    pass


@activity.defn
async def schedule_delivery_activity(order_id: str) -> dict[str, Any]:
    """Запланировать доставку."""
    return {"delivery_id": "DEL-012"}


# Workflow с простым list
@workflow.defn
class SimpleListPatternWorkflow:
    """Паттерн 1: Простой list компенсаций.

    Официальный паттерн Temporal из документации.
    Минималистичный и идиоматичный для Python.

    Используй когда:
    - 2-4 шага
    - Компенсации не требуют разных аргументов
    - Простая линейная логика

    Ключевые моменты:
    1. compensations.append() ДО выполнения activity
    2. reversed(compensations) — LIFO порядок
    """

    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        compensations: list[Callable[..., Any]] = []

        try:
            # Step 1: Create order
            compensations.append(cancel_order_activity)
            order = await workflow.execute_activity(
                create_order_activity,
                data.model_dump(),
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Step 2: Reserve inventory
            compensations.append(cancel_reservation_activity)
            reservation = await workflow.execute_activity(
                reserve_inventory_activity,
                order["order_id"],
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Step 3: Charge payment
            compensations.append(refund_payment_activity)
            payment = await workflow.execute_activity(
                charge_payment_activity,
                order["order_id"],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            # Step 4: Schedule delivery (no compensation needed)
            delivery = await workflow.execute_activity(
                schedule_delivery_activity,
                order["order_id"],
                start_to_close_timeout=timedelta(seconds=30),
            )

            return Success(
                OrderResult(
                    order_id=order["order_id"],
                    reservation_id=reservation["reservation_id"],
                    payment_id=payment["payment_id"],
                    delivery_id=delivery["delivery_id"],
                )
            )

        except Exception as ex:
            # Компенсации в ОБРАТНОМ порядке (LIFO)
            for compensation in reversed(compensations):
                try:
                    await workflow.execute_activity(
                        compensation,
                        data.model_dump(),
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                except Exception:
                    workflow.logger.exception(f"Compensation {compensation.__name__} failed")

            return Failure(OrderError(message=f"Order creation failed: {ex}"))


# ============================================================================
# Паттерн 2: SagaCompensations КЛАСС (Улучшенный паттерн)
# ============================================================================


# Activities с аргументами
@activity.defn
async def cancel_order_with_id(order_id: str) -> None:
    """Отменить заказ по ID."""
    # В реальности: await uow.orders.cancel(order_id)
    pass


@activity.defn
async def cancel_reservation_with_id(reservation_id: str) -> None:
    """Отменить резервацию по ID."""
    pass


@activity.defn
async def refund_payment_with_args(payment_id: str, amount: str) -> None:
    """Вернуть платеж с суммой."""
    pass


@workflow.defn
class CompensationsClassPatternWorkflow:
    """Паттерн 2: SagaCompensations класс.

    Улучшенный паттерн с поддержкой:
    - Аргументов для каждой компенсации
    - Параллельного выполнения
    - Graceful error handling

    Используй когда:
    - 5+ шагов
    - Компенсации требуют разных аргументов
    - Нужен контроль над порядком выполнения

    Ключевой момент: comp.add() ПОСЛЕ успешного выполнения activity,
    потому что компенсируем конкретный результат!
    """

    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        comp = SagaCompensations()

        try:
            # Step 1: Create order
            order = await workflow.execute_activity(
                create_order_activity,
                data.model_dump(),
                start_to_close_timeout=timedelta(seconds=30),
            )
            comp.add(cancel_order_with_id, order["order_id"])  # С аргументом!

            # Step 2: Reserve inventory
            reservation = await workflow.execute_activity(
                reserve_inventory_activity,
                order["order_id"],
                start_to_close_timeout=timedelta(seconds=30),
            )
            comp.add(cancel_reservation_with_id, reservation["reservation_id"])

            # Step 3: Charge payment
            payment = await workflow.execute_activity(
                charge_payment_activity,
                order["order_id"],
                start_to_close_timeout=timedelta(seconds=60),
            )
            # Несколько аргументов!
            comp.add(refund_payment_with_args, payment["payment_id"], data.total_amount)

            # Step 4: Schedule delivery (no compensation)
            delivery = await workflow.execute_activity(
                schedule_delivery_activity,
                order["order_id"],
                start_to_close_timeout=timedelta(seconds=30),
            )

            return Success(
                OrderResult(
                    order_id=order["order_id"],
                    reservation_id=reservation["reservation_id"],
                    payment_id=payment["payment_id"],
                    delivery_id=delivery["delivery_id"],
                )
            )

        except Exception as ex:
            await comp.run_all()  # Автоматически LIFO
            return Failure(OrderError(message=f"Order creation failed: {ex}"))


# ============================================================================
# Паттерн 3: ДЕКЛАРАТИВНЫЙ (Для сложных workflows)
# ============================================================================


# Activities для декларативного паттерна (принимают dict с результатами)
@activity.defn
async def create_order_declarative(input_data: dict[str, Any]) -> dict[str, Any]:
    """Создать заказ (декларативный)."""
    user_id = input_data.get("user_id")
    return {"id": "ORD-123", "user_id": user_id}


@activity.defn
async def cancel_order_declarative(order_result: dict[str, Any]) -> None:
    """Компенсация заказа (декларативный)."""
    _ = order_result.get("id")  # order_id for cancellation
    # Cancel order by id
    pass


@activity.defn
async def reserve_inventory_declarative(input_data: dict[str, Any]) -> dict[str, Any]:
    """Зарезервировать инвентарь (декларативный)."""
    # Можно получить order_id из предыдущих результатов
    order_id = input_data.get("order", {}).get("id") if "order" in input_data else None
    return {"id": "RES-456", "order_id": order_id}


@activity.defn
async def cancel_reservation_declarative(reservation_result: dict[str, Any]) -> None:
    """Компенсация резервации (декларативный)."""
    pass


@activity.defn
async def charge_payment_declarative(input_data: dict[str, Any]) -> dict[str, Any]:
    """Провести оплату (декларативный)."""
    return {"id": "PAY-789", "amount": "99.99"}


@activity.defn
async def refund_payment_declarative(payment_result: dict[str, Any]) -> None:
    """Компенсация платежа (декларативный)."""
    pass


@activity.defn
async def schedule_delivery_declarative(input_data: dict[str, Any]) -> dict[str, Any]:
    """Запланировать доставку (декларативный)."""
    return {"id": "DEL-012"}


@workflow.defn
class DeclarativePatternWorkflow:
    """Паттерн 3: Декларативный.

    Самый продвинутый паттерн для:
    - Сложных зависимостей между шагами
    - Динамического построения Saga
    - Полной информации о выполнении

    Преимущества:
    - Шаги описаны как данные, легко тестировать
    - Автоматическое управление компенсациями
    - Результаты всех шагов в одном dict
    """

    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        saga_steps = [
            SagaStep(
                name="order",
                action=create_order_declarative,
                compensate=cancel_order_declarative,
                description="Create order record",
            ),
            SagaStep(
                name="reservation",
                action=reserve_inventory_declarative,
                compensate=cancel_reservation_declarative,
                description="Reserve inventory for items",
            ),
            SagaStep(
                name="payment",
                action=charge_payment_declarative,
                compensate=refund_payment_declarative,
                timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=3),
                description="Process payment",
            ),
            SagaStep(
                name="delivery",
                action=schedule_delivery_declarative,
                compensate=None,  # Нет компенсации для доставки
                description="Schedule delivery",
            ),
        ]

        result = await execute_saga(
            saga_steps,
            data.model_dump(),
            pass_all_results=True,  # Передаем все результаты в каждый шаг
        )

        match result:
            case Success(saga_result):
                return Success(
                    OrderResult(
                        order_id=saga_result["order"]["id"],
                        reservation_id=saga_result["reservation"]["id"],
                        payment_id=saga_result["payment"]["id"],
                        delivery_id=saga_result["delivery"]["id"],
                    )
                )
            case Failure(error):
                return Failure(
                    OrderError(
                        message=f"Order failed at {error.failed_step}: {error.cause}",
                        code=error.code,
                    )
                )


@workflow.defn
class DeclarativeWithBuilderWorkflow:
    """Вариант декларативного паттерна с SagaBuilder.

    Более fluent API для создания шагов.
    """

    @workflow.run
    async def run(self, data: CreateOrderInput) -> Result[OrderResult, OrderError]:
        # Fluent builder API
        saga_steps = (
            SagaBuilder()
            .add_step(
                "order",
                create_order_declarative,
                cancel_order_declarative,
                description="Create order record",
            )
            .add_step(
                "reservation",
                reserve_inventory_declarative,
                cancel_reservation_declarative,
                description="Reserve inventory",
            )
            .add_step(
                "payment",
                charge_payment_declarative,
                refund_payment_declarative,
                description="Process payment",
            )
            .with_timeout(60)  # Установить timeout для последнего шага
            .with_retry(maximum_attempts=3)  # И retry
            .add_step("delivery", schedule_delivery_declarative, description="Schedule delivery")
            .build()
        )

        result = await execute_saga(saga_steps, data.model_dump(), pass_all_results=True)

        match result:
            case Success(saga_result):
                return Success(
                    OrderResult(
                        order_id=saga_result["order"]["id"],
                        reservation_id=saga_result["reservation"]["id"],
                        payment_id=saga_result["payment"]["id"],
                        delivery_id=saga_result["delivery"]["id"],
                    )
                )
            case Failure(error):
                return Failure(
                    OrderError(
                        message=f"Order failed: {error.cause}",
                        code=error.code,
                    )
                )


# ============================================================================
# РЕКОМЕНДАЦИИ ПО ВЫБОРУ ПАТТЕРНА
# ============================================================================

"""
1. НАЧНИ С ПРОСТОГО LIST
   - 2-4 шага
   - Компенсации одинаковые (data передается всем)
   - Линейная логика без ветвлений
   
   Пример: Простое бронирование, одношаговый заказ

2. ПЕРЕХОДИ НА SagaCompensations КОГДА
   - Нужно передавать разные аргументы в компенсации
   - Нужен ID ресурса для компенсации (order_id, payment_id)
   - 5+ шагов
   
   Пример: E-commerce checkout с инвентарем и платежами

3. ИСПОЛЬЗУЙ ДЕКЛАРАТИВНЫЙ КОГДА
   - Шаги зависят от результатов предыдущих
   - Динамическое построение Saga (условные шаги)
   - Нужна полная информация о выполнении
   
   Пример: Сложный B2B процесс, multi-step approval

ВАЖНЫЕ ПРАВИЛА TEMPORAL:
1. Регистрируй компенсацию ДО или ПОСЛЕ activity в зависимости от паттерна
2. Компенсации ДОЛЖНЫ быть идемпотентными
3. НЕ устанавливай workflow execution_timeout если нужны компенсации
4. Используй RetryPolicy для transient failures
"""


# Export all example workflows and activities
__all__ = [
    # Pattern 1: Simple list
    "SimpleListPatternWorkflow",
    "create_order_activity",
    "cancel_order_activity",
    "reserve_inventory_activity",
    "cancel_reservation_activity",
    "charge_payment_activity",
    "refund_payment_activity",
    "schedule_delivery_activity",
    # Pattern 2: SagaCompensations
    "CompensationsClassPatternWorkflow",
    "cancel_order_with_id",
    "cancel_reservation_with_id",
    "refund_payment_with_args",
    # Pattern 3: Declarative
    "DeclarativePatternWorkflow",
    "DeclarativeWithBuilderWorkflow",
    "create_order_declarative",
    "cancel_order_declarative",
    "reserve_inventory_declarative",
    "cancel_reservation_declarative",
    "charge_payment_declarative",
    "refund_payment_declarative",
    "schedule_delivery_declarative",
    # DTOs
    "CreateOrderInput",
    "OrderResult",
    "OrderError",
]
