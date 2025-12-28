"""Telegram интеграции."""
from app.integrations.telegram.get_chat_members_count import TelegramGetChatMembersCountIntegration
from app.integrations.registry import registry

# Регистрируем интеграции
registry.register(TelegramGetChatMembersCountIntegration())

__all__ = [
    "TelegramGetChatMembersCountIntegration",
]