from .create_task import AmoCrmCreateTaskIntegration
from app.integrations.registry import registry

# Регистрируем интеграцию
registry.register(AmoCrmCreateTaskIntegration())
