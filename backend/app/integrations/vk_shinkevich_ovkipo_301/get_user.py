import asyncio
from typing import Dict, Any
from uuid import UUID
import vk_api
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

class VkGetUserInfoIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_get_user_info_shinkevich_ovkipo_301",
            version="1.0.0",
            name="VK Get User Info (Shinkevich)",
            description="Инфо о пользователе (Shinkevich)",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#0077FF",
            credentials_provider="vk",
            credentials_strategy="api_key",
            library_name="vk_api",
            config_schema={
                "type": "object",
                "properties": {"user_id": {"type": "string", "title": "ID"}},
                "required": ["user_id"]
            }
        )

    async def execute(self, config, credentials_resolver, bot_id, logger) -> Dict[str, Any]:
        creds = await credentials_resolver.get_default_for(bot_id, "vk", "api_key")
        if not creds: return {"response": {"ok": False, "error_code": 401}}
        payload = creds.get("payload") or {}
        token = payload.get("token") or payload.get("api_key") or creds.get("token")
        if not token: return {"response": {"ok": False, "error_code": 401, "description": "Token not found"}}

        try:
            def _get():
                return vk_api.VkApi(token=token).get_api().users.get(user_ids=config.get("user_id"), fields="city")
            
            users = await asyncio.to_thread(_get)
            if not users: return {"response": {"ok": False, "error_code": 404}}
            
            u = users[0]
            city = u.get("city", {}).get("title") if isinstance(u.get("city"), dict) else "Не указан"
            fmt = f"👤 Имя: {u.get('first_name')}\n👤 Фамилия: {u.get('last_name')}\n🏙 Город: {city}"
            
            return {"response": {"ok": True, "result": {**u, "formatted_text": fmt}}}
        except Exception as e:
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
