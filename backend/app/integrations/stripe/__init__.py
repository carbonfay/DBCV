"""Stripe интеграции."""
from .update_customer import StripeUpdateCustomerIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(StripeUpdateCustomerIntegration())
