"""VK интеграции."""
from .send_message import VkSendMessageIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(VkSendMessageIntegration())
