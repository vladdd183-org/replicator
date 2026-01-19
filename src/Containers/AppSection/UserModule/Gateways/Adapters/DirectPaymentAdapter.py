"""Direct Payment Adapter - in-process calls for monolith deployment.

This adapter calls PaymentModule's Actions directly, without any
network overhead. Used when both modules are in the same process.

Benefits:
- Zero network latency
- Full type safety
- Shared transaction context (if needed)
- No serialization overhead

Responsibilities:
1. Map UserModule DTOs → PaymentModule DTOs
2. Call PaymentModule Actions
3. Map PaymentModule results → UserModule DTOs
4. Map PaymentModule errors → UserModule errors

Important: Even in monolith mode, we maintain the abstraction.
This allows easy transition to microservices later.

Thread Safety:
    This adapter is stateless - safe for concurrent use.
    PaymentModule Actions handle their own thread safety.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from returns.result import Result, Success, Failure

from src.Ship.Parents.Gateway import DirectAdapterBase
from src.Containers.AppSection.UserModule.Gateways.Types import (
    PaymentRequest,
    PaymentResult,
    PaymentStatus,
    PaymentGatewayError,
    PaymentDeclinedError,
    PaymentNotFoundError,
    RefundRequest,
    RefundResult,
    RefundNotAllowedError,
    InsufficientFundsError,
)

# PaymentModule imports - only used in Direct adapter
from src.Containers.VendorSection.PaymentModule.Actions.CreatePaymentAction import (
    CreatePaymentAction,
)
from src.Containers.VendorSection.PaymentModule.Actions.RefundPaymentAction import (
    RefundPaymentAction,
    RefundRequest as PaymentModuleRefundRequest,
)
from src.Containers.VendorSection.PaymentModule.Tasks.ProcessPaymentTask import (
    PaymentData as PaymentModulePaymentData,
    PaymentResult as PaymentModulePaymentResult,
)
from src.Containers.VendorSection.PaymentModule.Errors import (
    PaymentError as PaymentModuleError,
    PaymentProcessingError,
    InvalidPaymentAmountError,
    InsufficientFundsError as PaymentModuleInsufficientFundsError,
    PaymentNotFoundError as PaymentModuleNotFoundError,
    RefundNotAllowedError as PaymentModuleRefundNotAllowedError,
)


@dataclass
class DirectPaymentAdapter(
    DirectAdapterBase[PaymentRequest, PaymentResult, PaymentGatewayError]
):
    """Direct adapter for PaymentGateway - calls PaymentModule in-process.
    
    Injected Dependencies:
        create_payment_action: CreatePaymentAction from PaymentModule
        refund_payment_action: RefundPaymentAction from PaymentModule
    
    Example:
        adapter = DirectPaymentAdapter(
            create_payment_action=create_payment_action,
            refund_payment_action=refund_payment_action,
        )
        result = await adapter.create_payment(PaymentRequest(...))
    """
    
    create_payment_action: CreatePaymentAction
    refund_payment_action: RefundPaymentAction
    
    async def create_payment(
        self,
        request: PaymentRequest,
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Create payment via direct call to PaymentModule.
        
        Mapping:
            UserModule.PaymentRequest → PaymentModule.PaymentData
            PaymentModule.PaymentResult → UserModule.PaymentResult
            PaymentModule.PaymentError → UserModule.PaymentGatewayError
        """
        # Pre-call hook (for logging, metrics)
        await self._pre_call("create_payment", request)
        
        try:
            # Map UserModule DTO → PaymentModule DTO
            payment_data = self._map_to_payment_data(request)
            
            # Call PaymentModule Action
            action_result = await self.create_payment_action.run(payment_data)
            
            # Map result back to UserModule types
            match action_result:
                case Success(payment_module_result):
                    user_result = self._map_from_payment_result(
                        payment_module_result,
                        request.user_id,
                    )
                    result = Success(user_result)
                    
                case Failure(error):
                    mapped_error = self._map_payment_error(error)
                    result = Failure(mapped_error)
            
            # Post-call hook
            await self._post_call("create_payment", request, result)
            
            return result
            
        except Exception as e:
            error = await self._on_error("create_payment", request, e)
            return Failure(error)
    
    async def get_payment_status(
        self,
        payment_id: UUID,
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Get payment status via direct call.
        
        Note: PaymentModule doesn't have a dedicated status query,
        so this is a simplified implementation. In real world,
        you would call PaymentModule.GetPaymentQuery.
        """
        await self._pre_call("get_payment_status", payment_id)
        
        # TODO: Implement when PaymentModule has GetPaymentQuery
        # For now, return not found as placeholder
        return Failure(PaymentNotFoundError(
            payment_id=payment_id,
            service_name="payment",
        ))
    
    async def refund_payment(
        self,
        request: RefundRequest,
    ) -> Result[RefundResult, PaymentGatewayError]:
        """Refund payment via direct call to PaymentModule.
        
        Mapping:
            UserModule.RefundRequest → PaymentModule.RefundRequest
            PaymentModule.RefundResult → UserModule.RefundResult
        """
        await self._pre_call("refund_payment", request)
        
        try:
            # Map UserModule DTO → PaymentModule DTO
            refund_data = PaymentModuleRefundRequest(
                payment_id=request.payment_id,
                user_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
                amount=request.amount or Decimal("0"),  # 0 = full refund
                currency="RUB",
                reason=request.reason,
            )
            
            # Call PaymentModule Action
            action_result = await self.refund_payment_action.run(refund_data)
            
            # Map result
            match action_result:
                case Success(refund_module_result):
                    user_result = RefundResult(
                        refund_id=refund_module_result.refund_id,
                        payment_id=refund_module_result.payment_id,
                        amount=refund_module_result.amount,
                        currency=refund_module_result.currency,
                        status=self._map_status(refund_module_result.status),
                        created_at=datetime.now(timezone.utc),
                        processed_at=refund_module_result.processed_at,
                        message=refund_module_result.message,
                    )
                    result = Success(user_result)
                    
                case Failure(error):
                    mapped_error = self._map_payment_error(error)
                    result = Failure(mapped_error)
            
            await self._post_call("refund_payment", request, result)
            
            return result
            
        except Exception as e:
            error = await self._on_error("refund_payment", request, e)
            return Failure(error)
    
    async def verify_payment(
        self,
        payment_id: UUID,
        expected_amount: int | None = None,
        expected_currency: str | None = None,
    ) -> Result[bool, PaymentGatewayError]:
        """Verify payment exists and matches expected parameters."""
        status_result = await self.get_payment_status(payment_id)
        
        match status_result:
            case Success(payment):
                # Check amount if expected
                if expected_amount is not None:
                    if int(payment.amount) != expected_amount:
                        return Success(False)
                
                # Check currency if expected
                if expected_currency is not None:
                    if payment.currency != expected_currency:
                        return Success(False)
                
                return Success(True)
                
            case Failure(PaymentNotFoundError()):
                return Failure(PaymentNotFoundError(
                    payment_id=payment_id,
                    service_name="payment",
                ))
                
            case Failure(error):
                return Failure(error)
    
    # =========================================================================
    # MAPPING HELPERS
    # =========================================================================
    
    def _map_to_payment_data(self, request: PaymentRequest) -> PaymentModulePaymentData:
        """Map UserModule PaymentRequest to PaymentModule PaymentData."""
        return PaymentModulePaymentData(
            user_id=request.user_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            metadata=request.metadata,
        )
    
    def _map_from_payment_result(
        self,
        result: PaymentModulePaymentResult,
        user_id: UUID,
    ) -> PaymentResult:
        """Map PaymentModule PaymentResult to UserModule PaymentResult."""
        return PaymentResult(
            payment_id=result.payment_id,
            user_id=user_id,
            amount=result.amount,
            currency=result.currency,
            status=self._map_status(result.status),
            created_at=datetime.now(timezone.utc),
            processed_at=result.processed_at,
            provider_reference=result.provider_transaction_id,
            message=result.message,
        )
    
    def _map_status(self, status: str) -> PaymentStatus:
        """Map PaymentModule status string to UserModule PaymentStatus enum."""
        status_mapping = {
            "success": PaymentStatus.SUCCESS,
            "failed": PaymentStatus.FAILED,
            "pending": PaymentStatus.PENDING,
            "refunded": PaymentStatus.REFUNDED,
        }
        return status_mapping.get(status, PaymentStatus.PENDING)
    
    def _map_payment_error(
        self,
        error: PaymentModuleError,
    ) -> PaymentGatewayError:
        """Map PaymentModule error to UserModule PaymentGatewayError.
        
        This is the key mapping function - converts provider-specific
        errors to consumer's error types.
        """
        match error:
            case PaymentModuleNotFoundError():
                return PaymentNotFoundError(
                    payment_id=error.payment_id,
                    service_name="payment",
                )
            
            case PaymentModuleInsufficientFundsError():
                return InsufficientFundsError(
                    amount=error.amount,
                    currency=error.currency,
                    service_name="payment",
                )
            
            case PaymentModuleRefundNotAllowedError():
                return RefundNotAllowedError(
                    payment_id=error.payment_id,
                    reason=error.reason,
                    service_name="payment",
                )
            
            case InvalidPaymentAmountError():
                return PaymentDeclinedError(
                    reason=f"Invalid amount: {error.amount}",
                    decline_code="INVALID_AMOUNT",
                    service_name="payment",
                )
            
            case PaymentProcessingError():
                return PaymentDeclinedError(
                    reason=error.reason,
                    decline_code="PROCESSING_FAILED",
                    service_name="payment",
                )
            
            case _:
                # Generic mapping for unknown errors
                return PaymentGatewayError(
                    message=str(error),
                    service_name="payment",
                )
    
    async def _on_error(
        self,
        method: str,
        request: PaymentRequest | RefundRequest | UUID,
        error: Exception,
    ) -> PaymentGatewayError:
        """Handle unexpected errors."""
        # Log error for debugging
        try:
            import logfire
            logfire.error(
                "DirectPaymentAdapter unexpected error",
                method=method,
                error=str(error),
                error_type=type(error).__name__,
            )
        except ImportError:
            print(f"DirectPaymentAdapter error in {method}: {error}")
        
        return PaymentGatewayError(
            message=f"Unexpected error in {method}: {error}",
            service_name="payment",
        )


__all__ = ["DirectPaymentAdapter"]
