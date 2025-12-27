"""VK интеграции."""
from .get_wall import VkGetWallIntegration
from app.integrations.registry import registry

# Регистрируем VK интеграции
registry.register(VkGetWallIntegration())
