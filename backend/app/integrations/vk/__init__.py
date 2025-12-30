"""VK интеграции."""
from .Create_Comment import VkCreateCommentIntegration
from .Get_Friends import VkGetFriendsIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(VkCreateCommentIntegration())
registry.register(VkGetFriendsIntegration())
