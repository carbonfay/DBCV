"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .get_chat import TelegramGetChatIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramGetChatIntegration())

