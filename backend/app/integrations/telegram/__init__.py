"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .send_audio import TelegramSendAudioIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramSendAudioIntegration())

