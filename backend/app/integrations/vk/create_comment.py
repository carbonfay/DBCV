"""VK Create Comment интеграция используя vk-api библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import vk_api
    VK_API_AVAILABLE = True
except ImportError:
    VK_API_AVAILABLE = False
    vk_api = None


class VkCreateCommentIntegration(BaseIntegration):
    """Интеграция для создания комментария к посту в VK через vk-api."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_create_comment",
            version="1.0.0",
            name="VK Create Comment",
            description="Создание комментария к посту в сообществе или на стене пользователя VK",
            category="social",
            icon_s3_key="icons/integrations/vk.svg",
            color="#4C75A3",
            config_schema={
                "type": "object",
                "required": ["owner_id", "post_id", "message"],
                "properties": {
                    "owner_id": {
                        "type": "string",
                        "title": "Owner ID",
                        "description": "ID владельца стены (положительное число для пользователя, отрицательное для сообщества)"
                    },
                    "post_id": {
                        "type": "string",
                        "title": "Post ID",
                        "description": "ID поста на стене"
                    },
                    "message": {
                        "type": "string",
                        "title": "Comment Text",
                        "description": "Текст комментария"
                    },
                    "access_token": {
                        "type": "string",
                        "title": "Access Token",
                        "description": "VK API access token (если не указан, будет использован из credentials)"
                    }
                }
            },
            credentials_provider="vk",
            credentials_strategy="oauth",
            library_name="vk-api>=11.9.9" if VK_API_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать комментарий к посту в сообществе",
                    "config": {
                        "owner_id": "-1",
                        "post_id": "123",
                        "message": "Отличный пост!"
                    }
                },
                {
                    "title": "Создать комментарий на стене пользователя",
                    "config": {
                        "owner_id": "123456",
                        "post_id": "456",
                        "message": "Спасибо за информацию!"
                    }
                },
                {
                    "title": "Создать комментарий с прямым указанием access_token",
                    "config": {
                        "owner_id": "-1",
                        "post_id": "123",
                        "message": "Комментарий через API",
                        "access_token": "ваш_vk_access_token"
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

        # Получаем параметры из config
        owner_id = config.get("owner_id")
        post_id = config.get("post_id")
        message = config.get("message")
        access_token = config.get("access_token")

        if not owner_id or not post_id or not message:
            await logger.error("owner_id, post_id and message are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner_id, post_id and message are required"
                }
            }

        # Получаем access_token: сначала из config, затем из credentials
        if not access_token:
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id,
                provider="vk",
                strategy="oauth"
            )

            if not creds:
                await logger.error("VK credentials not found and access_token not provided in config")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "VK access_token not found in credentials or config"
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

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            vk = vk_api.VkApi(token=access_token)
            result = vk.method('wall.createComment', {
                'owner_id': int(owner_id),
                'post_id': int(post_id),
                'message': str(message)
            })

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "comment_id": result.get("comment_id"),
                        "parent_stack": result.get("parent_stack", []),
                        "date": result.get("date")
                    }
                }
            }
        except vk_api.exceptions.VkApiError as e:
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