# 03. Data Patterns

> **Управление данными в распределённой системе**

---

## Проблема данных в микросервисах

В монолите всё просто: одна БД, одна транзакция, JOIN любых таблиц.

В микросервисах:
- Данные разбросаны по разным БД
- Нет единой транзакции
- JOIN невозможен
- Консистентность под вопросом

Data Patterns решают эти проблемы.

---

## Паттерн 1: CQRS (Command Query Responsibility Segregation)

### 💡 Суть

**Разделить операции чтения и записи** на разные модели (и даже разные БД).

### 📝 Техническое объяснение

- **Command** — изменяет состояние (CREATE, UPDATE, DELETE)
- **Query** — только читает (SELECT)

В классической архитектуре одна модель для всего. В CQRS:
- **Write Model** — оптимизирована для записи, нормализованная
- **Read Model** — оптимизирована для чтения, денормализованная

### 🏠 Аналогия: Библиотека

В библиотеке есть:
- **Архив** (Write Model) — все книги хранятся по правилам каталогизации, строго по полкам
- **Каталог** (Read Model) — карточки с информацией, удобные для поиска

Когда приходит новая книга:
1. Её ставят в архив (write)
2. Создают карточку в каталоге (read model)

Читатель ищет по каталогу (быстро), а не бегает по архиву.

### ✅ Когда использовать

- Чтение >> записи (90% read, 10% write)
- Сложные запросы на чтение
- Разные требования к масштабированию read/write
- Нужны разные представления одних данных

### ❌ Когда НЕ использовать

- Простой CRUD без сложных запросов
- Нужна мгновенная консистентность (read your writes)
- Маленькая система без нагрузки

### 🔧 Пример реализации

```python
# ═══════════════════════════════════════════════════════════════
# WRITE SIDE (Commands)
# ═══════════════════════════════════════════════════════════════

class CreateOrderCommand(BaseModel):
    """Команда на создание заказа."""
    user_id: UUID
    items: list[OrderItemDTO]
    shipping_address: str


class CreateOrderAction(Action[CreateOrderCommand, Order, OrderError]):
    """Обработчик команды — изменяет состояние."""
    
    async def run(self, cmd: CreateOrderCommand) -> Result[Order, OrderError]:
        async with self.uow:
            order = Order(
                user_id=cmd.user_id,
                status=OrderStatus.PENDING,
                items=cmd.items,
            )
            await self.uow.orders.add(order)
            
            # Публикуем событие для обновления Read Model
            self.uow.add_event(OrderCreated(
                order_id=order.id,
                user_id=order.user_id,
                total=order.total,
            ))
            
            await self.uow.commit()
        
        return Success(order)


# ═══════════════════════════════════════════════════════════════
# READ SIDE (Queries)
# ═══════════════════════════════════════════════════════════════

class GetOrdersForDashboardQuery(Query[DashboardQueryInput, DashboardData]):
    """Запрос для дашборда — только читает, оптимизирован."""
    
    async def execute(self, input: DashboardQueryInput) -> DashboardData:
        # Читаем из денормализованной Read Model
        # Никакой бизнес-логики, просто SELECT
        return await self.read_db.fetch_dashboard(input.user_id)


# ═══════════════════════════════════════════════════════════════
# SYNC: Write → Read Model
# ═══════════════════════════════════════════════════════════════

@subscribe("OrderCreated")
async def update_dashboard_read_model(order_id: str, user_id: str, total: float, **kwargs):
    """Обновляем Read Model после записи."""
    await dashboard_read_model.update_user_stats(
        user_id=user_id,
        increment_orders=1,
        increment_total=total,
    )
```

### Архитектура CQRS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CQRS ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              ┌───────────┐                                  │
│                              │  Client   │                                  │
│                              └─────┬─────┘                                  │
│                                    │                                        │
│                    ┌───────────────┴───────────────┐                       │
│                    │                               │                        │
│                    ▼                               ▼                        │
│           ┌────────────────┐             ┌────────────────┐                │
│           │   Commands     │             │    Queries     │                │
│           │   (Write)      │             │    (Read)      │                │
│           └────────┬───────┘             └────────┬───────┘                │
│                    │                               │                        │
│                    ▼                               ▼                        │
│           ┌────────────────┐             ┌────────────────┐                │
│           │  Write Model   │             │   Read Model   │                │
│           │                │             │                │                │
│           │  • Actions     │   Events    │  • Queries     │                │
│           │  • Domain      │ ──────────► │  • Views       │                │
│           │  • Validation  │             │  • Projections │                │
│           └────────┬───────┘             └────────┬───────┘                │
│                    │                               │                        │
│                    ▼                               ▼                        │
│           ┌────────────────┐             ┌────────────────┐                │
│           │  PostgreSQL    │             │  Elasticsearch │                │
│           │  (normalized)  │             │  (denormalized)│                │
│           └────────────────┘             └────────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 2: Event Sourcing

### 💡 Суть

Хранить **не текущее состояние**, а **историю всех событий**, которые к нему привели.

### 📝 Техническое объяснение

Вместо:
```sql
UPDATE accounts SET balance = 150 WHERE id = 1
```

Храним:
```sql
INSERT INTO events (type, data) VALUES 
  ('AccountOpened', {account_id: 1, initial: 100}),
  ('MoneyDeposited', {account_id: 1, amount: 50})
```

Текущее состояние = replay всех событий.

### 🏠 Аналогия: Бухгалтерская книга

Бухгалтер не стирает старые записи и не пишет "баланс = 1 000 000 ₽".

Он ведёт **журнал операций**:
- 01.01: Получено от клиента А: +50 000 ₽
- 02.01: Оплата поставщику: -30 000 ₽
- 03.01: Получено от клиента Б: +20 000 ₽

Баланс = сумма всех операций. Можно проверить любую цифру, найти ошибку, увидеть историю.

Event Sourcing = бухгалтерская книга для данных.

### ✅ Когда использовать

- Нужен полный audit trail (финансы, медицина, юриспруденция)
- Важна история изменений
- Нужен "replay" для отладки или восстановления
- Сложная бизнес-логика с временными зависимостями

### ❌ Когда НЕ использовать

- Простой CRUD
- Не нужна история
- Большой объём событий → сложность
- Команда не готова к paradigm shift

### 🔧 Пример реализации

```python
# ═══════════════════════════════════════════════════════════════
# EVENTS (источник истины)
# ═══════════════════════════════════════════════════════════════

class AccountEvent(BaseModel):
    """Базовое событие счёта."""
    event_id: UUID = Field(default_factory=uuid4)
    account_id: UUID
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AccountOpened(AccountEvent):
    """Счёт открыт."""
    owner_name: str
    initial_balance: Decimal


class MoneyDeposited(AccountEvent):
    """Деньги внесены."""
    amount: Decimal
    description: str


class MoneyWithdrawn(AccountEvent):
    """Деньги сняты."""
    amount: Decimal
    description: str


# ═══════════════════════════════════════════════════════════════
# AGGREGATE (восстанавливается из событий)
# ═══════════════════════════════════════════════════════════════

@dataclass
class Account:
    """Агрегат счёта — состояние вычисляется из событий."""
    
    id: UUID
    owner_name: str
    balance: Decimal
    is_closed: bool = False
    
    @classmethod
    def from_events(cls, events: list[AccountEvent]) -> "Account":
        """Восстановить состояние из истории событий."""
        account = None
        
        for event in events:
            match event:
                case AccountOpened():
                    account = cls(
                        id=event.account_id,
                        owner_name=event.owner_name,
                        balance=event.initial_balance,
                    )
                case MoneyDeposited():
                    account.balance += event.amount
                case MoneyWithdrawn():
                    account.balance -= event.amount
        
        return account
    
    def deposit(self, amount: Decimal, description: str) -> MoneyDeposited:
        """Внести деньги — возвращает событие."""
        if self.is_closed:
            raise AccountClosedError()
        
        return MoneyDeposited(
            account_id=self.id,
            amount=amount,
            description=description,
        )
    
    def withdraw(self, amount: Decimal, description: str) -> MoneyWithdrawn:
        """Снять деньги — возвращает событие."""
        if self.balance < amount:
            raise InsufficientFundsError()
        
        return MoneyWithdrawn(
            account_id=self.id,
            amount=amount,
            description=description,
        )


# ═══════════════════════════════════════════════════════════════
# EVENT STORE (хранилище событий)
# ═══════════════════════════════════════════════════════════════

class EventStore:
    """Хранилище событий."""
    
    async def append(self, event: AccountEvent) -> None:
        """Добавить событие в store."""
        await self.db.execute(
            "INSERT INTO account_events (event_id, account_id, event_type, data, occurred_at) "
            "VALUES ($1, $2, $3, $4, $5)",
            event.event_id,
            event.account_id,
            type(event).__name__,
            event.model_dump_json(),
            event.occurred_at,
        )
    
    async def get_events(self, account_id: UUID) -> list[AccountEvent]:
        """Получить все события счёта."""
        rows = await self.db.fetch_all(
            "SELECT event_type, data FROM account_events "
            "WHERE account_id = $1 ORDER BY occurred_at",
            account_id,
        )
        return [self._deserialize(row) for row in rows]


# ═══════════════════════════════════════════════════════════════
# ИСПОЛЬЗОВАНИЕ
# ═══════════════════════════════════════════════════════════════

async def transfer_money(from_id: UUID, to_id: UUID, amount: Decimal):
    # 1. Загружаем историю и восстанавливаем состояние
    from_events = await event_store.get_events(from_id)
    from_account = Account.from_events(from_events)
    
    to_events = await event_store.get_events(to_id)
    to_account = Account.from_events(to_events)
    
    # 2. Выполняем операции — получаем новые события
    withdraw_event = from_account.withdraw(amount, f"Transfer to {to_id}")
    deposit_event = to_account.deposit(amount, f"Transfer from {from_id}")
    
    # 3. Сохраняем события (источник истины)
    await event_store.append(withdraw_event)
    await event_store.append(deposit_event)
```

### Event Sourcing + CQRS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVENT SOURCING + CQRS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Command ──► Aggregate ──► Event ──► Event Store                          │
│                                            │                                │
│                                            │ (append-only)                  │
│                                            ▼                                │
│                                    ┌──────────────┐                        │
│                                    │ Event Store  │                        │
│                                    │              │                        │
│                                    │ AccountOpen  │                        │
│                                    │ Deposited    │                        │
│                                    │ Withdrawn    │                        │
│                                    │ Deposited    │                        │
│                                    └──────┬───────┘                        │
│                                           │                                 │
│                          ┌────────────────┼────────────────┐               │
│                          │                │                │                │
│                          ▼                ▼                ▼                │
│                   ┌────────────┐   ┌────────────┐   ┌────────────┐        │
│                   │ Projection │   │ Projection │   │ Projection │        │
│                   │ "Balance"  │   │ "History"  │   │ "Reports"  │        │
│                   └────────────┘   └────────────┘   └────────────┘        │
│                          │                │                │                │
│                          ▼                ▼                ▼                │
│                   ┌────────────┐   ┌────────────┐   ┌────────────┐        │
│                   │  balance   │   │  history   │   │  monthly   │        │
│                   │  = 150.00  │   │  table     │   │  reports   │        │
│                   └────────────┘   └────────────┘   └────────────┘        │
│                                                                             │
│   Query: "Какой баланс?" ──► Read Model (balance) ──► 150.00               │
│   Query: "История?" ──► Read Model (history) ──► [events...]               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 3: Transactional Outbox

### 💡 Суть

Записывать события в **ту же транзакцию**, что и бизнес-данные, чтобы гарантировать доставку.

### 📝 Техническое объяснение

**Проблема Dual Write:**
```python
async with db.transaction():
    await db.insert(order)  # 1. Сохранили в БД ✅

await message_broker.publish(OrderCreated)  # 2. Отправили событие
# ❌ Если упало между 1 и 2 — событие потеряно!
```

**Решение Outbox:**
```python
async with db.transaction():
    await db.insert(order)           # 1. Сохранили заказ
    await db.insert(outbox_event)    # 2. Сохранили событие в ту же БД
# Оба в одной транзакции — атомарно!

# Отдельный worker читает outbox и публикует
```

### 🏠 Аналогия: Почтовый ящик в офисе

Вы написали важное письмо (событие). Два способа отправить:

**Без Outbox:**
1. Положили на стол
2. Пошли на почту
3. По дороге потеряли 💀

**С Outbox:**
1. Положили в запертый ящик "Исходящие" в офисе (в той же комнате где работаете)
2. Курьер забирает из ящика и везёт на почту

Даже если курьер заболел — письмо в ящике, его заберёт другой курьер.

### ✅ Когда использовать

- Критичные события (платежи, заказы)
- Distributed система с брокером
- Нужна гарантия "at-least-once" delivery

### ❌ Когда НЕ использовать

- In-memory events в монолите
- События не критичны (логирование)
- Можем позволить потерю

### 🔧 Пример реализации

```python
# ═══════════════════════════════════════════════════════════════
# OUTBOX TABLE
# ═══════════════════════════════════════════════════════════════

class OutboxEvent(Table):
    """Таблица исходящих событий."""
    
    id = UUID(primary_key=True, default=uuid4)
    event_name = Varchar(index=True)
    payload = JSONB()
    created_at = Timestamptz(default=TimestamptzNow())
    published = Boolean(default=False, index=True)
    published_at = Timestamptz(null=True)


# ═══════════════════════════════════════════════════════════════
# WRITE: Бизнес-данные + Event в одной транзакции
# ═══════════════════════════════════════════════════════════════

class CreateOrderAction(Action):
    async def run(self, data: CreateOrderRequest) -> Result[Order, OrderError]:
        async with self.uow:
            # 1. Создаём заказ
            order = Order(user_id=data.user_id, items=data.items)
            await self.uow.orders.add(order)
            
            # 2. Записываем событие в OUTBOX (та же транзакция!)
            await self.uow.outbox.add(OutboxEvent(
                event_name="OrderCreated",
                payload={
                    "order_id": str(order.id),
                    "user_id": str(order.user_id),
                    "total": str(order.total),
                },
            ))
            
            # 3. COMMIT — оба атомарно
            await self.uow.commit()
        
        return Success(order)


# ═══════════════════════════════════════════════════════════════
# WORKER: Читает outbox и публикует в брокер
# ═══════════════════════════════════════════════════════════════

async def outbox_publisher():
    """Фоновый процесс публикации событий."""
    while True:
        # Читаем неопубликованные события
        events = await OutboxEvent.select().where(
            OutboxEvent.published == False
        ).limit(100)
        
        for event in events:
            try:
                # Публикуем в брокер
                await message_broker.publish(
                    topic=f"events.{event.event_name}",
                    message=event.payload,
                )
                
                # Помечаем как опубликованное
                await OutboxEvent.update({
                    OutboxEvent.published: True,
                    OutboxEvent.published_at: datetime.now(timezone.utc),
                }).where(OutboxEvent.id == event.id)
                
            except Exception as e:
                logger.error(f"Failed to publish {event.id}: {e}")
                # Событие останется в outbox, попробуем снова
        
        await asyncio.sleep(1)  # Polling interval
```

### Архитектура Outbox

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TRANSACTIONAL OUTBOX                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────┐          │
│   │                    ОДНА ТРАНЗАКЦИЯ                           │          │
│   │                                                              │          │
│   │   ┌──────────────┐        ┌──────────────┐                  │          │
│   │   │   orders     │        │   outbox     │                  │          │
│   │   │              │        │              │                  │          │
│   │   │  INSERT      │        │  INSERT      │                  │          │
│   │   │  order       │        │  event       │                  │          │
│   │   └──────────────┘        └──────────────┘                  │          │
│   │                                                              │          │
│   │                         COMMIT                               │          │
│   └─────────────────────────────────────────────────────────────┘          │
│                                    │                                        │
│                                    │ Атомарно: или оба, или ничего         │
│                                    ▼                                        │
│                           ┌──────────────┐                                 │
│                           │   Database   │                                 │
│                           │              │                                 │
│                           │ orders: [x]  │                                 │
│                           │ outbox: [e]  │                                 │
│                           └──────┬───────┘                                 │
│                                  │                                          │
│                           Outbox Worker                                     │
│                           (polling)                                         │
│                                  │                                          │
│                                  ▼                                          │
│                           ┌──────────────┐                                 │
│                           │   Message    │                                 │
│                           │   Broker     │                                 │
│                           │              │                                 │
│                           │ Redis/Kafka  │                                 │
│                           └──────────────┘                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 4: Saga

### 💡 Суть

Управлять **распределённой транзакцией** через последовательность локальных транзакций с **компенсациями** при ошибке.

### 📝 Техническое объяснение

В микросервисах нет единой транзакции. Saga заменяет её:
- Каждый шаг — локальная транзакция в своём сервисе
- При ошибке — запуск **компенсирующих действий** в обратном порядке

### 🏠 Аналогия: Бронирование путешествия

Вы планируете отпуск:
1. Забронировали авиабилет ✅
2. Забронировали отель ✅
3. Арендовали машину ❌ — нет свободных!

Что делать? **Отменить предыдущие бронирования**:
- Отменить отель (compensation)
- Отменить авиабилет (compensation)

Saga = координатор, который знает что делать при ошибке на каждом шаге.

### ✅ Когда использовать

- Бизнес-операция затрагивает несколько сервисов
- Нужна "виртуальная транзакция" без ACID
- Операция должна быть либо выполнена полностью, либо откачена

### ❌ Когда НЕ использовать

- Один сервис (обычная транзакция)
- Не нужен откат при ошибке
- Compensation невозможна (email уже отправлен)

### Два типа Saga

| Тип | Координация | Когда |
|-----|-------------|-------|
| **Orchestration** | Центральный оркестратор управляет | Сложные, много шагов |
| **Choreography** | Каждый сервис слушает события и реагирует | Простые, 2-3 шага |

### 🔧 Пример: Orchestration Saga (Temporal)

```python
from temporalio import workflow

@workflow.defn
class CreateOrderSaga:
    """Saga оформления заказа с компенсациями."""
    
    @workflow.run
    async def run(self, order_data: OrderData) -> OrderResult:
        compensations = []  # Стек компенсаций
        
        try:
            # Шаг 1: Создать заказ
            order_id = await workflow.execute_activity(
                create_order,
                order_data,
                start_to_close_timeout=timedelta(seconds=30),
            )
            compensations.append(("cancel_order", order_id))
            
            # Шаг 2: Зарезервировать товар
            reservation_id = await workflow.execute_activity(
                reserve_inventory,
                order_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            compensations.append(("release_inventory", reservation_id))
            
            # Шаг 3: Списать деньги
            payment_id = await workflow.execute_activity(
                charge_payment,
                order_data.payment_info,
                start_to_close_timeout=timedelta(seconds=60),
            )
            compensations.append(("refund_payment", payment_id))
            
            # Шаг 4: Назначить доставку
            delivery_id = await workflow.execute_activity(
                schedule_delivery,
                order_id,
                start_to_close_timeout=timedelta(minutes=5),
            )
            # Последний шаг — без компенсации
            
            return OrderResult.success(order_id, delivery_id)
            
        except Exception as e:
            # ROLLBACK: выполняем компенсации в обратном порядке
            workflow.logger.error(f"Saga failed: {e}")
            
            for action, entity_id in reversed(compensations):
                await workflow.execute_activity(
                    action,  # cancel_order, release_inventory, etc.
                    entity_id,
                    start_to_close_timeout=timedelta(seconds=30),
                )
            
            return OrderResult.failed(str(e))
```

### Архитектура Saga

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SAGA: УСПЕШНЫЙ СЦЕНАРИЙ                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐        │
│   │  Order    │    │ Inventory │    │  Payment  │    │ Delivery  │        │
│   │  Service  │    │  Service  │    │  Service  │    │  Service  │        │
│   └─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘        │
│         │                │                │                │               │
│    1. Create ─────►      │                │                │               │
│       Order ✅           │                │                │               │
│         │                │                │                │               │
│         │          2. Reserve ────►       │                │               │
│         │            Stock ✅             │                │               │
│         │                │                │                │               │
│         │                │          3. Charge ─────►       │               │
│         │                │           Payment ✅            │               │
│         │                │                │                │               │
│         │                │                │          4. Schedule ──►      │
│         │                │                │           Delivery ✅         │
│         │                │                │                │               │
│   ◄─────┴────────────────┴────────────────┴────────────────┘               │
│                         SUCCESS!                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        SAGA: СЦЕНАРИЙ С ОШИБКОЙ                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐        │
│   │  Order    │    │ Inventory │    │  Payment  │    │ Delivery  │        │
│   │  Service  │    │  Service  │    │  Service  │    │  Service  │        │
│   └─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘        │
│         │                │                │                │               │
│    1. Create ─────►      │                │                │               │
│       Order ✅           │                │                │               │
│         │                │                │                │               │
│         │          2. Reserve ────►       │                │               │
│         │            Stock ✅             │                │               │
│         │                │                │                │               │
│         │                │          3. Charge ─────►       │               │
│         │                │           Payment ✅            │               │
│         │                │                │                │               │
│         │                │                │          4. Schedule ──►      │
│         │                │                │           Delivery ❌         │
│         │                │                │                │               │
│         │                │                │        COMPENSATION:          │
│         │                │                │                │               │
│         │                │         ◄── 3. Refund ◄────────┘               │
│         │                │             Payment                             │
│         │                │                │                                 │
│         │         ◄── 2. Release ◄───────┘                                │
│         │              Stock                                               │
│         │                │                                                  │
│  ◄── 1. Cancel ◄────────┘                                                 │
│       Order                                                                 │
│         │                                                                   │
│      ROLLED BACK                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Сравнение Data Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      СРАВНЕНИЕ DATA PATTERNS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Паттерн           │ Проблема              │ Решение                       │
│  ──────────────────│───────────────────────│──────────────────────────────│
│                    │                       │                               │
│  CQRS              │ Read ≠ Write          │ Разные модели для            │
│                    │ требования            │ чтения и записи              │
│                    │                       │                               │
│  Event Sourcing    │ Нужна история +       │ Хранить события,             │
│                    │ audit trail           │ не состояние                 │
│                    │                       │                               │
│  Transactional     │ Dual Write Problem    │ События в той же             │
│  Outbox            │ (потеря событий)      │ транзакции                   │
│                    │                       │                               │
│  Saga              │ Нет распределённых    │ Локальные транзакции         │
│                    │ транзакций            │ + компенсации                │
│                    │                       │                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Чеклист Data Patterns

```markdown
## Data Patterns Checklist

### CQRS
- [ ] Write Model для бизнес-логики
- [ ] Read Model для запросов (projections)
- [ ] Синхронизация через события
- [ ] Eventual consistency приемлема

### Event Sourcing
- [ ] Все события immutable
- [ ] Event Store append-only
- [ ] Aggregate восстанавливается из событий
- [ ] Snapshots для оптимизации (опционально)

### Transactional Outbox
- [ ] Outbox table в той же БД
- [ ] Events в той же транзакции
- [ ] Worker для публикации
- [ ] Idempotency в consumers

### Saga
- [ ] Каждый шаг = локальная транзакция
- [ ] Compensation для каждого шага
- [ ] Compensations идемпотентны
- [ ] Мониторинг (Temporal UI / логи)
```

---

<div align="center">

[← Decomposition](./02-decomposition-patterns.md) | **Data Patterns** | [Communication →](./04-communication-patterns.md)

</div>
