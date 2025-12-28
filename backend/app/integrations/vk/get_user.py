"""VK Get User интеграция используя vk-api библиотеку."""
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


class VkGetUserIntegration(BaseIntegration):
    """Интеграция для получения информации о пользователе VK через vk-api."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_get_user",
            version="1.0.0",
            name="VK Get User",
            description="Получение информации о пользователе ВКонтакте через VK API",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#0077FF",
            config_schema={
                "type": "object",
                "required": ["user_ids"],
                "properties": {
                    "user_ids": {
                        "type": ["string", "integer", "array"],
                        "title": "User IDs",
                        "description": "ID пользователя VK или список ID (например: '123456' или [123456, 789012] или {$user.vk_user_id$})"
                    },
                    "fields": {
                        "type": "array",
                        "title": "Fields",
                        "description": "Дополнительные поля для получения",
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
                        "description": "Падеж для имени пользователя",
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
                    "title": "Получить базовую информацию",
                    "config": {
                        "user_ids": "{$user.vk_user_id$}",
                        "fields": ["photo_100", "online", "domain"]
                    }
                },
                {
                    "title": "Получить расширенную информацию",
                    "config": {
                        "user_ids": "123456789",
                        "fields": [
                            "photo_200",
                            "online",
                            "domain",
                            "bdate",
                            "city",
                            "country",
                            "status"
                        ]
                    }
                },
                {
                    "title": "Получить информацию о нескольких пользователях",
                    "config": {
                        "user_ids": [123456, 789012],
                        "fields": ["photo_100", "online"]
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
        user_ids = config.get("user_ids")
        fields = config.get("fields", ["photo_100", "online", "domain"])
        name_case = config.get("name_case", "nom")
        
        if not user_ids:
            await logger.error("user_ids is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "user_ids is required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем VK API сессию
            vk_session = vk_api.VkApi(token=access_token)
            vk = vk_session.get_api()
            
            # Преобразуем user_ids в правильный формат
            if isinstance(user_ids, list):
                user_ids_str = ",".join(str(uid) for uid in user_ids)
            else:
                user_ids_str = str(user_ids)
            
            # Подготавливаем параметры для запроса
            request_params = {
                "user_ids": user_ids_str,
                "name_case": name_case
            }
            
            # Добавляем fields если указаны
            if fields:
                if isinstance(fields, list):
                    request_params["fields"] = ",".join(fields)
                else:
                    request_params["fields"] = str(fields)
            
            # Получаем информацию о пользователе
            result = vk.users.get(**request_params)
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "users": result,
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
            await logger.error(f"Invalid user_ids or parameters: {e}")
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
