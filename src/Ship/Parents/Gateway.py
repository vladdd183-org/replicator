"""Base Gateway classes for inter-module communication.

Module Gateway Pattern implements Ports & Adapters (Hexagonal Architecture)
for synchronous cross-module communication in Hyper-Porto.

Key Concepts:
- Gateway (Port): Protocol/interface defined by consumer module
- Adapter: Implementation of gateway for specific transport (Direct/HTTP)
- Consumer defines the contract, provider implements adapters

Why Gateways?
- Events are great for async, fire-and-forget scenarios
- But sometimes you need synchronous response (e.g., check payment status)
- Gateway provides clean abstraction with swappable implementations
- Monolith → Microservices: just switch adapter, no business logic changes

Architecture:
- Consumer Module defines Gateway Protocol and DTOs
- Direct Adapter: calls provider module's Actions directly (monolith)
- HTTP Adapter: calls provider module's API via HTTP (microservices)
- Future adapters: gRPC, Message Queue with reply, etc.

Usage Pattern:
    # In UserModule (consumer)
    class PaymentGateway(Protocol):
        async def create_payment(self, data: PaymentRequest) -> Result[PaymentResult, PaymentError]: ...
    
    # In Providers
    @provide
    def payment_gateway(self, settings: Settings) -> PaymentGateway:
        if settings.deployment_mode == "microservices":
            return HttpPaymentAdapter(...)
        return DirectPaymentAdapter(...)

Example:
    @dataclass
    class CreateOrderAction(Action[CreateOrderRequest, Order, OrderError]):
        payment_gateway: PaymentGateway  # Injected by Dishka
        
        async def run(self, data: CreateOrderRequest) -> Result[Order, OrderError]:
            payment_result = await self.payment_gateway.create_payment(
                PaymentRequest(user_id=data.user_id, amount=data.total)
            )
            match payment_result:
                case Success(payment):
                    # Continue with order creation
                    ...
                case Failure(error):
                    return Failure(OrderPaymentFailedError(reason=str(error)))
"""

from abc import ABC, abstractmethod
from typing import Generic, Protocol, TypeVar, runtime_checkable

from returns.result import Result

# Type variables for generic Gateway
RequestT = TypeVar("RequestT", contravariant=True)
ResponseT = TypeVar("ResponseT", covariant=True)
ErrorT = TypeVar("ErrorT", covariant=True)


@runtime_checkable
class GatewayProtocol(Protocol):
    """Base protocol marker for all gateways.
    
    All gateway protocols should be runtime_checkable to allow
    isinstance() checks for debugging and validation.
    
    This is a marker protocol - specific gateways define their own methods.
    """
    
    pass


class BaseGateway(ABC, Generic[RequestT, ResponseT, ErrorT]):
    """Abstract base class for gateway implementations.
    
    Provides common functionality for all gateway adapters:
    - Logging hooks
    - Error mapping helpers
    - Circuit breaker integration points
    
    Subclasses implement the actual communication logic.
    
    Type Parameters:
        RequestT: Input data type for gateway operations
        ResponseT: Success response type
        ErrorT: Error type for failures
    
    Example:
        class PaymentGatewayBase(BaseGateway[PaymentRequest, PaymentResult, PaymentError]):
            async def _pre_call(self, method: str, request: PaymentRequest) -> None:
                # Logging, metrics, etc.
                pass
    """
    
    async def _pre_call(self, method: str, request: RequestT) -> None:
        """Hook called before gateway operation.
        
        Override for logging, metrics, tracing, etc.
        
        Args:
            method: Name of the gateway method being called
            request: Request data
        """
        pass
    
    async def _post_call(
        self,
        method: str,
        request: RequestT,
        result: Result[ResponseT, ErrorT],
    ) -> None:
        """Hook called after gateway operation.
        
        Override for logging, metrics, tracing, etc.
        
        Args:
            method: Name of the gateway method that was called
            request: Original request data
            result: Result of the operation
        """
        pass
    
    async def _on_error(self, method: str, request: RequestT, error: Exception) -> ErrorT:
        """Hook for handling unexpected errors.
        
        Override to map transport-specific errors to domain errors.
        
        Args:
            method: Name of the gateway method that failed
            request: Original request data
            error: Exception that was raised
            
        Returns:
            Domain error to wrap in Failure
        """
        raise error


class DirectAdapterBase(BaseGateway[RequestT, ResponseT, ErrorT]):
    """Base class for direct (in-process) gateway adapters.
    
    Direct adapters call provider module's Actions directly.
    Used in monolith deployment mode.
    
    Benefits:
    - Zero network overhead
    - Full type safety at compile time
    - Transaction sharing possible (if needed)
    
    Responsibilities:
    - Map consumer DTOs → provider DTOs
    - Call provider Action
    - Map provider result → consumer DTOs
    
    Example:
        @dataclass
        class DirectPaymentAdapter(DirectAdapterBase[PaymentRequest, PaymentResult, PaymentError]):
            create_payment_action: CreatePaymentAction  # From PaymentModule
            
            async def create_payment(self, request: PaymentRequest) -> Result[PaymentResult, PaymentError]:
                # Map request
                provider_request = CreatePaymentRequest(
                    user_id=request.user_id,
                    amount=request.amount,
                )
                # Call action
                result = await self.create_payment_action.run(provider_request)
                # Map result
                return result.map(lambda p: PaymentResult(payment_id=p.id, status=p.status))
    """
    
    pass


class HttpAdapterBase(BaseGateway[RequestT, ResponseT, ErrorT]):
    """Base class for HTTP gateway adapters.
    
    HTTP adapters call provider module's API via HTTP.
    Used in microservices deployment mode.
    
    Benefits:
    - Service isolation
    - Independent scaling
    - Technology agnostic
    
    Responsibilities:
    - Serialize request to JSON
    - Make HTTP call with proper headers/auth
    - Handle HTTP errors (timeouts, 4xx, 5xx)
    - Deserialize response
    - Map HTTP errors to domain errors
    
    Configuration (via Settings):
    - base_url: Service URL
    - timeout: Request timeout
    - retry_config: Retry policy
    - auth_config: Authentication method
    
    Example:
        @dataclass
        class HttpPaymentAdapter(HttpAdapterBase[PaymentRequest, PaymentResult, PaymentError]):
            base_url: str
            client: httpx.AsyncClient
            
            async def create_payment(self, request: PaymentRequest) -> Result[PaymentResult, PaymentError]:
                try:
                    response = await self.client.post(
                        f"{self.base_url}/api/v1/payments",
                        json=request.model_dump(),
                    )
                    response.raise_for_status()
                    return Success(PaymentResult.model_validate(response.json()))
                except httpx.HTTPError as e:
                    return Failure(self._map_http_error(e))
    """
    
    @abstractmethod
    def _get_base_url(self) -> str:
        """Get base URL for HTTP calls.
        
        Returns:
            Base URL string (e.g., "http://payment-service:8080")
        """
        ...
    
    def _get_default_headers(self) -> dict[str, str]:
        """Get default headers for HTTP calls.
        
        Override to add authentication, tracing, etc.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def _get_timeout(self) -> float:
        """Get timeout for HTTP calls in seconds.
        
        Override to customize timeout.
        
        Returns:
            Timeout in seconds
        """
        return 30.0


class GrpcAdapterBase(BaseGateway[RequestT, ResponseT, ErrorT]):
    """Base class for gRPC gateway adapters.
    
    gRPC adapters call provider module via gRPC protocol.
    Used for high-performance microservices communication.
    
    Benefits:
    - Binary protocol (faster than JSON)
    - Strongly typed contracts (protobuf)
    - Bidirectional streaming support
    - Built-in load balancing
    
    Note: This is a placeholder for future gRPC support.
    Implement when gRPC integration is needed.
    """
    
    pass


# Type aliases for common patterns
GatewayResult = Result[ResponseT, ErrorT]


__all__ = [
    "GatewayProtocol",
    "BaseGateway",
    "DirectAdapterBase",
    "HttpAdapterBase",
    "GrpcAdapterBase",
    "GatewayResult",
]
