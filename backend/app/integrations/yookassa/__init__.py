"""YooKassa интеграции."""
from .cancel_payment import YooKassaCancelPaymentIntegration
from .refund import YooKassaRefundIntegration
from .get_receipt import YooKassaGetReceiptIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YooKassaCancelPaymentIntegration())
registry.register(YooKassaRefundIntegration())
registry.register(YooKassaGetReceiptIntegration())
