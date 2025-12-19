"""Telegram Get User Info интеграция используя python-telegram-bot библиотеку."""
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


class TelegramGetUserInfoIntegration(BaseIntegration):
    """Интеграция для получения информации о пользователе Telegram через Bot API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_get_user_info",
            version="1.0.0",
            name="Telegram Get User Info",
            description="Получение информации о пользователе Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["user_id"],
                "properties": {
                    "user_id": {
                        "type": "string",
                        "title": "User ID",
                        "description": "ID пользователя Telegram для получения информации"
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о пользователе",
                    "config": {
                        "user_id": "{$user.telegram_user_id$}"
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
        user_id = config.get("user_id")

        if not user_id:
            await logger.error("user_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "user_id is required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            
            # Получаем информацию о пользователе
            user_info = await bot.get_chat_member(
                chat_id=str(user_id),
                user_id=str(user_id)
            )

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "user": {
                            "id": user_info.user.id,
                            "is_bot": user_info.user.is_bot,
                            "first_name": user_info.user.first_name,
                            "last_name": user_info.user.last_name,
                            "username": user_info.user.username,
                            "language_code": user_info.user.language_code,
                            "is_premium": getattr(user_info.user, 'is_premium', False),
                        },
                        "status": user_info.status,
                        "date": user_info.date,
                        "custom_title": user_info.custom_title
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

