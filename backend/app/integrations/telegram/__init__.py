"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .edit_message import TelegramEditMessageIntegration
from .delete_message import TelegramDeleteMessageIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramEditMessageIntegration())
registry.register(TelegramDeleteMessageIntegration())

__all__ = [
    "TelegramSendMessageIntegration",
    "TelegramEditMessageIntegration",
    "TelegramDeleteMessageIntegration"
]
