"""AmoCRM интеграции."""
from .update_task import AmoCRMUpdateTaskIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(AmoCRMUpdateTaskIntegration())

__all__ = ["AmoCRMUpdateTaskIntegration"]
