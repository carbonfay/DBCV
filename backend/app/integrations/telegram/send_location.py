"""Telegram Send Location интеграция используя python-telegram-bot библиотеку."""
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


class TelegramSendLocationIntegration(BaseIntegration):
    """Интеграция для отправки геолокации в Telegram через python-telegram-bot."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_location",
            version="1.0.0",
            name="Telegram Send Location",
            description="Отправка геолокации в Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id", "latitude", "longitude"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "latitude": {
                        "type": "number",
                        "title": "Latitude",
                        "description": "Широта (например, 55.751244)"
                    },
                    "longitude": {
                        "type": "number",
                        "title": "Longitude",
                        "description": "Долгота (например, 37.618423)"
                    },
                    "disable_notification": {
                        "type": "boolean",
                        "title": "Disable Notification",
                        "description": "Отключить уведомление у пользователя",
                        "default": False
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправка геолокации",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "latitude": 55.751244,
                        "longitude": 37.618423
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

        payload = creds.get("payload", {})
        if not payload:
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

        chat_id = config.get("chat_id")
        latitude = config.get("latitude")
        longitude = config.get("longitude")
        disable_notification = config.get("disable_notification", False)

        if not chat_id or latitude is None or longitude is None:
            await logger.error("chat_id, latitude и longitude обязательны")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id, latitude и longitude обязательны"
                }
            }

        try:
            bot = Bot(token=bot_token)
            result = await bot.send_location(
                chat_id=str(chat_id),
                latitude=latitude,
                longitude=longitude,
                disable_notification=disable_notification
            )
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": result.message_id,
                        "chat": {
                            "id": result.chat.id,
                            "type": result.chat.type
                        },
                        "latitude": result.location.latitude,
                        "longitude": result.location.longitude,
                        "date": result.date
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
