"""YooKassa интеграции."""

from app.integrations.registry import registry

from .create_payment import YookassaCreatePaymentIntegration
from .get_payment import YookassaGetPaymentIntegration

# Автоматическая регистрация интеграций
registry.register(YookassaGetPaymentIntegration())
registry.register(YookassaCreatePaymentIntegration())
