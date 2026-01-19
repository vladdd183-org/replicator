# 🔄 Saga Pattern в Hyper-Porto

> **Версия:** 1.0
> **Дата:** Январь 2026
> **Назначение:** Руководство по реализации распределенных транзакций (Saga) с использованием TaskIQ и Dishka.

---

## 1. Введение: Зачем нужна Saga?

В модульном монолите (и микросервисах) каждый модуль имеет свою базу данных (или изолированные таблицы). Мы не можем сделать `JOIN` или общую транзакцию `BEGIN...COMMIT` между модулями `OrderModule` и `PaymentModule`.

**Проблема:**
1.  Пользователь нажимает "Оформить заказ".
2.  `OrderModule` создает заказ (Status: Pending).
3.  `PaymentModule` списывает деньги.
4.  `DeliveryModule` пытается назначить курьера... **и падает с ошибкой** (нет курьеров).

**Результат без Saga:** Деньги списаны, заказ завис, пользователь зол.

**Решение (Saga):** Механизм, который при ошибке на шаге 3 автоматически запустит "компенсирующие действия" (откат) для шагов 2 и 1.

---

## 2. Архитектура Saga Orchestrator

Мы используем **Orchestration-based Saga**. Это значит, что есть один "дирижер" (Orchestrator), который говорит, что делать.

### Компоненты

1.  **Saga Definition**: Описание шагов и их компенсаций.
2.  **Saga State**: Текущее состояние процесса (сохраняется в БД/Redis).
3.  **Saga Orchestrator (TaskIQ Task)**: Исполнитель, который запускает шаги.

### Стек
*   **TaskIQ**: Запуск шагов и ретраи.
*   **Piccolo/Redis**: Хранение состояния саги.
*   **Dishka**: Внедрение зависимостей в шаги.

---

## 3. Пример реализации: CreateOrderSaga

### 3.1 Определение шагов (Steps)

Каждый шаг — это TaskIQ задача. Но мы оборачиваем их в специальный интерфейс.

```python
# src/Ship/Parents/Saga.py (Абстракция)

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

class SagaStep(ABC, Generic[InputT, OutputT]):
    """Один шаг саги."""
    
    @abstractmethod
    async def execute(self, data: InputT) -> OutputT:
        """Выполнить действие."""
        ...

    @abstractmethod
    async def compensate(self, data: InputT, result: OutputT | None) -> None:
        """Отменить действие (Compensating Transaction)."""
        ...
```

### 3.2 Реализация конкретных шагов

```python
# src/Containers/AppSection/OrderModule/Sagas/Steps/ReserveInventoryStep.py

class ReserveInventoryStep(SagaStep[ReserveDto, str]):
    def __init__(self, inventory_gateway: InventoryGateway):
        self.gateway = inventory_gateway

    async def execute(self, data: ReserveDto) -> str:
        # Вызов другого модуля (возможно, через Gateway)
        reservation_id = await self.gateway.reserve(data.product_id, data.qty)
        return reservation_id

    async def compensate(self, data: ReserveDto, result: str | None) -> None:
        if result:
            await self.gateway.cancel_reservation(result)
```

```python
# src/Containers/AppSection/OrderModule/Sagas/Steps/ChargePaymentStep.py

class ChargePaymentStep(SagaStep[PaymentDto, str]):
    def __init__(self, payment_gateway: PaymentGateway):
        self.gateway = payment_gateway

    async def execute(self, data: PaymentDto) -> str:
        tx_id = await self.gateway.charge(data.amount, data.card_token)
        return tx_id

    async def compensate(self, data: PaymentDto, result: str | None) -> None:
        if result:
            await self.gateway.refund(result)
```

### 3.3 Оркестратор (Дирижер)

Оркестратор — это TaskIQ задача, которая запускает шаги последовательно.

```python
# src/Containers/AppSection/OrderModule/Sagas/CreateOrderSaga.py

@dataclass
class SagaContext:
    order_id: UUID
    # Данные для каждого шага
    inventory_data: ReserveDto
    payment_data: PaymentDto

@broker.task
async def create_order_saga(
    context: SagaContext,
    # DI инъекции шагов
    step_inventory: FromDishka[ReserveInventoryStep],
    step_payment: FromDishka[ChargePaymentStep],
    step_delivery: FromDishka[ScheduleDeliveryStep],
):
    # Храним результаты для компенсации
    results = {}
    
    try:
        # Шаг 1: Инвентарь
        results['inventory'] = await step_inventory.execute(context.inventory_data)
        
        # Шаг 2: Оплата
        results['payment'] = await step_payment.execute(context.payment_data)
        
        # Шаг 3: Доставка
        results['delivery'] = await step_delivery.execute(...)
        
        # Финал: Успех
        await mark_order_completed(context.order_id)

    except Exception as e:
        # ОШИБКА! Запускаем компенсацию в обратном порядке
        log.error(f"Saga failed: {e}. Starting rollback.")
        
        # Откат Шага 2 (если успел выполниться)
        if 'payment' in results:
            await step_payment.compensate(context.payment_data, results['payment'])
            
        # Откат Шага 1 (если успел выполниться)
        if 'inventory' in results:
            await step_inventory.compensate(context.inventory_data, results['inventory'])
            
        # Финал: Провал
        await mark_order_failed(context.order_id, reason=str(e))
```

---

## 4. Как запускать Сагу?

Сага запускается из Action, как обычная фоновая задача.

```python
# src/Containers/AppSection/OrderModule/Actions/CreateOrderAction.py

async def run(self, data: CreateOrderRequest) -> Result[Order, Error]:
    # 1. Создаем заказ в статусе PENDING
    async with self.uow:
        order = Order(status="PENDING", ...)
        await self.uow.orders.add(order)
        await self.uow.commit()

    # 2. Запускаем Сагу (асинхронно)
    context = SagaContext(...)
    await create_order_saga.kiq(context)

    # 3. Возвращаем заказ (клиент видит статус Pending)
    return Success(order)
```

---

## 5. Обработка сбоев самой Саги

Что если упадет сам процесс оркестратора (сервер перезагрузился)?

1.  **TaskIQ Retry:** Обязательно настраиваем ретраи для задачи саги.
2.  **Idempotency:** Все шаги (`execute` и `compensate`) **ДОЛЖНЫ БЫТЬ ИДЕМПОТЕНТНЫМИ**. Если мы попытаемся списать деньги второй раз по тому же `order_id`, платежный шлюз должен вернуть "Уже оплачено" (успех), а не списывать снова.

---

## 6. Чек-лист реализации

1.  [ ] Определить бизнес-процесс и возможные точки отказа.
2.  [ ] Для каждого действия (Write) придумать обратное действие (Compensate).
3.  [ ] Убедиться, что компенсация возможна (например, refund возможен не всегда, тогда нужен manual review).
4.  [ ] Реализовать Steps как отдельные классы.
5.  [ ] Написать TaskIQ task, который связывает шаги.
6.  [ ] Написать тесты, имитирующие падение на каждом шаге и проверяющие откат.


