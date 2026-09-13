"""Stripe интеграции."""
from .create_subscription import StripeCreateSubscriptionIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(StripeCreateSubscriptionIntegration())
