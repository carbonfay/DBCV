"""Discord интеграции."""
from .send_message import DiscordSendMessageIntegration
from .send_photo import DiscordSendPhotoIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(DiscordSendMessageIntegration())
registry.register(DiscordSendPhotoIntegration())
