"""Telegram Get Updates интеграция (заглушка).

Этот файл создан для целей коммита — реализация может быть добавлена позже.
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class TelegramGetUpdatesIntegration(BaseIntegration):
    """Заглушка интеграции для получения обновлений (getUpdates).

    Реальная реализация должна использовать python-telegram-bot и
    credentials_resolver аналогично другим интеграциям.
    """

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_get_updates",
            version="1.0.0",
            name="Telegram Get Updates (stub)",
            description="Заглушка для интеграции getUpdates",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "properties": {}
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name=None,
            examples=[]
        )

    async def execute(self, config: Dict[str, Any], credentials_resolver: CredentialsResolver, bot_id: UUID, logger: BotLogger) -> Dict[str, Any]:
        await logger.info("TelegramGetUpdatesIntegration is a stub and not implemented")
        return {"response": {"ok": False, "error_code": 501, "description": "Not implemented"}}
