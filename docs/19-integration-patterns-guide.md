# 🔀 Руководство по выбору паттерна интеграции

> **Версия:** 4.3  
> **Дата:** Январь 2026  
> **Назначение:** Когда использовать Event Bus, Module Gateway, Temporal.io или TaskIQ

---

## 📋 Содержание

1. [Обзор паттернов](#1-обзор-паттернов)
2. [Дерево принятия решений](#2-дерево-принятия-решений)
3. [Unified Event Bus + UoW + Outbox](#3-unified-event-bus--uow--outbox)
4. [Module Gateway](#4-module-gateway)
5. [Temporal.io](#5-temporalio)
6. [TaskIQ](#6-taskiq)
7. [Сравнительная таблица](#7-сравнительная-таблица)
8. [Реальные сценарии](#8-реальные-сценарии)
9. [Anti-patterns](#9-anti-patterns)

---

## 1. Обзор паттернов

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ПАТТЕРНЫ ИНТЕГРАЦИИ В HYPER-PORTO                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │   Event Bus     │    │ Module Gateway  │    │   Temporal.io   │          │
│  │   + Outbox      │    │                 │    │                 │          │
│  │                 │    │                 │    │                 │          │
│  │  Асинхронно     │    │   Синхронно     │    │   Оркестрация   │          │
│  │  Fire-and-forget│    │   Request/Reply │    │   Durable       │          │
│  │  Eventual       │    │   Strong        │    │   Saga          │          │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘          │
│           │                      │                      │                   │
│           ▼                      ▼                      ▼                   │
│  "Сделал и забыл"     "Нужен ответ сейчас"    "Сложный процесс"            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                        TaskIQ                               │            │
│  │                                                             │            │
│  │  Background tasks • Отложенные задачи • Периодические jobs  │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Краткое описание

| Паттерн | Тип связи | Консистентность | Сложность | Когда |
|---------|-----------|-----------------|-----------|-------|
| **Event Bus + Outbox** | Асинхронная | Eventual | ⭐⭐ | "Уведомить других" |
| **Module Gateway** | Синхронная | Strong | ⭐⭐ | "Получить данные" |
| **Temporal.io** | Оркестрация | Eventual + Compensations | ⭐⭐⭐⭐ | "Сложный процесс с откатами" |
| **TaskIQ** | Background | N/A | ⭐ | "Выполнить позже" |

---

## 2. Дерево принятия решений

```
                           ┌─────────────────────────┐
                           │  Нужна интеграция       │
                           │  между модулями?        │
                           └───────────┬─────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
            ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
            │ Нужен ответ   │  │ Уведомить о   │  │ Выполнить     │
            │ СЕЙЧАС?       │  │ событии?      │  │ позже/фоном?  │
            └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
                    │                  │                  │
        ┌───────────┴───────────┐      │                  │
        ▼                       ▼      ▼                  ▼
┌───────────────┐      ┌───────────────────────┐  ┌───────────────┐
│ Module Gateway│      │ Event Bus             │  │ TaskIQ        │
│               │      │                       │  │               │
│ • Чтение данных      │ • Отправка email      │  │ • Периодические│
│ • Валидация   │      │ • Обновление индекса  │  │ • Heavy compute│
│ • Проверка цены      │ • Логирование         │  │ • Отложенные   │
└───────────────┘      └───────────────────────┘  └───────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Критично не потерять│
                    │ событие?            │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                 ▼
      ┌───────────────┐                 ┌───────────────┐
      │ ДА            │                 │ НЕТ           │
      │               │                 │               │
      │ + Outbox      │                 │ Event Bus     │
      │ Pattern       │                 │ (in-memory)   │
      └───────────────┘                 └───────────────┘


                    ┌─────────────────────────────┐
                    │ Нужны несколько шагов       │
                    │ с возможностью ОТКАТА?      │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼                             ▼
            ┌───────────────┐             ┌───────────────┐
            │ ДА            │             │ НЕТ           │
            │               │             │               │
            │ Temporal.io   │             │ Event Bus     │
            │ Saga Pattern  │             │ или TaskIQ    │
            └───────────────┘             └───────────────┘
```

---

## 3. Unified Event Bus + UoW + Outbox

### Когда использовать

✅ **ИСПОЛЬЗУЙ Event Bus когда:**

1. **Нужно уведомить другие модули** о произошедшем событии
2. **Не ждёшь ответа** — "fire and forget"
3. **Eventual consistency** приемлема
4. **Слабая связность** — модули не должны знать друг о друге

❌ **НЕ используй Event Bus когда:**

1. Нужен **немедленный ответ** с данными
2. Нужна **транзакционная консистентность** между модулями
3. **Порядок выполнения** критичен
4. Нужен **откат** при ошибке в другом модуле

### Когда добавлять Outbox

```
┌────────────────────────────────────────────────────────────────┐
│  БЕЗ OUTBOX (in-memory)          │  С OUTBOX (guaranteed)      │
├──────────────────────────────────┼─────────────────────────────┤
│  • Dev/Test окружение            │  • Production               │
│  • Потеря события допустима      │  • Потеря недопустима       │
│  • Один процесс                  │  • Несколько процессов      │
│  • Логирование, статистика       │  • Финансовые операции      │
│                                  │  • Синхронизация данных     │
└──────────────────────────────────┴─────────────────────────────┘
```

### Реальные примеры из Hyper-Porto

#### Пример 1: Регистрация пользователя → Отправка email

```python
# UserModule: Action создаёт пользователя и публикует событие
# EmailModule: Listener получает событие и отправляет письмо

# src/Containers/AppSection/UserModule/Actions/CreateUserAction.py
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        async with self.uow:
            user = AppUser(email=data.email, name=data.name, ...)
            await self.uow.users.add(user)
            
            # 📤 Публикуем событие — НЕ ЖДЁМ ответа
            self.uow.add_event(UserCreated(
                user_id=str(user.id),
                email=user.email,
                name=user.name,
            ))
            
            await self.uow.commit()
        
        return Success(user)


# src/Containers/VendorSection/EmailModule/Listeners.py
@subscribe("UserCreated")
async def on_user_created_send_welcome(
    user_id: str,
    email: str,
    name: str,
    **kwargs,
) -> None:
    """
    ✅ Правильный use case для Event Bus:
    - Асинхронно (не блокирует регистрацию)
    - Не ждём ответа
    - Потеря email не критична (можно переотправить)
    - EmailModule не знает о UserModule
    """
    await send_email(
        to=email,
        template="welcome",
        context={"name": name},
    )
```

#### Пример 2: Создание пользователя → Индексация в поиске

```python
# SearchModule/Listeners.py
@subscribe("UserCreated")
async def on_user_created_index(user_id: str, email: str, name: str, **kwargs):
    """
    ✅ Правильный use case для Event Bus:
    - Асинхронно
    - Eventual consistency (поиск может отставать на секунды)
    - SearchModule не должен блокировать регистрацию
    """
    await index_entity(
        entity_type="User",
        entity_id=user_id,
        content=f"{name} ({email})",
    )


@subscribe("UserUpdated")
async def on_user_updated_reindex(user_id: str, **kwargs):
    await reindex_entity("User", user_id)


@subscribe("UserDeleted")  
async def on_user_deleted_remove_index(user_id: str, **kwargs):
    await remove_from_index("User", user_id)
```

#### Пример 3: С Outbox для критичных событий

```python
# PaymentModule — потеря события недопустима!

# При создании платежа событие сохраняется в outbox_events
# В ТОЙ ЖЕ транзакции что и сам платёж

# Фоновый worker читает outbox и надёжно публикует:
# PaymentCompleted → NotificationModule
# PaymentCompleted → AuditModule  
# PaymentCompleted → AnalyticsModule
```

---

## 4. Module Gateway

### Когда использовать

✅ **ИСПОЛЬЗУЙ Module Gateway когда:**

1. Нужно **получить данные** из другого модуля
2. Нужен **немедленный ответ** для продолжения работы
3. **Синхронный** запрос-ответ
4. **Валидация** или **проверка** перед действием

❌ **НЕ используй Module Gateway когда:**

1. Просто **уведомляешь** о событии
2. **Не ждёшь ответа**
3. Операция **не критична** для текущего action

### Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        OrderModule                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CreateOrderAction                                      │    │
│  │                                                         │    │
│  │  async def run(self, data):                            │    │
│  │      # Нужна цена товара СЕЙЧАС                        │    │
│  │      price = await self.product_gateway.get_price(     │    │
│  │          product_id=data.product_id                    │    │
│  │      )                                                  │    │
│  │      if price is None:                                  │    │
│  │          return Failure(ProductNotFoundError())        │    │
│  │                                                         │    │
│  │      order = Order(product_id=..., price=price, ...)   │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                             │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐    │
│  │  Gateways/ProductGateway.py (Protocol)                  │    │
│  │                                                         │    │
│  │  class ProductGateway(Protocol):                        │    │
│  │      async def get_price(self, product_id: UUID)        │    │
│  │          -> Decimal | None: ...                         │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                             │                                   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │  Adapters (выбор через DI)        │
            │                                   │
    ┌───────▼───────┐               ┌───────────▼───────────┐
    │ Direct        │               │ HTTP                  │
    │ Adapter       │               │ Adapter               │
    │               │               │                       │
    │ Монолит:      │               │ Микросервис:          │
    │ Прямой вызов  │               │ HTTP запрос к         │
    │ ProductQuery  │               │ product-service       │
    └───────────────┘               └───────────────────────┘
```

### Реальные примеры

#### Пример 1: Проверка цены товара при заказе

```python
# src/Containers/AppSection/OrderModule/Gateways/ProductGateway.py
from typing import Protocol
from decimal import Decimal
from uuid import UUID


class ProductGateway(Protocol):
    """Интерфейс для получения данных о товарах.
    
    Используется OrderModule для получения цен и наличия.
    Реализация зависит от deployment:
    - Монолит: DirectProductAdapter (прямой вызов ProductModule)
    - Микросервис: HttpProductAdapter (HTTP к product-service)
    """
    
    async def get_price(self, product_id: UUID) -> Decimal | None:
        """Получить текущую цену товара."""
        ...
    
    async def check_availability(self, product_id: UUID, quantity: int) -> bool:
        """Проверить наличие на складе."""
        ...


# src/Containers/AppSection/OrderModule/Gateways/Adapters/DirectProductAdapter.py
from src.Containers.AppSection.ProductModule.Queries.GetProductQuery import (
    GetProductQuery,
    GetProductInput,
)


class DirectProductAdapter:
    """Адаптер для монолита — прямой вызов ProductModule."""
    
    def __init__(self, get_product_query: GetProductQuery):
        self.query = get_product_query
    
    async def get_price(self, product_id: UUID) -> Decimal | None:
        product = await self.query.execute(GetProductInput(product_id=product_id))
        return product.price if product else None
    
    async def check_availability(self, product_id: UUID, quantity: int) -> bool:
        product = await self.query.execute(GetProductInput(product_id=product_id))
        return product is not None and product.stock >= quantity


# src/Containers/AppSection/OrderModule/Gateways/Adapters/HttpProductAdapter.py
import httpx


class HttpProductAdapter:
    """Адаптер для микросервиса — HTTP вызов к product-service."""
    
    def __init__(self, base_url: str = "http://product-service:8000"):
        self.base_url = base_url
    
    async def get_price(self, product_id: UUID) -> Decimal | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/products/{product_id}")
            if resp.status_code == 404:
                return None
            data = resp.json()
            return Decimal(data["price"])
```

#### Пример 2: Использование в Action

```python
# src/Containers/AppSection/OrderModule/Actions/CreateOrderAction.py

class CreateOrderAction(Action[CreateOrderRequest, Order, OrderError]):
    """
    ✅ Правильный use case для Module Gateway:
    - Нужна цена СЕЙЧАС (синхронно)
    - Без цены нельзя создать заказ
    - Ответ влияет на логику (проверка наличия)
    """
    
    def __init__(
        self,
        product_gateway: ProductGateway,  # DI инъекция
        uow: OrderUnitOfWork,
    ):
        self.product_gateway = product_gateway
        self.uow = uow
    
    async def run(self, data: CreateOrderRequest) -> Result[Order, OrderError]:
        # 1. Синхронный запрос через Gateway
        price = await self.product_gateway.get_price(data.product_id)
        if price is None:
            return Failure(ProductNotFoundError(product_id=data.product_id))
        
        # 2. Проверка наличия
        available = await self.product_gateway.check_availability(
            data.product_id, 
            data.quantity
        )
        if not available:
            return Failure(OutOfStockError(product_id=data.product_id))
        
        # 3. Создаём заказ с актуальной ценой
        async with self.uow:
            order = Order(
                product_id=data.product_id,
                quantity=data.quantity,
                price=price,
                total=price * data.quantity,
                status=OrderStatus.PENDING,
            )
            await self.uow.orders.add(order)
            
            # Событие — асинхронно уведомить других
            self.uow.add_event(OrderCreated(order_id=str(order.id)))
            await self.uow.commit()
        
        return Success(order)
```

#### Пример 3: DI регистрация в Providers

```python
# src/Containers/AppSection/OrderModule/Providers.py
from dishka import Provider, Scope, provide
from src.Ship.Configs.Settings import get_settings


class OrderModuleProvider(Provider):
    scope = Scope.REQUEST
    
    @provide
    def provide_product_gateway(self) -> ProductGateway:
        settings = get_settings()
        
        if settings.deployment_mode == "monolith":
            # Монолит: прямой вызов
            from src.Containers.AppSection.OrderModule.Gateways.Adapters.DirectProductAdapter import (
                DirectProductAdapter,
            )
            return DirectProductAdapter(get_product_query=...)
        else:
            # Микросервис: HTTP
            from src.Containers.AppSection.OrderModule.Gateways.Adapters.HttpProductAdapter import (
                HttpProductAdapter,
            )
            return HttpProductAdapter(base_url=settings.product_service_url)
```

---

## 5. Temporal.io

### Когда использовать

✅ **ИСПОЛЬЗУЙ Temporal когда:**

1. **Несколько шагов записи** в разных модулях/сервисах
2. Нужен **откат (compensation)** при ошибке на любом шаге
3. Процесс **долгоживущий** (минуты, часы, дни, месяцы)
4. Нужна **гарантия выполнения** — процесс ДОЛЖЕН завершиться
5. **Human-in-the-loop** — ожидание действия пользователя
6. **Mission-critical** операции (платежи, заказы)

❌ **НЕ используй Temporal когда:**

1. Простая **отправка уведомления** → Event Bus
2. Простой **background task** → TaskIQ
3. **Один модуль**, нет распределённых операций
4. Не нужен откат при ошибке
5. Команда не готова к learning curve (1+ месяц)

### Архитектура Temporal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TEMPORAL ARCHITECTURE                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     Temporal Server (self-hosted)                   │    │
│  │                                                                     │    │
│  │  • Хранит состояние всех Workflows (Event History)                 │    │
│  │  • Управляет Task Queues                                           │    │
│  │  • Гарантирует выполнение                                          │    │
│  │  • Web UI для мониторинга                                          │    │
│  │                                                                     │    │
│  │  🔒 MIT License — 100% open source, self-hosted                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │                          │                          │             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐        │
│  │  Worker 1   │           │  Worker 2   │           │  Worker N   │        │
│  │             │           │             │           │             │        │
│  │  Workflows  │           │  Activities │           │  Activities │        │
│  │  Activities │           │             │           │             │        │
│  └─────────────┘           └─────────────┘           └─────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Реальные примеры

#### Пример 1: Saga оформления заказа

```
Шаги:
1. Создать заказ (status=PENDING)
2. Зарезервировать товар на складе
3. Списать деньги с карты
4. Назначить курьера

Если шаг 4 упал → отменить шаги 3, 2, 1 (compensations)
```

```python
# src/Containers/AppSection/OrderModule/Workflows/CreateOrderWorkflow.py
from temporalio import workflow
from temporalio.workflow import execute_activity
from datetime import timedelta


@workflow.defn
class CreateOrderWorkflow:
    """
    ✅ Правильный use case для Temporal:
    - 4 шага записи в разных модулях
    - Нужны compensations (откаты)
    - Mission-critical (деньги)
    - Может занять минуты (назначение курьера)
    """
    
    @workflow.run
    async def run(self, order_data: OrderData) -> OrderResult:
        
        # Шаг 1: Создать заказ
        order_id = await workflow.execute_activity(
            create_order_activity,
            order_data,
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        try:
            # Шаг 2: Зарезервировать товар
            reservation_id = await workflow.execute_activity(
                reserve_inventory_activity,
                ReserveInput(
                    product_id=order_data.product_id,
                    quantity=order_data.quantity,
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            try:
                # Шаг 3: Списать деньги
                payment_id = await workflow.execute_activity(
                    charge_payment_activity,
                    PaymentInput(
                        amount=order_data.total,
                        card_token=order_data.card_token,
                    ),
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
                
                try:
                    # Шаг 4: Назначить курьера (может занять время!)
                    delivery_id = await workflow.execute_activity(
                        schedule_delivery_activity,
                        DeliveryInput(
                            order_id=order_id,
                            address=order_data.address,
                        ),
                        start_to_close_timeout=timedelta(minutes=10),
                    )
                    
                    # ✅ Успех — все 4 шага выполнены
                    await workflow.execute_activity(
                        complete_order_activity,
                        order_id,
                    )
                    
                    return OrderResult.success(
                        order_id=order_id,
                        delivery_id=delivery_id,
                    )
                    
                except Exception as e:
                    # ❌ Шаг 4 упал → откат шага 3
                    workflow.logger.error(f"Delivery failed: {e}")
                    await workflow.execute_activity(
                        refund_payment_activity,
                        payment_id,
                    )
                    raise
                    
            except Exception as e:
                # ❌ Шаг 3 или 4 упал → откат шага 2
                workflow.logger.error(f"Payment/Delivery failed: {e}")
                await workflow.execute_activity(
                    cancel_reservation_activity,
                    reservation_id,
                )
                raise
                
        except Exception as e:
            # ❌ Любой шаг упал → отменить заказ
            workflow.logger.error(f"Order failed: {e}")
            await workflow.execute_activity(
                cancel_order_activity,
                order_id,
            )
            
            return OrderResult.failed(
                order_id=order_id,
                reason=str(e),
            )
```

#### Пример 2: Human-in-the-loop (подтверждение)

```python
@workflow.defn
class ApprovalWorkflow:
    """
    ✅ Правильный use case для Temporal:
    - Ожидание действия пользователя (часы/дни)
    - Таймаут с эскалацией
    - Гарантия что процесс не потеряется
    """
    
    def __init__(self):
        self.approved: bool | None = None
    
    @workflow.signal
    async def approve(self, approved: bool):
        """Signal от UI/API когда пользователь нажал кнопку."""
        self.approved = approved
    
    @workflow.run
    async def run(self, request: ApprovalRequest) -> ApprovalResult:
        # Отправить уведомление approver'у
        await workflow.execute_activity(
            send_approval_request_activity,
            request,
        )
        
        # Ждём Signal (до 7 дней!)
        try:
            await workflow.wait_condition(
                lambda: self.approved is not None,
                timeout=timedelta(days=7),
            )
        except asyncio.TimeoutError:
            # Эскалация если не ответили
            await workflow.execute_activity(
                escalate_to_manager_activity,
                request,
            )
            return ApprovalResult.escalated()
        
        if self.approved:
            await workflow.execute_activity(
                process_approved_request_activity,
                request,
            )
            return ApprovalResult.approved()
        else:
            await workflow.execute_activity(
                process_rejected_request_activity,
                request,
            )
            return ApprovalResult.rejected()
```

#### Пример 3: Запуск Workflow из Action

```python
# src/Containers/AppSection/OrderModule/Actions/CreateOrderAction.py
from temporalio.client import Client

class CreateOrderAction(Action[CreateOrderRequest, Order, OrderError]):
    def __init__(self, temporal_client: Client, uow: OrderUnitOfWork):
        self.temporal = temporal_client
        self.uow = uow
    
    async def run(self, data: CreateOrderRequest) -> Result[Order, OrderError]:
        # 1. Валидация (синхронно)
        if not data.items:
            return Failure(EmptyOrderError())
        
        # 2. Создаём заказ в PENDING
        async with self.uow:
            order = Order(status=OrderStatus.PENDING, ...)
            await self.uow.orders.add(order)
            await self.uow.commit()
        
        # 3. Запускаем Workflow (асинхронно)
        #    Temporal гарантирует выполнение!
        await self.temporal.start_workflow(
            CreateOrderWorkflow.run,
            OrderData.from_request(data, order_id=order.id),
            id=f"create-order-{order.id}",
            task_queue="orders",
        )
        
        # 4. Возвращаем заказ (статус PENDING)
        #    Клиент увидит обновления через WebSocket/polling
        return Success(order)
```

---

## 6. TaskIQ

### Когда использовать

✅ **ИСПОЛЬЗУЙ TaskIQ когда:**

1. **Background task** — выполнить вне HTTP запроса
2. **Отложенное выполнение** — через N минут/часов
3. **Периодические задачи** — cron-style
4. **Heavy computation** — не блокировать web worker
5. **Простые retry** — без сложной логики откатов

❌ **НЕ используй TaskIQ когда:**

1. Нужен **откат (compensation)** → Temporal
2. Нужна **оркестрация** нескольких шагов → Temporal  
3. Просто **уведомление** между модулями → Event Bus
4. Нужен **синхронный ответ** → Module Gateway

### Реальные примеры

#### Пример 1: Отложенная отправка email

```python
# src/Containers/VendorSection/EmailModule/UI/Workers/Tasks.py
from taskiq import TaskiqDecoratedTask
from src.Ship.Infrastructure.Workers.Broker import broker


@broker.task
async def send_email_task(
    to: str,
    subject: str,
    template: str,
    context: dict,
) -> None:
    """
    ✅ Правильный use case для TaskIQ:
    - Простой background task
    - Не блокирует HTTP ответ
    - Встроенные retry достаточны
    """
    await email_service.send(to=to, subject=subject, ...)


@broker.task
async def send_scheduled_reminder(user_id: str) -> None:
    """Напоминание через 24 часа после регистрации."""
    user = await user_repo.get(user_id)
    if user and user.is_active:
        await send_email_task.kiq(
            to=user.email,
            template="reminder_24h",
            ...
        )


# Использование
await send_email_task.kiq(to="user@example.com", ...)

# Отложенное выполнение
await send_scheduled_reminder.kicker().with_delay(hours=24).kiq(user_id="123")
```

#### Пример 2: Периодические задачи

```python
# src/Ship/Infrastructure/Workers/Scheduler.py
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource


scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


@broker.task(schedule=[{"cron": "0 * * * *"}])  # Каждый час
async def cleanup_expired_sessions() -> None:
    """
    ✅ Правильный use case для TaskIQ:
    - Периодическая задача
    - Простая логика (нет orchestration)
    """
    await session_repo.delete_expired()


@broker.task(schedule=[{"cron": "0 0 * * *"}])  # Каждый день в полночь
async def generate_daily_report() -> None:
    """Генерация ежедневного отчёта."""
    report = await analytics_service.generate_daily()
    await report_repo.save(report)
```

#### Пример 3: Heavy computation

```python
@broker.task(timeout=600)  # 10 минут
async def process_large_file(file_id: str) -> ProcessingResult:
    """
    ✅ Правильный use case для TaskIQ:
    - Heavy computation (не блокирует web)
    - Длительное выполнение
    - Простые retry
    """
    file = await file_storage.get(file_id)
    
    # CPU-intensive обработка
    result = await anyio.to_thread.run_sync(
        process_file_sync,
        file.content,
    )
    
    await file_storage.save_result(file_id, result)
    return result


# Запуск из Controller
@post("/files/{file_id}/process")
async def start_processing(file_id: UUID) -> Response:
    # Запускаем в background, сразу отвечаем клиенту
    task = await process_large_file.kiq(str(file_id))
    
    return Response(
        content={"task_id": task.task_id, "status": "processing"},
        status_code=202,  # Accepted
    )
```

---

## 7. Сравнительная таблица

### По типу задачи

| Задача | Event Bus | Gateway | Temporal | TaskIQ |
|--------|-----------|---------|----------|--------|
| Уведомить о событии | ✅ | ❌ | ❌ | ❌ |
| Получить данные синхронно | ❌ | ✅ | ❌ | ❌ |
| Background task | ❌ | ❌ | ⚠️ overkill | ✅ |
| Периодическая задача | ❌ | ❌ | ⚠️ overkill | ✅ |
| Отложенное выполнение | ❌ | ❌ | ✅ | ✅ |
| Saga с откатами | ❌ | ❌ | ✅ | ❌ |
| Long-running (дни/недели) | ❌ | ❌ | ✅ | ❌ |
| Human-in-the-loop | ❌ | ❌ | ✅ | ❌ |

### По характеристикам

| Характеристика | Event Bus | Gateway | Temporal | TaskIQ |
|----------------|-----------|---------|----------|--------|
| **Связность** | Слабая | Средняя | Средняя | Слабая |
| **Консистентность** | Eventual | Strong | Eventual + Comp | N/A |
| **Сложность** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| **Learning curve** | Низкая | Низкая | Высокая | Низкая |
| **Self-hosted** | ✅ | ✅ | ✅ (MIT) | ✅ |

### По операциям

| Операция | Event Bus | Gateway | Temporal | TaskIQ |
|----------|-----------|---------|----------|--------|
| **Read** | ❌ | ✅ | ❌ | ❌ |
| **Write (один модуль)** | ✅ notify | ❌ | ⚠️ overkill | ✅ |
| **Write (несколько модулей)** | ❌ no rollback | ❌ | ✅ | ❌ |

---

## 8. Реальные сценарии

### Сценарий 1: Регистрация пользователя

```
Шаги:
1. Создать пользователя в БД
2. Отправить welcome email
3. Проиндексировать в поиске
4. Записать в аудит лог
```

**Решение: Event Bus**

```python
# CreateUserAction
async with self.uow:
    user = AppUser(...)
    await self.uow.users.add(user)
    
    # Один Event → множество listeners
    self.uow.add_event(UserCreated(user_id=str(user.id), email=user.email))
    await self.uow.commit()

# Listeners (разные модули)
@subscribe("UserCreated") → send_welcome_email
@subscribe("UserCreated") → index_in_search
@subscribe("UserCreated") → write_audit_log
```

**Почему Event Bus:**
- Шаги 2-4 НЕ влияют на успех регистрации
- Eventual consistency приемлема
- Не нужны откаты

---

### Сценарий 2: Создание заказа с проверкой цены

```
Шаги:
1. Получить текущую цену товара
2. Проверить наличие на складе
3. Создать заказ
```

**Решение: Gateway + Event Bus**

```python
# CreateOrderAction
price = await self.product_gateway.get_price(product_id)  # Gateway
if price is None:
    return Failure(ProductNotFoundError())

available = await self.product_gateway.check_availability(product_id, qty)  # Gateway
if not available:
    return Failure(OutOfStockError())

async with self.uow:
    order = Order(price=price, ...)
    await self.uow.orders.add(order)
    self.uow.add_event(OrderCreated(...))  # Event Bus
    await self.uow.commit()
```

**Почему Gateway:**
- Цена нужна СЕЙЧАС (синхронно)
- Без цены нельзя создать заказ

**Почему Event Bus:**
- Уведомить о созданном заказе (асинхронно)

---

### Сценарий 3: Оформление заказа с оплатой и доставкой

```
Шаги:
1. Создать заказ
2. Зарезервировать товар
3. Списать деньги
4. Назначить курьера

При ошибке на любом шаге → откатить предыдущие
```

**Решение: Temporal**

```python
@workflow.defn
class CreateOrderWorkflow:
    @workflow.run
    async def run(self, data):
        order_id = await execute_activity(create_order, ...)
        try:
            reservation_id = await execute_activity(reserve_inventory, ...)
            try:
                payment_id = await execute_activity(charge_payment, ...)
                try:
                    delivery_id = await execute_activity(schedule_delivery, ...)
                    return Success(...)
                except:
                    await execute_activity(refund_payment, payment_id)
                    raise
            except:
                await execute_activity(cancel_reservation, reservation_id)
                raise
        except:
            await execute_activity(cancel_order, order_id)
            return Failed(...)
```

**Почему Temporal:**
- 4 шага ЗАПИСИ в разных сервисах
- Нужны compensations (откаты)
- Mission-critical (деньги)
- Может занять минуты (назначение курьера)

---

### Сценарий 4: Ежечасная очистка сессий

```
Каждый час удалять истёкшие сессии из БД
```

**Решение: TaskIQ**

```python
@broker.task(schedule=[{"cron": "0 * * * *"}])
async def cleanup_expired_sessions():
    await session_repo.delete_expired()
```

**Почему TaskIQ:**
- Простая периодическая задача
- Нет orchestration
- Нет откатов
- Не mission-critical

---

### Сценарий 5: Обработка большого файла

```
Пользователь загрузил файл → нужно обработать (занимает 5 минут)
```

**Решение: TaskIQ**

```python
@post("/files")
async def upload_file(file: UploadFile):
    file_id = await storage.save(file)
    
    # Запустить обработку в background
    await process_file_task.kiq(file_id)
    
    return {"file_id": file_id, "status": "processing"}


@broker.task(timeout=600)
async def process_file_task(file_id: str):
    # Heavy processing
    ...
```

**Почему TaskIQ:**
- Не блокировать HTTP ответ
- Простой background task
- Встроенные retry достаточны

---

### Сценарий 6: Подтверждение платежа вручную

```
1. Создать запрос на платёж
2. Отправить уведомление финансисту
3. Ждать подтверждения (до 3 дней)
4. Если не подтвердили → эскалация
5. После подтверждения → выполнить платёж
```

**Решение: Temporal**

```python
@workflow.defn
class PaymentApprovalWorkflow:
    def __init__(self):
        self.approved = None
    
    @workflow.signal
    async def approve(self, approved: bool):
        self.approved = approved
    
    @workflow.run
    async def run(self, request):
        await execute_activity(send_approval_notification, request)
        
        try:
            await workflow.wait_condition(
                lambda: self.approved is not None,
                timeout=timedelta(days=3),
            )
        except TimeoutError:
            await execute_activity(escalate_to_cfo, request)
            return Escalated()
        
        if self.approved:
            await execute_activity(execute_payment, request)
            return Approved()
        else:
            return Rejected()
```

**Почему Temporal:**
- Human-in-the-loop (ожидание решения)
- Long-running (дни)
- Гарантия что процесс не потеряется
- Таймаут с эскалацией

---

## 9. Anti-patterns

### ❌ Event Bus для синхронных зависимостей

```python
# ❌ ПЛОХО — нужен ответ, но используется Event
async def create_order(self, data):
    self.uow.add_event(GetPriceRequested(product_id=data.product_id))
    await self.uow.commit()
    
    # Как получить цену? Событие асинхронное!
    price = ???  # НЕ РАБОТАЕТ
```

```python
# ✅ ХОРОШО — Gateway для синхронных данных
async def create_order(self, data):
    price = await self.product_gateway.get_price(data.product_id)
    order = Order(price=price, ...)
```

---

### ❌ TaskIQ для Saga с откатами

```python
# ❌ ПЛОХО — ручной rollback в TaskIQ
@broker.task
async def create_order_saga(data):
    order_id = await create_order(data)
    try:
        payment_id = await charge_payment(data)
    except:
        await cancel_order(order_id)  # А если этот вызов упадёт?
        raise
```

```python
# ✅ ХОРОШО — Temporal с гарантированными compensations
@workflow.defn
class CreateOrderWorkflow:
    # Temporal гарантирует выполнение compensations
```

---

### ❌ Temporal для простых background tasks

```python
# ❌ ПЛОХО — overkill для простой задачи
@workflow.defn
class SendEmailWorkflow:
    @workflow.run
    async def run(self, email_data):
        await execute_activity(send_email, email_data)

# Это workflow из одного activity без compensations!
```

```python
# ✅ ХОРОШО — TaskIQ для простых задач
@broker.task
async def send_email_task(email_data):
    await send_email(email_data)
```

---

### ❌ Module Gateway для уведомлений

```python
# ❌ ПЛОХО — блокируем регистрацию ради email
async def create_user(self, data):
    user = await create_user_in_db(data)
    await self.email_gateway.send_welcome(user.email)  # Блокирует!
    return user
```

```python
# ✅ ХОРОШО — Event Bus для уведомлений
async def create_user(self, data):
    async with self.uow:
        user = AppUser(...)
        await self.uow.users.add(user)
        self.uow.add_event(UserCreated(...))  # Асинхронно
        await self.uow.commit()
    return user
```

---

## 📚 Связанные документы

- [17-unified-event-bus.md](17-unified-event-bus.md) — Детальная реализация Event Bus
- [14-module-gateway-pattern.md](14-module-gateway-pattern.md) — Детальная реализация Gateway
- [15-saga-patterns.md](15-saga-patterns.md) — Saga Patterns (Temporal + TaskIQ)

---

<div align="center">

**Hyper-Porto v4.3**

*Правильный паттерн для правильной задачи*

🔌 Event Bus → 🚪 Gateway → ⏰ Temporal → 📋 TaskIQ

</div>

