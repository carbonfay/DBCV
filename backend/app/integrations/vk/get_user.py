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
            id="vk_get_user_info",
            version="1.0.0",
            name="VK Get User Info",
            description="Получение информации о пользователе ВКонтакте (Имя, Фамилия, Город)",
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
                        "type": "string",
                        "title": "ID пользователя",
                        "description": "ID пользователя (число или короткое имя, например 'durov')",
                        "minLength": 1
                    }
                },
                "required": ["user_id"],
                "examples": [
                    {"user_id": "1"},
                    {"user_id": "durov"}
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

        token = creds.get("token") or creds.get("api_key")
        if not token:
             return {"response": {"ok": False, "error_code": 401, "description": "Token not found"}}

        user_id_to_find = config.get("user_id")

        try:
            def _get_info():
                vk_session = vk_api.VkApi(token=token)
                vk = vk_session.get_api()
                # Запрашиваем информацию с полем city
                return vk.users.get(user_ids=user_id_to_find, fields="city")

            # Выполняем синхронный запрос в потоке
            users = await asyncio.to_thread(_get_info)
            
            if not users:
                return {"response": {"ok": False, "error_code": 404, "description": "User not found"}}

            user_info = users[0]
            
            # Парсим данные как в вашем боте
            first_name = user_info.get("first_name", "Неизвестно")
            last_name = user_info.get("last_name", "Неизвестно")
            
            city_data = user_info.get("city")
            city_title = city_data.get("title") if isinstance(city_data, dict) else "Не указан"

            # Формируем красивый текст
            formatted_text = (
                f"👤 Имя: {first_name}\n"
                f"👤 Фамилия: {last_name}\n"
                f"🏙 Город: {city_title}"
            )

            result_data = {
                "id": user_info.get("id"),
                "first_name": first_name,
                "last_name": last_name,
                "city": city_title,
                "formatted_text": formatted_text,
                "full_json": user_info
            }

            return {"response": {"ok": True, "result": result_data}}

        except vk_api.ApiError as e:
            logger.error(f"VK API Error (Get User): {e}")
            return {"response": {"ok": False, "error_code": e.code, "description": str(e)}}
        except Exception as e:
            logger.error(f"Unexpected error in VK Get User: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}