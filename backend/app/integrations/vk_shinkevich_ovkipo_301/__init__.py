from .send_message import VkSendMessageIntegration
from .send_photo import VkSendPhotoIntegration
from .get_user import VkGetUserInfoIntegration
from app.integrations.registry import registry

registry.register(VkSendMessageIntegration())
registry.register(VkSendPhotoIntegration())
registry.register(VkGetUserInfoIntegration())
