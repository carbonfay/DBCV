"""Stripe интеграции."""
from .create_customer import StripeCreateCustomerIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(StripeCreateCustomerIntegration())

__all__ = [
    "StripeCreateCustomerIntegration"
]
