"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .get_chat_members_count import TelegramGetChatMembersCountIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramGetChatMembersCountIntegration())

