"""Stripe интеграции."""
from .refund import StripeRefundIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(StripeRefundIntegration())
