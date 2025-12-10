"""YooKassa интеграции."""
from .cancel_payment import YooKassaCancelPaymentIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YooKassaCancelPaymentIntegration())
