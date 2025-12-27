from .get_current import OpenweathermapGetCurrentIntegration
from app.integrations.registry import registry

# Регистрация интеграции
registry.register(OpenweathermapGetCurrentIntegration())
