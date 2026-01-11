"""PayPal интеграции."""
from .get_payout import PayPalGetPayoutIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(PayPalGetPayoutIntegration())

