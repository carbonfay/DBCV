"""VK Get Wall интеграция используя vk-api библиотеку."""
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


class VkGetWallIntegration(BaseIntegration):
    """Интеграция для получения записей со стены VK через vk-api."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_get_wall",
            version="1.0.0",
            name="VK Get Wall",
            description="Получение записей со стены пользователя или сообщества ВКонтакте",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#4680C2",
            config_schema={
                "type": "object",
                "required": ["owner_id"],
                "properties": {
                    "owner_id": {
                        "type": "string",
                        "title": "Owner ID",
                        "description": "ID пользователя или сообщества (со знаком минус для сообществ). Например: 1 для пользователя, -1 для сообщества"
                    },
                    "count": {
                        "type": "integer",
                        "title": "Count",
                        "description": "Количество записей для получения (максимум 100)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "filter": {
                        "type": "string",
                        "title": "Filter",
                        "description": "Фильтр записей: owner - записи на стене, others - записи на чужих стенах, all - все записи",
                        "enum": ["owner", "others", "all"],
                        "default": "owner"
                    },
                    "extended": {
                        "type": "boolean",
                        "title": "Extended",
                        "description": "Получать расширенную информацию о записях (лайки, комментарии и т.д.)",
                        "default": True
                    }
                }
            },
            credentials_provider="vk",
            credentials_strategy="api_key",
            library_name="vk-api>=11.9.9" if VK_API_AVAILABLE else None,
            examples=[
                {
                    "title": "Получение записей со стены пользователя",
                    "config": {
                        "owner_id": "1",
                        "count": 10,
                        "filter": "owner",
                        "extended": True
                    }
                },
                {
                    "title": "Получение записей из сообщества",
                    "config": {
                        "owner_id": "-1",
                        "count": 20,
                        "filter": "owner",
                        "extended": True
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
            strategy="api_key"
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
        owner_id = config.get("owner_id")
        count = config.get("count", 20)
        filter_param = config.get("filter", "owner")
        extended = config.get("extended", True)
        
        if not owner_id:
            await logger.error("owner_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner_id is required"
                }
            }
        
        # Валидация параметров
        try:
            owner_id_int = int(owner_id)
            if count < 1 or count > 100:
                await logger.error("count must be between 1 and 100")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "count must be between 1 and 100"
                    }
                }
        except ValueError:
            await logger.error("owner_id must be a valid integer")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner_id must be a valid integer"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем сессию VK API
            vk_session = vk_api.VkApi(token=access_token)
            vk = vk_session.get_api()
            
            # Получаем записи со стены
            wall_response = vk.wall.get(
                owner_id=owner_id_int,
                count=count,
                filter=filter_param,
                extended=extended
            )
            
            # Формируем результат
            posts = []
            for item in wall_response.get("items", []):
                post_data = {
                    "id": item.get("id"),
                    "from_id": item.get("from_id"),
                    "owner_id": item.get("owner_id"),
                    "date": item.get("date"),
                    "text": item.get("text", ""),
                    "post_type": item.get("post_type", "post"),
                    "comments_count": item.get("comments", {}).get("count", 0),
                    "likes_count": item.get("likes", {}).get("count", 0),
                    "reposts_count": item.get("reposts", {}).get("count", 0),
                    "views_count": item.get("views", {}).get("count", 0)
                }
                
                # Добавляем информацию о вложениях, если есть
                if "attachments" in item:
                    post_data["attachments"] = []
                    for attachment in item["attachments"]:
                        attachment_data = {
                            "type": attachment.get("type"),
                            "url": None
                        }
                        
                        # Получаем URL для разных типов вложений
                        if attachment.get("type") == "photo" and "photo" in attachment:
                            sizes = attachment["photo"].get("sizes", [])
                            if sizes:
                                # Берем самое большое изображение
                                largest_size = max(sizes, key=lambda x: x.get("width", 0) * x.get("height", 0))
                                attachment_data["url"] = largest_size.get("url")
                        elif attachment.get("type") == "video" and "video" in attachment:
                            attachment_data["url"] = attachment["video"].get("player")
                        elif attachment.get("type") == "link" and "link" in attachment:
                            attachment_data["url"] = attachment["link"].get("url")
                        
                        post_data["attachments"].append(attachment_data)
                
                posts.append(post_data)
            
            # Добавляем информацию о профиле/сообществе, если extended=True
            profiles = {}
            groups = {}
            if extended and "profiles" in wall_response:
                for profile in wall_response["profiles"]:
                    profiles[profile["id"]] = {
                        "id": profile["id"],
                        "first_name": profile.get("first_name", ""),
                        "last_name": profile.get("last_name", ""),
                        "screen_name": profile.get("screen_name", ""),
                        "photo_50": profile.get("photo_50")
                    }
            
            if extended and "groups" in wall_response:
                for group in wall_response["groups"]:
                    groups[group["id"]] = {
                        "id": group["id"],
                        "name": group.get("name", ""),
                        "screen_name": group.get("screen_name", ""),
                        "photo_50": group.get("photo_50")
                    }
            
            # Возвращаем результат в формате системы
            result = {
                "posts": posts,
                "count": len(posts),
                "total_count": wall_response.get("count", 0)
            }
            
            if extended:
                result["profiles"] = profiles
                result["groups"] = groups
            
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
            
        except VkApiError as e:
            await logger.error(f"VK API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.code if hasattr(e, 'code') else 400,
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
