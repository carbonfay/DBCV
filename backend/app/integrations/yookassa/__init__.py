from .refund import YookassaRefundIntegration
from app.integrations.registry import registry

registry.register(YookassaRefundIntegration())

__all__ = ["YookassaRefundIntegration"]

