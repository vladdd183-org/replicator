"""WebhookModule DI providers."""

from dishka import Provider, Scope, provide

from src.Containers.VendorSection.WebhookModule.Actions.DeleteWebhookAction import (
    DeleteWebhookAction,
)
from src.Containers.VendorSection.WebhookModule.Actions.RegisterWebhookAction import (
    RegisterWebhookAction,
)
from src.Containers.VendorSection.WebhookModule.Actions.ResetWebhookAction import (
    ResetWebhookAction,
)
from src.Containers.VendorSection.WebhookModule.Actions.ToggleWebhookAction import (
    ToggleWebhookAction,
)
from src.Containers.VendorSection.WebhookModule.Actions.TriggerWebhookAction import (
    TriggerWebhookAction,
)
from src.Containers.VendorSection.WebhookModule.Data.Repositories.WebhookRepository import (
    WebhookDeliveryRepository,
    WebhookRepository,
)
from src.Containers.VendorSection.WebhookModule.Queries.GetWebhookQuery import GetWebhookQuery
from src.Containers.VendorSection.WebhookModule.Queries.ListWebhookDeliveriesQuery import (
    ListWebhookDeliveriesQuery,
)
from src.Containers.VendorSection.WebhookModule.Queries.ListWebhooksQuery import (
    ListWebhooksQuery,
)
from src.Containers.VendorSection.WebhookModule.Tasks.DeliverWebhookTask import (
    DeliverWebhookTask,
)


class WebhookModuleProvider(Provider):
    """App-scoped provider for WebhookModule."""

    scope = Scope.APP

    deliver_webhook_task = provide(DeliverWebhookTask)


class WebhookRequestProvider(Provider):
    """Request-scoped provider for WebhookModule."""

    scope = Scope.REQUEST

    webhook_repository = provide(WebhookRepository)
    webhook_delivery_repository = provide(WebhookDeliveryRepository)
    list_webhooks_query = provide(ListWebhooksQuery)
    get_webhook_query = provide(GetWebhookQuery)
    list_webhook_deliveries_query = provide(ListWebhookDeliveriesQuery)
    register_webhook_action = provide(RegisterWebhookAction)
    trigger_webhook_action = provide(TriggerWebhookAction)
    toggle_webhook_action = provide(ToggleWebhookAction)
    reset_webhook_action = provide(ResetWebhookAction)
    delete_webhook_action = provide(DeleteWebhookAction)
