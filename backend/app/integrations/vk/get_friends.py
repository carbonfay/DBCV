"""VK Get Friends интеграция используя vk-api библиотеку."""
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


class VkGetFriendsIntegration(BaseIntegration):
    """Интеграция для получения списка друзей пользователя VK через vk-api."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_get_friends",
            version="1.0.0",
            name="VK Get Friends",
            description="Получение списка друзей пользователя ВКонтакте через VK API",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#0077FF",
            config_schema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": ["string", "integer"],
                        "title": "User ID",
                        "description": "ID пользователя VK (если не указан - получает своих друзей). Например: '123456' или {$user.vk_user_id$}"
                    },
                    "order": {
                        "type": "string",
                        "title": "Order",
                        "description": "Порядок сортировки друзей",
                        "enum": ["hints", "random", "mobile", "name"],
                        "default": "hints"
                    },
                    "count": {
                        "type": "integer",
                        "title": "Count",
                        "description": "Количество друзей для получения (максимум 5000)",
                        "minimum": 1,
                        "maximum": 5000,
                        "default": 100
                    },
                    "offset": {
                        "type": "integer",
                        "title": "Offset",
                        "description": "Смещение для пагинации",
                        "minimum": 0,
                        "default": 0
                    },
                    "fields": {
                        "type": "array",
                        "title": "Fields",
                        "description": "Дополнительные поля профиля для каждого друга",
                        "items": {
                            "type": "string",
                            "enum": [
                                "photo_50",
                                "photo_100",
                                "photo_200",
                                "photo_max",
                                "online",
                                "domain",
                                "sex",
                                "bdate",
                                "city",
                                "country",
                                "timezone",
                                "photo_max_orig",
                                "has_mobile",
                                "contacts",
                                "education",
                                "online_mobile",
                                "relation",
                                "last_seen",
                                "status",
                                "can_write_private_message",
                                "can_see_all_posts",
                                "can_post",
                                "universities"
                            ]
                        },
                        "default": ["photo_100", "online", "domain"]
                    },
                    "name_case": {
                        "type": "string",
                        "title": "Name Case",
                        "description": "Падеж для имени и фамилии",
                        "enum": ["nom", "gen", "dat", "acc", "ins", "abl"],
                        "default": "nom"
                    }
                }
            },
            credentials_provider="vk",
            credentials_strategy="api_key",
            library_name="vk-api>=11.9.9" if VK_API_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить своих друзей (первые 10)",
                    "config": {
                        "count": 10,
                        "fields": ["photo_100", "online", "domain"]
                    }
                },
                {
                    "title": "Получить друзей конкретного пользователя",
                    "config": {
                        "user_id": "{$user.vk_user_id$}",
                        "count": 50,
                        "order": "name",
                        "fields": ["photo_100", "online", "city", "bdate"]
                    }
                },
                {
                    "title": "Получить друзей с пагинацией",
                    "config": {
                        "user_id": "123456",
                        "count": 100,
                        "offset": 0,
                        "order": "hints",
                        "fields": ["photo_100", "online", "domain", "status"]
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
        user_id = config.get("user_id")
        order = config.get("order", "hints")
        count = config.get("count", 100)
        offset = config.get("offset", 0)
        fields = config.get("fields", ["photo_100", "online", "domain"])
        name_case = config.get("name_case", "nom")
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем VK API сессию
            vk_session = vk_api.VkApi(token=access_token)
            vk = vk_session.get_api()
            
            # Подготавливаем параметры для запроса
            request_params = {
                "order": order,
                "count": count,
                "offset": offset,
                "name_case": name_case
            }
            
            # Добавляем user_id если указан
            if user_id:
                request_params["user_id"] = str(user_id)
            
            # Добавляем fields если указаны
            if fields:
                if isinstance(fields, list):
                    request_params["fields"] = ",".join(fields)
                else:
                    request_params["fields"] = str(fields)
            
            # Получаем список друзей
            result = vk.friends.get(**request_params)
            
            # result содержит:
            # {
            #   "count": общее количество друзей,
            #   "items": массив с данными друзей
            # }
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "count": result.get("count", 0),
                        "items": result.get("items", []),
                        "total_count": result.get("count", 0),
                        "offset": offset,
                        "has_more": (offset + count) < result.get("count", 0)
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
            await logger.error(f"Invalid user_id or parameters: {e}")
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
