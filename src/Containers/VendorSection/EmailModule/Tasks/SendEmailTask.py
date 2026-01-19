"""Task for sending emails.

This is an async Task because it involves I/O operations.
Virtual implementation for development - logs instead of real sending.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.Ship.Parents.Task import Task


class EmailData(BaseModel):
    """Data for sending email."""

    model_config = {"frozen": True}

    recipient: str
    subject: str
    body: str
    is_html: bool = False
    reply_to: str | None = None


class EmailResult(BaseModel):
    """Result of email sending operation."""

    model_config = {"frozen": True}

    email_id: UUID
    recipient: str
    subject: str
    status: str  # "sent", "failed", "queued"
    sent_at: datetime | None = None
    message: str = ""


class SendEmailTask(Task[EmailData, EmailResult]):
    """Async task for sending emails.

    Uses Task (async) because email sending involves I/O.

    This is a VIRTUAL implementation - it simulates email sending
    by logging instead of real SMTP/API calls.

    In production, inject a real email client:
    - SendGrid
    - Mailgun
    - Amazon SES
    - SMTP

    Example:
        task = SendEmailTask()
        result = await task.run(EmailData(
            recipient="user@example.com",
            subject="Hello!",
            body="Welcome to our platform.",
        ))
    """

    def __init__(self) -> None:
        """Initialize task."""
        # TODO: Inject real email client when available
        pass

    async def run(self, data: EmailData) -> EmailResult:
        """Send email (virtual implementation).

        Args:
            data: EmailData with recipient, subject, body

        Returns:
            EmailResult with status and email_id
        """
        email_id = uuid4()
        sent_at = datetime.now(UTC)

        # Virtual implementation - log instead of real sending
        try:
            import logfire

            logfire.info(
                "📧 Email sent (virtual)",
                email_id=str(email_id),
                to=data.recipient,
                subject=data.subject,
                is_html=data.is_html,
            )
        except ImportError:
            print(f"📧 Email sent (virtual) to {data.recipient}: {data.subject}")

        return EmailResult(
            email_id=email_id,
            recipient=data.recipient,
            subject=data.subject,
            status="sent",
            sent_at=sent_at,
            message="Email sent successfully (virtual)",
        )
