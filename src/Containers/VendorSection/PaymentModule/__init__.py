"""PaymentModule - Virtual payment processing service.

This module provides a virtual payment service for development.
In production, it would integrate with a real payment provider like:
- Stripe
- PayPal
- YooKassa
- Tinkoff

Components:
- Actions: CreatePaymentAction, RefundPaymentAction
- Tasks: ProcessPaymentTask
- Events: PaymentCreated, PaymentProcessed, PaymentFailed, PaymentRefunded
- Schemas: PaymentRequest, PaymentResponse
"""

from src.Containers.VendorSection.PaymentModule.UI.API.Routes import payment_router

__all__ = ["payment_router"]
