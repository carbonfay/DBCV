"""Stripe интеграции."""
from .get_payment import StripeGetPaymentIntegration
from ...integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(StripeGetPaymentIntegration())

