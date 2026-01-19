"""EmailModule response DTOs.

Response DTOs inherit from EntitySchema for automatic conversion.
"""

from datetime import datetime
from uuid import UUID

from src.Ship.Core.BaseSchema import EntitySchema


class EmailResponse(EntitySchema):
    """Response DTO for email operation.

    Attributes:
        email_id: Unique email identifier
        recipient: Email recipient
        subject: Email subject
        status: Email status (sent, failed, queued)
        sent_at: When email was sent
        message: Additional message
    """

    email_id: UUID
    recipient: str
    subject: str
    status: str
    sent_at: datetime | None = None
    message: str = ""
