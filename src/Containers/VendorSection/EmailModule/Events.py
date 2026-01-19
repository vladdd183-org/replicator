"""EmailModule domain events.

Events for tracking email operations.
"""

from uuid import UUID

from src.Ship.Parents.Event import DomainEvent


class EmailSent(DomainEvent):
    """Event raised when an email is successfully sent.

    Attributes:
        email_id: Unique identifier for the email
        recipient: Email recipient address
        subject: Email subject
        template: Template name used (if any)
    """

    email_id: UUID
    recipient: str
    subject: str
    template: str | None = None


class EmailFailed(DomainEvent):
    """Event raised when email sending fails.

    Attributes:
        email_id: Unique identifier for the failed email attempt
        recipient: Email recipient address
        subject: Email subject
        error_message: Description of the failure
    """

    email_id: UUID
    recipient: str
    subject: str
    error_message: str


class EmailQueued(DomainEvent):
    """Event raised when an email is queued for sending.

    Attributes:
        email_id: Unique identifier for the email
        recipient: Email recipient address
        scheduled_at: When the email should be sent (if scheduled)
    """

    email_id: UUID
    recipient: str
    scheduled_at: str | None = None


__all__ = ["EmailFailed", "EmailQueued", "EmailSent"]
