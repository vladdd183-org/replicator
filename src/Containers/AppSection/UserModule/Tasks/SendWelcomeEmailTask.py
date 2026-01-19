"""Task for sending welcome emails to new users.

This is an async Task because it involves I/O operations (sending email).
"""

from typing import Protocol, Optional

from pydantic import BaseModel

from src.Ship.Parents.Task import Task


class EmailClient(Protocol):
    """Protocol for email client implementations."""
    
    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: str | None = None,
    ) -> bool:
        """Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html: Optional HTML body
            
        Returns:
            True if sent successfully
        """
        ...


class WelcomeEmailData(BaseModel):
    """Data for welcome email."""
    
    model_config = {"frozen": True}
    
    email: str
    name: str


class SendWelcomeEmailTask(Task[WelcomeEmailData, bool]):
    """Async task for sending welcome emails.
    
    Uses Task (async) because email sending involves I/O.
    
    Example:
        task = SendWelcomeEmailTask()
        success = await task.run(WelcomeEmailData(
            email="user@example.com",
            name="John Doe",
        ))
    """
    
    def __init__(self) -> None:
        """Initialize task."""
        # TODO: Inject EmailClient when available
        self.email_client: Optional[EmailClient] = None
    
    async def run(self, data: WelcomeEmailData) -> bool:
        """Send welcome email to new user.
        
        Args:
            data: WelcomeEmailData with email and name
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Welcome to Hyper-Porto!"
        body = f"""
Hello {data.name}!

Welcome to our platform. We're excited to have you on board.

Your account has been successfully created with the email: {data.email}

Best regards,
The Hyper-Porto Team
        """.strip()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2563eb;">Welcome to Hyper-Porto!</h1>
        <p>Hello <strong>{data.name}</strong>!</p>
        <p>Welcome to our platform. We're excited to have you on board.</p>
        <p>Your account has been successfully created with the email: <code>{data.email}</code></p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
        <p style="color: #6b7280; font-size: 14px;">
            Best regards,<br>
            The Hyper-Porto Team
        </p>
    </div>
</body>
</html>
        """.strip()
        
        if self.email_client is not None:
            return await self.email_client.send(
                to=data.email,
                subject=subject,
                body=body,
                html=html,
            )
        
        # Mock implementation for development/testing
        try:
            import logfire
            logfire.info(
                "📧 Welcome email (mock)",
                to=data.email,
                subject=subject,
            )
        except ImportError:
            print(f"📧 Welcome email (mock) to {data.email}: {subject}")
            
        return True
