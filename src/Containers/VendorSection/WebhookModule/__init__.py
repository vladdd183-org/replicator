"""WebhookModule - Входящие и исходящие вебхуки.

Демонстрирует:
- Регистрация webhook endpoints
- Signature verification (HMAC)
- Retry logic с exponential backoff
- Webhook event queue
- Входящие/исходящие интеграции
"""

from src.Containers.VendorSection.WebhookModule.UI.API.Routes import webhook_router

__all__ = ["webhook_router"]
