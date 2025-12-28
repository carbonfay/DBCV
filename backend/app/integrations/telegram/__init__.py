"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .send_video_note import TelegramSendVideoNoteIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramSendVideoNoteIntegration())

