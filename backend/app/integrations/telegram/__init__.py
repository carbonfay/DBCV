"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .telegram_edit_message import TelegramEditMessageIntegration

from app.integrations.registry import registry


# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramEditMessageIntegration())

