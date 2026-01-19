# 🌉 Module Gateway Pattern

> **Версия:** 4.3 | **Дата:** Январь 2026

Синхронная межмодульная коммуникация через **Ports & Adapters** (Hexagonal Architecture).

---

## 📋 Содержание

1. [Проблема прямой связи](#-проблема-прямой-связи)
2. [Когда использовать Gateway](#-когда-использовать-gateway)
3. [Архитектура паттерна](#-архитектура-паттерна)
4. [Ключевые принципы](#-ключевые-принципы)
5. [Структура файлов](#-структура-файлов)
6. [Реализация компонентов](#-реализация-компонентов)
7. [DI конфигурация](#-di-конфигурация)
8. [Использование в Action](#-использование-в-action)
9. [Обработка ошибок](#-обработка-ошибок)
10. [Direct vs HTTP Adapter](#-direct-vs-http-adapter)
11. [Best Practices](#-best-practices)
12. [Миграция: Монолит → Микросервисы](#-миграция-монолит--микросервисы)
13. [Тестирование](#-тестирование)
14. [Альтернативные паттерны](#-альтернативные-паттерны)
15. [Сводная таблица паттернов](#-сводная-таблица-паттернов)
16. [Чеклист внедрения](#-чеклист-внедрения)

---

## 🛑 Проблема прямой связи

В монолите часто возникает соблазн просто импортировать класс из соседнего модуля:

```python
# ❌ ПЛОХО: Жёсткая связь (Tight Coupling)
from src.Containers.VendorSection.PaymentModule.Actions.ProcessPaymentAction import ProcessPaymentAction

class CreateOrderAction(Action):
    def __init__(self, payment_action: ProcessPaymentAction):
        self.payment_action = payment_action
```

**Почему это плохо:**

| Проблема | Описание |
|----------|----------|
| **Refactoring Hell** | Изменения в `PaymentModule` ломают `OrderModule` |
| **Monolith Lock** | Невозможно вынести модуль в микросервис без переписывания |
| **Testing** | Трудно мокать зависимости |
| **Нарушение Porto** | Прямые импорты между секциями запрещены |

---

## 🎯 Когда использовать Gateway

Events хороши для асинхронных сценариев "fire-and-forget", но иногда нужен **синхронный ответ**:

| Сценарий | Events | Gateway |
|----------|--------|---------|
| Отправить уведомление | ✅ | ❌ |
| Записать в аудит-лог | ✅ | ❌ |
| Проверить права доступа | ❌ | ✅ |
| Создать платёж и получить статус | ❌ | ✅ |
| Получить данные из другого модуля | ❌ | ✅ |
| Валидация данных в реальном времени | ❌ | ✅ |

**Правило:** Если нужен **немедленный результат** для продолжения бизнес-логики — используй Gateway.

---

## 🏗️ Архитектура паттерна

```
┌─────────────────────────────────────────────────────────────────────┐
│                       OrderModule (Consumer)                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   PaymentGateway (Protocol)                     │ │
│  │  - create_payment()                                             │ │
│  │  - get_payment_status()                                         │ │
│  │  - refund_payment()                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                               │                                      │
│               ┌───────────────┴───────────────┐                     │
│               ▼                               ▼                     │
│  ┌──────────────────────┐       ┌────────────────────────────────┐ │
│  │ DirectPaymentAdapter │       │     HttpPaymentAdapter         │ │
│  │   (Monolith mode)    │       │    (Microservices mode)        │ │
│  └──────────────────────┘       └────────────────────────────────┘ │
│               │                               │                     │
└───────────────│───────────────────────────────│─────────────────────┘
                │                               │
                ▼                               ▼
   ┌──────────────────────┐       ┌────────────────────────────────┐
   │    PaymentModule     │       │       PaymentService           │
   │ CreatePaymentAction  │       │    POST /api/v1/payments       │
   └──────────────────────┘       └────────────────────────────────┘
```

**Суть паттерна:** Модуль-потребитель (Consumer) определяет **интерфейс (Port)** того, что ему нужно. Модуль-провайдер или внешний сервис реализует этот интерфейс через **Adapter**.

---

## 🔑 Ключевые принципы

### 1. Consumer Owns the Interface

**Модуль-потребитель** (OrderModule) определяет интерфейс Gateway:

```python
# OrderModule/Gateways/PaymentGateway.py
from typing import Protocol, runtime_checkable
from returns.result import Result

@runtime_checkable
class PaymentGateway(Protocol):
    """Интерфейс определяет OrderModule, а не PaymentModule!"""
    
    async def create_payment(
        self, request: PaymentRequest
    ) -> Result[PaymentResult, PaymentGatewayError]: ...
    
    async def get_payment_status(
        self, payment_id: UUID
    ) -> Result[PaymentStatus, PaymentGatewayError]: ...
    
    async def refund_payment(
        self, payment_id: UUID, reason: str
    ) -> Result[RefundResult, PaymentGatewayError]: ...
```

**Это обеспечивает:**

- **Dependency Inversion**: высокоуровневый модуль не зависит от низкоуровневого
- **Loose Coupling**: изменения в PaymentModule не затрагивают интерфейс
- **Easy Testing**: легко мокать в тестах
- **Независимая эволюция**: Consumer и Provider развиваются независимо

### 2. Own Types (DTOs)

Consumer определяет **свои** типы данных:

```python
# OrderModule/Gateways/Types.py
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentRequest(BaseModel):
    """OrderModule's view of payment request."""
    user_id: UUID
    amount: Decimal
    currency: str = "RUB"
    order_id: UUID
    idempotency_key: str | None = None  # Для безопасных ретраев

class PaymentResult(BaseModel):
    """OrderModule's view of payment result."""
    payment_id: UUID
    status: PaymentStatus
    transaction_id: str | None = None
```

**Почему не использовать типы PaymentModule?**

- Consumer знает только то, что **ему нужно**
- Внутренние поля PaymentModule **скрыты**
- **Независимая эволюция** схем
- Защита от **breaking changes** провайдера

### 3. Adapter Mapping

Адаптеры отвечают за маппинг типов между Consumer и Provider:

```python
# DirectPaymentAdapter
def _map_to_payment_data(self, request: PaymentRequest) -> PaymentModulePaymentData:
    """OrderModule DTO → PaymentModule DTO"""
    return PaymentModulePaymentData(
        user_id=request.user_id,
        amount=request.amount,
        currency=request.currency,
        external_order_id=str(request.order_id),
    )

def _map_from_payment_result(
    self, result: PaymentModulePaymentResult
) -> PaymentResult:
    """PaymentModule result → OrderModule DTO"""
    return PaymentResult(
        payment_id=result.payment_id,
        status=self._map_status(result.status),
        transaction_id=result.external_transaction_id,
    )

def _map_status(self, status: PaymentModuleStatus) -> PaymentStatus:
    """Маппинг статусов между модулями"""
    mapping = {
        PaymentModuleStatus.CREATED: PaymentStatus.PENDING,
        PaymentModuleStatus.COMPLETED: PaymentStatus.SUCCESS,
        PaymentModuleStatus.REJECTED: PaymentStatus.FAILED,
    }
    return mapping.get(status, PaymentStatus.PENDING)
```

---

## 📁 Структура файлов

```
OrderModule/
├── Actions/
│   └── CreateOrderAction.py      # Использует PaymentGateway
├── ...
└── Gateways/
    ├── __init__.py               # Экспорты
    ├── Types.py                  # DTOs: PaymentRequest, PaymentResult, Errors
    ├── PaymentGateway.py         # Protocol (интерфейс)
    └── Adapters/
        ├── __init__.py
        ├── DirectPaymentAdapter.py   # Монолит: прямые вызовы Action
        └── HttpPaymentAdapter.py     # Микросервисы: HTTP REST
```

**Пример `__init__.py`:**

```python
# OrderModule/Gateways/__init__.py
from src.Containers.AppSection.OrderModule.Gateways.PaymentGateway import PaymentGateway
from src.Containers.AppSection.OrderModule.Gateways.Types import (
    PaymentRequest,
    PaymentResult,
    PaymentStatus,
    PaymentGatewayError,
    PaymentDeclinedError,
    PaymentNotFoundError,
)
from src.Containers.AppSection.OrderModule.Gateways.Adapters.DirectPaymentAdapter import (
    DirectPaymentAdapter,
)
from src.Containers.AppSection.OrderModule.Gateways.Adapters.HttpPaymentAdapter import (
    HttpPaymentAdapter,
)

__all__ = [
    "PaymentGateway",
    "PaymentRequest",
    "PaymentResult",
    "PaymentStatus",
    "PaymentGatewayError",
    "PaymentDeclinedError",
    "PaymentNotFoundError",
    "DirectPaymentAdapter",
    "HttpPaymentAdapter",
]
```

---

## 🔧 Реализация компонентов

### 1. Protocol (Интерфейс)

```python
# OrderModule/Gateways/PaymentGateway.py
from typing import Protocol, runtime_checkable
from uuid import UUID
from returns.result import Result

from src.Containers.AppSection.OrderModule.Gateways.Types import (
    PaymentRequest,
    PaymentResult,
    PaymentGatewayError,
    PaymentStatus,
    RefundResult,
)

@runtime_checkable
class PaymentGateway(Protocol):
    """
    Порт для взаимодействия с платёжной системой.
    
    Определяется модулем-потребителем (OrderModule).
    Реализуется адаптерами для разных режимов развёртывания.
    """
    
    async def create_payment(
        self, request: PaymentRequest
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Создать платёж."""
        ...
    
    async def get_payment_status(
        self, payment_id: UUID
    ) -> Result[PaymentStatus, PaymentGatewayError]:
        """Получить статус платежа."""
        ...
    
    async def refund_payment(
        self, payment_id: UUID,
        reason: str,
    ) -> Result[RefundResult, PaymentGatewayError]:
        """Выполнить возврат платежа."""
        ...
```

### 2. Types (DTOs и Errors)

```python
# OrderModule/Gateways/Types.py
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
from enum import Enum
from typing import ClassVar

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate

# === Enums ===

class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

# === Request DTOs ===

class PaymentRequest(BaseModel):
    """Запрос на создание платежа."""
    model_config = {"frozen": True}
    
    user_id: UUID
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="RUB", pattern=r"^[A-Z]{3}$")
    order_id: UUID
    description: str | None = None
    idempotency_key: str | None = None

# === Response DTOs ===

class PaymentResult(BaseModel):
    """Результат создания платежа."""
    model_config = {"frozen": True}
    
    payment_id: UUID
    status: PaymentStatus
    transaction_id: str | None = None
    created_at: datetime | None = None

class RefundResult(BaseModel):
    """Результат возврата платежа."""
    model_config = {"frozen": True}
    
    refund_id: UUID
    payment_id: UUID
    amount: Decimal
    status: str

# === Errors ===

class PaymentGatewayError(BaseError):
    """Базовая ошибка PaymentGateway."""
    code: str = "PAYMENT_GATEWAY_ERROR"
    service_name: str = "payment"

class PaymentDeclinedError(ErrorWithTemplate, PaymentGatewayError):
    """Платёж отклонён."""
    _message_template: ClassVar[str] = "Payment declined: {reason}"
    code: str = "PAYMENT_DECLINED"
    http_status: int = 422
    reason: str

class PaymentNotFoundError(ErrorWithTemplate, PaymentGatewayError):
    """Платёж не найден."""
    _message_template: ClassVar[str] = "Payment {payment_id} not found"
    code: str = "PAYMENT_NOT_FOUND"
    http_status: int = 404
    payment_id: UUID

class InsufficientFundsError(ErrorWithTemplate, PaymentGatewayError):
    """Недостаточно средств."""
    _message_template: ClassVar[str] = "Insufficient funds for amount {amount}"
    code: str = "INSUFFICIENT_FUNDS"
    http_status: int = 422
    amount: Decimal

class PaymentGatewayConnectionError(PaymentGatewayError):
    """Ошибка соединения с платёжной системой."""
    code: str = "PAYMENT_CONNECTION_ERROR"
    http_status: int = 503
    message: str = "Payment service unavailable"

class PaymentGatewayTimeoutError(PaymentGatewayError):
    """Таймаут при обращении к платёжной системе."""
    code: str = "PAYMENT_TIMEOUT"
    http_status: int = 504
    message: str = "Payment service timeout"
```

### 3. DirectAdapter (Монолит)

```python
# OrderModule/Gateways/Adapters/DirectPaymentAdapter.py
from dataclasses import dataclass
from uuid import UUID
from returns.result import Result, Success, Failure

from src.Containers.AppSection.OrderModule.Gateways.PaymentGateway import PaymentGateway
from src.Containers.AppSection.OrderModule.Gateways.Types import (
    PaymentRequest,
    PaymentResult,
    PaymentStatus,
    PaymentGatewayError,
    PaymentDeclinedError,
    PaymentNotFoundError,
    RefundResult,
)

# Импорты из PaymentModule (только в адаптере!)
from src.Containers.VendorSection.PaymentModule.Actions.CreatePaymentAction import (
    CreatePaymentAction,
)
from src.Containers.VendorSection.PaymentModule.Actions.GetPaymentAction import (
    GetPaymentAction,
)
from src.Containers.VendorSection.PaymentModule.Actions.RefundPaymentAction import (
    RefundPaymentAction,
)
from src.Containers.VendorSection.PaymentModule.Data.Schemas import (
    CreatePaymentRequest as PaymentModuleRequest,
)
from src.Containers.VendorSection.PaymentModule.Errors import (
    PaymentError as PaymentModuleError,
    PaymentNotFoundError as PaymentModuleNotFoundError,
    PaymentDeclinedError as PaymentModuleDeclinedError,
)

import logfire

@dataclass
class DirectPaymentAdapter:
    """
    Адаптер для монолитного режима.
    
    Вызывает Actions из PaymentModule напрямую в том же процессе.
    Все зависимости инжектируются через Dishka.
    """
    
    create_payment_action: CreatePaymentAction
    get_payment_action: GetPaymentAction
    refund_payment_action: RefundPaymentAction
    
    async def create_payment(
        self, request: PaymentRequest
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Создать платёж через PaymentModule."""
        logfire.info(
            "DirectPaymentAdapter.create_payment",
            order_id=str(request.order_id),
            amount=float(request.amount),
        )
        
        # Маппинг: OrderModule DTO → PaymentModule DTO
        payment_module_request = self._map_to_payment_module_request(request)
        
        # Вызов Action
        result = await self.create_payment_action.run(payment_module_request)
        
        # Маппинг результата: PaymentModule → OrderModule
        match result:
            case Success(payment):
                return Success(self._map_to_payment_result(payment))
            case Failure(error):
                return Failure(self._map_error(error))
    
    async def get_payment_status(
        self, payment_id: UUID
    ) -> Result[PaymentStatus, PaymentGatewayError]:
        """Получить статус платежа."""
        result = await self.get_payment_action.run(payment_id)
        
        match result:
            case Success(payment):
                return Success(self._map_status(payment.status))
            case Failure(error):
                return Failure(self._map_error(error))
    
    async def refund_payment(
        self, payment_id: UUID,
        reason: str,
    ) -> Result[RefundResult, PaymentGatewayError]:
        """Выполнить возврат платежа."""
        result = await self.refund_payment_action.run(payment_id, reason)
        
        match result:
            case Success(refund):
                return Success(RefundResult(
                    refund_id=refund.id,
                    payment_id=refund.payment_id,
                    amount=refund.amount,
                    status=refund.status,
                ))
            case Failure(error):
                return Failure(self._map_error(error))
    
    # === Private Mapping Methods ===
    
    def _map_to_payment_module_request(
        self, request: PaymentRequest
    ) -> PaymentModuleRequest:
        """OrderModule DTO → PaymentModule DTO"""
        return PaymentModuleRequest(
            user_id=request.user_id,
            amount=request.amount,
            currency=request.currency,
            external_order_id=str(request.order_id),
            description=request.description,
            idempotency_key=request.idempotency_key,
        )
    
    def _map_to_payment_result(self, payment) -> PaymentResult:
        """PaymentModule entity → OrderModule DTO"""
        return PaymentResult(
            payment_id=payment.id,
            status=self._map_status(payment.status),
            transaction_id=payment.transaction_id,
            created_at=payment.created_at,
        )
    
    def _map_status(self, status) -> PaymentStatus:
        """PaymentModule status → OrderModule status"""
        status_mapping = {
            "created": PaymentStatus.PENDING,
            "pending": PaymentStatus.PENDING,
            "completed": PaymentStatus.SUCCESS,
            "success": PaymentStatus.SUCCESS,
            "failed": PaymentStatus.FAILED,
            "rejected": PaymentStatus.FAILED,
            "refunded": PaymentStatus.REFUNDED,
        }
        return status_mapping.get(str(status).lower(), PaymentStatus.PENDING)
    
    def _map_error(self, error: PaymentModuleError) -> PaymentGatewayError:
        """PaymentModule error → OrderModule error"""
        match error:
            case PaymentModuleNotFoundError():
                return PaymentNotFoundError(payment_id=error.payment_id)
            case PaymentModuleDeclinedError():
                return PaymentDeclinedError(reason=error.reason)
            case _:
                return PaymentGatewayError(message=str(error))
```

### 4. HttpAdapter (Микросервисы)

```python
# OrderModule/Gateways/Adapters/HttpPaymentAdapter.py
from dataclasses import dataclass
from uuid import UUID
import httpx
from returns.result import Result, Success, Failure

from src.Containers.AppSection.OrderModule.Gateways.PaymentGateway import PaymentGateway
from src.Containers.AppSection.OrderModule.Gateways.Types import (
    PaymentRequest,
    PaymentResult,
    PaymentStatus,
    PaymentGatewayError,
    PaymentDeclinedError,
    PaymentNotFoundError,
    PaymentGatewayConnectionError,
    PaymentGatewayTimeoutError,
    RefundResult,
)

import logfire

@dataclass
class HttpPaymentAdapter:
    """
    Адаптер для микросервисного режима.
    
    Обращается к PaymentService через HTTP REST API.
    """
    
    base_url: str
    client: httpx.AsyncClient
    api_key: str | None = None
    timeout: float = 30.0
    
    async def create_payment(
        self, request: PaymentRequest
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Создать платёж через HTTP API."""
        logfire.info(
            "HttpPaymentAdapter.create_payment",
            base_url=self.base_url,
            order_id=str(request.order_id),
        )
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/payments",
                json={
                    "user_id": str(request.user_id),
                    "amount": str(request.amount),
                    "currency": request.currency,
                    "order_id": str(request.order_id),
                    "description": request.description,
                    "idempotency_key": request.idempotency_key,
                },
                headers=self._get_headers(request.idempotency_key),
                timeout=self.timeout,
            )
            
            return self._handle_response(response)
            
        except httpx.ConnectError as e:
            logfire.error("Payment service connection error", error=str(e))
            return Failure(PaymentGatewayConnectionError())
        except httpx.TimeoutException as e:
            logfire.error("Payment service timeout", error=str(e))
            return Failure(PaymentGatewayTimeoutError())
        except httpx.HTTPError as e:
            logfire.error("Payment service HTTP error", error=str(e))
            return Failure(PaymentGatewayError(message=str(e)))
    
    async def get_payment_status(
        self, payment_id: UUID
    ) -> Result[PaymentStatus, PaymentGatewayError]:
        """Получить статус платежа через HTTP API."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/payments/{payment_id}",
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            
            if response.status_code == 404:
                return Failure(PaymentNotFoundError(payment_id=payment_id))
            
            response.raise_for_status()
            data = response.json()
            return Success(PaymentStatus(data["status"]))
            
        except httpx.ConnectError:
            return Failure(PaymentGatewayConnectionError())
        except httpx.TimeoutException:
            return Failure(PaymentGatewayTimeoutError())
        except httpx.HTTPError as e:
            return Failure(PaymentGatewayError(message=str(e)))
    
    async def refund_payment(
        self, payment_id: UUID,
        reason: str,
    ) -> Result[RefundResult, PaymentGatewayError]:
        """Выполнить возврат через HTTP API."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/payments/{payment_id}/refund",
                json={"reason": reason},
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            
            if response.status_code == 404:
                return Failure(PaymentNotFoundError(payment_id=payment_id))
            
            response.raise_for_status()
            data = response.json()
            
            return Success(RefundResult(
                refund_id=UUID(data["refund_id"]),
                payment_id=UUID(data["payment_id"]),
                amount=Decimal(data["amount"]),
                status=data["status"],
            ))
            
        except httpx.ConnectError:
            return Failure(PaymentGatewayConnectionError())
        except httpx.TimeoutException:
            return Failure(PaymentGatewayTimeoutError())
        except httpx.HTTPError as e:
            return Failure(PaymentGatewayError(message=str(e)))
    
    # === Private Methods ===
    
    def _get_headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        """Сформировать заголовки запроса."""
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        
        return headers
    
    def _handle_response(
        self, response: httpx.Response
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Обработать HTTP ответ."""
        if response.status_code == 201:
            data = response.json()
            return Success(PaymentResult(
                payment_id=UUID(data["id"]),
                status=PaymentStatus(data["status"]),
                transaction_id=data.get("transaction_id"),
            ))
        
        if response.status_code == 422:
            data = response.json()
            error_code = data.get("code", "")
            
            if error_code == "PAYMENT_DECLINED":
                return Failure(PaymentDeclinedError(reason=data.get("reason", "Unknown")))
            if error_code == "INSUFFICIENT_FUNDS":
                return Failure(InsufficientFundsError(amount=Decimal(data.get("amount", 0))))
        
        if response.status_code == 404:
            return Failure(PaymentNotFoundError(payment_id=UUID("00000000-0000-0000-0000-000000000000")))
        
        return Failure(PaymentGatewayError(
            message=f"Unexpected response: {response.status_code}"
        ))
```

---

## ⚙️ DI конфигурация

Gateway выбирается на основе `deployment_mode` в настройках:

### Settings

```python
# Ship/Configs/Settings.py
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # Deployment
    deployment_mode: Literal["monolith", "microservices"] = "monolith"
    
    # Payment Service (для микросервисов)
    payment_service_url: str = "http://localhost:8001"
    payment_service_api_key: str | None = None
    payment_service_timeout: float = 30.0
    
    @property
    def is_microservices(self) -> bool:
        return self.deployment_mode == "microservices"
```

### Providers

```python
# OrderModule/Providers.py
from dishka import Provider, Scope, provide
import httpx

from src.Ship.Configs.Settings import Settings
from src.Containers.AppSection.OrderModule.Gateways import (
    PaymentGateway,
    DirectPaymentAdapter,
    HttpPaymentAdapter,
)
from src.Containers.VendorSection.PaymentModule.Actions.CreatePaymentAction import (
    CreatePaymentAction,
)
from src.Containers.VendorSection.PaymentModule.Actions.GetPaymentAction import (
    GetPaymentAction,
)
from src.Containers.VendorSection.PaymentModule.Actions.RefundPaymentAction import (
    RefundPaymentAction,
)


class OrderGatewayProvider(Provider):
    """Провайдер Gateway для OrderModule."""
    
    scope = Scope.REQUEST
    
    @provide
    def provide_payment_gateway(
        self,
        settings: Settings,
        # Зависимости для DirectAdapter (игнорируются в microservices mode)
        create_payment_action: CreatePaymentAction | None = None,
        get_payment_action: GetPaymentAction | None = None,
        refund_payment_action: RefundPaymentAction | None = None,
        # HTTP клиент (игнорируется в monolith mode)
        http_client: httpx.AsyncClient | None = None,
    ) -> PaymentGateway:
        """
        Выбор адаптера на основе deployment_mode.
        
        - monolith: DirectPaymentAdapter (прямые вызовы)
        - microservices: HttpPaymentAdapter (HTTP REST)
        """
        if settings.is_microservices:
            if http_client is None:
                http_client = httpx.AsyncClient()
            
            return HttpPaymentAdapter(
                base_url=settings.payment_service_url,
                client=http_client,
                api_key=settings.payment_service_api_key,
                timeout=settings.payment_service_timeout,
            )
        
        # Monolith mode
        return DirectPaymentAdapter(
            create_payment_action=create_payment_action,
            get_payment_action=get_payment_action,
            refund_payment_action=refund_payment_action,
        )
```

### Альтернатива: Явная регистрация

```python
# Простой вариант без условной логики
class OrderMonolithProvider(Provider):
    """Для монолита."""
    scope = Scope.REQUEST
    payment_gateway = provide(DirectPaymentAdapter, provides=PaymentGateway)

class OrderMicroservicesProvider(Provider):
    """Для микросервисов."""
    scope = Scope.REQUEST
    payment_gateway = provide(HttpPaymentAdapter, provides=PaymentGateway)

# В App.py выбираем нужный провайдер
if settings.is_microservices:
    container.register_provider(OrderMicroservicesProvider)
else:
    container.register_provider(OrderMonolithProvider)
```

---

## 🎬 Использование в Action

```python
# OrderModule/Actions/CreateOrderAction.py
from dataclasses import dataclass
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.OrderModule.Data.Schemas import (
    CreateOrderRequest,
    OrderResponse,
)
from src.Containers.AppSection.OrderModule.Data.UnitOfWork import OrderUnitOfWork
from src.Containers.AppSection.OrderModule.Errors import (
    OrderError,
    OrderPaymentFailedError,
    OrderServiceUnavailableError,
)
from src.Containers.AppSection.OrderModule.Gateways import (
    PaymentGateway,
    PaymentRequest,
    PaymentDeclinedError,
    PaymentGatewayConnectionError,
    InsufficientFundsError,
)
from src.Containers.AppSection.OrderModule.Models.Order import Order

@dataclass
class CreateOrderAction(Action[CreateOrderRequest, Order, OrderError]):
    """
    Создание заказа с оплатой.
    
    Использует PaymentGateway для создания платежа.
    Не зависит от конкретной реализации (Direct/HTTP).
    """
    
    payment_gateway: PaymentGateway  # Protocol, не конкретный адаптер!
    uow: OrderUnitOfWork
    
    async def run(self, data: CreateOrderRequest) -> Result[Order, OrderError]:
        # 1. Создаём заказ в статусе "pending_payment"
        order = Order(
            user_id=data.user_id,
            items=data.items,
            total_amount=self._calculate_total(data.items),
            status="pending_payment",
        )
        
        # 2. Создаём платёж через Gateway
        payment_result = await self.payment_gateway.create_payment(
            PaymentRequest(
                user_id=data.user_id,
                amount=order.total_amount,
                currency="RUB",
                order_id=order.id,
                idempotency_key=f"order-{order.id}",
            )
        )
        
        # 3. Обрабатываем результат платежа
        match payment_result:
            case Success(payment):
                # Платёж успешен — сохраняем заказ
                order.payment_id = payment.payment_id
                order.status = "paid" if payment.status == "success" else "pending_payment"
                
                async with self.uow:
                    await self.uow.orders.add(order)
                    await self.uow.commit()
                
                return Success(order)
            
            case Failure(PaymentDeclinedError() as e):
                return Failure(OrderPaymentFailedError(
                    order_id=order.id,
                    reason=e.reason,
                ))
            
            case Failure(InsufficientFundsError() as e):
                return Failure(OrderPaymentFailedError(
                    order_id=order.id,
                    reason=f"Insufficient funds for {e.amount}",
                ))
            
            case Failure(PaymentGatewayConnectionError()):
                return Failure(OrderServiceUnavailableError(
                    service="payment",
                    message="Payment service is temporarily unavailable",
                ))
            
            case Failure(error):
                return Failure(OrderPaymentFailedError(
                    order_id=order.id,
                    reason=str(error),
                ))
    
    def _calculate_total(self, items: list) -> Decimal:
        return sum(item.price * item.quantity for item in items)
```

---

## ⚠️ Обработка ошибок

### Иерархия ошибок

```
GatewayError (Ship/Core)
├── GatewayConnectionError      # Сеть недоступна
├── GatewayTimeoutError         # Таймаут
└── GatewayServerError          # 5xx ответы

PaymentGatewayError (Consumer)
├── PaymentDeclinedError        # Платёж отклонён
├── PaymentNotFoundError        # Платёж не найден
├── InsufficientFundsError      # Недостаточно средств
├── PaymentGatewayConnectionError  # extends GatewayConnectionError
└── PaymentGatewayTimeoutError     # extends GatewayTimeoutError
```

### Базовые Gateway Errors

```python
# Ship/Core/GatewayErrors.py
from src.Ship.Core.Errors import BaseError

class GatewayError(BaseError):
    """Базовая ошибка для всех Gateway."""
    service_name: str
    code: str = "GATEWAY_ERROR"

class GatewayConnectionError(GatewayError):
    """Ошибка соединения с внешним сервисом."""
    code: str = "GATEWAY_CONNECTION_ERROR"
    http_status: int = 503

class GatewayTimeoutError(GatewayError):
    """Таймаут при обращении к внешнему сервису."""
    code: str = "GATEWAY_TIMEOUT"
    http_status: int = 504

class GatewayServerError(GatewayError):
    """Внутренняя ошибка внешнего сервиса (5xx)."""
    code: str = "GATEWAY_SERVER_ERROR"
    http_status: int = 502
```

### Маппинг ошибок в адаптере

```python
def _map_error(self, error: PaymentModuleError) -> PaymentGatewayError:
    """Маппинг ошибок провайдера в Consumer domain errors."""
    match error:
        case PaymentModuleNotFoundError():
            return PaymentNotFoundError(payment_id=error.payment_id)
        case PaymentModuleDeclinedError():
            return PaymentDeclinedError(reason=error.reason)
        case PaymentModuleInsufficientFundsError():
            return InsufficientFundsError(amount=error.amount)
        case _:
            # Fallback для неизвестных ошибок
            return PaymentGatewayError(message=str(error))
```

---

## ⚖️ Direct vs HTTP Adapter

| Аспект | DirectAdapter | HttpAdapter |
|--------|---------------|-------------|
| **Транспорт** | In-process call | HTTP/REST |
| **Latency** | ~0ms | 1-100ms+ |
| **Failures** | Exception | Network errors |
| **Transactions** | Shared possible | Separate |
| **Deployment** | Same process | Separate service |
| **Scaling** | Together | Independent |
| **Dependencies** | Import Actions | Only HTTP client |

### DirectAdapter Flow

```
OrderModule.CreateOrderAction
    → DirectPaymentAdapter.create_payment()
        → map OrderModule.PaymentRequest → PaymentModule.CreatePaymentRequest
        → PaymentModule.CreatePaymentAction.run()
        → map PaymentModule.Payment → OrderModule.PaymentResult
    → Result[PaymentResult, PaymentGatewayError]
```

### HttpAdapter Flow

```
OrderModule.CreateOrderAction
    → HttpPaymentAdapter.create_payment()
        → serialize PaymentRequest to JSON
        → POST http://payment-service/api/v1/payments
        → parse JSON response
        → deserialize to PaymentResult
    → Result[PaymentResult, PaymentGatewayError]
```

---

## 💡 Best Practices

### 1. Minimal Interface

Определяй только методы, которые **реально нужны**:

```python
# ❌ Слишком много методов — Interface Segregation violation
class PaymentGateway(Protocol):
    async def create_payment(): ...
    async def get_payment(): ...
    async def list_payments(): ...    # Нужен ли?
    async def update_payment(): ...   # Нужен ли?
    async def delete_payment(): ...   # Зачем?
    async def get_statistics(): ...   # Это вообще другой домен

# ✅ Только необходимое для Consumer
class PaymentGateway(Protocol):
    async def create_payment(): ...
    async def get_payment_status(): ...
    async def refund_payment(): ...
```

### 2. Idempotency

Всегда поддерживай idempotency для операций изменения:

```python
class PaymentRequest(BaseModel):
    # Для безопасных ретраев при сетевых проблемах
    idempotency_key: str | None = None

# В адаптере
headers["Idempotency-Key"] = request.idempotency_key
```

### 3. Error Mapping

Маппь ошибки провайдера в **свои domain errors**:

```python
def _map_error(self, error: PaymentModuleError) -> PaymentGatewayError:
    """Никогда не пробрасывай ошибки провайдера напрямую!"""
    match error:
        case PaymentModuleNotFoundError():
            return PaymentNotFoundError(payment_id=error.payment_id)
        case PaymentModuleInsufficientFundsError():
            return InsufficientFundsError(amount=error.amount)
        case _:
            return PaymentGatewayError(message=str(error))
```

### 4. Logging & Tracing

Добавляй логирование в адаптеры:

```python
import logfire

async def create_payment(self, request: PaymentRequest) -> Result[...]:
    # Pre-call logging
    logfire.info(
        "PaymentGateway.create_payment starting",
        order_id=str(request.order_id),
        amount=float(request.amount),
    )
    
    result = await self._do_create_payment(request)
    
    # Post-call logging
    logfire.info(
        "PaymentGateway.create_payment completed",
        success=result.is_success(),
    )
    
    return result
```

### 5. Retry & Circuit Breaker

Для HttpAdapter добавляй retry и circuit breaker:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class HttpPaymentAdapter:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _do_request(self, method: str, url: str, **kwargs):
        return await self.client.request(method, url, **kwargs)
```

---

## 🚀 Миграция: Монолит → Микросервисы

Gateway Pattern делает миграцию **бесшовной**:

### Шаг 1: Монолит (начальное состояние)

```yaml
# .env
DEPLOYMENT_MODE=monolith
```

```
┌────────────────────────────────────────┐
│              Monolith                   │
│  ┌──────────────┐  ┌────────────────┐  │
│  │ OrderModule  │→ │ PaymentModule  │  │
│  │ (Direct)     │  │                │  │
│  └──────────────┘  └────────────────┘  │
└────────────────────────────────────────┘
```

### Шаг 2: Выделение PaymentModule

1. Создай HTTP API в PaymentModule
2. Разверни PaymentModule как отдельный сервис
3. Переключи режим:

```yaml
# .env
DEPLOYMENT_MODE=microservices
PAYMENT_SERVICE_URL=http://payment-service:8080
PAYMENT_SERVICE_API_KEY=secret
```

```
┌──────────────────┐      HTTP      ┌──────────────────┐
│   OrderModule    │ ───────────────│ PaymentService   │
│   (HttpAdapter)  │                │ (standalone)     │
└──────────────────┘                └──────────────────┘
```

### Шаг 3: Готово!

**OrderModule продолжает работать без изменений кода!**

Только конфигурация определяет режим работы.

---

## 🧪 Тестирование

### Unit Tests с Mock Gateway

```python
# tests/unit/order/test_create_order_action.py
import pytest
from uuid import uuid4
from decimal import Decimal
from returns.result import Success, Failure

from src.Containers.AppSection.OrderModule.Actions.CreateOrderAction import (
    CreateOrderAction,
)
from src.Containers.AppSection.OrderModule.Gateways import (
    PaymentGateway,
    PaymentRequest,
    PaymentResult,
    PaymentStatus,
    PaymentDeclinedError,
)


class MockPaymentGateway:
    """Mock для unit-тестов."""
    
    def __init__(self, should_succeed: bool = True, error: Exception | None = None):
        self.should_succeed = should_succeed
        self.error = error
        self.calls: list[PaymentRequest] = []
    
    async def create_payment(
        self, request: PaymentRequest
    ) -> Result[PaymentResult, PaymentGatewayError]:
        self.calls.append(request)
        
        if self.error:
            return Failure(self.error)
        
        if self.should_succeed:
            return Success(PaymentResult(
                payment_id=uuid4(),
                status=PaymentStatus.SUCCESS,
                transaction_id="txn_123",
            ))
        
        return Failure(PaymentDeclinedError(reason="Declined by bank"))
    
    async def get_payment_status(self, payment_id):
        return Success(PaymentStatus.SUCCESS)
    
    async def refund_payment(self, payment_id, reason):
        return Success(RefundResult(...))


class TestCreateOrderAction:
    @pytest.fixture
    def mock_gateway(self):
        return MockPaymentGateway()
    
    @pytest.fixture
    def mock_uow(self):
        return MockOrderUnitOfWork()
    
    async def test_successful_order_creation(self, mock_gateway, mock_uow):
        """Успешное создание заказа с оплатой."""
        action = CreateOrderAction(
            payment_gateway=mock_gateway,
            uow=mock_uow,
        )
        
        request = CreateOrderRequest(
            user_id=uuid4(),
            items=[OrderItem(product_id=uuid4(), quantity=1, price=Decimal("100.00"))],
        )
        
        result = await action.run(request)
        
        assert result.is_success()
        assert len(mock_gateway.calls) == 1
        assert mock_gateway.calls[0].amount == Decimal("100.00")
    
    async def test_payment_declined(self, mock_uow):
        """Платёж отклонён — заказ не создаётся."""
        gateway = MockPaymentGateway(should_succeed=False)
        action = CreateOrderAction(payment_gateway=gateway, uow=mock_uow)
        
        result = await action.run(CreateOrderRequest(...))
        
        assert result.is_failure()
        assert isinstance(result.failure(), OrderPaymentFailedError)
    
    async def test_payment_service_unavailable(self, mock_uow):
        """Платёжный сервис недоступен."""
        gateway = MockPaymentGateway(
            error=PaymentGatewayConnectionError()
        )
        action = CreateOrderAction(payment_gateway=gateway, uow=mock_uow)
        
        result = await action.run(CreateOrderRequest(...))
        
        assert result.is_failure()
        assert isinstance(result.failure(), OrderServiceUnavailableError)
```

### Integration Tests

```python
# tests/integration/order/test_payment_gateway.py
import pytest
from src.Containers.AppSection.OrderModule.Gateways import (
    DirectPaymentAdapter,
    HttpPaymentAdapter,
)


@pytest.fixture
def direct_adapter(payment_module_actions):
    """Real DirectAdapter для интеграционных тестов."""
    return DirectPaymentAdapter(
        create_payment_action=payment_module_actions.create,
        get_payment_action=payment_module_actions.get,
        refund_payment_action=payment_module_actions.refund,
    )


@pytest.fixture
def http_adapter(test_payment_service_url):
    """Real HttpAdapter против тестового сервера."""
    return HttpPaymentAdapter(
        base_url=test_payment_service_url,
        client=httpx.AsyncClient(),
    )


class TestDirectPaymentAdapter:
    async def test_create_payment_success(self, direct_adapter):
        request = PaymentRequest(
            user_id=uuid4(),
            amount=Decimal("100.00"),
            order_id=uuid4(),
        )
        
        result = await direct_adapter.create_payment(request)
        
        assert result.is_success()
        assert result.unwrap().status == PaymentStatus.PENDING


class TestHttpPaymentAdapter:
    @pytest.mark.integration
    async def test_create_payment_success(self, http_adapter):
        request = PaymentRequest(
            user_id=uuid4(),
            amount=Decimal("100.00"),
            order_id=uuid4(),
        )
        
        result = await http_adapter.create_payment(request)
        
        assert result.is_success()
```

---

## 🔄 Альтернативные паттерны

### Data Replication (Event-Carried State Transfer)

**Философия:** "Не спрашивай данные у соседа, имей свою копию".

Используется, когда нужна **максимальная автономность** и скорость чтения.

```python
# OrderModule/Models/UserReplica.py
class UserReplica(Model):
    """Урезанная копия пользователя для OrderModule."""
    id = UUID(primary_key=True)
    email = Varchar()
    discount_percent = Integer()  # Специфичное для заказов

# OrderModule/Listeners.py
@listener("UserUpdated")
async def on_user_updated(user_id: str, email: str, **kwargs):
    """Обновляем локальную реплику при изменении User."""
    await UserReplica.update({
        UserReplica.email: email,
    }).where(UserReplica.id == UUID(user_id))
```

| ✅ Плюсы | ❌ Минусы |
|----------|-----------|
| **Zero Latency**: Читаем локальную БД | **Eventual Consistency**: Данные отстают |
| **High Availability**: Работаем автономно | **Storage**: Дублирование данных |

### RPC через TaskIQ

Использование брокера сообщений как транспорта для вызова функций:

```python
# PaymentModule регистрирует задачу
@broker.task(task_name="payment.get_balance")
async def get_balance(user_id: int) -> int:
    ...

# OrderModule вызывает и ждёт ответ
balance = await get_balance.kiq(user_id=123).wait_result()
```

Хороший компромисс, если лень писать HTTP-адаптеры, но хочется развязать код.

---

## ⚖️ Сводная таблица паттернов

| Паттерн | Связность | Сложность | Когда использовать |
|---------|-----------|-----------|-------------------|
| **Events** | ⭐ Низкая | ⭐ Низкая | Fire-and-forget (уведомления, логи, аудит) |
| **Module Gateway** | ⭐⭐ Средняя | ⭐⭐ Средняя | Нужен синхронный ответ (платежи, проверки) |
| **Data Replication** | ⭐ Низкая | ⭐⭐⭐ Высокая | Высокая нагрузка, полная автономность |
| **RPC (TaskIQ)** | ⭐⭐ Средняя | ⭐⭐ Средняя | Async с ожиданием результата |
| **Direct Import** | ❌ Высокая | ⭐ Низкая | **Никогда** в Production |

---

## ✅ Чеклист внедрения

### Создание Gateway

- [ ] Создать `Gateways/Types.py` с DTOs и Errors
- [ ] Создать `Gateways/XxxGateway.py` с Protocol
- [ ] Создать `Gateways/Adapters/DirectXxxAdapter.py`
- [ ] Создать `Gateways/Adapters/HttpXxxAdapter.py`
- [ ] Обновить `Gateways/__init__.py`

### Интеграция

- [ ] Добавить настройки в `Settings.py` (URLs, API keys, timeouts)
- [ ] Зарегистрировать в `Providers.py`
- [ ] Использовать Protocol в Action (не конкретный адаптер!)

### Качество

- [ ] Написать unit-тесты с MockGateway
- [ ] Написать integration-тесты для адаптеров
- [ ] Добавить логирование и tracing
- [ ] Реализовать idempotency для изменяющих операций
- [ ] Добавить retry logic для HttpAdapter
- [ ] Обновить документацию модуля

---

## 📚 Связанные документы

- [03-components.md](03-components.md) — Action, Task, Repository
- [04-result-railway.md](04-result-railway.md) — Result[T, E] и pattern matching
- [10-registration.md](10-registration.md) — Dishka DI
- [13-cross-module-communication.md](13-cross-module-communication.md) — Events и асинхронная коммуникация
- [17-microservice-extraction-guide.md](17-microservice-extraction-guide.md) — Выделение в микросервис

---

<div align="center">

**Hyper-Porto v4.3**

*Module Gateway Pattern — чистая синхронная межмодульная коммуникация*

</div>
