"""Telegram интеграции."""
from .send_message import TelegramSendMessageIntegration
from .send_photo import TelegramSendPhotoIntegration
from .send_document_old import TelegramSendDocumentOldIntegration
from .get_user_info import TelegramGetUserInfoIntegration
from .get_updates import TelegramGetUpdatesIntegration
from .send_inline_keyboard import TelegramSendInlineKeyboardIntegration
from .send_voice import TelegramSendVoiceIntegration
from .send_poll import TelegramSendPollIntegration
from .get_chat import TelegramGetChatIntegration
from .send_document import TelegramSendDocumentIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(TelegramSendMessageIntegration())
registry.register(TelegramSendPhotoIntegration())
registry.register(TelegramSendDocumentOldIntegration())
registry.register(TelegramGetUserInfoIntegration())
registry.register(TelegramGetUpdatesIntegration())
registry.register(TelegramSendInlineKeyboardIntegration())
registry.register(TelegramSendVoiceIntegration())
registry.register(TelegramSendPollIntegration())
registry.register(TelegramGetChatIntegration())
registry.register(TelegramSendDocumentIntegration())

