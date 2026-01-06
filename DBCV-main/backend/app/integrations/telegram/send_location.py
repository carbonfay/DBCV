from typing import Any, Dict
from uuid import UUID
from telegram import Bot
# Добавляем импорт IntegrationMetadata
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

class TelegramSendLocationIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        # Оборачиваем в класс IntegrationMetadata
        return IntegrationMetadata(
            id="telegram_send_location",
            name="Telegram Send Location",
            description="Отправка геолокации в Telegram чат",
            version="1.0.0",
            category="social",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc", 
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot",
            config_schema={
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string", "title": "Chat ID", "description": "ID чата"},
                    "latitude": {"type": "number", "title": "Latitude"},
                    "longitude": {"type": "number", "title": "Longitude"}
                },
                "required": ["chat_id", "latitude", "longitude"]
            }
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="telegram",
            strategy="api_key"
        )
        
        if not creds:
            return {"response": {"ok": False, "error_code": 401}}

        payload_creds = creds.get("payload", creds)
        bot_token = payload_creds.get("bot_token") or payload_creds.get("token")

        if not bot_token:
             return {"response": {"ok": False, "error_code": 401, "description": "Token not found"}}

        try:
            bot = Bot(token=bot_token)
            message = await bot.send_location(
                chat_id=config["chat_id"],
                latitude=float(config["latitude"]),
                longitude=float(config["longitude"])
            )
            return {"response": {"ok": True, "result": {"message_id": message.message_id}}}
        except Exception as e:
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}