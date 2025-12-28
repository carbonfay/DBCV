"""Telegram Get Chat Members Count интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Используем python-telegram-bot библиотеку
try:
    from telegram import Bot
    from telegram.error import TelegramError, BadRequest, Forbidden, InvalidToken
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


class TelegramGetChatMembersCountIntegration(BaseIntegration):
    """Интеграция для получения количества участников чата в Telegram."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_get_chat_members_count",
            version="1.0.0",
            name="Telegram Get Chat Members Count",
            description="Получение количества участников (подписчиков) в Telegram чате, группе или канале",
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
                        "description": "ID чата, группы или канала (можно использовать @username для публичных каналов/групп)"
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot",
            examples=[
                {
                    "title": "Получить количество подписчиков канала по username",
                    "config": {
                        "chat_id": "@channelname"
                    }
                },
                {
                    "title": "Получить количество участников группы по ID",
                    "config": {
                        "chat_id": "-1001234567890"
                    }
                },
                {
                    "title": "Получить количество участников супергруппы",
                    "config": {
                        "chat_id": "-100987654321"
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
        Выполняет получение количества участников чата через Telegram Bot API.
        
        API документация: https://core.telegram.org/bots/api#getchatmembercount
        
        Args:
            config: Параметры интеграции (chat_id)
            credentials_resolver: Резолвер для получения bot token
            bot_id: ID бота
            logger: Логгер
        
        Returns:
            Результат с количеством участников чата
        """
        if not TELEGRAM_AVAILABLE:
            await logger.error("python-telegram-bot library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "python-telegram-bot library is not installed"
                }
            }
        
        # Получаем chat_id из config
        chat_id = config.get("chat_id")
        if not chat_id:
            await logger.error("chat_id parameter is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id parameter is required"
                }
            }
        
        # Получаем bot token из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="telegram",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Telegram bot token not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Telegram bot token not found in credentials"
                }
            }
        
        # Получаем bot token из credentials
        payload = creds.get("payload", {})
        if not payload:
            payload = creds
        
        bot_token = payload.get("bot_token") or payload.get("token") or payload.get("api_key")
        if not bot_token:
            await logger.error(f"bot_token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "bot_token not found in credentials"
                }
            }
        
        try:
            # Создаем экземпляр Bot с токеном
            bot = Bot(token=bot_token)
            
            # Вызываем метод get_chat_member_count библиотеки
            # Это асинхронный метод, который возвращает количество участников
            member_count = await bot.get_chat_member_count(chat_id=chat_id)
            
            await logger.info(f"Successfully got chat members count for chat_id={chat_id}: {member_count}")
            
            # Получаем дополнительную информацию о чате
            try:
                chat_info = await bot.get_chat(chat_id=chat_id)
                chat_data = {
                    "id": chat_info.id,
                    "type": chat_info.type,
                    "title": chat_info.title,
                    "username": chat_info.username,
                }
            except Exception as e:
                await logger.warning(f"Could not get additional chat info: {e}")
                chat_data = {
                    "id": chat_id,
                    "type": "unknown"
                }
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "chat_id": chat_id,
                        "member_count": member_count,
                        "chat": chat_data
                    }
                }
            }
        
        except InvalidToken as e:
            await logger.error(f"Invalid Telegram bot token: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": f"Invalid Telegram bot token: {str(e)}"
                }
            }
        
        except BadRequest as e:
            # Ошибки вроде "Chat not found", "Invalid chat_id", etc.
            await logger.error(f"Telegram API bad request: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Bad request: {str(e)}"
                }
            }
        
        except Forbidden as e:
            # Бот был заблокирован пользователем или удален из чата
            await logger.error(f"Telegram API forbidden: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 403,
                    "description": f"Forbidden: {str(e)}. Bot may not have access to this chat or was blocked."
                }
            }
        
        except TelegramError as e:
            # Общие ошибки Telegram API
            await logger.error(f"Telegram API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Telegram API error: {str(e)}"
                }
            }
        
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(e)}"
                }
            }
