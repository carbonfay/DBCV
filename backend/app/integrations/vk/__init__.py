"""VK интеграции."""
from .upload_photo import VkUploadPhotoIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(VkUploadPhotoIntegration())