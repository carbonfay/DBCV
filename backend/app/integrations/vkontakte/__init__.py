"""Vkontakte integrations package: import and register implementations."""
from .wall_get import VkontakteWallGetIntegration

from app.integrations.registry import registry


# Register integrations on import
registry.register(VkontakteWallGetIntegration())
