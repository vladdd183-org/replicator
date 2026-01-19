"""WebhookModule API controller."""

from uuid import UUID

from dishka.integrations.litestar import FromDishka
from litestar import Controller, Request, delete, get, patch, post
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from returns.result import Result

from src.Containers.VendorSection.WebhookModule.Actions.DeleteWebhookAction import (
    DeleteWebhookAction,
    DeleteWebhookInput,
)
from src.Containers.VendorSection.WebhookModule.Actions.RegisterWebhookAction import (
    RegisterWebhookAction,
    RegisterWebhookInput,
)
from src.Containers.VendorSection.WebhookModule.Actions.ResetWebhookAction import (
    ResetWebhookAction,
    ResetWebhookInput,
)
from src.Containers.VendorSection.WebhookModule.Actions.ToggleWebhookAction import (
    ToggleWebhookAction,
    ToggleWebhookInput,
)
from src.Containers.VendorSection.WebhookModule.Actions.TriggerWebhookAction import (
    TriggerWebhookAction,
)
from src.Containers.VendorSection.WebhookModule.Data.Schemas.Requests import (
    IncomingWebhookPayload,
    RegisterWebhookRequest,
    TriggerWebhookRequest,
)
from src.Containers.VendorSection.WebhookModule.Data.Schemas.Responses import (
    TriggerWebhookResponse,
    WebhookDeliveriesListResponse,
    WebhookDeliveryResponse,
    WebhookResponse,
    WebhooksListResponse,
    WebhookWithSecretResponse,
)
from src.Containers.VendorSection.WebhookModule.Errors import (
    WebhookError,
    WebhookNotFoundError,
)
from src.Containers.VendorSection.WebhookModule.Models.Webhook import Webhook
from src.Containers.VendorSection.WebhookModule.Queries.GetWebhookQuery import (
    GetWebhookQuery,
    GetWebhookQueryInput,
)
from src.Containers.VendorSection.WebhookModule.Queries.ListWebhookDeliveriesQuery import (
    ListWebhookDeliveriesQuery,
    ListWebhookDeliveriesQueryInput,
)
from src.Containers.VendorSection.WebhookModule.Queries.ListWebhooksQuery import (
    ListWebhooksQuery,
    ListWebhooksQueryInput,
)
from src.Containers.VendorSection.WebhookModule.Tasks.DeliverWebhookTask import (
    DeliveryResult,
)
from src.Ship.Core.Errors import DomainException
from src.Ship.Decorators.result_handler import result_handler


class WebhookController(Controller):
    """Controller for outgoing webhook management."""

    path = "/webhooks"
    tags = ["Webhooks"]

    @get("/")
    async def list_webhooks(
        self,
        query: FromDishka[ListWebhooksQuery],
        user_id: UUID | None = None,
    ) -> WebhooksListResponse:
        """List registered webhooks."""
        result = await query.execute(ListWebhooksQueryInput(user_id=user_id))

        return WebhooksListResponse(
            webhooks=[
                WebhookResponse(
                    id=w.id,
                    user_id=w.user_id,
                    url=w.url,
                    events=w.events,
                    is_active=w.is_active,
                    description=w.description,
                    failure_count=int(w.failure_count or "0"),
                    last_triggered_at=w.last_triggered_at,
                    created_at=w.created_at,
                    updated_at=w.updated_at,
                )
                for w in result.webhooks
            ],
            total=result.total,
        )

    @post("/")
    @result_handler(WebhookWithSecretResponse, success_status=HTTP_201_CREATED)
    async def register_webhook(
        self,
        data: RegisterWebhookRequest,
        action: FromDishka[RegisterWebhookAction],
    ) -> Result[Webhook, WebhookError]:
        """Register a new webhook.

        The secret is only returned once during registration.
        Store it securely for verifying webhook signatures.
        """
        return await action.run(RegisterWebhookInput(request=data))

    @get("/{webhook_id:uuid}")
    async def get_webhook(
        self,
        webhook_id: UUID,
        query: FromDishka[GetWebhookQuery],
    ) -> WebhookResponse:
        """Get a specific webhook by ID."""
        webhook = await query.execute(GetWebhookQueryInput(webhook_id=webhook_id))
        if not webhook:
            raise DomainException(WebhookNotFoundError(webhook_id=webhook_id))

        return WebhookResponse(
            id=webhook.id,
            user_id=webhook.user_id,
            url=webhook.url,
            events=webhook.events,
            is_active=webhook.is_active,
            description=webhook.description,
            failure_count=int(webhook.failure_count or "0"),
            last_triggered_at=webhook.last_triggered_at,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
        )

    @patch("/{webhook_id:uuid}/toggle")
    @result_handler(WebhookResponse, success_status=HTTP_200_OK)
    async def toggle_webhook(
        self,
        webhook_id: UUID,
        action: FromDishka[ToggleWebhookAction],
        is_active: bool = True,
    ) -> Result[Webhook, WebhookError]:
        """Enable or disable a webhook."""
        return await action.run(
            ToggleWebhookInput(
                webhook_id=webhook_id,
                is_active=is_active,
            )
        )

    @post("/{webhook_id:uuid}/reset")
    @result_handler(WebhookResponse, success_status=HTTP_200_OK)
    async def reset_webhook(
        self,
        webhook_id: UUID,
        action: FromDishka[ResetWebhookAction],
    ) -> Result[Webhook, WebhookError]:
        """Reset webhook failure count and re-enable."""
        return await action.run(ResetWebhookInput(webhook_id=webhook_id))

    @delete("/{webhook_id:uuid}", status_code=HTTP_200_OK)
    @result_handler(None, success_status=HTTP_204_NO_CONTENT)
    async def delete_webhook(
        self,
        webhook_id: UUID,
        action: FromDishka[DeleteWebhookAction],
    ) -> Result[None, WebhookError]:
        """Delete a webhook."""
        return await action.run(DeleteWebhookInput(webhook_id=webhook_id))

    @post("/trigger")
    @result_handler(TriggerWebhookResponse, success_status=HTTP_200_OK)
    async def trigger_webhook(
        self,
        data: TriggerWebhookRequest,
        action: FromDishka[TriggerWebhookAction],
    ) -> Result[DeliveryResult, WebhookError]:
        """Manually trigger a webhook delivery."""
        return await action.run(data)

    @get("/{webhook_id:uuid}/deliveries")
    async def get_deliveries(
        self,
        webhook_id: UUID,
        query: FromDishka[ListWebhookDeliveriesQuery],
        limit: int = 50,
        offset: int = 0,
    ) -> WebhookDeliveriesListResponse:
        """Get delivery history for a webhook."""
        result = await query.execute(
            ListWebhookDeliveriesQueryInput(
                webhook_id=webhook_id,
                limit=min(limit, 100),
                offset=offset,
            )
        )

        return WebhookDeliveriesListResponse(
            deliveries=[
                WebhookDeliveryResponse(
                    id=d.id,
                    webhook_id=d.webhook_id,
                    event_type=d.event_type,
                    status=d.status,
                    response_status=int(d.response_status) if d.response_status else None,
                    error_message=d.error_message,
                    attempt=d.attempt,
                    delivered_at=d.delivered_at,
                    created_at=d.created_at,
                )
                for d in result.deliveries
            ],
            total=result.total,
        )


class IncomingWebhookController(Controller):
    """Controller for receiving incoming webhooks from external services."""

    path = "/webhooks/incoming"
    tags = ["Webhooks"]

    @post("/stripe")
    async def stripe_webhook(
        self,
        request: Request,
    ) -> dict:
        """Receive Stripe webhook (virtual).

        In production, verify signature using Stripe SDK.
        """
        body = await request.body()
        signature = request.headers.get("stripe-signature", "")

        import logfire

        logfire.info(
            "📥 Received Stripe webhook",
            signature=signature[:20] + "..." if signature else "none",
            body_size=len(body),
        )

        # Virtual: always acknowledge
        return {"received": True}

    @post("/github")
    async def github_webhook(
        self,
        request: Request,
    ) -> dict:
        """Receive GitHub webhook (virtual).

        In production, verify X-Hub-Signature-256 header.
        """
        body = await request.body()
        signature = request.headers.get("x-hub-signature-256", "")
        event_type = request.headers.get("x-github-event", "unknown")

        import logfire

        logfire.info(
            "📥 Received GitHub webhook",
            event_type=event_type,
            signature=signature[:20] + "..." if signature else "none",
            body_size=len(body),
        )

        return {"received": True, "event": event_type}

    @post("/custom/{provider:str}")
    async def custom_webhook(
        self,
        provider: str,
        data: IncomingWebhookPayload,
        request: Request,
    ) -> dict:
        """Receive custom webhook from any provider.

        Signature can be verified using the X-Webhook-Signature header.
        """
        signature = request.headers.get("x-webhook-signature", "")

        import logfire

        logfire.info(
            "📥 Received custom webhook",
            provider=provider,
            event_type=data.event_type,
            has_signature=bool(signature),
        )

        # In production, verify signature and process event
        return {
            "received": True,
            "provider": provider,
            "event_type": data.event_type,
        }
