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
            id="vk_send_photo",
            version="1.0.0",
            name="VK Send Photo",
            description="Загрузка и отправка фотографии пользователю ВКонтакте",
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
                    "photo_path": {
                        "type": "string",
                        "title": "Путь к фото",
                        "description": "Локальный путь к файлу внутри контейнера (например, /app/photos/cat.jpg)",
                        "minLength": 1
                    },
                    "caption": {
                        "type": "string",
                        "title": "Подпись",
                        "description": "Текст сообщения вместе с фото (необязательно)",
                    }
                },
                "required": ["user_id", "photo_path"],
                "examples": [
                    {
                        "user_id": 1,
                        "photo_path": "photos/cat.jpg",
                        "caption": "Смотри какой кот!"
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

        token = creds.get("token") or creds.get("api_key")
        if not token:
             return {"response": {"ok": False, "error_code": 401, "description": "Token not found"}}

        user_id = config.get("user_id")
        photo_path = config.get("photo_path")
        caption = config.get("caption", "")

        try:
            # Логика загрузки и отправки
            def _send_photo_logic():
                vk_session = vk_api.VkApi(token=token)
                vk = vk_session.get_api()
                upload = VkUpload(vk_session)

                # 1. Загружаем фото на сервер VK
                # Внимание: путь должен быть доступен внутри Docker контейнера
                photo_list = upload.photo_messages(photos=photo_path)
                if not photo_list:
                    raise Exception("Failed to upload photo to VK server")
                
                photo = photo_list[0]
                
                # 2. Формируем attachment: photo{owner_id}_{id}
                owner_id = photo['owner_id']
                media_id = photo['id']
                attachment = f"photo{owner_id}_{media_id}"

                # 3. Отправляем сообщение
                return vk.messages.send(
                    user_id=user_id,
                    message=caption,
                    attachment=attachment,
                    random_id=random.randint(1, 2147483647)
                )

            # Выполнение в потоке
            result = await asyncio.to_thread(_send_photo_logic)
            return {"response": {"ok": True, "result": result}}

        except FileNotFoundError:
            return {
                "response": {
                    "ok": False, 
                    "error_code": 400, 
                    "description": f"File not found at path: {photo_path}"
                }
            }
        except vk_api.ApiError as e:
            logger.error(f"VK API Error (Send Photo): {e}")
            return {"response": {"ok": False, "error_code": e.code, "description": str(e)}}
        except Exception as e:
            logger.error(f"Unexpected error in VK Send Photo: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}