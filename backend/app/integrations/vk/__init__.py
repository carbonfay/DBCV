"""VK интеграции."""
from .send_message import VkSendMessageIntegration
from .get_user import VkGetUserIntegration
from .get_group import VkGetGroupIntegration
from .get_friends import VkGetFriendsIntegration
from app.integrations.registry import registry

# Регистрируем VK интеграции
registry.register(VkSendMessageIntegration())
registry.register(VkGetUserIntegration())
registry.register(VkGetGroupIntegration())
registry.register(VkGetFriendsIntegration())
