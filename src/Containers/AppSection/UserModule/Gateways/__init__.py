"""Gateways for UserModule inter-module communication.

This package contains gateway protocols and adapters for
communicating with other modules/services.

Architecture (Ports & Adapters):
- Gateways (Ports): Protocol interfaces defined by UserModule
- Adapters: Implementations for different transport mechanisms

Available Gateways:
- PaymentGateway: Communication with PaymentModule

Usage:
    # In UserModule Action
    @dataclass
    class CreateSubscriptionAction(Action[...]):
        payment_gateway: PaymentGateway  # Injected by Dishka
        
        async def run(self, data: ...) -> Result[...]:
            result = await self.payment_gateway.create_payment(...)

See Also:
    - Types.py: DTOs for gateway operations
    - PaymentGateway.py: Payment gateway protocol
    - Adapters/: Gateway implementations
"""

from src.Containers.AppSection.UserModule.Gateways.PaymentGateway import (
    PaymentGateway,
)
from src.Containers.AppSection.UserModule.Gateways.Types import (
    # Payment Gateway Types
    PaymentRequest,
    PaymentResult,
    PaymentStatus,
    PaymentStatusRequest,
    RefundRequest,
    RefundResult,
    # Errors
    PaymentGatewayError,
    PaymentGatewayConnectionError,
    PaymentGatewayTimeoutError,
    PaymentDeclinedError,
    PaymentNotFoundError,
    RefundNotAllowedError,
)

__all__ = [
    # Gateway Protocols
    "PaymentGateway",
    # Payment Types
    "PaymentRequest",
    "PaymentResult",
    "PaymentStatus",
    "PaymentStatusRequest",
    "RefundRequest",
    "RefundResult",
    # Errors
    "PaymentGatewayError",
    "PaymentGatewayConnectionError",
    "PaymentGatewayTimeoutError",
    "PaymentDeclinedError",
    "PaymentNotFoundError",
    "RefundNotAllowedError",
]
