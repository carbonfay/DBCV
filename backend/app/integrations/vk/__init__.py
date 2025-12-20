from .get_user import VkGetUserIntegration
from app.integrations.registry import registry

registry.register(VkGetUserIntegration())
