"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .forward_message import TelegramForwardMessageIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramForwardMessageIntegration())