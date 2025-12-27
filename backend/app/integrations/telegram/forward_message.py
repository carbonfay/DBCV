"""Telegram Forward Message интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
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


class TelegramForwardMessageIntegration(BaseIntegration):
    """Интеграция для пересылки сообщений в Telegram через python-telegram-bot."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_forward_message",
            version="1.0.0",
            name="Telegram Forward Message",
            description="Пересылка сообщения из одного чата в другой через Bot API с сохранением автора и источника",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id", "from_chat_id", "message_id"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_to_chat_id$})"
                    },
                    "from_chat_id": {
                        "type": "string",
                        "title": "From Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_from_chat_id$})"
                    },
                    "message_id": {
                        "type": "string",
                        "title": "Message ID",
                        "description": "ID сообщения для пересылки"
                    },
                    "message_thread_id": {
                        "type": "string", 
                        "description": "ID темы (для forum supergroups, опционально)"
                    },
                    "disable_notification": {
                        "type": "boolean",
                        "title": "Disable Notification",
                        "description": "Отправить без звука"
                    },
                    "protect_content": {
                        "type": "boolean",
                        "title": "Protect Content",
                        "description": "Запретить пересылку/сохранение сообщения"
                    } 
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Простая пересылка",
                    "config": {
                        "chat_id": "@my_channel",
                        "from_chat_id": "123456789",
                        "message_id": 42
                    }
                },
                {
                    "title": "Пересылка с защитой контента",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "from_chat_id": "@source_channel",
                        "message_id": 100,
                        "protect_content": True,
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
            # Создаем экземпляр бота (НЕ Application, т.к. используем как сервисный клиент)
            bot = Bot(token=bot_token)
            
            # Формируем параметры для forward_message
            forward_kwargs = {
                "chat_id": config["chat_id"],
                "from_chat_id": config["from_chat_id"],
                "message_id": config["message_id"],
            }
            
            # Добавляем опциональные параметры
            if "message_thread_id" in config:
                forward_kwargs["message_thread_id"] = config["message_thread_id"]
            if "disable_notification" in config:
                forward_kwargs["disable_notification"] = config["disable_notification"]
            if "protect_content" in config:
                forward_kwargs["protect_content"] = config["protect_content"]
            
            await logger.info(f"Forwarding message from {config['from_chat_id']} to {config['chat_id']}, message_id={config['message_id']}")
            
            # Вызываем метод библиотеки
            result = await bot.forward_message(**forward_kwargs)
            
            await logger.info(f"Message forwarded successfully: new message_id={result.message_id}")
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": result.message_id,
                        "date": result.date.timestamp() if result.date else None,
                        "chat": {
                            "id": result.chat.id,
                            "type": result.chat.type,
                            "title": result.chat.title if hasattr(result.chat, "title") else None,
                            "username": result.chat.username if hasattr(result.chat, "username") else None
                        },
                        "from": {
                            "id": result.from_user.id if result.from_user else None,
                            "is_bot": result.from_user.is_bot if result.from_user else None,
                            "first_name": result.from_user.first_name if result.from_user else None,
                            "username": result.from_user.username if result.from_user else None
                        } if result.from_user else None,
                        "text": result.text if hasattr(result, "text") else None
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
                        "message": "Bot is blocked by user or has no access to chat"
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
