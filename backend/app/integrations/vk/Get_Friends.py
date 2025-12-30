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
    """Интеграция для получения списка друзей в VK через vk-api."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_get_friends",
            version="1.0.0",
            name="VK Get Friends",
            description="Получение списка друзей пользователя в VK через API",
            category="social",
            icon_s3_key="icons/integrations/vk.svg",
            color="#4680C2",
            config_schema={
                "type": "object",
                "required": ["user_id"],
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "title": "User ID",
                        "description": "ID пользователя для получения друзей (можно использовать текущий ID)"
                    },
                    "count": {
                        "type": "integer",
                        "title": "Count",
                        "description": "Количество друзей для получения (максимум 1000)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    },
                    "fields": {
                        "type": "string",
                        "title": "Fields",
                        "description": "Дополнительные поля друзей через запятую (например: photo_100,online,last_seen)",
                        "default": "photo_100,online,first_name,last_name"
                    },
                    "order": {
                        "type": "string",
                        "title": "Order",
                        "description": "Сортировка: name, hints, random",
                        "enum": ["name", "hints", "random"],
                        "default": "name"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="vk-api>=11.9.9" if VK_API_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить друзей текущего пользователя",
                    "config": {
                        "user_id": 12345678,
                        "count": 50,
                        "fields": "photo_100,online,first_name,last_name",
                        "order": "name"
                    }
                },
                {
                    "title": "Получить всех друзей с детальной информацией",
                    "config": {
                        "user_id": 12345678,
                        "count": 1000,
                        "fields": "photo_200,online,last_seen,city,country,bdate",
                        "order": "name"
                    }
                },
                {
                    "title": "Получить случайных друзей",
                    "config": {
                        "user_id": 12345678,
                        "count": 20,
                        "fields": "photo_100,online",
                        "order": "random"
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
            provider="other",
            strategy="api_key"
        )
        
        await logger.error(f"VK credentials debug: creds={creds}")
        
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
        await logger.error(f"VK payload debug: payload={payload}")
        
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
            await logger.error(f"VK fallback payload: {payload}")
        
        access_token = payload.get("access_token") or payload.get("token")
        await logger.error(f"VK access_token debug: access_token={access_token}")
        
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
        count = config.get("count", 100)
        fields = config.get("fields", "photo_100,online,first_name,last_name")
        order = config.get("order", "name")
        
        if not user_id:
            await logger.error("user_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "user_id is required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            await logger.error(f"VK API attempt with token: {access_token[:10]}...")
            
            # Создаем сессию VK API
            vk_session = vk_api.VkApi(token=access_token)
            vk = vk_session.get_api()
            
            # Подготавливаем параметры
            friends_params = {
                'user_id': int(user_id),
                'count': min(int(count), 1000),  # VK ограничивает 1000
                'fields': str(fields),
                'order': str(order)
            }
            
            await logger.error(f"VK friends params: {friends_params}")
            
            # Получаем список друзей
            result = vk.friends.get(**friends_params)
            await logger.error(f"VK friends result count: {result.get('count', 0)}")
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "count": result.get('count', 0),
                        "friends": result.get('items', []),
                        "user_id": int(user_id),
                        "fields_used": str(fields),
                        "order": str(order)
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
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
