"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .edit_message import TelegramEditMessageIntegration
from .get_chat_members_count import TelegramGetChatMembersCountIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramEditMessageIntegration())
registry.register(TelegramGetChatMembersCountIntegration())