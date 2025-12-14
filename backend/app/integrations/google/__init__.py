"""Google интеграции."""
from .read_sheet import GoogleSheetsReadIntegration
from .file_upload import GoogleDriveFileUploadIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GoogleSheetsReadIntegration())
registry.register(GoogleDriveFileUploadIntegration())
