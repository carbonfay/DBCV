"""Telegram Get Updates интеграция используя python-telegram-bot библиотеку."""
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


class TelegramGetUpdatesIntegration(BaseIntegration):
    """Интеграция для получения обновлений из Telegram через python-telegram-bot."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_get_updates",
            version="1.0.0",
            name="Telegram Get Updates",
            description="Получение обновлений (сообщений, команд, и т.д.) из Telegram Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "properties": {
                    "offset": {
                        "type": "integer",
                        "title": "Offset",
                        "description": "Offset для получения обновлений (по умолчанию 0)",
                        "default": 0,
                        "minimum": 0
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Limit",
                        "description": "Максимальное количество обновлений (1-100, по умолчанию 100)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 100
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить последние обновления",
                    "config": {
                        "offset": 0,
                        "limit": 100
                    }
                },
                {
                    "title": "Получить обновления с смещением",
                    "config": {
                        "offset": 5,
                        "limit": 10
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
            config: Параметры интеграции (offset, limit)
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
        offset = config.get("offset", 0)
        limit = config.get("limit", 100)
        
        # Валидация параметров
        if not isinstance(offset, int) or offset < 0:
            await logger.error("offset must be a non-negative integer")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "offset must be a non-negative integer"
                }
            }
        
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            await logger.error("limit must be an integer between 1 and 100")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "limit must be an integer between 1 and 100"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            updates = await bot.get_updates(offset=offset, limit=limit)
            
            # Преобразуем обновления в формат для ответа
            updates_list = []
            for update in updates:
                update_dict = {
                    "update_id": update.update_id,
                    "message": None,
                    "edited_message": None,
                    "channel_post": None,
                    "edited_channel_post": None,
                    "inline_query": None,
                    "chosen_inline_result": None,
                    "callback_query": None,
                    "shipping_query": None,
                    "pre_checkout_query": None,
                    "poll": None,
                    "poll_answer": None,
                    "my_chat_member": None,
                    "chat_member": None,
                    "chat_join_request": None
                }
                
                # Заполняем доступные поля
                if update.message:
                    update_dict["message"] = {
                        "message_id": update.message.message_id,
                        "date": update.message.date,
                        "chat": {
                            "id": update.message.chat.id,
                            "type": update.message.chat.type,
                            "title": getattr(update.message.chat, 'title', None),
                            "username": getattr(update.message.chat, 'username', None),
                            "first_name": getattr(update.message.chat, 'first_name', None),
                            "last_name": getattr(update.message.chat, 'last_name', None)
                        },
                        "from": {
                            "id": update.message.from_user.id,
                            "is_bot": update.message.from_user.is_bot,
                            "first_name": update.message.from_user.first_name,
                            "last_name": getattr(update.message.from_user, 'last_name', None),
                            "username": getattr(update.message.from_user, 'username', None)
                        } if update.message.from_user else None,
                        "text": getattr(update.message, 'text', None),
                        "caption": getattr(update.message, 'caption', None),
                        "document": getattr(update.message, 'document', None),
                        "photo": getattr(update.message, 'photo', None),
                        "video": getattr(update.message, 'video', None),
                        "audio": getattr(update.message, 'audio', None),
                        "voice": getattr(update.message, 'voice', None),
                        "animation": getattr(update.message, 'animation', None),
                        "entities": [
                            {
                                "type": entity.type,
                                "offset": entity.offset,
                                "length": entity.length
                            }
                            for entity in (getattr(update.message, 'entities', None) or [])
                        ]
                    }
                
                updates_list.append(update_dict)
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "updates": updates_list,
                        "count": len(updates_list)
                    }
                }
            }
        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.error_code if hasattr(e, 'error_code') else 400,
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
