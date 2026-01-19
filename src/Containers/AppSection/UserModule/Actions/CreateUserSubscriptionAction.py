"""CreateUserSubscriptionAction - Example of Gateway usage.

This Action demonstrates the Module Gateway Pattern by using
PaymentGateway to process subscription payments.

Key Points:
1. Action depends on PaymentGateway Protocol, not concrete adapter
2. Gateway is injected by Dishka based on deployment_mode
3. Same Action code works for both monolith and microservices
4. Error handling maps gateway errors to domain errors

Flow:
1. Validate subscription request
2. Calculate subscription price
3. Create payment via PaymentGateway
4. Update user subscription status
5. Return subscription details
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Ship.Core.Errors import BaseError, ErrorWithTemplate

# Gateway import - Protocol only, no concrete adapter
from src.Containers.AppSection.UserModule.Gateways.PaymentGateway import PaymentGateway
from src.Containers.AppSection.UserModule.Gateways.Types import (
    PaymentRequest,
    PaymentStatus,
    PaymentDeclinedError,
    InsufficientFundsError,
    PaymentGatewayConnectionError,
    PaymentGatewayTimeoutError,
)

# User module imports
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork


# ============================================================================
# DTOs
# ============================================================================

class SubscriptionPlan(StrEnum):
    """Available subscription plans."""
    
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class CreateSubscriptionRequest(BaseModel):
    """Request to create user subscription.
    
    Attributes:
        user_id: User to create subscription for
        plan: Subscription plan to activate
        period_months: Subscription period (1, 3, 6, 12 months)
        promo_code: Optional promo code for discount
    """
    
    model_config = {"frozen": True}
    
    user_id: UUID
    plan: SubscriptionPlan
    period_months: int = Field(default=1, ge=1, le=12)
    promo_code: str | None = None


class SubscriptionResult(BaseModel):
    """Result of subscription creation.
    
    Attributes:
        subscription_id: Unique subscription identifier
        user_id: User who subscribed
        plan: Active subscription plan
        payment_id: Associated payment ID
        amount: Amount paid
        currency: Currency used
        starts_at: Subscription start date
        expires_at: Subscription expiration date
    """
    
    model_config = {"frozen": True}
    
    subscription_id: UUID
    user_id: UUID
    plan: SubscriptionPlan
    payment_id: UUID
    amount: Decimal
    currency: str
    starts_at: datetime
    expires_at: datetime


# ============================================================================
# ERRORS
# ============================================================================

class SubscriptionError(BaseError):
    """Base error for subscription operations."""
    
    code: str = "SUBSCRIPTION_ERROR"


class SubscriptionPaymentFailedError(ErrorWithTemplate, SubscriptionError):
    """Error when subscription payment fails.
    
    This wraps gateway payment errors for the subscription context.
    """
    
    _message_template: ClassVar[str] = (
        "Subscription payment failed: {reason}"
    )
    code: str = "SUBSCRIPTION_PAYMENT_FAILED"
    http_status: int = 402  # Payment Required
    reason: str
    decline_code: str | None = None


class SubscriptionServiceUnavailableError(ErrorWithTemplate, SubscriptionError):
    """Error when payment service is unavailable.
    
    Indicates temporary failure - client can retry.
    """
    
    _message_template: ClassVar[str] = (
        "Subscription service temporarily unavailable: {details}"
    )
    code: str = "SUBSCRIPTION_SERVICE_UNAVAILABLE"
    http_status: int = 503  # Service Unavailable
    details: str
    retry_after_seconds: float = 60.0


class InvalidSubscriptionPlanError(ErrorWithTemplate, SubscriptionError):
    """Error when subscription plan is invalid."""
    
    _message_template: ClassVar[str] = (
        "Invalid subscription plan: {plan}"
    )
    code: str = "INVALID_SUBSCRIPTION_PLAN"
    http_status: int = 400
    plan: str


# ============================================================================
# ACTION
# ============================================================================

# Pricing table (in production, this would be in database or config)
PLAN_PRICES: dict[SubscriptionPlan, Decimal] = {
    SubscriptionPlan.FREE: Decimal("0"),
    SubscriptionPlan.BASIC: Decimal("499.00"),
    SubscriptionPlan.PREMIUM: Decimal("999.00"),
    SubscriptionPlan.ENTERPRISE: Decimal("4999.00"),
}


@dataclass
class CreateUserSubscriptionAction(
    Action[CreateSubscriptionRequest, SubscriptionResult, SubscriptionError]
):
    """Use Case: Create subscription with payment processing.
    
    This action demonstrates the Gateway Pattern for inter-module
    communication. It uses PaymentGateway to process payments,
    which works identically in monolith and microservices modes.
    
    Dependencies (injected by Dishka):
        payment_gateway: PaymentGateway - Protocol-based gateway
        uow: UserUnitOfWork - For transaction management
    
    Flow:
        1. Validate subscription request
        2. Calculate price based on plan and period
        3. Create payment via PaymentGateway
        4. On success: create subscription record
        5. Return subscription details
    
    Error Handling:
        - PaymentDeclinedError → SubscriptionPaymentFailedError
        - InsufficientFundsError → SubscriptionPaymentFailedError
        - PaymentGatewayConnectionError → SubscriptionServiceUnavailableError
        - PaymentGatewayTimeoutError → SubscriptionServiceUnavailableError
    
    Example:
        action = CreateUserSubscriptionAction(
            payment_gateway=payment_gateway,  # Injected
            uow=user_uow,  # Injected
        )
        
        result = await action.run(CreateSubscriptionRequest(
            user_id=user_id,
            plan=SubscriptionPlan.PREMIUM,
            period_months=12,
        ))
        
        match result:
            case Success(subscription):
                print(f"Subscription created: {subscription.subscription_id}")
            case Failure(SubscriptionPaymentFailedError() as e):
                print(f"Payment failed: {e.reason}")
    """
    
    # Dependencies - injected by Dishka
    payment_gateway: PaymentGateway
    uow: UserUnitOfWork
    
    async def run(
        self,
        data: CreateSubscriptionRequest,
    ) -> Result[SubscriptionResult, SubscriptionError]:
        """Execute subscription creation.
        
        Args:
            data: CreateSubscriptionRequest with user_id, plan, period
            
        Returns:
            Result[SubscriptionResult, SubscriptionError]
        """
        # Step 1: Validate plan
        if data.plan not in PLAN_PRICES:
            return Failure(InvalidSubscriptionPlanError(plan=data.plan))
        
        # Step 2: Calculate price
        base_price = PLAN_PRICES[data.plan]
        total_price = base_price * data.period_months
        
        # Apply discounts for longer periods
        if data.period_months >= 12:
            total_price = total_price * Decimal("0.8")  # 20% off annual
        elif data.period_months >= 6:
            total_price = total_price * Decimal("0.9")  # 10% off 6+ months
        
        # Free plan doesn't need payment
        if data.plan == SubscriptionPlan.FREE or total_price == 0:
            return await self._create_free_subscription(data)
        
        # Step 3: Process payment via Gateway
        payment_result = await self.payment_gateway.create_payment(
            PaymentRequest(
                user_id=data.user_id,
                amount=total_price,
                currency="RUB",
                description=f"Subscription: {data.plan.value} ({data.period_months} months)",
                idempotency_key=f"sub_{data.user_id}_{data.plan}_{data.period_months}",
                metadata={
                    "subscription_plan": data.plan.value,
                    "period_months": data.period_months,
                    "promo_code": data.promo_code,
                },
            )
        )
        
        # Step 4: Handle payment result
        match payment_result:
            case Success(payment):
                # Payment successful - create subscription
                if payment.status == PaymentStatus.SUCCESS:
                    return await self._create_subscription(
                        data=data,
                        payment_id=payment.payment_id,
                        amount=payment.amount,
                        currency=payment.currency,
                    )
                elif payment.status == PaymentStatus.PENDING:
                    # Payment pending - in real app, we'd wait for webhook
                    return Failure(SubscriptionPaymentFailedError(
                        reason="Payment is pending confirmation",
                        decline_code="PENDING",
                    ))
                else:
                    return Failure(SubscriptionPaymentFailedError(
                        reason=payment.message or "Payment failed",
                        decline_code="FAILED",
                    ))
            
            case Failure(PaymentDeclinedError() as e):
                return Failure(SubscriptionPaymentFailedError(
                    reason=e.reason,
                    decline_code=e.decline_code,
                ))
            
            case Failure(InsufficientFundsError() as e):
                return Failure(SubscriptionPaymentFailedError(
                    reason=f"Insufficient funds: {e.amount} {e.currency}",
                    decline_code="INSUFFICIENT_FUNDS",
                ))
            
            case Failure(PaymentGatewayConnectionError() as e):
                return Failure(SubscriptionServiceUnavailableError(
                    details=e.details,
                    retry_after_seconds=30.0,
                ))
            
            case Failure(PaymentGatewayTimeoutError() as e):
                return Failure(SubscriptionServiceUnavailableError(
                    details=f"Payment request timed out after {e.timeout_seconds}s",
                    retry_after_seconds=60.0,
                ))
            
            case Failure(error):
                # Generic gateway error
                return Failure(SubscriptionPaymentFailedError(
                    reason=str(error),
                    decline_code="GATEWAY_ERROR",
                ))
    
    async def _create_free_subscription(
        self,
        data: CreateSubscriptionRequest,
    ) -> Result[SubscriptionResult, SubscriptionError]:
        """Create free subscription without payment."""
        now = datetime.now(timezone.utc)
        from dateutil.relativedelta import relativedelta
        
        try:
            expires_at = now + relativedelta(months=data.period_months)
        except ImportError:
            # Fallback if dateutil not installed
            from datetime import timedelta
            expires_at = now + timedelta(days=data.period_months * 30)
        
        return Success(SubscriptionResult(
            subscription_id=uuid4(),
            user_id=data.user_id,
            plan=data.plan,
            payment_id=UUID("00000000-0000-0000-0000-000000000000"),  # No payment
            amount=Decimal("0"),
            currency="RUB",
            starts_at=now,
            expires_at=expires_at,
        ))
    
    async def _create_subscription(
        self,
        data: CreateSubscriptionRequest,
        payment_id: UUID,
        amount: Decimal,
        currency: str,
    ) -> Result[SubscriptionResult, SubscriptionError]:
        """Create subscription after successful payment.
        
        In real application, this would:
        1. Create Subscription record in database
        2. Update User.subscription_plan
        3. Emit SubscriptionCreated event
        """
        now = datetime.now(timezone.utc)
        
        try:
            from dateutil.relativedelta import relativedelta
            expires_at = now + relativedelta(months=data.period_months)
        except ImportError:
            from datetime import timedelta
            expires_at = now + timedelta(days=data.period_months * 30)
        
        subscription_id = uuid4()
        
        # TODO: In real implementation:
        # async with self.uow:
        #     subscription = Subscription(
        #         id=subscription_id,
        #         user_id=data.user_id,
        #         plan=data.plan,
        #         payment_id=payment_id,
        #         starts_at=now,
        #         expires_at=expires_at,
        #     )
        #     await self.uow.subscriptions.add(subscription)
        #     self.uow.add_event(SubscriptionCreated(
        #         subscription_id=subscription_id,
        #         user_id=data.user_id,
        #         plan=data.plan,
        #     ))
        #     await self.uow.commit()
        
        return Success(SubscriptionResult(
            subscription_id=subscription_id,
            user_id=data.user_id,
            plan=data.plan,
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            starts_at=now,
            expires_at=expires_at,
        ))


__all__ = [
    "CreateUserSubscriptionAction",
    "CreateSubscriptionRequest",
    "SubscriptionResult",
    "SubscriptionPlan",
    "SubscriptionError",
    "SubscriptionPaymentFailedError",
    "SubscriptionServiceUnavailableError",
    "InvalidSubscriptionPlanError",
]
