"""WebhookModule DI providers."""

from dishka import Provider, Scope, provide

from src.Containers.VendorSection.WebhookModule.Data.Repositories.WebhookRepository import (
    WebhookRepository,
    WebhookDeliveryRepository,
)
from src.Containers.VendorSection.WebhookModule.Tasks.DeliverWebhookTask import (
    DeliverWebhookTask,
)
from src.Containers.VendorSection.WebhookModule.Actions.RegisterWebhookAction import (
    RegisterWebhookAction,
)
from src.Containers.VendorSection.WebhookModule.Actions.TriggerWebhookAction import (
    TriggerWebhookAction,
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
    register_webhook_action = provide(RegisterWebhookAction)
    trigger_webhook_action = provide(TriggerWebhookAction)



