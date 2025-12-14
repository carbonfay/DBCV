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
    """Интеграция для получения информации о чате в Telegram."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_get_chat",
            version="1.0.0",
            name="Telegram Get Chat",
            description="Получение информации о чате в Telegram через Bot API",
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
                        "description": "ID чата для получения информации (можно использовать переменные: {$user.telegram_chat_id$})"
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о чате пользователя",
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
            
            # Получаем информацию о чате
            chat_info = await bot.get_chat(chat_id=str(chat_id))

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": chat_info.id,
                        "type": chat_info.type,
                        "title": getattr(chat_info, 'title', None),
                        "username": chat_info.username,
                        "first_name": getattr(chat_info, 'first_name', None),
                        "last_name": getattr(chat_info, 'last_name', None),
                        "bio": getattr(chat_info, 'bio', None),
                        "description": getattr(chat_info, 'description', None),
                        "invite_link": getattr(chat_info, 'invite_link', None),
                        "pinned_message": {
                            "message_id": getattr(getattr(chat_info, 'pinned_message', None), 'message_id', None),
                            "text": getattr(getattr(chat_info, 'pinned_message', None), 'text', None),
                            "date": str(getattr(getattr(chat_info, 'pinned_message', None), 'date', None))
                        } if getattr(chat_info, 'pinned_message', None) else None,
                        "permissions": {
                            "can_send_messages": getattr(getattr(chat_info, 'permissions', None), 'can_send_messages', None),
                            "can_send_media_messages": getattr(getattr(chat_info, 'permissions', None), 'can_send_media_messages', None),
                            "can_send_polls": getattr(getattr(chat_info, 'permissions', None), 'can_send_polls', None),
                            "can_send_other_messages": getattr(getattr(chat_info, 'permissions', None), 'can_send_other_messages', None),
                            "can_add_web_page_previews": getattr(getattr(chat_info, 'permissions', None), 'can_add_web_page_previews', None),
                            "can_change_info": getattr(getattr(chat_info, 'permissions', None), 'can_change_info', None),
                            "can_invite_users": getattr(getattr(chat_info, 'permissions', None), 'can_invite_users', None),
                            "can_pin_messages": getattr(getattr(chat_info, 'permissions', None), 'can_pin_messages', None)
                        } if getattr(chat_info, 'permissions', None) else None,
                        "slow_mode_delay": getattr(chat_info, 'slow_mode_delay', None),
                        "message_auto_delete_time": getattr(chat_info, 'message_auto_delete_time', None),
                        "has_protected_content": getattr(chat_info, 'has_protected_content', None),
                        "sticker_set_name": getattr(chat_info, 'sticker_set_name', None),
                        "can_set_sticker_set": getattr(chat_info, 'can_set_sticker_set', None),
                        "linked_chat_id": getattr(chat_info, 'linked_chat_id', None),
                        "location": {
                            "location": {
                                "longitude": getattr(getattr(getattr(chat_info, 'location', None), 'location', None), 'longitude', None),
                                "latitude": getattr(getattr(getattr(chat_info, 'location', None), 'location', None), 'latitude', None),
                            },
                            "address": getattr(getattr(chat_info, 'location', None), 'address', None)
                        } if getattr(chat_info, 'location', None) else None
                    }
                }
            }
        except TelegramError as e:
            await logger.error(f"Telegram API error: {e}")
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

