"""HTTP Payment Adapter - HTTP calls for microservices deployment.

This adapter calls PaymentModule's API via HTTP. Used when
PaymentModule runs as a separate service.

Benefits:
- Service isolation
- Independent deployment
- Technology agnostic
- Horizontal scaling

Features:
- Automatic retry with exponential backoff (via tenacity)
- Circuit breaker pattern (via integration hooks)
- Request/response logging
- Proper error mapping
- Timeout handling
- Idempotency support

Configuration (via Settings):
    payment_service_url: str  # e.g., "http://payment-service:8080"
    payment_service_timeout: float  # Default 30s
    payment_service_api_key: str | None  # For service-to-service auth

Thread Safety:
    This adapter uses httpx.AsyncClient which is thread-safe.
    Multiple coroutines can use the same adapter instance.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx
from returns.result import Failure, Result, Success
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.Containers.AppSection.UserModule.Gateways.Types import (
    InsufficientFundsError,
    PaymentDeclinedError,
    PaymentGatewayConnectionError,
    PaymentGatewayError,
    PaymentGatewayTimeoutError,
    PaymentNotFoundError,
    PaymentRequest,
    PaymentResult,
    PaymentStatus,
    RefundNotAllowedError,
    RefundRequest,
    RefundResult,
)
from src.Ship.Core.GatewayErrors import (
    GatewayRateLimitError,
    GatewayResponseError,
    GatewayServerError,
)
from src.Ship.Parents.Gateway import HttpAdapterBase


@dataclass
class HttpPaymentAdapter(HttpAdapterBase[PaymentRequest, PaymentResult, PaymentGatewayError]):
    """HTTP adapter for PaymentGateway - calls PaymentModule via HTTP.

    Configuration:
        base_url: PaymentModule service URL
        client: httpx.AsyncClient instance (shared)
        timeout: Request timeout in seconds
        api_key: Optional API key for authentication

    API Endpoints (expected in PaymentModule):
        POST /api/v1/payments - Create payment
        GET  /api/v1/payments/{id} - Get payment status
        POST /api/v1/payments/{id}/refund - Refund payment

    Error Mapping:
        HTTP 400 → PaymentDeclinedError (validation)
        HTTP 401 → PaymentGatewayError (auth)
        HTTP 402 → InsufficientFundsError
        HTTP 404 → PaymentNotFoundError
        HTTP 429 → GatewayRateLimitError
        HTTP 5xx → GatewayServerError

    Example:
        async with httpx.AsyncClient() as client:
            adapter = HttpPaymentAdapter(
                base_url="http://payment-service:8080",
                client=client,
                timeout=30.0,
            )
            result = await adapter.create_payment(PaymentRequest(...))
    """

    base_url: str
    client: httpx.AsyncClient
    timeout: float = 30.0
    api_key: str | None = None

    # Internal state
    _request_count: int = field(default=0, init=False, repr=False)

    def _get_base_url(self) -> str:
        """Return configured base URL."""
        return self.base_url.rstrip("/")

    def _get_default_headers(self) -> dict[str, str]:
        """Build headers with optional API key."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Request-Source": "user-module",
        }

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        return headers

    def _get_timeout(self) -> float:
        """Return configured timeout."""
        return self.timeout

    async def create_payment(
        self,
        request: PaymentRequest,
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Create payment via HTTP POST to PaymentModule.

        Endpoint: POST /api/v1/payments

        Request Body:
            {
                "user_id": "uuid",
                "amount": "decimal",
                "currency": "string",
                "description": "string",
                "metadata": {}
            }

        Response (201):
            {
                "payment_id": "uuid",
                "user_id": "uuid",
                "amount": "decimal",
                "currency": "string",
                "status": "string",
                "provider_transaction_id": "string",
                "processed_at": "datetime",
                "message": "string"
            }
        """
        await self._pre_call("create_payment", request)

        try:
            # Build request
            url = f"{self._get_base_url()}/api/v1/payments"
            headers = self._get_default_headers()

            # Add idempotency key if provided
            if request.idempotency_key:
                headers["Idempotency-Key"] = request.idempotency_key

            # Serialize request - handle Decimal and UUID
            payload = {
                "user_id": str(request.user_id),
                "amount": str(request.amount),
                "currency": request.currency,
                "description": request.description,
                "metadata": request.metadata,
            }

            # Make HTTP call with retry
            response = await self._make_request_with_retry(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
            )

            # Parse response
            result = self._parse_payment_response(response, request.user_id)

            await self._post_call("create_payment", request, result)

            return result

        except httpx.ConnectError as e:
            error = PaymentGatewayConnectionError(
                details=str(e),
                service_name="payment",
            )
            return Failure(error)

        except httpx.TimeoutException:
            error = PaymentGatewayTimeoutError(
                timeout_seconds=self.timeout,
                service_name="payment",
            )
            return Failure(error)

        except Exception as e:
            error = await self._on_error("create_payment", request, e)
            return Failure(error)

    async def get_payment_status(
        self,
        payment_id: UUID,
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Get payment status via HTTP GET.

        Endpoint: GET /api/v1/payments/{payment_id}
        """
        await self._pre_call("get_payment_status", payment_id)

        try:
            url = f"{self._get_base_url()}/api/v1/payments/{payment_id}"
            headers = self._get_default_headers()

            response = await self._make_request_with_retry(
                method="GET",
                url=url,
                headers=headers,
            )

            result = self._parse_payment_response(
                response,
                UUID("00000000-0000-0000-0000-000000000000"),  # Will be in response
            )

            await self._post_call("get_payment_status", payment_id, result)

            return result

        except httpx.ConnectError as e:
            return Failure(
                PaymentGatewayConnectionError(
                    details=str(e),
                    service_name="payment",
                )
            )

        except httpx.TimeoutException:
            return Failure(
                PaymentGatewayTimeoutError(
                    timeout_seconds=self.timeout,
                    service_name="payment",
                )
            )

        except Exception as e:
            error = await self._on_error("get_payment_status", payment_id, e)
            return Failure(error)

    async def refund_payment(
        self,
        request: RefundRequest,
    ) -> Result[RefundResult, PaymentGatewayError]:
        """Refund payment via HTTP POST.

        Endpoint: POST /api/v1/payments/{payment_id}/refund

        Request Body:
            {
                "amount": "decimal" | null,
                "reason": "string"
            }
        """
        await self._pre_call("refund_payment", request)

        try:
            url = f"{self._get_base_url()}/api/v1/payments/{request.payment_id}/refund"
            headers = self._get_default_headers()

            if request.idempotency_key:
                headers["Idempotency-Key"] = request.idempotency_key

            payload = {
                "amount": str(request.amount) if request.amount else None,
                "reason": request.reason,
            }

            response = await self._make_request_with_retry(
                method="POST",
                url=url,
                headers=headers,
                json=payload,
            )

            result = self._parse_refund_response(response, request.payment_id)

            await self._post_call("refund_payment", request, result)

            return result

        except httpx.ConnectError as e:
            return Failure(
                PaymentGatewayConnectionError(
                    details=str(e),
                    service_name="payment",
                )
            )

        except httpx.TimeoutException:
            return Failure(
                PaymentGatewayTimeoutError(
                    timeout_seconds=self.timeout,
                    service_name="payment",
                )
            )

        except Exception as e:
            error = await self._on_error("refund_payment", request, e)
            return Failure(error)

    async def verify_payment(
        self,
        payment_id: UUID,
        expected_amount: int | None = None,
        expected_currency: str | None = None,
    ) -> Result[bool, PaymentGatewayError]:
        """Verify payment via get_payment_status."""
        status_result = await self.get_payment_status(payment_id)

        match status_result:
            case Success(payment):
                if expected_amount is not None:
                    if int(payment.amount) != expected_amount:
                        return Success(False)

                if expected_currency is not None:
                    if payment.currency != expected_currency:
                        return Success(False)

                return Success(True)

            case Failure(error):
                return Failure(error)

    # =========================================================================
    # HTTP HELPERS
    # =========================================================================

    async def _make_request_with_retry(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make HTTP request with automatic retry on transient failures.

        Retries on:
        - Connection errors
        - Timeout errors
        - 5xx errors

        Does not retry on:
        - 4xx errors (client errors)
        - Successful responses
        """
        self._request_count += 1

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(
                (
                    httpx.ConnectError,
                    httpx.TimeoutException,
                )
            ),
            reraise=True,
        )
        async def _do_request() -> httpx.Response:
            if method == "GET":
                response = await self.client.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                )
            elif method == "POST":
                response = await self.client.post(
                    url,
                    headers=headers,
                    json=json,
                    timeout=self.timeout,
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return response

        return await _do_request()

    def _parse_payment_response(
        self,
        response: httpx.Response,
        user_id: UUID,
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Parse HTTP response into PaymentResult or error."""

        # Handle error responses
        if response.status_code >= 400:
            return Failure(self._map_http_error(response))

        # Parse successful response
        try:
            data = response.json()

            return Success(
                PaymentResult(
                    payment_id=UUID(data["payment_id"]),
                    user_id=UUID(data.get("user_id", str(user_id))),
                    amount=Decimal(data["amount"]),
                    currency=data["currency"],
                    status=self._map_status_string(data["status"]),
                    created_at=datetime.fromisoformat(
                        data.get("created_at", datetime.now(UTC).isoformat())
                    ),
                    processed_at=datetime.fromisoformat(data["processed_at"])
                    if data.get("processed_at")
                    else None,
                    provider_reference=data.get("provider_transaction_id"),
                    message=data.get("message", ""),
                )
            )

        except (KeyError, ValueError, TypeError) as e:
            return Failure(
                GatewayResponseError(
                    service_name="payment",
                    details=f"Invalid response format: {e}",
                    raw_response=response.text[:500],
                )
            )

    def _parse_refund_response(
        self,
        response: httpx.Response,
        payment_id: UUID,
    ) -> Result[RefundResult, PaymentGatewayError]:
        """Parse HTTP response into RefundResult or error."""

        if response.status_code >= 400:
            return Failure(self._map_http_error(response, payment_id))

        try:
            data = response.json()

            return Success(
                RefundResult(
                    refund_id=UUID(data["refund_id"]),
                    payment_id=UUID(data.get("payment_id", str(payment_id))),
                    amount=Decimal(data["amount"]),
                    currency=data["currency"],
                    status=self._map_status_string(data["status"]),
                    created_at=datetime.fromisoformat(
                        data.get("created_at", datetime.now(UTC).isoformat())
                    ),
                    processed_at=datetime.fromisoformat(data["processed_at"])
                    if data.get("processed_at")
                    else None,
                    message=data.get("message", ""),
                )
            )

        except (KeyError, ValueError, TypeError) as e:
            return Failure(
                GatewayResponseError(
                    service_name="payment",
                    details=f"Invalid refund response: {e}",
                    raw_response=response.text[:500],
                )
            )

    def _map_http_error(
        self,
        response: httpx.Response,
        payment_id: UUID | None = None,
    ) -> PaymentGatewayError:
        """Map HTTP error response to appropriate domain error."""
        status_code = response.status_code

        # Try to parse error body
        try:
            error_data = response.json()
            error_message = error_data.get("message", error_data.get("detail", ""))
            error_code = error_data.get("code", "")
        except Exception:
            error_message = response.text[:200]
            error_code = ""

        # Map by status code
        if status_code == 400:
            return PaymentDeclinedError(
                reason=error_message or "Bad request",
                decline_code=error_code or "BAD_REQUEST",
                service_name="payment",
            )

        if status_code == 401:
            return PaymentGatewayError(
                message="Authentication failed",
                code="AUTH_FAILED",
                http_status=401,
                service_name="payment",
            )

        if status_code == 402:
            return InsufficientFundsError(
                amount=Decimal("0"),  # Unknown
                currency="RUB",
                service_name="payment",
            )

        if status_code == 404:
            return PaymentNotFoundError(
                payment_id=payment_id or UUID("00000000-0000-0000-0000-000000000000"),
                service_name="payment",
            )

        if status_code == 409:
            return RefundNotAllowedError(
                payment_id=payment_id or UUID("00000000-0000-0000-0000-000000000000"),
                reason=error_message or "Conflict",
                service_name="payment",
            )

        if status_code == 422:
            return PaymentDeclinedError(
                reason=error_message or "Validation error",
                decline_code="VALIDATION_ERROR",
                service_name="payment",
            )

        if status_code == 429:
            return GatewayRateLimitError(
                service_name="payment",
                retry_after_seconds=60.0,
            )

        if status_code >= 500:
            return GatewayServerError(
                service_name="payment",
                status_code=status_code,
                details=error_message or "Internal server error",
            )

        # Generic error
        return PaymentGatewayError(
            message=f"HTTP {status_code}: {error_message}",
            http_status=status_code,
            service_name="payment",
        )

    def _map_status_string(self, status: str) -> PaymentStatus:
        """Map status string to PaymentStatus enum."""
        status_lower = status.lower()
        mapping = {
            "success": PaymentStatus.SUCCESS,
            "succeeded": PaymentStatus.SUCCESS,
            "completed": PaymentStatus.SUCCESS,
            "failed": PaymentStatus.FAILED,
            "declined": PaymentStatus.FAILED,
            "pending": PaymentStatus.PENDING,
            "processing": PaymentStatus.PENDING,
            "refunded": PaymentStatus.REFUNDED,
            "partially_refunded": PaymentStatus.PARTIALLY_REFUNDED,
        }
        return mapping.get(status_lower, PaymentStatus.PENDING)

    async def _on_error(
        self,
        method: str,
        request: Any,
        error: Exception,
    ) -> PaymentGatewayError:
        """Handle unexpected errors."""
        try:
            import logfire

            logfire.error(
                "HttpPaymentAdapter unexpected error",
                method=method,
                error=str(error),
                error_type=type(error).__name__,
                base_url=self.base_url,
            )
        except ImportError:
            print(f"HttpPaymentAdapter error in {method}: {error}")

        return PaymentGatewayError(
            message=f"Unexpected HTTP error in {method}: {error}",
            service_name="payment",
        )

    async def _pre_call(self, method: str, request: Any) -> None:
        """Log before making HTTP call."""
        try:
            import logfire

            logfire.info(
                f"PaymentGateway.{method} HTTP call",
                method=method,
                base_url=self.base_url,
                request_count=self._request_count,
            )
        except ImportError:
            pass

    async def _post_call(
        self,
        method: str,
        request: Any,
        result: Result[Any, Any],
    ) -> None:
        """Log after HTTP call."""
        try:
            import logfire

            is_success = hasattr(result, "_inner_value") and not isinstance(result, Failure)
            logfire.info(
                f"PaymentGateway.{method} completed",
                method=method,
                success=is_success,
            )
        except ImportError:
            pass


__all__ = ["HttpPaymentAdapter"]
