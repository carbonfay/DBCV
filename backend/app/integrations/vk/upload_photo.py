"""VK Upload Photo интеграция используя vk-api библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import vk_api
    from vk_api.exceptions import VkApiError
    VK_API_AVAILABLE = True
except ImportError:
    VK_API_AVAILABLE = False
    vk_api = None
    VkApiError = Exception


class VkUploadPhotoIntegration(BaseIntegration):
    """Интеграция для загрузки фото в VK через vk-api."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_upload_photo",
            version="1.0.0",
            name="VK Upload Photo",
            description="Загрузка фото в альбом или на стену VK",
            category="social",
            icon_s3_key="icons/integrations/vk.svg",
            color="#4C75A3",
            config_schema={
                "type": "object",
                "required": ["photo"],
                "properties": {
                    "photo": {
                        "type": "string",
                        "title": "Photo File",
                        "description": "Путь к файлу фото для загрузки"
                    },
                    "album_id": {
                        "type": "integer",
                        "title": "Album ID",
                        "description": "ID альбома для загрузки (опционально, по умолчанию - на стену)",
                        "default": None
                    },
                    "group_id": {
                        "type": "integer",
                        "title": "Group ID",
                        "description": "ID группы для загрузки (опционально)",
                        "default": None
                    },
                    "caption": {
                        "type": "string",
                        "title": "Caption",
                        "description": "Подпись к фото",
                        "default": ""
                    }
                }
            },
            credentials_provider="vk",
            credentials_strategy="oauth",
            library_name="vk-api>=11.9.9" if VK_API_AVAILABLE else None,
            examples=[
                {
                    "title": "Загрузка фото на стену",
                    "config": {
                        "photo": "/path/to/photo.jpg",
                        "caption": "Мое фото"
                    }
                },
                {
                    "title": "Загрузка фото в альбом",
                    "config": {
                        "photo": "/path/to/photo.jpg",
                        "album_id": 123456789,
                        "caption": "Фото в альбом"
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
        Выполняет интеграцию используя библиотеку vk-api.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        if not VK_API_AVAILABLE:
            await logger.error("vk-api library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "vk-api library is not installed"
                }
            }
        
        # Получаем access_token из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="vk",
            strategy="oauth"
        )
        
        if not creds:
            await logger.error("VK credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "VK access_token not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        access_token = payload.get("access_token") or payload.get("token")
        if not access_token:
            await logger.error(f"access_token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "access_token not found in credentials"
                }
            }
        
        # Получаем параметры из config
        photo = config.get("photo")
        album_id = config.get("album_id")
        group_id = config.get("group_id")
        caption = config.get("caption", "")
        
        if not photo:
            await logger.error("photo is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "photo is required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            vk_session = vk_api.VkApi(token=access_token)
            vk = vk_session.get_api()
            upload = vk_api.VkUpload(vk_session)
            
            # Загружаем фото
            if album_id:
                # Загрузка в альбом
                photo_list = upload.photo(
                    photos=photo,
                    album_id=album_id,
                    group_id=group_id
                )
            else:
                # Загрузка на стену
                photo_list = upload.photo_wall(
                    photos=photo,
                    caption=caption,
                    group_id=group_id
                )
            
            # photo_list - список загруженных фото
            if photo_list:
                photo_info = photo_list[0]  # Берем первое фото
                
                # Если альбом и есть caption, редактируем подпись
                if album_id and caption:
                    vk.photos.edit(
                        photo_id=photo_info['id'],
                        owner_id=photo_info['owner_id'],
                        caption=caption
                    )
                
                # Возвращаем результат в формате системы
                return {
                    "response": {
                        "ok": True,
                        "result": {
                            "photo_id": photo_info['id'],
                            "owner_id": photo_info['owner_id'],
                            "album_id": photo_info.get('album_id'),
                            "sizes": photo_info.get('sizes', [])
                        }
                    }
                }
            else:
                await logger.error("No photos were uploaded")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": "Failed to upload photo"
                    }
                }
        except VkApiError as e:
            await logger.error(f"VK API error: {e}")
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