"""Payment module dependency injection providers.

Consolidated providers with clear scope separation.
"""

from dishka import Provider, Scope, provide

from src.Containers.VendorSection.PaymentModule.Tasks.ProcessPaymentTask import (
    ProcessPaymentTask,
)
from src.Containers.VendorSection.PaymentModule.Actions.CreatePaymentAction import (
    CreatePaymentAction,
)
from src.Containers.VendorSection.PaymentModule.Actions.RefundPaymentAction import (
    RefundPaymentAction,
)


class PaymentModuleProvider(Provider):
    """Core provider for PaymentModule - APP scope dependencies.
    
    Stateless services that can be reused across requests.
    """
    
    scope = Scope.APP
    
    # Tasks - stateless, reusable
    process_payment_task = provide(ProcessPaymentTask)


class PaymentRequestProvider(Provider):
    """HTTP request-scoped provider for PaymentModule."""
    
    scope = Scope.REQUEST
    
    # Actions
    create_payment_action = provide(CreatePaymentAction)
    refund_payment_action = provide(RefundPaymentAction)



