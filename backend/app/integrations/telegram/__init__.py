"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .Send_Location import TelegramSendLocationIntegration
from .Pin_Message import TelegramPinMessageIntegration
from app.integrations.registry import registry
# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramSendLocationIntegration())
registry.register(TelegramPinMessageIntegration())