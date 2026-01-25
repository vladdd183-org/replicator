# 07. Observability Patterns

> **Мониторинг и отладка распределённой системы**

---

## Проблема наблюдаемости

В монолите отладка простая: один лог, один стектрейс.

В микросервисах:
- Запрос проходит через **N сервисов**
- Логи разбросаны по разным машинам
- Сложно понять, **где проблема**
- Сложно измерить **производительность**

**Observability** = способность понять состояние системы по её выводу.

### Три столпа Observability

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ТРИ СТОЛПА OBSERVABILITY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐               │
│   │     LOGS       │  │    METRICS     │  │    TRACES      │               │
│   │                │  │                │  │                │               │
│   │  "Что          │  │  "Сколько?"    │  │  "Как запрос   │               │
│   │   произошло?"  │  │                │  │   прошёл?"     │               │
│   │                │  │  • RPS         │  │                │               │
│   │  • Errors      │  │  • Latency     │  │  • Span A      │               │
│   │  • Events      │  │  • CPU/Memory  │  │  • Span B      │               │
│   │  • Debug info  │  │  • Queue size  │  │  • Span C      │               │
│   │                │  │                │  │                │               │
│   └────────────────┘  └────────────────┘  └────────────────┘               │
│                                                                             │
│   Пример:                                                                   │
│   Logs:   "Error: connection timeout"                                       │
│   Metrics: "p99 latency = 5s, error_rate = 15%"                            │
│   Traces:  "Request → Auth(50ms) → Order(4.5s) → Payment(timeout)"         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 1: Distributed Tracing

### 💡 Суть

**Отслеживать путь запроса** через все сервисы с временными метками.

### 📝 Техническое объяснение

- **Trace** — полный путь запроса (от входа до ответа)
- **Span** — единица работы в одном сервисе
- **Context Propagation** — передача trace ID между сервисами

### 🏠 Аналогия: Трекинг посылки

Когда заказываете посылку:
1. Посылке присваивают **трек-номер** (Trace ID)
2. На каждом этапе **сканируют** (Span):
   - Склад отправителя: 10:00
   - Сортировочный центр: 14:00
   - Транспортировка: 14:00-20:00
   - Пункт выдачи: 21:00
3. Вы видите **весь путь** и **где задержка**

Distributed Tracing = трекинг для HTTP запросов.

### ✅ Когда использовать

- **Всегда** в микросервисах
- Отладка медленных запросов
- Поиск bottlenecks
- Понимание зависимостей

### 🔧 Пример (OpenTelemetry / Logfire)

```python
import logfire

# Автоматическая инструментация
logfire.configure(service_name="order-service")

# Span создаётся автоматически для HTTP запросов
@app.post("/orders")
async def create_order(data: CreateOrderRequest):
    # Вложенный span
    with logfire.span("validate_order"):
        validate(data)
    
    with logfire.span("save_to_db"):
        order = await repository.save(data)
    
    with logfire.span("send_notification"):
        await notify(order)
    
    return order

# Trace ID передаётся автоматически в заголовках:
# traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
```

### Визуализация Trace

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace: Create Order (trace_id: abc123)                      Total: 250ms   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ├─ API Gateway                    ████░░░░░░░░░░░░░░░░░░░░░░ 20ms          │
│ │                                                                           │
│ ├─ Order Service                  ░░░░████████████████████░░ 200ms         │
│ │  ├─ validate_order              ░░░░██░░░░░░░░░░░░░░░░░░░░ 10ms          │
│ │  ├─ User Service (HTTP)         ░░░░░░████░░░░░░░░░░░░░░░░ 30ms          │
│ │  ├─ save_to_db                  ░░░░░░░░░░██████░░░░░░░░░░ 50ms          │
│ │  └─ Payment Service (HTTP)      ░░░░░░░░░░░░░░░░████████░░ 100ms         │
│ │                                                                           │
│ └─ Response                       ░░░░░░░░░░░░░░░░░░░░░░░░██ 10ms          │
│                                                                             │
│ 💡 Bottleneck: Payment Service занимает 40% времени                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 2: Log Aggregation

### 💡 Суть

**Собирать логи** со всех сервисов в **одно место** для поиска и анализа.

### 📝 Техническое объяснение

- Каждый сервис пишет логи (stdout/файл)
- **Log shipper** (Fluentd, Filebeat) отправляет в хранилище
- **Хранилище** (Elasticsearch, Loki) индексирует
- **UI** (Kibana, Grafana) для поиска

### 🏠 Аналогия: Центральный архив

Вместо того чтобы искать документы по разным кабинетам:
- Все документы (логи) отправляют в **центральный архив**
- Архив **индексирует** по дате, отделу, типу
- Можно **найти** любой документ за секунды

### ✅ Когда использовать

- **Всегда** (без логов вы слепы)
- Отладка ошибок
- Аудит и compliance
- Анализ поведения

### 🔧 Structured Logging

```python
import logfire

# ❌ ПЛОХО — неструктурированный лог
logger.info(f"User {user_id} created order {order_id}")

# ✅ ХОРОШО — структурированный лог
logfire.info(
    "Order created",
    user_id=str(user_id),
    order_id=str(order_id),
    total=float(order.total),
    items_count=len(order.items),
)

# Результат в JSON:
# {
#   "message": "Order created",
#   "user_id": "123",
#   "order_id": "456",
#   "total": 99.99,
#   "items_count": 3,
#   "timestamp": "2026-01-25T10:00:00Z",
#   "service": "order-service",
#   "trace_id": "abc123"
# }
```

### Архитектура Log Aggregation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LOG AGGREGATION                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                                 │
│   │  User    │  │  Order   │  │ Payment  │                                 │
│   │ Service  │  │ Service  │  │ Service  │                                 │
│   │          │  │          │  │          │                                 │
│   │  stdout  │  │  stdout  │  │  stdout  │                                 │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘                                 │
│        │             │             │                                        │
│        └─────────────┼─────────────┘                                        │
│                      │                                                      │
│                      ▼                                                      │
│        ┌─────────────────────────────┐                                     │
│        │       Log Shipper           │                                     │
│        │   (Fluentd / Filebeat)      │                                     │
│        └──────────────┬──────────────┘                                     │
│                       │                                                     │
│                       ▼                                                     │
│        ┌─────────────────────────────┐                                     │
│        │       Log Storage           │                                     │
│        │  (Elasticsearch / Loki)     │                                     │
│        └──────────────┬──────────────┘                                     │
│                       │                                                     │
│                       ▼                                                     │
│        ┌─────────────────────────────┐                                     │
│        │      Visualization          │                                     │
│        │   (Kibana / Grafana)        │                                     │
│        │                             │                                     │
│        │  Search: "error AND order"  │                                     │
│        └─────────────────────────────┘                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 3: Application Metrics

### 💡 Суть

**Собирать числовые показатели** о работе системы для мониторинга и алертинга.

### 📝 Техническое объяснение

Типы метрик:
- **Counter** — только растёт (requests_total)
- **Gauge** — текущее значение (memory_usage)
- **Histogram** — распределение (request_duration)

### 🏠 Аналогия: Приборная панель автомобиля

Водитель не читает "мотор работает нормально" (лог). Он смотрит на **приборы**:
- Спидометр: 80 км/ч (gauge)
- Одометр: 45,000 км (counter)
- Температура двигателя: 90°C (gauge)

Если стрелка в красной зоне — проблема. Метрики = приборная панель для софта.

### ✅ Когда использовать

- **Всегда** для production
- Алертинг (уведомления о проблемах)
- Capacity planning
- SLA мониторинг

### 🔧 RED Method (Rate, Errors, Duration)

```python
# Базовые метрики для каждого сервиса

# RATE — запросов в секунду
requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

# ERRORS — процент ошибок
errors_total = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "error_type"],
)

# DURATION — время ответа
request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 5],
)

# Middleware для сбора
@middleware
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    requests_total.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code,
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.path,
    ).observe(duration)
    
    return response
```

---

## Паттерн 4: Health Check API

### 💡 Суть

**Endpoints** для проверки состояния сервиса: жив ли, готов ли принимать трафик.

### 📝 Техническое объяснение

- **Liveness** (`/health`) — сервис работает (не завис)
- **Readiness** (`/ready`) — сервис готов принимать запросы (БД подключена)

### 🏠 Аналогия: Проверка сотрудника

**Liveness**: "Ты на работе?" — Да, я здесь (процесс запущен)

**Readiness**: "Ты готов работать?" — Да, компьютер включён, программы загружены, база открыта

Сотрудник может быть на работе (liveness), но не готов работать (readiness) — например, ждёт загрузки системы.

### ✅ Когда использовать

- **Всегда** в контейнерных окружениях
- Kubernetes probes
- Load balancer health checks
- Мониторинг доступности

### 🔧 Пример реализации

```python
from litestar import Controller, get
from litestar.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

class HealthController(Controller):
    path = "/health"
    
    @get("/")
    async def liveness(self) -> dict:
        """Liveness probe — сервис работает."""
        return {"status": "healthy"}
    
    @get("/ready")
    async def readiness(self) -> Response:
        """Readiness probe — сервис готов принимать трафик."""
        checks = {}
        
        # Проверка БД
        try:
            await database.execute("SELECT 1")
            checks["database"] = True
        except Exception:
            checks["database"] = False
        
        # Проверка Redis
        try:
            await redis.ping()
            checks["redis"] = True
        except Exception:
            checks["redis"] = False
        
        all_healthy = all(checks.values())
        status_code = HTTP_200_OK if all_healthy else HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(
            content={"status": "ready" if all_healthy else "not_ready", "checks": checks},
            status_code=status_code,
        )
```

### Kubernetes Probes

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: app
      livenessProbe:
        httpGet:
          path: /health
          port: 8000
        initialDelaySeconds: 10
        periodSeconds: 10
        failureThreshold: 3  # 3 failures → restart
      
      readinessProbe:
        httpGet:
          path: /health/ready
          port: 8000
        initialDelaySeconds: 5
        periodSeconds: 5
        failureThreshold: 3  # 3 failures → remove from LB
```

---

## Паттерн 5: Audit Logging

### 💡 Суть

**Логировать все значимые действия** для безопасности и compliance.

### 📝 Техническое объяснение

Audit log содержит:
- **Кто** (actor)
- **Что сделал** (action)
- **С чем** (entity)
- **Когда** (timestamp)
- **Откуда** (IP, user agent)

### 🏠 Аналогия: Журнал охраны

В офисе охрана записывает:
- Иванов вошёл в 9:00
- Иванов открыл серверную в 10:30
- Петров вынес ноутбук в 18:00

Если что-то пропало — можно найти, кто и когда.

### ✅ Когда использовать

- **Финансовые операции** (обязательно)
- **Персональные данные** (GDPR)
- **Изменение критичных настроек**
- Security incidents investigation

### 🔧 Пример (Hyper-Porto @audited)

```python
from src.Ship.Decorators import audited

@audited(action="create", entity_type="User")
class CreateUserAction(Action[CreateUserRequest, User, UserError]):
    async def run(self, data: CreateUserRequest) -> Result[User, UserError]:
        # Бизнес-логика
        ...

# Результат в AuditLog:
# {
#   "action": "create_success",
#   "entity_type": "User",
#   "entity_id": "user-123",
#   "actor_id": "admin-456",
#   "actor_email": "admin@example.com",
#   "timestamp": "2026-01-25T10:00:00Z",
#   "input_data": {"email": "new@user.com", "password": "***REDACTED***"},
#   "duration_ms": 150
# }
```

---

## Паттерн 6: Exception Tracking

### 💡 Суть

**Агрегировать и анализировать** исключения для быстрого реагирования.

### 📝 Техническое объяснение

Инструменты (Sentry, Rollbar) собирают:
- Stack trace
- Context (request, user)
- Группировку похожих ошибок
- Тренды (новая ошибка? регрессия?)
- Алертинг

### 🏠 Аналогия: Журнал инцидентов

Вместо того чтобы искать ошибки по логам:
- Все ошибки автоматически **группируются**
- Видно **частоту** (100 раз за час!)
- **Контекст** (какой юзер, какой запрос)
- **Алерт** если новая ошибка

### 🔧 Пример (Sentry)

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://xxx@sentry.io/123",
    traces_sample_rate=0.1,
    environment="production",
)

# Автоматический capture через middleware
# или ручной:
try:
    process_payment(order)
except PaymentError as e:
    sentry_sdk.capture_exception(e)
    sentry_sdk.set_context("order", {"id": order.id, "total": order.total})
    raise
```

---

## Сводная таблица

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY PATTERNS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Паттерн            │ Вопрос              │ Инструменты                    │
│  ───────────────────│─────────────────────│────────────────────────────────│
│                     │                     │                                 │
│  Distributed        │ "Как прошёл         │ Jaeger, Zipkin, Logfire,       │
│  Tracing            │  запрос?"           │ Datadog APM                    │
│                     │                     │                                 │
│  Log Aggregation    │ "Что произошло?"    │ ELK, Loki, CloudWatch          │
│                     │                     │                                 │
│  Metrics            │ "Сколько/какой?"    │ Prometheus, Datadog,           │
│                     │                     │ CloudWatch                     │
│                     │                     │                                 │
│  Health Checks      │ "Сервис жив?"       │ Kubernetes probes,             │
│                     │                     │ Load Balancer checks           │
│                     │                     │                                 │
│  Audit Logging      │ "Кто что сделал?"   │ Custom (DB/ELK)               │
│                     │                     │                                 │
│  Exception Tracking │ "Какие ошибки?"     │ Sentry, Rollbar, Bugsnag       │
│                     │                     │                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Чеклист Observability

```markdown
## Observability Checklist

### Distributed Tracing
- [ ] Trace ID в каждом запросе
- [ ] Context propagation между сервисами
- [ ] Sampling настроен (не 100% в prod)
- [ ] Интеграция с UI (Jaeger/Grafana)

### Logging
- [ ] Structured logging (JSON)
- [ ] Log levels (debug/info/warn/error)
- [ ] Correlation ID (trace_id) в логах
- [ ] Centralized storage

### Metrics
- [ ] RED metrics (Rate, Errors, Duration)
- [ ] Business metrics
- [ ] Dashboards в Grafana
- [ ] Alerts настроены

### Health Checks
- [ ] /health endpoint
- [ ] /ready endpoint с проверкой зависимостей
- [ ] Kubernetes probes настроены
- [ ] Alerting на downtime

### Audit & Exceptions
- [ ] Audit log для критичных операций
- [ ] Exception tracking (Sentry)
- [ ] Alerting на новые ошибки
```

---

<div align="center">

[← Discovery](./06-discovery-patterns.md) | **Observability** | [Resilience →](./08-resilience-patterns.md)

</div>
