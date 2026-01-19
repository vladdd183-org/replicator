# Module Gateway Pattern

> Синхронная межмодульная коммуникация через Ports & Adapters

---

## Зачем нужны Gateway?

Events хороши для асинхронных сценариев "fire-and-forget", но иногда нужен **синхронный ответ**:

| Сценарий | Events | Gateway |
|----------|--------|---------|
| Отправить уведомление | ✅ | ❌ |
| Записать в аудит-лог | ✅ | ❌ |
| Проверить права доступа | ❌ | ✅ |
| Создать платёж и получить статус | ❌ | ✅ |
| Получить данные из другого модуля | ❌ | ✅ |

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        UserModule (Consumer)                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    PaymentGateway (Protocol)                │  │
│  │  - create_payment()                                         │  │
│  │  - get_payment_status()                                     │  │
│  │  - refund_payment()                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│              ┌───────────────┴───────────────┐                   │
│              ▼                               ▼                   │
│  ┌─────────────────────┐       ┌─────────────────────────────┐  │
│  │ DirectPaymentAdapter │       │   HttpPaymentAdapter        │  │
│  │   (Monolith mode)    │       │   (Microservices mode)      │  │
│  └─────────────────────┘       └─────────────────────────────┘  │
│              │                               │                   │
└──────────────│───────────────────────────────│───────────────────┘
               │                               │
               ▼                               ▼
    ┌─────────────────────┐       ┌─────────────────────────────┐
    │    PaymentModule    │       │      PaymentService         │
    │  CreatePaymentAction │       │   POST /api/v1/payments     │
    └─────────────────────┘       └─────────────────────────────┘
```

## Ключевые принципы

### 1. Consumer Owns the Interface

**Модуль-потребитель** (UserModule) определяет интерфейс Gateway:

```python
# UserModule/Gateways/PaymentGateway.py
@runtime_checkable
class PaymentGateway(Protocol):
    """Интерфейс определяет UserModule, а не PaymentModule!"""
    
    async def create_payment(
        self, request: PaymentRequest
    ) -> Result[PaymentResult, PaymentGatewayError]: ...
```

Это обеспечивает:
- **Dependency Inversion**: высокоуровневый модуль не зависит от низкоуровневого
- **Loose Coupling**: изменения в PaymentModule не затрагивают интерфейс
- **Easy Testing**: легко мокать в тестах

### 2. Own Types (DTOs)

Consumer определяет **свои** типы данных:

```python
# UserModule/Gateways/Types.py
class PaymentRequest(BaseModel):
    """UserModule's view of payment request."""
    user_id: UUID
    amount: Decimal
    currency: str

class PaymentResult(BaseModel):
    """UserModule's view of payment result."""
    payment_id: UUID
    status: PaymentStatus
```

**Почему не использовать типы PaymentModule?**
- Consumer знает только то, что ему нужно
- Внутренние поля PaymentModule скрыты
- Независимая эволюция схем

### 3. Adapter Mapping

Адаптеры отвечают за маппинг типов:

```python
# DirectPaymentAdapter
def _map_to_payment_data(self, request: PaymentRequest) -> PaymentModulePaymentData:
    """UserModule DTO → PaymentModule DTO"""
    return PaymentModulePaymentData(
        user_id=request.user_id,
        amount=request.amount,
        currency=request.currency,
    )

def _map_from_payment_result(self, result: PaymentModulePaymentResult) -> PaymentResult:
    """PaymentModule result → UserModule DTO"""
    return PaymentResult(
        payment_id=result.payment_id,
        status=self._map_status(result.status),
    )
```

## Структура файлов

```
UserModule/
├── Gateways/
│   ├── __init__.py              # Экспорты
│   ├── Types.py                 # DTOs и Errors
│   ├── PaymentGateway.py        # Protocol (интерфейс)
│   └── Adapters/
│       ├── __init__.py
│       ├── DirectPaymentAdapter.py   # Монолит: прямые вызовы
│       └── HttpPaymentAdapter.py     # Микросервисы: HTTP
```

## DI Configuration

Gateway выбирается на основе `deployment_mode`:

```python
# Settings.py
class Settings(BaseSettings):
    deployment_mode: Literal["monolith", "microservices"] = "monolith"
    payment_service_url: str = "http://localhost:8001"

# Providers.py
class UserGatewayProvider(Provider):
    @provide
    def provide_payment_gateway(
        self,
        settings: Settings,
        create_payment_action: CreatePaymentAction,  # For direct
        http_client: httpx.AsyncClient,              # For HTTP
    ) -> PaymentGateway:
        if settings.is_microservices:
            return HttpPaymentAdapter(
                base_url=settings.payment_service_url,
                client=http_client,
            )
        return DirectPaymentAdapter(
            create_payment_action=create_payment_action,
        )
```

## Использование в Action

```python
@dataclass
class CreateSubscriptionAction(Action[CreateSubscriptionRequest, SubscriptionResult, SubscriptionError]):
    payment_gateway: PaymentGateway  # Protocol, не конкретный адаптер!
    
    async def run(self, data: CreateSubscriptionRequest) -> Result[SubscriptionResult, SubscriptionError]:
        # Создаём платёж через gateway
        payment_result = await self.payment_gateway.create_payment(
            PaymentRequest(
                user_id=data.user_id,
                amount=calculate_price(data.plan),
                currency="RUB",
            )
        )
        
        # Обрабатываем результат
        match payment_result:
            case Success(payment):
                return await self._create_subscription(payment)
            case Failure(PaymentDeclinedError() as e):
                return Failure(SubscriptionPaymentFailedError(reason=e.reason))
            case Failure(PaymentGatewayConnectionError()):
                return Failure(SubscriptionServiceUnavailableError())
```

## Error Handling

### Gateway Errors (Infrastructure)

```python
# Ship/Core/GatewayErrors.py
class GatewayError(BaseError):
    """Base for all gateway errors"""
    service_name: str

class GatewayConnectionError(GatewayError): ...
class GatewayTimeoutError(GatewayError): ...
class GatewayServerError(GatewayError): ...
```

### Domain Errors (Consumer-specific)

```python
# UserModule/Gateways/Types.py
class PaymentGatewayError(GatewayError):
    """Base for PaymentGateway errors"""
    service_name: str = "payment"

class PaymentDeclinedError(PaymentGatewayError): ...
class PaymentNotFoundError(PaymentGatewayError): ...
class InsufficientFundsError(PaymentGatewayError): ...
```

## Direct vs HTTP Adapter

| Аспект | DirectAdapter | HttpAdapter |
|--------|---------------|-------------|
| Транспорт | In-process call | HTTP/REST |
| Latency | ~0ms | 1-100ms+ |
| Failures | Exception | Network errors |
| Transactions | Shared possible | Separate |
| Deployment | Same process | Separate service |

### DirectAdapter Flow

```
UserModule.Action
    → DirectPaymentAdapter.create_payment()
        → map UserModule.PaymentRequest → PaymentModule.PaymentData
        → PaymentModule.CreatePaymentAction.run()
        → map PaymentModule.PaymentResult → UserModule.PaymentResult
    → Result[PaymentResult, Error]
```

### HttpAdapter Flow

```
UserModule.Action
    → HttpPaymentAdapter.create_payment()
        → serialize PaymentRequest to JSON
        → POST http://payment-service/api/v1/payments
        → parse JSON response
        → deserialize to PaymentResult
    → Result[PaymentResult, Error]
```

## Best Practices

### 1. Minimal Interface

Определяй только методы, которые реально нужны:

```python
# ❌ Слишком много методов
class PaymentGateway(Protocol):
    async def create_payment(): ...
    async def get_payment(): ...
    async def list_payments(): ...  # Нужен ли?
    async def update_payment(): ...  # Нужен ли?
    async def delete_payment(): ...  # Зачем?

# ✅ Только необходимое
class PaymentGateway(Protocol):
    async def create_payment(): ...
    async def get_payment_status(): ...
    async def refund_payment(): ...
```

### 2. Idempotency

Всегда поддерживай idempotency для операций изменения:

```python
class PaymentRequest(BaseModel):
    idempotency_key: str | None = None  # Для безопасных ретраев
```

### 3. Error Mapping

Маппь ошибки провайдера в свои domain errors:

```python
def _map_payment_error(self, error: PaymentModuleError) -> PaymentGatewayError:
    match error:
        case PaymentModuleNotFoundError():
            return PaymentNotFoundError(payment_id=error.payment_id)
        case PaymentModuleInsufficientFundsError():
            return InsufficientFundsError(amount=error.amount)
        case _:
            return PaymentGatewayError(message=str(error))
```

### 4. Logging & Tracing

Добавляй логирование в adapter hooks:

```python
async def _pre_call(self, method: str, request: Any) -> None:
    logfire.info(f"PaymentGateway.{method} starting", request=request)

async def _post_call(self, method: str, request: Any, result: Result) -> None:
    logfire.info(f"PaymentGateway.{method} completed", success=is_success(result))
```

## Migration: Monolith → Microservices

1. **Изначально** используй `DirectAdapter` (монолит)
2. **При выделении** PaymentModule в сервис:
   - Создай HTTP API в PaymentModule
   - Переключи `deployment_mode: microservices`
   - UserModule продолжает работать без изменений!

```yaml
# .env для монолита
DEPLOYMENT_MODE=monolith

# .env для микросервисов
DEPLOYMENT_MODE=microservices
PAYMENT_SERVICE_URL=http://payment-service:8080
PAYMENT_SERVICE_API_KEY=secret
```

## Тестирование

### Мок Gateway для Unit Tests

```python
class MockPaymentGateway:
    async def create_payment(self, request: PaymentRequest) -> Result[PaymentResult, PaymentGatewayError]:
        return Success(PaymentResult(
            payment_id=uuid4(),
            user_id=request.user_id,
            amount=request.amount,
            status=PaymentStatus.SUCCESS,
        ))

# В тесте
action = CreateSubscriptionAction(
    payment_gateway=MockPaymentGateway(),
    uow=mock_uow,
)
result = await action.run(request)
assert result.is_success()
```

### Integration Tests

```python
@pytest.fixture
def payment_gateway(settings):
    """Real gateway for integration tests."""
    if settings.is_microservices:
        return HttpPaymentAdapter(...)
    return DirectPaymentAdapter(...)
```

## Checklist: Adding New Gateway

- [ ] Создать `Gateways/Types.py` с DTOs и Errors
- [ ] Создать `Gateways/XxxGateway.py` с Protocol
- [ ] Создать `Gateways/Adapters/DirectXxxAdapter.py`
- [ ] Создать `Gateways/Adapters/HttpXxxAdapter.py`
- [ ] Обновить `Gateways/__init__.py`
- [ ] Добавить настройки в `Settings.py`
- [ ] Зарегистрировать в `Providers.py`
- [ ] Написать тесты
- [ ] Обновить документацию

---

**Module Gateway Pattern** — чистый способ организации синхронной коммуникации между модулями с поддержкой миграции монолит → микросервисы.
