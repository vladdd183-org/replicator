"""EmailModule - Virtual email sending service.

This module provides a virtual email sending service for development.
In production, it would integrate with a real email provider like:
- SendGrid
- Mailgun
- Amazon SES
- SMTP server

Components:
- Actions: SendEmailAction
- Tasks: SendEmailTask
- Events: EmailSent, EmailFailed
- Schemas: EmailRequest, EmailResponse
"""

from src.Containers.VendorSection.EmailModule.UI.API.Routes import email_router

__all__ = ["email_router"]
