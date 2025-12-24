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

        if not chat_id or chat_id == "":
            await logger.error(f"chat_id is required, got: {chat_id}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"chat_id is required, got: '{chat_id}'. Make sure the variable is properly set in the context."
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            chat = await bot.get_chat(chat_id=str(chat_id))

            # Извлекаем полную информацию о чате с использованием всех доступных атрибутов
            result = {
                "id": chat.id,
                "type": chat.type,
                "title": getattr(chat, 'title', None),
                "username": getattr(chat, 'username', None),
                "first_name": getattr(chat, 'first_name', None),
                "last_name": getattr(chat, 'last_name', None),
                "bio": getattr(chat, 'bio', None),  # био пользователя или описание канала
                "description": getattr(chat, 'description', None),  # описание супергруппы или канала
                "invite_link": getattr(chat, 'invite_link', None),
                "pinned_message": getattr(chat, 'pinned_message', None),  # закрепленное сообщение
                "permissions": {
                    "can_send_messages": getattr(chat.permissions, 'can_send_messages', None) if chat.permissions else None,
                    "can_send_media_messages": getattr(chat.permissions, 'can_send_media_messages', None) if chat.permissions else None,
                    "can_send_polls": getattr(chat.permissions, 'can_send_polls', None) if chat.permissions else None,
                    "can_send_other_messages": getattr(chat.permissions, 'can_send_other_messages', None) if chat.permissions else None,
                    "can_add_web_page_previews": getattr(chat.permissions, 'can_add_web_page_previews', None) if chat.permissions else None,
                    "can_change_info": getattr(chat.permissions, 'can_change_info', None) if chat.permissions else None,
                    "can_invite_users": getattr(chat.permissions, 'can_invite_users', None) if chat.permissions else None,
                    "can_pin_messages": getattr(chat.permissions, 'can_pin_messages', None) if chat.permissions else None,
                    "can_manage_topics": getattr(chat.permissions, 'can_manage_topics', None) if chat.permissions else None,  # для форумов
                } if chat.permissions else None,
                "slow_mode_delay": getattr(chat, 'slow_mode_delay', None),  # задержка медленного режима
                "message_auto_delete_time": getattr(chat, 'message_auto_delete_time', None),  # время автоудаления сообщений
                "has_protected_content": getattr(chat, 'has_protected_content', None),
                "has_visible_history": getattr(chat, 'has_visible_history', None),  # видимость истории для новых участников
                "sticker_set_name": getattr(chat, 'sticker_set_name', None),  # название набора стикеров
                "can_set_sticker_set": getattr(chat, 'can_set_sticker_set', None),
                "linked_chat_id": getattr(chat, 'linked_chat_id', None),  # ID связанного чата (для каналов)
                "location": {
                    "location": {
                        "longitude": getattr(getattr(chat, 'location', None), 'location', None).longitude if getattr(chat, 'location', None) and getattr(getattr(chat, 'location', None), 'location', None) else None,
                        "latitude": getattr(getattr(chat, 'location', None), 'location', None).latitude if getattr(chat, 'location', None) and getattr(getattr(chat, 'location', None), 'location', None) else None,
                    } if getattr(chat, 'location', None) else None,
                    "address": getattr(getattr(chat, 'location', None), 'address', None) if getattr(chat, 'location', None) else None,
                } if getattr(chat, 'location', None) else None,
                "join_to_send_messages": getattr(chat, 'join_to_send_messages', None),  # нужно присоединиться, чтобы отправлять сообщения
                "join_by_request": getattr(chat, 'join_by_request', None),  # нужно запросить присоединение
                "is_forum": getattr(chat, 'is_forum', None),  # является ли чат форумом
                "active_usernames": getattr(chat, 'active_usernames', None),  # активные юзернеймы
                "emoji_status_custom_emoji_id": getattr(chat, 'emoji_status_custom_emoji_id', None),  # кастомный эмодзи статус
                "emoji_status_expiration_date": getattr(chat, 'emoji_status_expiration_date', None),  # срок действия эмодзи статуса
                "has_aggressive_anti_spam_enabled": getattr(chat, 'has_aggressive_anti_spam_enabled', None),  # включена ли агрессивная защита от спама
                "has_hidden_members": getattr(chat, 'has_hidden_members', None),  # есть ли скрытые участники
                "has_restricted_voice_and_video_messages": getattr(chat, 'has_restricted_voice_and_video_messages', None),  # ограничены ли голосовые и видео сообщения
                "has_scheduled_messages": getattr(chat, 'has_scheduled_messages', None),  # есть ли запланированные сообщения
                "is_joined": getattr(chat, 'is_joined', None),  # присоединен ли бот к чату
                "is_marked_as_unread": getattr(chat, 'is_marked_as_unread', None),  # отмечен ли чат как непрочитанный
                "message_thread_id": getattr(chat, 'message_thread_id', None),  # ID темы сообщений
                "photo": {
                    "small_file_id": getattr(getattr(chat, 'photo', None), 'small_file_id', None),
                    "small_file_unique_id": getattr(getattr(chat, 'photo', None), 'small_file_unique_id', None),
                    "big_file_id": getattr(getattr(chat, 'photo', None), 'big_file_id', None),
                    "big_file_unique_id": getattr(getattr(chat, 'photo', None), 'big_file_unique_id', None),
                } if getattr(chat, 'photo', None) else None,
                "available_reactions": getattr(chat, 'available_reactions', None),  # доступные реакции
                "accent_color_id": getattr(chat, 'accent_color_id', None),  # ID акцентного цвета
                "background_custom_emoji_id": getattr(chat, 'background_custom_emoji_id', None),  # кастомный эмодзи фона
                "profile_accent_color_id": getattr(chat, 'profile_accent_color_id', None),  # ID акцентного цвета профиля
                "profile_background_custom_emoji_id": getattr(chat, 'profile_background_custom_emoji_id', None),  # кастомный эмодзи фона профиля
                "custom_emoji_sticker_set_name": getattr(chat, 'custom_emoji_sticker_set_name', None),  # название набора кастомных эмодзи
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