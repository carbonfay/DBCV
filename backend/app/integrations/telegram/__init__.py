"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .get_user import TelegramGetUserIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramGetUserIntegration())

