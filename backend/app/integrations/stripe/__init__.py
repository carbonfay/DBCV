"""Stripe интеграции."""
from .create_payment_intent import StripeCreatePaymentIntentIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(StripeCreatePaymentIntentIntegration())
