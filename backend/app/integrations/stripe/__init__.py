"""Stripe интеграции."""
from .get_customer import StripeGetCustomerIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(StripeGetCustomerIntegration())

__all__ = [
    "StripeGetCustomerIntegration"
]
