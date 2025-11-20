"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())

