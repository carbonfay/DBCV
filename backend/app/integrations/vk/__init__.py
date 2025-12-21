from .send_photo import VkSendPhotoIntegration
from app.integrations.registry import registry

# Регистрация интеграции
registry.register(VkSendPhotoIntegration())
