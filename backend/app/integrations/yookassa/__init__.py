"""YooKassa интеграции."""
from .get_receipt import YooKassaGetReceiptIntegration
from .refund import YooKassaRefundIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YooKassaGetReceiptIntegration())
registry.register(YooKassaRefundIntegration())

