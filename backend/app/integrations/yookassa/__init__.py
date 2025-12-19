from app.integrations.registry import registry
from app.integrations.yookassa.cancel_payment import (
    YooKassaCancelPaymentIntegration,
)
from app.integrations.yookassa.refund import (
    YooKassaRefundIntegration,
)

registry.register(YooKassaCancelPaymentIntegration())
registry.register(YooKassaRefundIntegration())

__all__ = [
    "YooKassaCancelPaymentIntegration",
    "YooKassaRefundIntegration",
]
