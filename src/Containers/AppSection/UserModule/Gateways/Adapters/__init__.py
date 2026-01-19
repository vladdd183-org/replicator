"""Gateway Adapters for UserModule.

Adapters implement gateway protocols for different transport mechanisms.

Available Adapters:
- DirectPaymentAdapter: Direct calls to PaymentModule (monolith)
- HttpPaymentAdapter: HTTP calls to PaymentModule (microservices)

Adapter Selection:
    Adapters are selected at DI configuration time based on
    deployment mode (settings.deployment_mode).

    # In Providers.py
    @provide
    def payment_gateway(self, settings: Settings) -> PaymentGateway:
        if settings.deployment_mode == "microservices":
            return HttpPaymentAdapter(...)
        return DirectPaymentAdapter(...)

Adding New Adapters:
    1. Create adapter class implementing PaymentGateway
    2. Add to __init__.py exports
    3. Add selection logic in Providers.py

    Examples: GrpcPaymentAdapter, AmqpPaymentAdapter, etc.
"""

from src.Containers.AppSection.UserModule.Gateways.Adapters.DirectPaymentAdapter import (
    DirectPaymentAdapter,
)
from src.Containers.AppSection.UserModule.Gateways.Adapters.HttpPaymentAdapter import (
    HttpPaymentAdapter,
)

__all__ = [
    "DirectPaymentAdapter",
    "HttpPaymentAdapter",
]
