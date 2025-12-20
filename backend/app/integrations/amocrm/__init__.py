"""AmoCRM интеграции."""
from .create_task import AmoCRMIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(AmoCRMIntegration())

__all__ = ["AmoCRMIntegration"]
