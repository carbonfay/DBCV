"""VK интеграции."""
from .send_message import VkSendMessageIntegration
from .get_user import VkGetUserIntegration
from app.integrations.registry import registry

# Регистрируем VK интеграции
registry.register(VkSendMessageIntegration())
registry.register(VkGetUserIntegration())
