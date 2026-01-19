"""SendEmailAction - Use case for sending emails."""

from returns.result import Failure, Result, Success

from src.Containers.VendorSection.EmailModule.Errors import EmailError, EmailSendFailedError
from src.Containers.VendorSection.EmailModule.Tasks.SendEmailTask import (
    EmailData,
    EmailResult,
    SendEmailTask,
)
from src.Ship.Parents.Action import Action


class SendEmailAction(Action[EmailData, EmailResult, EmailError]):
    """Use Case: Send an email.

    Steps:
    1. Validate email data (handled by Pydantic)
    2. Send email via SendEmailTask
    3. Return result

    Example:
        action = SendEmailAction(send_email_task)
        result = await action.run(EmailData(
            recipient="user@example.com",
            subject="Hello!",
            body="Welcome to our platform.",
        ))
    """

    def __init__(self, send_email_task: SendEmailTask) -> None:
        """Initialize action with dependencies.

        Args:
            send_email_task: Task for sending emails
        """
        self.send_email_task = send_email_task

    async def run(self, data: EmailData) -> Result[EmailResult, EmailError]:
        """Execute the send email use case.

        Args:
            data: EmailData with recipient, subject, body

        Returns:
            Result[EmailResult, EmailError]: Success with result or Failure with error
        """
        try:
            result = await self.send_email_task.run(data)

            if result.status == "failed":
                return Failure(
                    EmailSendFailedError(
                        recipient=data.recipient,
                        reason=result.message,
                    )
                )

            return Success(result)

        except Exception as e:
            return Failure(
                EmailSendFailedError(
                    recipient=data.recipient,
                    reason=str(e),
                )
            )
