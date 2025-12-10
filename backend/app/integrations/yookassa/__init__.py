"""YooKassa интеграции."""
from .refund import YooKassaRefundIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YooKassaRefundIntegration())
