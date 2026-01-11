"""YooKassa интеграции."""
from .create_refund import YooKassaCreateRefundIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YooKassaCreateRefundIntegration())
