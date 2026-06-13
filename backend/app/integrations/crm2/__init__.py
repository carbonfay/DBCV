""""""
from .get_update import AmoCRMCreateLeadIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(AmoCRMCreateLeadIntegration())

