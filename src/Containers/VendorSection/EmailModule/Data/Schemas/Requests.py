"""EmailModule request DTOs.

Request DTOs use Pydantic for validation.
"""

from pydantic import BaseModel, EmailStr, Field


class SendEmailRequest(BaseModel):
    """Request DTO for sending an email.
    
    Attributes:
        recipient: Email recipient address
        subject: Email subject
        body: Email body (plain text or HTML)
        is_html: Whether body is HTML
        reply_to: Optional reply-to address
    """
    
    recipient: EmailStr
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body")
    is_html: bool = Field(default=False, description="Whether body is HTML")
    reply_to: EmailStr | None = Field(default=None, description="Reply-to address")
