"""YooKassa интеграции."""
from .get_receipt import YooKassaGetReceiptIntegration
from .refund import YooKassaRefundIntegration
from .create_receipt import YooKassaCreateReceiptIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YooKassaGetReceiptIntegration())
registry.register(YooKassaRefundIntegration())
registry.register(YooKassaCreateReceiptIntegration())

