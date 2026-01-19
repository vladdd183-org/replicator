"""Gateways for UserModule inter-module communication.

This package contains gateway protocols and adapters for
communicating with other modules/services.

Architecture (Ports & Adapters) - Consumer Owns Interface:
- Gateways (Ports): Protocol interfaces defined by UserModule
- Types: DTOs and Errors defined by UserModule (NOT from PaymentModule)
- Adapters: Implementations for different transport mechanisms

IMPORTANT:
    UserModule defines its OWN types (PaymentRequest, PaymentResult, etc.)
    Adapters are responsible for mapping between UserModule and PaymentModule types.
    This ensures loose coupling - changes in PaymentModule don't break UserModule.

Available Gateways:
- PaymentGateway: Communication with PaymentModule

Available Adapters:
- DirectPaymentAdapter: Direct calls for monolith deployment
- HttpPaymentAdapter: HTTP calls for microservices deployment

Usage:
    # In UserModule Action
    @dataclass
    class CreateSubscriptionAction(Action[...]):
        payment_gateway: PaymentGateway  # Injected by Dishka

        async def run(self, data: ...) -> Result[...]:
            result = await self.payment_gateway.create_payment(...)

See Also:
    - docs/14-module-gateway-pattern.md: Gateway pattern documentation
    - Types.py: DTOs for gateway operations
    - PaymentGateway.py: Payment gateway protocol
    - Adapters/: Gateway implementations
"""

# Gateway Protocol
from src.Containers.AppSection.UserModule.Gateways.PaymentGateway import (
    PaymentGateway,
)

# Types - DTOs and Errors (UserModule's own types!)
from src.Containers.AppSection.UserModule.Gateways.Types import (
    # Enums
    Currency,
    PaymentStatus,
    # Request DTOs
    PaymentRequest,
    PaymentStatusRequest,
    RefundRequest,
    # Response DTOs
    PaymentResult,
    RefundResult,
    # Errors
    InsufficientFundsError,
    PaymentDeclinedError,
    PaymentGatewayConnectionError,
    PaymentGatewayError,
    PaymentGatewayTimeoutError,
    PaymentNotFoundError,
    RefundNotAllowedError,
)

# Adapters - implementations for different deployment modes
from src.Containers.AppSection.UserModule.Gateways.Adapters.DirectPaymentAdapter import (
    DirectPaymentAdapter,
)
from src.Containers.AppSection.UserModule.Gateways.Adapters.HttpPaymentAdapter import (
    HttpPaymentAdapter,
)

__all__ = [
    # Gateway Protocol
    "PaymentGateway",
    # Adapters
    "DirectPaymentAdapter",
    "HttpPaymentAdapter",
    # Enums
    "Currency",
    "PaymentStatus",
    # Request DTOs
    "PaymentRequest",
    "PaymentStatusRequest",
    "RefundRequest",
    # Response DTOs
    "PaymentResult",
    "RefundResult",
    # Errors
    "PaymentGatewayError",
    "PaymentGatewayConnectionError",
    "PaymentGatewayTimeoutError",
    "PaymentDeclinedError",
    "PaymentNotFoundError",
    "RefundNotAllowedError",
    "InsufficientFundsError",
]
