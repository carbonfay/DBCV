"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .pin_message import TelegramPinMessageIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramPinMessageIntegration())

