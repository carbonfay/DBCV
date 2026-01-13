"""Telegram интеграции."""
from .get_user import TelegramGetUserIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramGetUserIntegration())

