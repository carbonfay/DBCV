"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .send_location import TelegramSendLocationIntegration  
from app.integrations.registry import registry

registry.register(TelegramSendMessageIntegration())
registry.register(TelegramSendLocationIntegration())    