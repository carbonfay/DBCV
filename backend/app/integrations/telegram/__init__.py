"""Telegram интеграции."""
from .edit_message import TelegramEditMessageIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramEditMessageIntegration())