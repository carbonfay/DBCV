"""Telegram Get Chat интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception


class TelegramGetChatIntegration(BaseIntegration):
    """Интеграция для получения информации о чате в Telegram через Bot API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_get_chat",
            version="1.0.0",
            name="Telegram Get Chat",
            description="Получение информации о чате или пользователе в Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о чате",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}"
                    }
                }
            ]
        )
    
    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """
        Выполняет интеграцию используя библиотеку python-telegram-bot.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        if not TELEGRAM_BOT_AVAILABLE:
            await logger.error("python-telegram-bot library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "python-telegram-bot library is not installed"
                }
            }
        
        # Получаем bot_token из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="telegram",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Telegram credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Telegram bot_token not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        bot_token = payload.get("bot_token") or payload.get("token")
        if not bot_token:
            await logger.error(f"bot_token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "bot_token not found in credentials"
                }
            }
        
        # Получаем параметры из config
        chat_id = config.get("chat_id")
        
        if not chat_id:
            await logger.error("chat_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id is required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            chat = await bot.get_chat(chat_id=str(chat_id))
            
            # Извлекаем информацию о чате
            result = {
                "id": chat.id,
                "type": chat.type,
                "title": getattr(chat, 'title', None),
                "username": getattr(chat, 'username', None),
                "first_name": getattr(chat, 'first_name', None),
                "last_name": getattr(chat, 'last_name', None),
                "description": getattr(chat, 'description', None),
                "invite_link": getattr(chat, 'invite_link', None),
                "member_count": getattr(chat, 'member_count', None),
                "is_forum": getattr(chat, 'is_forum', None),
                "has_protected_content": getattr(chat, 'has_protected_content', None),
                "can_set_sticker_set": getattr(chat, 'can_set_sticker_set', None),
                "permissions": {
                    "can_send_messages": getattr(chat.permissions, 'can_send_messages', None) if chat.permissions else None,
                    "can_send_media_messages": getattr(chat.permissions, 'can_send_media_messages', None) if chat.permissions else None,
                    "can_send_polls": getattr(chat.permissions, 'can_send_polls', None) if chat.permissions else None,
                    "can_send_other_messages": getattr(chat.permissions, 'can_send_other_messages', None) if chat.permissions else None,
                    "can_add_web_page_previews": getattr(chat.permissions, 'can_add_web_page_previews', None) if chat.permissions else None,
                    "can_change_info": getattr(chat.permissions, 'can_change_info', None) if chat.permissions else None,
                    "can_invite_users": getattr(chat.permissions, 'can_invite_users', None) if chat.permissions else None,
                    "can_pin_messages": getattr(chat.permissions, 'can_pin_messages', None) if chat.permissions else None,
                } if chat.permissions else None
            }
            
            await logger.info(f"Successfully retrieved chat info for ID: {chat_id}")
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.error_code if hasattr(e, 'error_code') else 500,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }