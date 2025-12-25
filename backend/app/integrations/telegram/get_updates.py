"""Telegram Get Updates интеграция используя python-telegram-bot библиотеку.

Получает апдейты через Bot API (метод getUpdates).
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception


class TelegramGetUpdatesIntegration(BaseIntegration):
    """Интеграция для получения обновлений (getUpdates) из Telegram."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_get_updates",
            version="1.0.0",
            name="Telegram Get Updates",
            description="Получение обновлений через Telegram Bot API (getUpdates)",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": [],
                "properties": {
                    "offset": {"type": "integer", "title": "Offset"},
                    "limit": {"type": "integer", "title": "Limit"},
                    "timeout": {"type": "integer", "title": "Timeout"}
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        # Проверяем наличие библиотеки
        if not TELEGRAM_BOT_AVAILABLE:
            await logger.error("python-telegram-bot library is not available")
            return {"response": {"ok": False, "error_code": 500, "description": "python-telegram-bot library is not installed"}}

        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="telegram", strategy="api_key")
        if not creds:
            await logger.error("Telegram credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "Telegram bot_token not found in credentials"}}

        payload = creds.get("payload", {}) or creds
        bot_token = payload.get("bot_token") or payload.get("token")
        if not bot_token:
            await logger.error("bot_token not found in credentials")
            return {"response": {"ok": False, "error_code": 401, "description": "bot_token not found in credentials"}}

        offset = config.get("offset")
        limit = config.get("limit")
        timeout = config.get("timeout")

        try:
            bot = Bot(token=bot_token)
            # В python-telegram-bot 20+ методы асинхронны
            updates = await bot.get_updates(offset=offset, limit=limit, timeout=timeout)

            # Преобразуем апдейты в простую структуру
            result = []
            for u in updates:
                result.append({
                    "update_id": getattr(u, "update_id", None)
                })

            return {"response": {"ok": True, "result": result}}

        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {"response": {"ok": False, "error_code": getattr(e, 'error_code', 500), "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
