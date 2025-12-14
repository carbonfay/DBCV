"""PayPal интеграции."""
from .create_payout import PayPalCreatePayoutIntegration
from .create_order import PayPalCreateOrderIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(PayPalCreatePayoutIntegration())
registry.register(PayPalCreateOrderIntegration())
