"""VK интеграции."""
from .send_message import VKSendMessageIntegration
from .get_user import VKGetUserIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(VKSendMessageIntegration())
registry.register(VKGetUserIntegration())
