"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .send_photo import TelegramSendPhotoIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramSendPhotoIntegration())

