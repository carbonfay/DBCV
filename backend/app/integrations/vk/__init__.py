"""VK интеграции."""
from .Create_Comment import VkCreateCommentIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(VkCreateCommentIntegration())
