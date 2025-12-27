"""YooKassa integrations package."""
from .get_payments import YoukassaGetPaymentsIntegration
from .get_payment import YoukassaGetPaymentIntegration
from .create_receipt import YoukassaCreateReceiptIntegration
from .create_payment import YoukassaCreatePaymentIntegration
from app.integrations.registry import registry

# Регистрация интеграций
registry.register(YoukassaGetPaymentsIntegration())
registry.register(YoukassaGetPaymentIntegration())
registry.register(YoukassaCreateReceiptIntegration())
registry.register(YoukassaCreatePaymentIntegration())

__all__ = [
    "YoukassaGetPaymentsIntegration",
    "YoukassaGetPaymentIntegration",
    "YoukassaCreateReceiptIntegration",
    "YoukassaCreatePaymentIntegration",
]
