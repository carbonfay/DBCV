"""VK интеграции."""
from .send_message import VkSendMessageIntegration
from app.integrations.registry import registry

# Регистрируем VK интеграции
registry.register(VkSendMessageIntegration())
