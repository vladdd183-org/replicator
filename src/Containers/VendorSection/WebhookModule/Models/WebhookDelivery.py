"""WebhookDelivery model for tracking delivery attempts."""

from piccolo.columns import JSONB, UUID, Integer, Text, Timestamptz, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.defaults.uuid import UUID4

from src.Ship.Parents.Model import Model


class WebhookDelivery(Model):
    """Tracks webhook delivery attempts.

    Attributes:
        id: Unique identifier
        webhook_id: Reference to the webhook
        event_type: Type of event delivered
        payload: JSON payload sent
        status: Delivery status ("pending", "success", "failed")
        response_status: HTTP response status code
        response_body: Response body (truncated)
        error_message: Error message if failed
        attempt: Attempt number (1-based)
        next_retry_at: When to retry (if failed)
        delivered_at: When successfully delivered
        created_at: When delivery was queued
    """

    id = UUID(primary_key=True, default=UUID4())
    webhook_id = UUID(required=True, index=True)
    event_type = Varchar(length=100, required=True, index=True)
    payload = JSONB(required=True)

    # Delivery status
    status = Varchar(length=20, default="pending", index=True)  # pending, success, failed
    response_status = Varchar(length=3, null=True)
    response_body = Text(null=True)
    error_message = Text(null=True)

    # Retry tracking
    attempt = Integer(default=1)
    next_retry_at = Timestamptz(null=True)

    delivered_at = Timestamptz(null=True)
    created_at = Timestamptz(default=TimestamptzNow())

    class Meta:
        tablename = "webhook_deliveries"
