"""YooKassa интеграции."""
from .get_payment import YookassaGetPaymentIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YookassaGetPaymentIntegration())
