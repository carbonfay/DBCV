"""VK Create Comment интеграция используя vk-api библиотеку."""
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


class VkCreateCommentIntegration(BaseIntegration):
    """Интеграция для создания комментариев в VK через vk-api."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_create_comment",
            version="1.0.0",
            name="VK Create Comment",
            description="Создание комментария к посту или фото в VK через API",
            category="social",
            icon_s3_key="icons/integrations/vk.svg",
            color="#4680C2",
            config_schema={
                "type": "object",
                "required": ["owner_id", "post_id", "message"],
                "properties": {
                    "owner_id": {
                        "type": "integer",
                        "title": "Owner ID",
                        "description": "ID владельца стены (положительный для пользователей, отрицательный для групп)"
                    },
                    "post_id": {
                        "type": "integer",
                        "title": "Post ID",
                        "description": "ID поста или фотографии для комментирования"
                    },
                    "message": {
                        "type": "string",
                        "title": "Comment Text",
                        "description": "Текст комментария"
                    },
                    "from_group": {
                        "type": "integer",
                        "title": "From Group",
                        "description": "ID группы от имени которой будет комментарий (опционально)",
                        "default": None
                    },
                    "reply_to_comment": {
                        "type": "integer",
                        "title": "Reply to Comment",
                        "description": "ID комментария на который отвечаем (опционально)",
                        "default": None
                    },
                    "attachments": {
                        "type": "string",
                        "title": "Attachments",
                        "description": "Вложения (фото, видео, документы) в формате attachments",
                        "default": None
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="vk-api>=11.9.9" if VK_API_AVAILABLE else None,
            examples=[
                {
                    "title": "Комментарий к посту",
                    "description": "Убедитесь что VK access_token добавлен в credentials",
                    "config": {
                        "owner_id": 1,
                        "post_id": 12345,
                        "message": "Отличный пост!"
                    }
                },
                {
                    "title": "Ответ на комментарий",
                    "config": {
                        "owner_id": -12345678,
                        "post_id": 98765,
                        "message": "Согласен с предыдущим комментарием",
                        "reply_to_comment": 54321
                    }
                },
                {
                    "title": "Комментарий от имени группы",
                    "config": {
                        "owner_id": 123456,
                        "post_id": 55555,
                        "message": "Официальный комментарий группы",
                        "from_group": 987654
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
        owner_id = config.get("owner_id")
        post_id = config.get("post_id")
        message = config.get("message")
        from_group = config.get("from_group")
        reply_to_comment = config.get("reply_to_comment")
        attachments = config.get("attachments")
        
        if not owner_id or not post_id or not message:
            await logger.error("owner_id, post_id and message are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner_id, post_id and message are required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            await logger.error(f"VK API attempt with token: {access_token[:10]}...")
            
            # Создаем сессию VK API
            vk_session = vk_api.VkApi(token=access_token)
            vk = vk_session.get_api()
            
            # Подготавливаем параметры
            comment_params = {
                'owner_id': int(owner_id),
                'post_id': int(post_id),
                'message': str(message)
            }
            
            # Добавляем опциональные параметры
            if from_group:
                comment_params['from_group'] = int(from_group)
            if reply_to_comment:
                comment_params['reply_to_comment'] = int(reply_to_comment)
            if attachments:
                comment_params['attachments'] = str(attachments)
            
            await logger.error(f"VK API params: {comment_params}")
            
            # Создаем комментарий
            result = vk.wall.addComment(**comment_params)
            await logger.error(f"VK API result: {result}")
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "comment_id": result.get('comment_id'),
                        "owner_id": int(owner_id),
                        "post_id": int(post_id),
                        "message": str(message),
                        "created": True
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
