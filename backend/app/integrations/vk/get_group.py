"""VK Get Group интеграция используя vk-api библиотеку."""
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


class VkGetGroupIntegration(BaseIntegration):
    """Интеграция для получения информации о группе/сообществе VK через vk-api."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_get_group",
            version="1.0.0",
            name="VK Get Group",
            description="Получение информации о группе/сообществе ВКонтакте через VK API",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#0077FF",
            config_schema={
                "type": "object",
                "required": ["group_id"],
                "properties": {
                    "group_id": {
                        "type": ["string", "integer"],
                        "title": "Group ID",
                        "description": "ID группы VK или короткое имя (например: '1' или 'apiclub' или {$group.vk_group_id$})"
                    },
                    "fields": {
                        "type": "array",
                        "title": "Fields",
                        "description": "Дополнительные поля для получения",
                        "items": {
                            "type": "string",
                            "enum": [
                                "activity",
                                "addresses",
                                "age_limits",
                                "ban_info",
                                "can_create_topic",
                                "can_message",
                                "can_post",
                                "can_see_all_posts",
                                "can_upload_doc",
                                "can_upload_story",
                                "can_upload_video",
                                "city",
                                "contacts",
                                "counters",
                                "country",
                                "cover",
                                "description",
                                "fixed_post",
                                "has_photo",
                                "is_favorite",
                                "is_hidden_from_feed",
                                "is_messages_blocked",
                                "links",
                                "main_album_id",
                                "main_section",
                                "market",
                                "member_status",
                                "members_count",
                                "place",
                                "public_date_label",
                                "site",
                                "start_date",
                                "finish_date",
                                "status",
                                "trending",
                                "verified",
                                "wall",
                                "wiki_page"
                            ]
                        },
                        "default": ["description", "members_count", "activity"]
                    }
                }
            },
            credentials_provider="vk",
            credentials_strategy="api_key",
            library_name="vk-api>=11.9.9" if VK_API_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить базовую информацию о группе",
                    "config": {
                        "group_id": "apiclub",
                        "fields": ["description", "members_count", "activity"]
                    }
                },
                {
                    "title": "Получить расширенную информацию",
                    "config": {
                        "group_id": "1",
                        "fields": [
                            "description",
                            "members_count",
                            "activity",
                            "city",
                            "country",
                            "site",
                            "contacts",
                            "verified",
                            "cover"
                        ]
                    }
                },
                {
                    "title": "Проверить статус участника",
                    "config": {
                        "group_id": "{$group.vk_group_id$}",
                        "fields": ["member_status", "can_post", "can_message"]
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
        group_id = config.get("group_id")
        fields = config.get("fields", ["description", "members_count", "activity"])
        
        if not group_id:
            await logger.error("group_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "group_id is required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем VK API сессию
            vk_session = vk_api.VkApi(token=access_token)
            vk = vk_session.get_api()
            
            # Преобразуем group_id в правильный формат
            group_id_str = str(group_id)
            
            # Подготавливаем параметры для запроса
            request_params = {
                "group_id": group_id_str
            }
            
            # Добавляем fields если указаны
            if fields:
                if isinstance(fields, list):
                    request_params["fields"] = ",".join(fields)
                else:
                    request_params["fields"] = str(fields)
            
            # Получаем информацию о группе
            result = vk.groups.getById(**request_params)
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "groups": result,
                        "count": len(result) if isinstance(result, list) else 1
                    }
                }
            }
        except VkApiError as e:
            await logger.error(f"VK API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.code if hasattr(e, 'code') else 500,
                    "description": str(e)
                }
            }
        except ValueError as e:
            await logger.error(f"Invalid group_id or parameters: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Invalid parameters: {str(e)}"
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
