"""Email HTTP API Controller.

Uses DishkaRouter - no need for @inject decorator.
"""

from dishka.integrations.litestar import FromDishka
from litestar import Controller, post
from litestar.status_codes import HTTP_200_OK
from returns.result import Result

from src.Containers.VendorSection.EmailModule.Actions.SendEmailAction import SendEmailAction
from src.Containers.VendorSection.EmailModule.Data.Schemas.Requests import SendEmailRequest
from src.Containers.VendorSection.EmailModule.Data.Schemas.Responses import EmailResponse
from src.Containers.VendorSection.EmailModule.Errors import EmailError
from src.Containers.VendorSection.EmailModule.Tasks.SendEmailTask import EmailData, EmailResult
from src.Ship.Decorators.result_handler import result_handler


class EmailController(Controller):
    """HTTP API controller for Email operations.

    Handles email sending endpoints.
    This is a VIRTUAL implementation for development.
    """

    path = "/emails"
    tags = ["Emails"]

    @post("/send")
    @result_handler(EmailResponse, success_status=HTTP_200_OK)
    async def send_email(
        self,
        data: SendEmailRequest,
        action: FromDishka[SendEmailAction],
    ) -> Result[EmailResult, EmailError]:
        """Send an email (virtual implementation).

        Args:
            data: SendEmailRequest with email data
            action: Injected SendEmailAction

        Returns:
            EmailResponse with send result
        """
        email_data = EmailData(
            recipient=data.recipient,
            subject=data.subject,
            body=data.body,
            is_html=data.is_html,
            reply_to=data.reply_to,
        )
        return await action.run(email_data)
