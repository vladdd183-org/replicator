"""Task for delivering webhooks with retry logic."""

import hashlib
import hmac
import json
import random
from datetime import UTC, datetime, timedelta
from uuid import UUID

import anyio
import logfire
from pydantic import BaseModel

from src.Containers.VendorSection.WebhookModule.Models.Webhook import Webhook
from src.Containers.VendorSection.WebhookModule.Models.WebhookDelivery import WebhookDelivery
from src.Ship.Parents.Task import SyncTask, Task


class WebhookPayload(BaseModel):
    """Data for webhook delivery."""

    model_config = {"frozen": True}

    webhook_id: UUID
    event_type: str
    payload: dict


class DeliveryResult(BaseModel):
    """Result of webhook delivery."""

    model_config = {"frozen": True}

    success: bool
    delivery_id: UUID
    status_code: int | None = None
    error: str | None = None
    attempt: int = 1


class DeliverWebhookTask(Task[WebhookPayload, DeliveryResult]):
    """Task for delivering a webhook to a registered endpoint.

    Features:
    - HMAC signature generation
    - Retry with exponential backoff
    - Delivery tracking
    - Virtual HTTP client (mock)
    """

    MAX_ATTEMPTS = 5
    BACKOFF_BASE = 60  # Base delay in seconds

    async def run(self, data: WebhookPayload) -> DeliveryResult:
        """Deliver webhook to endpoint."""
        # Get webhook
        webhook = await Webhook.objects().where(Webhook.id == data.webhook_id).first()

        if not webhook:
            return DeliveryResult(
                success=False,
                delivery_id=UUID("00000000-0000-0000-0000-000000000000"),
                error="Webhook not found",
            )

        if not webhook.is_active:
            return DeliveryResult(
                success=False,
                delivery_id=UUID("00000000-0000-0000-0000-000000000000"),
                error="Webhook is disabled",
            )

        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=data.webhook_id,
            event_type=data.event_type,
            payload=data.payload,
            status="pending",
            attempt=1,
        )
        await delivery.save()

        # Attempt delivery
        result = await self._attempt_delivery(webhook, delivery, data)

        return result

    async def _attempt_delivery(
        self,
        webhook: Webhook,
        delivery: WebhookDelivery,
        data: WebhookPayload,
    ) -> DeliveryResult:
        """Attempt to deliver webhook with retries."""
        # Prepare payload
        payload_json = json.dumps(data.payload, default=str)

        # Generate signature
        signature = self._generate_signature(webhook.secret, payload_json)

        # Virtual HTTP call (mock)
        success, status_code, response_body, error = await self._virtual_http_post(
            url=webhook.url,
            payload=payload_json,
            signature=signature,
        )

        # Update delivery record
        delivery.response_status = str(status_code) if status_code else None
        delivery.response_body = response_body[:1000] if response_body else None

        if success:
            delivery.status = "success"
            delivery.delivered_at = datetime.now(UTC)
            await delivery.save()

            # Reset failure count
            webhook.failure_count = 0
            webhook.last_triggered_at = datetime.now(UTC)
            await webhook.save()

            logfire.info(
                "✅ Webhook delivered",
                webhook_id=str(data.webhook_id),
                url=webhook.url,
                event=data.event_type,
            )

            return DeliveryResult(
                success=True,
                delivery_id=delivery.id,
                status_code=status_code,
                attempt=delivery.attempt,
            )
        else:
            delivery.status = "failed"
            delivery.error_message = error

            # Calculate retry time with exponential backoff
            if delivery.attempt < self.MAX_ATTEMPTS:
                delay = self.BACKOFF_BASE * (2 ** (delivery.attempt - 1))
                delivery.next_retry_at = datetime.now(UTC) + timedelta(seconds=delay)

            await delivery.save()

            # Increment failure count
            webhook.failure_count = (webhook.failure_count or 0) + 1

            # Disable webhook after too many failures
            if webhook.failure_count >= 10:
                webhook.is_active = False

            await webhook.save()

            logfire.warning(
                "❌ Webhook delivery failed",
                webhook_id=str(data.webhook_id),
                url=webhook.url,
                event=data.event_type,
                error=error,
                attempt=delivery.attempt,
            )

            return DeliveryResult(
                success=False,
                delivery_id=delivery.id,
                status_code=status_code,
                error=error,
                attempt=delivery.attempt,
            )

    def _generate_signature(self, secret: str, payload: str) -> str:
        """Generate HMAC-SHA256 signature."""
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    async def _virtual_http_post(
        self,
        url: str,
        payload: str,
        signature: str,
    ) -> tuple[bool, int | None, str | None, str | None]:
        """Virtual HTTP POST for testing.

        In production, use httpx or aiohttp.

        Returns:
            Tuple of (success, status_code, response_body, error)
        """

        # Simulate network latency
        await self._simulate_delay()

        # Validate URL
        if not url.startswith(("http://", "https://")):
            return False, None, None, "Invalid URL scheme"

        # Simulate responses
        # 90% success rate for demo
        if random.random() < 0.9:
            logfire.info(
                "📤 Virtual webhook POST",
                url=url,
                signature=signature[:20] + "...",
                payload_size=len(payload),
            )
            return True, 200, '{"status": "ok"}', None
        else:
            # Simulate various failures
            failure_scenarios = [
                (500, "Internal Server Error"),
                (502, "Bad Gateway"),
                (503, "Service Unavailable"),
                (408, "Request Timeout"),
                (None, "Connection refused"),
            ]
            status, error = random.choice(failure_scenarios)
            return False, status, None, error

    async def _simulate_delay(self) -> None:
        """Simulate network delay."""
        await anyio.sleep(random.uniform(0.1, 0.3))


class VerifySignatureInput(BaseModel):
    """Input for signature verification."""

    model_config = {"frozen": True}

    secret: str
    payload: str
    signature: str


class VerifySignatureTask(SyncTask[VerifySignatureInput, bool]):
    """Synchronous task for verifying incoming webhook signatures.

    Uses SyncTask because HMAC verification is CPU-bound.

    Example:
        task = VerifySignatureTask()
        is_valid = task.run(VerifySignatureInput(
            secret="webhook_secret",
            payload='{"event": "user.created"}',
            signature="sha256=abc123...",
        ))
    """

    def run(self, data: VerifySignatureInput) -> bool:
        """Verify HMAC signature.

        Args:
            data: Verification input with secret, payload, and signature

        Returns:
            True if signature is valid
        """
        if not data.signature.startswith("sha256="):
            return False

        expected_sig = data.signature[7:]  # Remove "sha256=" prefix

        computed_sig = hmac.new(
            data.secret.encode("utf-8"),
            data.payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_sig, computed_sig)
