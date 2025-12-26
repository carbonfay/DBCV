"""VK Send Photo интеграция используя vk-api библиотеку."""
import random
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import vk_api
    from vk_api import VkApi
    from vk_api.upload import VkUpload
    from vk_api.exceptions import ApiError
    VK_API_AVAILABLE = True
except Exception:
    VK_API_AVAILABLE = False
    VkApi = None
    VkUpload = None
    ApiError = Exception


class VkSendPhotoIntegration(BaseIntegration):
    """Интеграция для отправки фото в VK через vk-api."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_send_photo",
            version="1.0.1",
            name="VK Send Photo",
            description="Отправка фото в VK (сообщение) через vk-api",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#4c75a3",
            config_schema={
                "type": "object",
                "required": ["peer_id", "photo_path"],
                "properties": {
                    "peer_id": {
                        "type": "integer",
                        "title": "Peer ID",
                        "description": "ID получателя (user_id / chat_id / conversation id)"
                    },
                    "photo_path": {
                        "type": "string",
                        "title": "Photo Path",
                        "description": "Путь к локальному файлу изображения на сервере"
                    },
                    "message": {
                        "type": "string",
                        "title": "Message",
                        "description": "Текст сообщения (опционально)",
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="vk-api>=11.9.9",
            examples=[
                {
                    "title": "Отправить фото пользователю",
                    "config": {
                        "peer_id": 12345678,
                        "photo_path": "/tmp/photo.jpg",
                        "message": "Привет!"
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Выполняет загрузку фото и отправку сообщения через VK API.

        Ожидает в `credentials` поле `access_token` или `token`.
        """
        if not VK_API_AVAILABLE:
            await logger.error("vk-api library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "vk-api library is not installed",
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id, provider="other", strategy="api_key"
        )

        if not creds:
            await logger.error("VK credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "VK access token not found in credentials",
                }
            }

        payload = creds.get("payload", creds)
        token = payload.get("access_token") or payload.get("token") or payload.get("vk_token")
        if not token:
            await logger.error("VK token not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "VK access token not present in credentials",
                }
            }

        peer_id = config.get("peer_id")
        photo_path = config.get("photo_path")
        message = config.get("message")

        if not peer_id or not photo_path:
            await logger.error("peer_id and photo_path are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "peer_id and photo_path are required",
                }
            }

        try:
            vk_session = VkApi(token=token)
            vk = vk_session.get_api()
            upload = VkUpload(vk_session)

            photos = upload.photo_messages([photo_path])
            if not photos:
                await logger.error("photo upload returned empty result")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": "Failed to upload photo",
                    }
                }

            p = photos[0]
            owner_id = p.get("owner_id")
            photo_id = p.get("id")
            access_key = p.get("access_key")
            attachment = f"photo{owner_id}_{photo_id}"
            if access_key:
                attachment = f"{attachment}_{access_key}"

            random_id = random.randint(1, 2 ** 31 - 1)
            send_result = vk.messages.send(
                peer_id=int(peer_id), random_id=random_id, attachment=attachment, message=message or ""
            )

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "vk_send_result": send_result,
                        "attachment": attachment,
                    },
                }
            }

        except ApiError as e:
            await logger.error(f"VK API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, "code", 500),
                    "description": str(e),
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error in VK integration: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }
