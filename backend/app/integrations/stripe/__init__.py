"""Stripe интеграции."""
from .cancel_subscription import StripeCancelSubscriptionIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(StripeCancelSubscriptionIntegration())
