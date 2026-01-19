"""CreatePaymentAction - Use case for creating and processing payments."""

from decimal import Decimal

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.VendorSection.PaymentModule.Tasks.ProcessPaymentTask import (
    ProcessPaymentTask,
    PaymentData,
    PaymentResult,
)
from src.Containers.VendorSection.PaymentModule.Errors import (
    PaymentError,
    PaymentProcessingError,
    InvalidPaymentAmountError,
)


class CreatePaymentAction(Action[PaymentData, PaymentResult, PaymentError]):
    """Use Case: Create and process a payment.
    
    Steps:
    1. Validate payment data
    2. Process payment via ProcessPaymentTask
    3. Return result
    
    Example:
        action = CreatePaymentAction(process_payment_task)
        result = await action.run(PaymentData(
            user_id=user_id,
            amount=Decimal("100.00"),
            currency="RUB",
        ))
    """
    
    def __init__(self, process_payment_task: ProcessPaymentTask) -> None:
        """Initialize action with dependencies.
        
        Args:
            process_payment_task: Task for processing payments
        """
        self.process_payment_task = process_payment_task
    
    async def run(self, data: PaymentData) -> Result[PaymentResult, PaymentError]:
        """Execute the create payment use case.
        
        Args:
            data: PaymentData with user_id, amount, currency
            
        Returns:
            Result[PaymentResult, PaymentError]: Success with result or Failure with error
        """
        # Validate amount
        if data.amount <= Decimal("0"):
            return Failure(InvalidPaymentAmountError(amount=data.amount))
        
        try:
            result = await self.process_payment_task.run(data)
            
            if result.status == "failed":
                return Failure(PaymentProcessingError(reason=result.message))
            
            return Success(result)
            
        except Exception as e:
            return Failure(PaymentProcessingError(reason=str(e)))



