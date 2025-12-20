"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .send_document import TelegramSendDocumentIntegration
from .get_updates import TelegramGetUpdatesIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramSendDocumentIntegration())
