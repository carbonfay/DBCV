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
    """Интеграция для получения обновлений от Telegram Bot API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_get_updates",
            version="1.0.0",
            name="Telegram Get Updates",
            description="Получение обновлений (сообщений, действий и т.д.) от Telegram Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "properties": {
                    "offset": {
                        "type": "integer",
                        "title": "Offset",
                        "description": "Смещение для получения обновлений (для пагинации)",
                        "default": 0
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Limit",
                        "description": "Количество обновлений для получения (максимум 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10
                    },
                    "timeout": {
                        "type": "integer",
                        "title": "Timeout",
                        "description": "Таймаут ожидания обновлений в секундах",
                        "default": 0
                    },
                    "allowed_updates": {
                        "type": "array",
                        "title": "Allowed Updates",
                        "description": "Список типов обновлений для получения",
                        "items": {
                            "type": "string",
                            "enum": [
                                "message", "edited_message", "channel_post", 
                                "edited_channel_post", "inline_query", 
                                "chosen_inline_result", "callback_query", 
                                "shipping_query", "pre_checkout_query", 
                                "poll", "poll_answer", "my_chat_member", 
                                "chat_member", "chat_join_request"
                            ]
                        }
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить последние 10 обновлений",
                    "config": {
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
        offset = config.get("offset", 0)
        limit = config.get("limit", 10)
        timeout = config.get("timeout", 0)
        allowed_updates = config.get("allowed_updates")

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            
            # Получаем обновления
            updates = await bot.get_updates(
                offset=offset,
                limit=limit,
                timeout=timeout,
                allowed_updates=allowed_updates
            )

            # Подготовим результат
            result_updates = []
            for update in updates:
                update_data = {
                    "update_id": update.update_id,
                }
                
                # Добавляем типы обновлений, которые присутствуют
                if update.message:
                    update_data["message"] = {
                        "message_id": update.message.message_id,
                        "date": update.message.date,
                        "chat": {
                            "id": update.message.chat.id,
                            "type": update.message.chat.type,
                            "title": getattr(update.message.chat, 'title', None),
                            "username": getattr(update.message.chat, 'username', None),
                            "first_name": getattr(update.message.chat, 'first_name', None),
                            "last_name": getattr(update.message.chat, 'last_name', None),
                        },
                        "from_user": {
                            "id": update.message.from_user.id,
                            "is_bot": update.message.from_user.is_bot,
                            "first_name": update.message.from_user.first_name,
                            "last_name": getattr(update.message.from_user, 'last_name', None),
                            "username": getattr(update.message.from_user, 'username', None),
                        } if update.message.from_user else None,
                        "text": update.message.text,
                        "caption": getattr(update.message, 'caption', None),
                    }
                
                if update.edited_message:
                    update_data["edited_message"] = {
                        "message_id": update.edited_message.message_id,
                        "date": update.edited_message.date,
                        "chat": {
                            "id": update.edited_message.chat.id,
                            "type": update.edited_message.chat.type,
                        },
                        "text": update.edited_message.text,
                    }
                
                if update.callback_query:
                    update_data["callback_query"] = {
                        "id": update.callback_query.id,
                        "from_user": {
                            "id": update.callback_query.from_user.id,
                            "first_name": update.callback_query.from_user.first_name,
                        },
                        "message": {
                            "message_id": update.callback_query.message.message_id,
                            "text": update.callback_query.message.text,
                        } if update.callback_query.message else None,
                        "data": update.callback_query.data,
                    }
                
                result_updates.append(update_data)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "updates": result_updates,
                        "total_updates": len(result_updates)
                    }
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

