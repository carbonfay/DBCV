import asyncio
import random
from typing import Dict, Any
from uuid import UUID

import vk_api
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

class VkSendMessageIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_send_message_shinkevichOVKIPo_301",
            version="1.0.0",
            name="VK Send Message",
            description="Отправка текстового сообщения пользователю ВКонтакте",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#0077FF",
            credentials_provider="vk",
            credentials_strategy="api_key",
            library_name="vk_api",
            config_schema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "title": "ID пользователя",
                        "description": "ID пользователя ВКонтакте (числовой)",
                        "examples": [123456789]
                    },
                    "message": {
                        "type": "string",
                        "title": "Сообщение",
                        "description": "Текст сообщения",
                        "minLength": 1
                    }
                },
                "required": ["user_id", "message"],
                "examples": [
                    {
                        "user_id": 1,
                        "message": "Привет из DBCV!"
                    }
                ]
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
            provider="vk",
            strategy="api_key"
        )
        
        if not creds:
            return {"response": {"ok": False, "error_code": 401, "description": "Credentials for VK not found"}}

        # === УНИВЕРСАЛЬНОЕ ПОЛУЧЕНИЕ ТОКЕНА ===
        payload = creds.get("payload") or {}
        token = payload.get("token") or payload.get("api_key")
        
        # Если в payload пусто, ищем на верхнем уровне
        if not token:
            token = creds.get("token") or creds.get("api_key")

        if not token:
             return {"response": {"ok": False, "error_code": 401, "description": "Token not found in credentials"}}
        # =======================================

        user_id = config.get("user_id")
        message = config.get("message")

        try:
            def _send():
                vk_session = vk_api.VkApi(token=token)
                vk = vk_session.get_api()
                return vk.messages.send(
                    user_id=user_id,
                    message=message,
                    random_id=random.randint(1, 2147483647)
                )

            result = await asyncio.to_thread(_send)
            return {"response": {"ok": True, "result": result}}

        except vk_api.ApiError as e:
            logger.error(f"VK API Error (Send Message): {e}")
            return {"response": {"ok": False, "error_code": e.code, "description": str(e)}}
        except Exception as e:
            logger.error(f"Unexpected error in VK Send Message: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}