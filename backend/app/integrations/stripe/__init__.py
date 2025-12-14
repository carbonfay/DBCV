"""Stripe интеграции."""
from .create_payment_intent import StripeCreatePaymentIntentIntegration
from .create_subscription import StripeCreateSubscriptionIntegration
from .cancel_subscription import StripeCancelSubscriptionIntegration
from .get_payment import StripeGetPaymentIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(StripeCreatePaymentIntentIntegration())
registry.register(StripeCreateSubscriptionIntegration())
registry.register(StripeCancelSubscriptionIntegration())
registry.register(StripeGetPaymentIntegration())
