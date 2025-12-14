"""YooKassa интеграции."""
from .create_payment import YooKassaCreatePaymentIntegration
from .capture_payment import YooKassaCapturePaymentIntegration
from .cancel_payment import YooKassaCancelPaymentIntegration
from .refund import YooKassaRefundIntegration
from .get_payment import YooKassaGetPaymentIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YooKassaCreatePaymentIntegration())
registry.register(YooKassaCapturePaymentIntegration())
registry.register(YooKassaCancelPaymentIntegration())
registry.register(YooKassaRefundIntegration())
registry.register(YooKassaGetPaymentIntegration())
