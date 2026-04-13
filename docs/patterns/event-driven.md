# Паттерн: Event-Driven архитектура

> Domain Events -- основа межмодульного общения. Подменяемые бэкенды: Memory -> Redis -> NATS -> libp2p.

---

## Принцип

Container-ы **не импортируют** друг из друга. Они общаются через **Domain Events**.

```
Container A                    Event Bus                    Container B
    |                              |                              |
    |-- uow.add_event(OrderCreated) -->|                         |
    |-- uow.commit() --->         |                              |
    |                              |-- OrderCreated ------------>|
    |                              |                    on_order_created()
```

---

## UnitOfWork + Events

Все события добавляются в UoW и публикуются **только после успешного commit**:

```python
async with self.uow:
    order = Order(...)
    await self.uow.orders.add(order)
    self.uow.add_event(OrderCreated(order_id=order.id, total=order.total))
    await self.uow.commit()
    # OrderCreated публикуется ЗДЕСЬ, после commit
```

Если commit упал -- события НЕ публикуются. Консистентность гарантирована.

---

## Listener-ы

```python
from litestar.events import listener

@listener("OrderCreated")
async def on_order_created(order_id: str, total: float, **kwargs):
    # Обработка в другом Container
    ...
```

Listener-ы регистрируются явно в `App.py`:

```python
app = Litestar(
    listeners=[on_order_created, on_order_cancelled, ...],
)
```

---

## Подменяемые бэкенды (EventBusPort)

```python
class EventBusPort(Protocol):
    async def emit(self, event_name: str, data: dict) -> None: ...
    async def on(self, event_name: str, handler: Callable) -> None: ...
```

| Бэкенд | Когда | Характеристики |
|---|---|---|
| `InMemoryEventBus` | Тесты | Синхронно, в процессе |
| `LitestarEventBus` | Монолит | litestar.events, в процессе |
| `RedisEventBus` | Distributed monolith | Redis Pub/Sub, между процессами |
| `NATSEventBus` | Микросервисы Web2 | NATS JetStream, durable, at-least-once |
| `LibP2PEventBus` | Web3 (будущее) | GossipSub, P2P, decentralized |

Переключение -- через DI Provider.

---

## Outbox Pattern (гарантия доставки)

Для продакшена используется Transactional Outbox:

```
1. Action записывает данные + событие в одну транзакцию
2. Outbox worker читает неотправленные события
3. Worker публикует в EventBus
4. Worker помечает как отправленные
```

Это гарантирует at-least-once доставку даже при падении процесса.

---

## Для Replicator

Events -- это:
- **Основа кросс-модульного общения** в Porto
- **Audit trail** (кто что сделал и когда)
- **Event sourcing ready** (можно восстановить состояние из событий)
- **Web3 ready** (события = append-only log = Ceramic stream)
- **Agent-friendly** (агенты подписываются на события и реагируют)
