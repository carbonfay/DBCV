"""PayPal integrations."""
from .create_subscription import PaypalCreateSubscriptionIntegration
from app.integrations.registry import registry

registry.register(PaypalCreateSubscriptionIntegration())

__all__ = ["PaypalCreateSubscriptionIntegration"]
