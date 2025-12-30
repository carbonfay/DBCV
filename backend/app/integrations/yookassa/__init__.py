"""YooKassa интеграции."""
from .get_receipt import YooKassaGetReceiptIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YooKassaGetReceiptIntegration())

