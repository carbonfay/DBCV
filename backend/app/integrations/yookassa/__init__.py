"""YooKassa интеграции."""
from .get_refund import YooKassaGetRefundIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YooKassaGetRefundIntegration())










