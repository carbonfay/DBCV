"""Storage интеграции."""
from .file_upload import DropboxFileUploadIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(DropboxFileUploadIntegration())
