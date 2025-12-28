import asyncio
import random
from typing import Dict, Any
from uuid import UUID
import vk_api
from vk_api.upload import VkUpload
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

class VkSendPhotoIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_send_photo_shinkevich_ovkipo_301",
            version="1.0.0",
            name="VK Send Photo (Shinkevich)",
            description="Отправка фото (Shinkevich)",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#0077FF",
            credentials_provider="vk",
            credentials_strategy="api_key",
            library_name="vk_api",
            config_schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "title": "ID"},
                    "photo_path": {"type": "string", "title": "Путь"},
                    "caption": {"type": "string", "title": "Подпись"}
                },
                "required": ["user_id", "photo_path"]
            }
        )

    async def execute(self, config, credentials_resolver, bot_id, logger) -> Dict[str, Any]:
        creds = await credentials_resolver.get_default_for(bot_id, "vk", "api_key")
        if not creds: return {"response": {"ok": False, "error_code": 401}}
        payload = creds.get("payload") or {}
        token = payload.get("token") or payload.get("api_key") or creds.get("token")
        if not token: return {"response": {"ok": False, "error_code": 401, "description": "Token not found"}}

        try:
            def _send():
                vk_s = vk_api.VkApi(token=token)
                api = vk_s.get_api()
                upl = VkUpload(vk_s)
                photos = upl.photo_messages(photos=config.get("photo_path"))
                if not photos: raise Exception("Upload failed")
                att = f"photo{photos[0]['owner_id']}_{photos[0]['id']}"
                return api.messages.send(
                    user_id=config.get("user_id"), 
                    message=config.get("caption", ""), 
                    attachment=att, 
                    random_id=random.randint(1, 2**31)
                )
            result = await asyncio.to_thread(_send)
            return {"response": {"ok": True, "result": result}}
        except Exception as e:
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
