"""VK Send Message интеграция используя vk-api библиотеку."""
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


class VkSendMessageIntegration(BaseIntegration):
    """Интеграция для отправки сообщений в VK через vk-api библиотеку."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_send_message",
            version="1.0.0",
            name="VK Send Message",
            description="Отправка текстового сообщения в ВКонтакте через VK API",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#0077FF",
            config_schema={
                "type": "object",
                "required": ["user_id", "message"],
                "properties": {
                    "user_id": {
                        "type": ["string", "integer"],
                        "title": "User ID",
                        "description": "ID пользователя VK или переменная (например: {$user.vk_user_id$})"
                    },
                    "message": {
                        "type": "string",
                        "title": "Message",
                        "description": "Текст сообщения"
                    },
                    "random_id": {
                        "type": "integer",
                        "title": "Random ID",
                        "description": "Случайный ID для предотвращения дублирования (по умолчанию генерируется автоматически)",
                        "default": 0
                    },
                    "keyboard": {
                        "type": "object",
                        "title": "Keyboard",
                        "description": "JSON клавиатуры VK (опционально)"
                    },
                    "attachment": {
                        "type": "string",
                        "title": "Attachment",
                        "description": "Вложения в формате type<owner_id>_<media_id> (например: photo-1234_5678)"
                    }
                }
            },
            credentials_provider="vk",
            credentials_strategy="api_key",
            library_name="vk-api>=11.9.9" if VK_API_AVAILABLE else None,
            examples=[
                {
                    "title": "Простое сообщение",
                    "config": {
                        "user_id": "{$user.vk_user_id$}",
                        "message": "Привет из DBCV!"
                    }
                },
                {
                    "title": "Сообщение с клавиатурой",
                    "config": {
                        "user_id": "123456789",
                        "message": "Выберите опцию:",
                        "keyboard": {
                            "one_time": False,
                            "buttons": [
                                [
                                    {
                                        "action": {
                                            "type": "text",
                                            "label": "Кнопка 1"
                                        },
                                        "color": "primary"
                                    }
                                ]
                            ]
                        }
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
        message = config.get("message")
        random_id = config.get("random_id", 0)
        keyboard = config.get("keyboard")
        attachment = config.get("attachment")
        
        if not user_id or not message:
            await logger.error("user_id and message are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "user_id and message are required"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем VK API сессию
            vk_session = vk_api.VkApi(token=access_token)
            vk = vk_session.get_api()
            
            # Если random_id не указан, генерируем автоматически
            if random_id == 0:
                import random
                random_id = random.randint(1, 2147483647)
            
            # Подготавливаем параметры для отправки
            send_params = {
                "user_id": int(user_id) if isinstance(user_id, (str, int)) else user_id,
                "message": str(message),
                "random_id": random_id
            }
            
            # Добавляем клавиатуру если указана
            if keyboard:
                import json
                send_params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
            
            # Добавляем вложение если указано
            if attachment:
                send_params["attachment"] = str(attachment)
            
            # Отправляем сообщение
            result = vk.messages.send(**send_params)
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": result,
                        "user_id": send_params["user_id"],
                        "message": send_params["message"],
                        "random_id": random_id
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
