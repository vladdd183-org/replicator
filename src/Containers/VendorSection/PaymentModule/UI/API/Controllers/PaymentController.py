"""Payment HTTP API Controller.

Uses DishkaRouter - no need for @inject decorator.
"""

from dishka.integrations.litestar import FromDishka
from litestar import Controller, post
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from returns.result import Result

from src.Containers.VendorSection.PaymentModule.Actions.CreatePaymentAction import (
    CreatePaymentAction,
)
from src.Containers.VendorSection.PaymentModule.Actions.RefundPaymentAction import (
    RefundPaymentAction,
    RefundRequest,
    RefundResult,
)
from src.Containers.VendorSection.PaymentModule.Data.Schemas.Requests import (
    CreatePaymentRequest,
    RefundPaymentRequest,
)
from src.Containers.VendorSection.PaymentModule.Data.Schemas.Responses import (
    PaymentResponse,
    RefundResponse,
)
from src.Containers.VendorSection.PaymentModule.Errors import PaymentError
from src.Containers.VendorSection.PaymentModule.Tasks.ProcessPaymentTask import (
    PaymentData,
    PaymentResult,
)
from src.Ship.Decorators.result_handler import result_handler


class PaymentController(Controller):
    """HTTP API controller for Payment operations.

    Handles payment processing endpoints.
    This is a VIRTUAL implementation for development.
    """

    path = "/payments"
    tags = ["Payments"]

    @post("/")
    @result_handler(PaymentResponse, success_status=HTTP_201_CREATED)
    async def create_payment(
        self,
        data: CreatePaymentRequest,
        action: FromDishka[CreatePaymentAction],
    ) -> Result[PaymentResult, PaymentError]:
        """Create and process a payment (virtual implementation).

        Args:
            data: CreatePaymentRequest with payment data
            action: Injected CreatePaymentAction

        Returns:
            PaymentResponse with processing result
        """
        payment_data = PaymentData(
            user_id=data.user_id,
            amount=data.amount,
            currency=data.currency,
            description=data.description,
        )
        return await action.run(payment_data)

    @post("/refund")
    @result_handler(RefundResponse, success_status=HTTP_200_OK)
    async def refund_payment(
        self,
        data: RefundPaymentRequest,
        action: FromDishka[RefundPaymentAction],
    ) -> Result[RefundResult, PaymentError]:
        """Refund a payment (virtual implementation).

        Args:
            data: RefundPaymentRequest with refund data
            action: Injected RefundPaymentAction

        Returns:
            RefundResponse with refund result
        """
        refund_request = RefundRequest(
            payment_id=data.payment_id,
            user_id=data.user_id,
            amount=data.amount,
            currency=data.currency,
            reason=data.reason,
        )
        return await action.run(refund_request)
