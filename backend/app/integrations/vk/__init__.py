"""VK интеграции."""
from .create_comment import VkCreateCommentIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(VkCreateCommentIntegration())