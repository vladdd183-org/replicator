# 🌉 Module Gateway Pattern & Advanced Communication

> **Версия:** 4.3 | **Дата:** Январь 2026

Этот документ описывает продвинутые способы связи между модулями, когда стандартного Event-Driven подхода недостаточно (например, нужен синхронный ответ).

---

## 🛑 Проблема прямой связи

В монолите часто возникает соблазн просто импортировать класс из соседнего модуля:

```python
# ❌ ПЛОХО: Жесткая связь (Coupling)
from src.Containers.VendorSection.PaymentModule.Actions.ProcessPaymentAction import ProcessPaymentAction

class CreateOrderAction(Action):
    def __init__(self, payment_action: ProcessPaymentAction):
        ...
```

**Почему это плохо:**
1.  **Refactoring Hell**: Если `PaymentModule` изменится, сломается `OrderModule`.
2.  **Monolith Lock**: Вы не сможете вынести `PaymentModule` в микросервис без переписывания кода `OrderModule`.
3.  **Testing**: Трудно мокать зависимости.

---

## 🛡️ Решение 1: Module Gateway Pattern (Ports & Adapters)

Также известен как **"Client Manager"** или **Hexagonal Architecture**.
Суть: Модуль А определяет **Интерфейс (Port)** того, что ему нужно. Модуль Б (или адаптер) реализует этот интерфейс.

### Структура

В модуле-потребителе (`OrderModule`) создается папка `Gateways`:

```
src/Containers/AppSection/OrderModule/
├── Actions/
├── ...
└── Gateways/            
    ├── PaymentGateway.py         # 1. Интерфейс (Protocol) + DTO
    └── Adapters/
        ├── DirectPaymentAdapter.py # 2. Реализация (Монолит)
        └── HttpPaymentAdapter.py   # 3. Реализация (Микросервис)
```

### 1. Интерфейс (Port)

`OrderModule` диктует условия. Этот файл лежит внутри `OrderModule` и не зависит от внешнего мира.

```python
# src/Containers/AppSection/OrderModule/Gateways/PaymentGateway.py
from typing import Protocol
from dataclasses import dataclass
from returns.result import Result

@dataclass
class ChargeParams:
    amount: int
    user_id: str

class PaymentGateway(Protocol):
    async def charge(self, params: ChargeParams) -> Result[str, Exception]:
        ...
```

### 2. Реализация (Adapter)

Адаптер "натягивает" реальность `PaymentModule` на интерфейс `OrderModule`.

```python
# src/Containers/AppSection/OrderModule/Gateways/Adapters/DirectPaymentAdapter.py
from src.Containers.VendorSection.PaymentModule.Actions import ProcessPaymentAction

class DirectPaymentAdapter(PaymentGateway):
    def __init__(self, action: ProcessPaymentAction):
        self.action = action

    async def charge(self, params: ChargeParams) -> Result[str, Exception]:
        # Маппинг DTO шлюза -> DTO экшена
        result = await self.action.run(...)
        return result.map(lambda r: r.transaction_id)
```

### 3. Использование (Action)

Бизнес-логика зависит только от абстракции.

```python
class CreateOrderAction(Action):
    def __init__(self, payment_gateway: PaymentGateway):  # <-- Зависимость от интерфейса
        self.payment_gateway = payment_gateway
```

### 4. Регистрация (DI)

В `Providers.py` мы решаем, какую реализацию использовать.

```python
class OrderProvider(Provider):
    # В Монолите:
    payment_gateway = provide(DirectPaymentAdapter, provides=PaymentGateway)
    
    # В Микросервисах (будущее):
    # payment_gateway = provide(HttpPaymentAdapter, provides=PaymentGateway)
```

---

## 🔥 Решение 2: Data Replication (Event-Carried State Transfer)

**Философия:** "Не спрашивай данные у соседа, имей свою копию".
Используется, когда нужна **максимальная автономность** и скорость чтения.

### Как это работает

1.  **UserModule** публикует событие `UserUpdated`.
2.  **OrderModule** слушает это событие.
3.  **OrderModule** обновляет **свою локальную таблицу** `order_user_replicas`.

```python
# OrderModule/Models/UserReplica.py
class UserReplica(Model):
    """Урезанная копия пользователя, специфичная для заказов."""
    id = UUID(primary_key=True)
    email = Varchar()
    discount_percent = Integer() # Поле, нужное только здесь
```

### Плюсы и Минусы

| ✅ Плюсы | ❌ Минусы |
|---|---|
| **Zero Latency**: Читаем локальную БД | **Eventual Consistency**: Данные могут отстать на секунду |
| **High Availability**: Работаем, даже если UserModule упал | **Storage**: Дублирование данных |

---

## ⚡ Решение 3: RPC (Remote Procedure Call)

Использование брокера сообщений (TaskIQ) как транспорта для вызова функций.

```python
# 1. PaymentModule регистрирует задачу
@broker.task(task_name="payment.get_balance")
async def get_balance(user_id: int) -> int: ...

# 2. OrderModule вызывает её и ждет ответ
balance = await get_balance.kiq(user_id=123).wait_result()
```

Хороший компромисс, если лень писать HTTP-адаптеры, но хочется развязать код.

---

## ⚖️ Сводная таблица

| Паттерн | Coupling (Связность) | Сложность | Use Case |
| :--- | :--- | :--- | :--- |
| **Events** | ⭐ Низкая (Лучшая) | ⭐ Низкая | "Fire-and-Forget" (уведомления, логи) |
| **Module Gateway** | ⭐⭐ Средняя | ⭐⭐ Средняя | Нужен синхронный ответ (платежи, проверки) |
| **Data Replication** | ⭐ Низкая | ⭐⭐⭐ Высокая | Высокая нагрузка, полная автономность |
| **Direct Import** | ❌ Высокая (Плохо) | ⭐ Низкая | Прототипирование (не рекомендуется в Prod) |

---

<div align="center">
**Hyper-Porto v4.3**
</div>


