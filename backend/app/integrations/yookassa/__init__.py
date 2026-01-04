"""YooKassa интеграции."""

from app.integrations.registry import registry

from .create_payment import YookassaCreatePaymentIntegration
from .create_payment_with_items import YookassaCreatePaymentWithItemsIntegration
from .create_receipt import YookassaCreateReceiptIntegration
from .get_payment import YookassaGetPaymentIntegration

# Автоматическая регистрация интеграций
registry.register(YookassaGetPaymentIntegration())
registry.register(YookassaCreatePaymentIntegration())
registry.register(YookassaCreatePaymentWithItemsIntegration())
registry.register(YookassaCreateReceiptIntegration())
