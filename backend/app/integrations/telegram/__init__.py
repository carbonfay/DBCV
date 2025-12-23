"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .send_voice import TelegramSendVoiceIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramSendVoiceIntegration())

