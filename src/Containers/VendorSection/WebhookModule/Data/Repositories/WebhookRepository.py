"""Repository for Webhooks."""

import secrets
from datetime import UTC, datetime
from uuid import UUID

from src.Containers.VendorSection.WebhookModule.Models.Webhook import Webhook
from src.Containers.VendorSection.WebhookModule.Models.WebhookDelivery import WebhookDelivery
from src.Ship.Parents.Repository import Repository


class WebhookRepository(Repository[Webhook]):
    """Repository for webhooks."""

    def __init__(self) -> None:
        super().__init__(Webhook)

    async def get_all(self) -> list[Webhook]:
        """Get all webhooks."""
        return await self.model.objects().order_by(self.model.created_at, ascending=False)

    async def get_by_user(self, user_id: UUID) -> list[Webhook]:
        """Get all webhooks for a user."""
        return await (
            self.model.objects()
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at, ascending=False)
        )

    async def get_active_for_event(self, event_type: str) -> list[Webhook]:
        """Get all active webhooks subscribed to an event."""
        all_webhooks = await self.model.objects().where(self.model.is_active == True)

        # Filter by event subscription (JSON array check)
        matching = []
        for webhook in all_webhooks:
            events = webhook.events or []
            if event_type in events or "*" in events:
                matching.append(webhook)

        return matching

    async def create_webhook(
        self,
        url: str,
        events: list[str],
        user_id: UUID | None = None,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> Webhook:
        """Create a new webhook with generated secret."""
        secret = secrets.token_urlsafe(32)

        webhook = Webhook(
            user_id=user_id,
            url=url,
            secret=secret,
            events=events,
            description=description,
            metadata=metadata,
        )
        await webhook.save()
        return webhook

    async def toggle_active(self, webhook_id: UUID, is_active: bool) -> Webhook | None:
        """Enable or disable a webhook."""
        webhook = await self.get(webhook_id)
        if webhook:
            webhook.is_active = is_active
            webhook.updated_at = datetime.now(UTC)
            await webhook.save()
        return webhook

    async def reset_failure_count(self, webhook_id: UUID) -> Webhook | None:
        """Reset failure count for a webhook."""
        webhook = await self.get(webhook_id)
        if webhook:
            webhook.failure_count = "0"
            webhook.is_active = True
            webhook.updated_at = datetime.now(UTC)
            await webhook.save()
        return webhook


class WebhookDeliveryRepository(Repository[WebhookDelivery]):
    """Repository for webhook deliveries."""

    def __init__(self) -> None:
        super().__init__(WebhookDelivery)

    async def get_by_webhook(
        self,
        webhook_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WebhookDelivery]:
        """Get deliveries for a webhook."""
        return await (
            self.model.objects()
            .where(self.model.webhook_id == webhook_id)
            .order_by(self.model.created_at, ascending=False)
            .limit(limit)
            .offset(offset)
        )

    async def get_pending_retries(self) -> list[WebhookDelivery]:
        """Get deliveries pending retry."""
        now = datetime.now(UTC)
        return await (
            self.model.objects()
            .where(self.model.status == "failed")
            .where(self.model.next_retry_at.is_not_null())
            .where(self.model.next_retry_at <= now)
        )

    async def count_by_status(self, webhook_id: UUID) -> dict[str, int]:
        """Count deliveries by status for a webhook."""
        deliveries = await self.model.select(self.model.status).where(
            self.model.webhook_id == webhook_id
        )

        counts: dict[str, int] = {"pending": 0, "success": 0, "failed": 0}
        for d in deliveries:
            status = d["status"]
            counts[status] = counts.get(status, 0) + 1

        return counts
