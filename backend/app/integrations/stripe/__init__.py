from .get_payment import StripeGetPaymentIntegration
from app.integrations.registry import registry

registry.register(StripeGetPaymentIntegration())
