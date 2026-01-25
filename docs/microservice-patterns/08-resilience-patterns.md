# 08. Resilience Patterns

> **Как система переживает сбои**

---

## Проблема отказоустойчивости

В распределённой системе **что-то всегда ломается**:
- Сеть нестабильна
- Сервисы падают
- Базы данных тормозят
- Внешние API недоступны

**Resilience** = способность системы продолжать работать при частичных сбоях.

### 🏠 Аналогия: Самолёт

Самолёт проектируют с избыточностью:
- 2-4 двигателя (один откажет — летим дальше)
- Дублированные системы управления
- Аварийные генераторы

Микросервисы должны проектироваться так же: **ожидай сбоев и готовься к ним**.

---

## Паттерн 1: Circuit Breaker

### 💡 Суть

**Прерывать вызовы** к неработающему сервису, чтобы не ждать timeout и дать время на восстановление.

### 📝 Техническое объяснение

Три состояния:
1. **Closed** — всё работает, запросы проходят
2. **Open** — сервис сломан, запросы отклоняются сразу (fast fail)
3. **Half-Open** — пробуем снова, если успех → Closed

### 🏠 Аналогия: Автоматический выключатель (автомат)

В электрощитке есть автоматы. Если короткое замыкание:
1. Автомат **выключается** (Open) — спасает проводку
2. Через время вы **пробуете включить** (Half-Open)
3. Если всё ок — работает (Closed). Если опять замыкание — снова выбивает

Circuit Breaker защищает систему от "короткого замыкания" в сети.

### ✅ Когда использовать

- Вызовы **внешних сервисов** (payment, email)
- Вызовы **других микросервисов**
- **Защита от cascade failure** (эффект домино)

### ❌ Когда НЕ использовать

- Локальные вызовы (в памяти)
- Критичные операции без fallback

### 🔧 Пример

```python
from circuitbreaker import circuit

@circuit(
    failure_threshold=5,      # 5 ошибок → Open
    recovery_timeout=30,      # 30 секунд в Open, потом Half-Open
    expected_exception=Exception,
)
async def call_payment_service(order_id: str, amount: float) -> PaymentResult:
    """Вызов Payment Service с Circuit Breaker."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            "http://payment-service/charge",
            json={"order_id": order_id, "amount": amount},
        )
        response.raise_for_status()
        return PaymentResult(**response.json())


# Использование
async def process_order(order: Order):
    try:
        result = await call_payment_service(order.id, order.total)
        return Success(result)
    except CircuitBreakerError:
        # Circuit открыт — сервис недоступен
        # Можно: отложить, уведомить, использовать fallback
        return Failure(PaymentServiceUnavailable())
```

### Диаграмма состояний

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CIRCUIT BREAKER STATES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                           ┌──────────────┐                                  │
│                           │    CLOSED    │                                  │
│                           │              │                                  │
│                           │  Запросы     │                                  │
│                           │  проходят    │                                  │
│                           └──────┬───────┘                                  │
│                                  │                                          │
│                    Failure threshold exceeded                               │
│                    (5 ошибок подряд)                                        │
│                                  │                                          │
│                                  ▼                                          │
│                           ┌──────────────┐                                  │
│                           │     OPEN     │                                  │
│                           │              │                                  │
│          ┌───────────────►│  Fast Fail   │◄───────────────┐                │
│          │                │  (мгновенно) │                │                │
│          │                └──────┬───────┘                │                │
│          │                       │                        │                │
│          │           Recovery timeout (30s)               │                │
│          │                       │                        │                │
│          │                       ▼                        │                │
│          │                ┌──────────────┐                │                │
│          │                │  HALF-OPEN   │                │                │
│          │                │              │                │                │
│          │   Failure      │  Пробный     │   Success     │                │
│          └────────────────│  запрос      │────────────────┘                │
│                           └──────────────┘                                  │
│                                  │                                          │
│                              Success                                        │
│                                  │                                          │
│                                  ▼                                          │
│                           ┌──────────────┐                                  │
│                           │    CLOSED    │                                  │
│                           └──────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 2: Retry with Backoff

### 💡 Суть

**Повторять** неудавшийся запрос с **увеличивающимися интервалами**.

### 📝 Техническое объяснение

Стратегии:
- **Fixed** — всегда одинаковый интервал (1s, 1s, 1s)
- **Linear** — линейное увеличение (1s, 2s, 3s)
- **Exponential** — экспоненциальное (1s, 2s, 4s, 8s)
- **Exponential + Jitter** — с рандомизацией (избежать thundering herd)

### 🏠 Аналогия: Звонок другу

Друг не отвечает на звонок:
1. Перезвонить через **1 минуту**
2. Снова не ответил → через **5 минут**
3. Снова → через **30 минут**
4. Если **10 раз** не ответил — сдаться

Не стоит звонить каждую секунду — будете раздражать (и его, и себя).

### ✅ Когда использовать

- Временные сбои сети
- Rate limiting (429)
- Перегрузка сервиса (503)

### ❌ Когда НЕ использовать

- Бизнес-ошибки (400, 404) — retry не поможет
- Долгие операции (суммирование таймаутов)
- Без Circuit Breaker (бесконечный retry)

### 🔧 Пример (tenacity)

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import httpx

@retry(
    stop=stop_after_attempt(5),                    # Максимум 5 попыток
    wait=wait_exponential(multiplier=1, max=60),   # 1s, 2s, 4s, 8s, 16s (max 60s)
    retry=retry_if_exception_type((                # Retry только для этих ошибок
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.HTTPStatusError,
    )),
)
async def fetch_user(user_id: str) -> dict:
    """Получить пользователя с retry."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"http://user-service/users/{user_id}")
        
        # Retry для 5xx и 429
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()
        
        return response.json()
```

### Exponential Backoff с Jitter

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  EXPONENTIAL BACKOFF + JITTER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Без Jitter (thundering herd):                                             │
│                                                                             │
│  Client A: ──────●────────●────────────●────────────────●                  │
│  Client B: ──────●────────●────────────●────────────────●                  │
│  Client C: ──────●────────●────────────●────────────────●                  │
│                  ↑        ↑            ↑                ↑                   │
│              Все retry одновременно → перегрузка!                          │
│                                                                             │
│  С Jitter (распределённые retry):                                          │
│                                                                             │
│  Client A: ────●──────────●─────────────────●──────────────────●           │
│  Client B: ──────●──────────●──────────────────●─────────────────●         │
│  Client C: ────────●──────────●────────────────────●───────────────●       │
│                                                                             │
│  Jitter = случайное добавление к интервалу                                 │
│  delay = base * 2^attempt + random(0, base)                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 3: Bulkhead

### 💡 Суть

**Изолировать** ресурсы (потоки, соединения), чтобы сбой одной части не влиял на другие.

### 📝 Техническое объяснение

Разделить пулы:
- Отдельный пул соединений для критичных операций
- Отдельный пул для некритичных
- Если некритичный сервис завис — критичные продолжают работать

### 🏠 Аналогия: Отсеки на корабле (bulkheads)

Корабль разделён на **водонепроницаемые отсеки**. Если пробоина в одном:
- Затапливает только этот отсек
- Остальные сухие
- Корабль не тонет

Без отсеков — одна дырка топит весь корабль.

### ✅ Когда использовать

- Разные уровни критичности операций
- Защита от медленных зависимостей
- Изоляция tenants (multi-tenant)

### 🔧 Пример

```python
import asyncio
from asyncio import Semaphore

# Отдельные "отсеки" для разных операций
class Bulkheads:
    # Критичные операции — больше ресурсов
    payment_semaphore = Semaphore(50)
    
    # Некритичные — меньше ресурсов
    notification_semaphore = Semaphore(10)
    
    # Внешние API — ограниченно
    external_api_semaphore = Semaphore(5)


async def charge_payment(order_id: str) -> PaymentResult:
    """Критичная операция — свой пул."""
    async with Bulkheads.payment_semaphore:
        return await payment_client.charge(order_id)


async def send_notification(user_id: str) -> None:
    """Некритичная операция — отдельный пул."""
    async with Bulkheads.notification_semaphore:
        await notification_client.send(user_id)


# Даже если notification_client завис и забил свой пул,
# payment_client продолжает работать со своим пулом!
```

---

## Паттерн 4: Timeout

### 💡 Суть

**Ограничить время ожидания** ответа, чтобы не ждать вечно.

### 📝 Техническое объяснение

Типы timeout:
- **Connection timeout** — время на установку соединения
- **Read timeout** — время на получение ответа
- **Total timeout** — общее время операции

### 🏠 Аналогия: Ожидание в очереди

Вы пришли в банк. Если очередь **30 минут** — может подождёте. Если **3 часа** — уйдёте и придёте завтра.

Timeout — это ваше "терпение". Не бесконечное.

### ✅ Когда использовать

- **Всегда** для сетевых вызовов
- Предотвращение зависших запросов
- Освобождение ресурсов

### 🔧 Пример

```python
import httpx
import anyio

# HTTP timeout
async def call_service():
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=5.0,   # 5s на соединение
            read=30.0,     # 30s на чтение
            write=10.0,    # 10s на запись
            pool=10.0,     # 10s на получение соединения из пула
        )
    ) as client:
        return await client.get("http://slow-service/data")


# Общий timeout для операции
async def process_with_timeout():
    with anyio.fail_after(60):  # 60s на всю операцию
        result1 = await call_service_a()
        result2 = await call_service_b()
        return combine(result1, result2)
```

---

## Паттерн 5: Idempotency

### 💡 Суть

Операция **безопасна для повторного выполнения** — результат тот же.

### 📝 Техническое объяснение

Если клиент не получил ответ (timeout), он может повторить запрос. Сервер должен:
- Распознать повторный запрос
- Вернуть тот же результат (не создавать дубликат)

### 🏠 Аналогия: Кнопка лифта

Нажали кнопку вызова лифта. Лифт не приехал. Нажали ещё раз, ещё раз...

Результат? Лифт приедет **один раз**, не три. Кнопка **идемпотентна**.

Если бы кнопка не была идемпотентной — приехало бы 3 лифта!

### ✅ Когда использовать

- **Платежи** (критично!)
- Создание ресурсов (POST)
- Любые операции с retry

### 🔧 Пример (Idempotency Key)

```python
# Клиент отправляет уникальный ключ
headers = {
    "X-Idempotency-Key": "order-123-payment-attempt-1"
}

# POST /payments
# Body: {"order_id": "123", "amount": 100}

# Сервер:
@post("/payments")
async def create_payment(
    data: PaymentRequest,
    idempotency_key: str = Header(alias="X-Idempotency-Key"),
):
    # Проверяем, был ли уже такой запрос
    existing = await cache.get(f"idempotency:{idempotency_key}")
    
    if existing:
        # Возвращаем сохранённый результат
        return PaymentResponse(**json.loads(existing))
    
    # Выполняем операцию
    payment = await process_payment(data)
    
    # Сохраняем результат
    await cache.set(
        f"idempotency:{idempotency_key}",
        payment.json(),
        expire=86400,  # 24 часа
    )
    
    return payment
```

---

## Комбинация паттернов

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    КОМБИНАЦИЯ RESILIENCE PATTERNS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Client Request                                                            │
│        │                                                                    │
│        ▼                                                                    │
│   ┌─────────────────────┐                                                  │
│   │   IDEMPOTENCY       │  ← Защита от дублей                              │
│   │   Check cache       │                                                  │
│   └──────────┬──────────┘                                                  │
│              │                                                              │
│              ▼                                                              │
│   ┌─────────────────────┐                                                  │
│   │   BULKHEAD          │  ← Изоляция ресурсов                             │
│   │   Acquire semaphore │                                                  │
│   └──────────┬──────────┘                                                  │
│              │                                                              │
│              ▼                                                              │
│   ┌─────────────────────┐                                                  │
│   │   CIRCUIT BREAKER   │  ← Fast fail если сервис сломан                  │
│   │   Check state       │                                                  │
│   └──────────┬──────────┘                                                  │
│              │                                                              │
│              ▼                                                              │
│   ┌─────────────────────┐                                                  │
│   │   RETRY + TIMEOUT   │  ← Повтор с ограничением времени                 │
│   │   Call with backoff │                                                  │
│   └──────────┬──────────┘                                                  │
│              │                                                              │
│              ▼                                                              │
│   ┌─────────────────────┐                                                  │
│   │   External Service  │                                                  │
│   └─────────────────────┘                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Сравнение паттернов

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RESILIENCE PATTERNS COMPARISON                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Паттерн         │ Защищает от           │ Механизм                        │
│  ────────────────│───────────────────────│─────────────────────────────────│
│                  │                       │                                  │
│  Circuit Breaker │ Cascade failure       │ Fast fail, recovery time        │
│                  │ Перегрузка            │                                  │
│                  │                       │                                  │
│  Retry + Backoff │ Временные сбои        │ Повторы с задержкой             │
│                  │ Rate limiting         │                                  │
│                  │                       │                                  │
│  Bulkhead        │ Resource exhaustion   │ Изоляция пулов                  │
│                  │ Cascade failure       │                                  │
│                  │                       │                                  │
│  Timeout         │ Зависшие запросы      │ Ограничение времени             │
│                  │ Resource leak         │                                  │
│                  │                       │                                  │
│  Idempotency     │ Дубликаты             │ Уникальный ключ + кэш           │
│                  │ Duplicate charges     │                                  │
│                  │                       │                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Чеклист Resilience

```markdown
## Resilience Checklist

### Circuit Breaker
- [ ] Настроен для внешних сервисов
- [ ] Failure threshold определён
- [ ] Recovery timeout определён
- [ ] Fallback для Open state
- [ ] Мониторинг состояния

### Retry
- [ ] Exponential backoff
- [ ] Jitter для распределения
- [ ] Max attempts ограничен
- [ ] Retry только для transient errors
- [ ] Комбинация с Circuit Breaker

### Bulkhead
- [ ] Отдельные пулы для критичных операций
- [ ] Лимиты на соединения
- [ ] Мониторинг использования пулов

### Timeout
- [ ] Connection timeout
- [ ] Read timeout
- [ ] Total operation timeout
- [ ] Разумные значения (не слишком большие)

### Idempotency
- [ ] X-Idempotency-Key для мутаций
- [ ] Кэширование результатов
- [ ] TTL для ключей
- [ ] Конфликт-детекция (разный body)
```

---

<div align="center">

[← Observability](./07-observability-patterns.md) | **Resilience** | [Security →](./09-security-patterns.md)

</div>
