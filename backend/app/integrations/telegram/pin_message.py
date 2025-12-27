"""Telegram Pin Message интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку
try:
    from telegram import Bot
    from telegram.error import TelegramError, Forbidden, BadRequest, RetryAfter, NetworkError
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception
    Forbidden = Exception
    BadRequest = Exception
    RetryAfter = Exception
    NetworkError = Exception


class TelegramPinMessageIntegration(BaseIntegration):
    """Интеграция для закрепления сообщений в Telegram через python-telegram-bot."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_pin_message",
            version="1.0.0",
            name="Telegram Pin Message",
            description="Закрепление сообщения в группе, супергруппе или канале. Бот должен быть администратором с правом can_pin_messages",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id", "message_id"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "message_id": {
                        "type": "string",
                        "title": "Message ID",
                        "description": "ID сообщения для закрепления"
                    },
                    "disable_notification": {
                        "type": "boolean",
                        "title": "Disable Notification",
                        "description": "Закрепить без уведомления (true - без уведомления, false - с уведомлением)"
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Закрепить с уведомлением",
                    "config": {
                        "chat_id": "@my_channel",
                        "message_id": 42,
                        "disable_notification": False
                    }
                },
                {
                    "title": "Закрепить без уведомления",
                    "config": {
                        "chat_id": "-1001234567890",
                        "message_id": 100,
                        "disable_notification": True
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
        
        # Credentials возвращаются с ключом "payload"
        payload = creds.get("payload", {})
        if not payload:
            payload = creds
        
        bot_token = payload.get("bot_token")
        if not bot_token:
            await logger.error("bot_token not found in Telegram credentials payload")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "bot_token not found in credentials payload"
                }
            }
        
        try:
            # Создаем экземпляр бота
            bot = Bot(token=bot_token)
            
            # Формируем параметры для pin_chat_message
            pin_kwargs = {
                "chat_id": config["chat_id"],
                "message_id": config["message_id"],
            }
            
            # Добавляем опциональный параметр
            if "disable_notification" in config:
                pin_kwargs["disable_notification"] = config["disable_notification"]
            
            await logger.info(f"Pinning message {config['message_id']} in chat {config['chat_id']}")
            
            # Вызываем метод библиотеки
            result = await bot.pin_chat_message(**pin_kwargs)
            
            await logger.info(f"Message pinned successfully")
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "pinned": result
                    }
                }
            }
            
        except Forbidden as e:
            await logger.error(f"Forbidden error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "Forbidden",
                        "message": "Bot is not an administrator or has no rights to pin messages"
                    }
                }
            }
        except BadRequest as e:
            await logger.error(f"BadRequest error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "BadRequest",
                        "message": str(e)
                    }
                }
            }
        except RetryAfter as e:
            await logger.error(f"RetryAfter error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "RetryAfter",
                        "message": f"Flood control exceeded. Retry after {e.retry_after} seconds"
                    }
                }
            }
        except NetworkError as e:
            await logger.error(f"Network error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "NetworkError",
                        "message": "Network connection error"
                    }
                }
            }
        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "TelegramError",
                        "message": str(e)
                    }
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
