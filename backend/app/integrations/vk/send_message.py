"""VK Send Message интеграция используя httpx для прямых API вызовов."""
from typing import Dict, Any
from uuid import UUID
import httpx
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# httpx уже в requirements.txt, поэтому проверяем доступность
HTTPX_AVAILABLE = True


class VKSendMessageIntegration(BaseIntegration):
    """Интеграция для отправки сообщений в VK."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_send_message",
            version="1.0.0",
            name="VK Send Message",
            description="Отправка сообщений в VK через API",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#4A76A8",
            config_schema={
                "type": "object",
                "required": ["user_id", "message"],
                "properties": {
                    "user_id": {
                        "type": "string",
                        "title": "User ID",
                        "description": "ID пользователя VK, которому отправляется сообщение"
                    },
                    "message": {
                        "type": "string",
                        "title": "Message",
                        "description": "Текст сообщения для отправки"
                    },
                    "peer_id": {
                        "type": "integer",
                        "title": "Peer ID",
                        "description": "ID чата или пользователя (альтернатива user_id)"
                    },
                    "domain": {
                        "type": "string",
                        "title": "Domain",
                        "description": "Короткий адрес пользователя"
                    },
                    "chat_id": {
                        "type": "integer",
                        "title": "Chat ID",
                        "description": "ID беседы"
                    },
                    "random_id": {
                        "type": "integer",
                        "title": "Random ID",
                        "description": "Уникальный идентификатор для предотвращения повторной отправки",
                        "default": 0
                    },
                    "keyboard": {
                        "type": "string",
                        "title": "Keyboard",
                        "description": "JSON-описание клавиатуры для сообщения"
                    },
                    "attachment": {
                        "type": "string",
                        "title": "Attachment",
                        "description": "Аттачи (медиафайлы), прикрепленные к сообщению"
                    },
                    "payload": {
                        "type": "string",
                        "title": "Payload",
                        "description": "Дополнительная информация для обработки нажатий клавиатуры"
                    },
                    "dont_parse_links": {
                        "type": "boolean",
                        "title": "Don't Parse Links",
                        "description": "Отключить генерацию сниппетов ссылок",
                        "default": False
                    },
                    "disable_mentions": {
                        "type": "boolean",
                        "title": "Disable Mentions",
                        "description": "Отключить упоминания",
                        "default": False
                    }
                }
            },
            credentials_provider="vk",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправить простое сообщение",
                    "config": {
                        "user_id": "{$session.vk_user_id$}",
                        "message": "Привет из бота DBCV!"
                    }
                },
                {
                    "title": "Отправить сообщение с клавиатурой",
                    "config": {
                        "user_id": "{$session.vk_user_id$}",
                        "message": "Выберите действие:",
                        "keyboard": '{"buttons":[[{"action":{"type":"text","label":"Да"},"color":"positive"},{"action":{"type":"text","label":"Нет"},"color":"negative"}]],"one_time":true}'
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
        Выполняет интеграцию используя httpx для прямых вызовов VK API.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not available"
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
            await logger.error(f"Access token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Access token not found in credentials"
                }
            }

        # Получаем параметры из config
        user_id = config.get("user_id")
        message = config.get("message")
        peer_id = config.get("peer_id")
        domain = config.get("domain")
        chat_id = config.get("chat_id")
        random_id = config.get("random_id", 0)
        keyboard = config.get("keyboard")
        attachment = config.get("attachment")
        payload_param = config.get("payload")
        dont_parse_links = config.get("dont_parse_links", False)
        disable_mentions = config.get("disable_mentions", False)

        if not message:
            await logger.error("message is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "message is required"
                }
            }

        # Проверяем, что хотя бы один из идентификаторов цели указан
        if not (user_id or peer_id or domain or chat_id):
            await logger.error("Either user_id, peer_id, domain, or chat_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Either user_id, peer_id, domain, or chat_id is required"
                }
            }

        # Подготавливаем параметры для API запроса
        params = {
            "access_token": access_token,
            "message": message,
            "random_id": random_id,
            "v": "5.131"  # используем актуальную версию API
        }

        # Добавляем параметры цели
        if user_id:
            params["user_id"] = user_id
        if peer_id:
            params["peer_id"] = peer_id
        if domain:
            params["domain"] = domain
        if chat_id:
            params["chat_id"] = chat_id
        if keyboard:
            params["keyboard"] = keyboard
        if attachment:
            params["attachment"] = attachment
        if payload_param:
            params["payload"] = payload_param
        if dont_parse_links:
            params["dont_parse_links"] = 1
        if disable_mentions:
            params["disable_mentions"] = 1

        # ИСПОЛЬЗУЕМ httpx НАПРЯМУЮ
        try:
            # URL для VK API метода messages.send
            url = "https://api.vk.com/method/messages.send"

            # Выполняем POST-запрос
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=params)

            # Проверяем статус ответа
            if response.status_code != 200:
                await logger.error(f"VK API returned status {response.status_code}: {response.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": response.status_code,
                        "description": f"VK API returned status {response.status_code}: {response.text}"
                    }
                }

            # Парсим JSON-ответ
            data = response.json()

            # Проверяем на наличие ошибки в ответе
            if "error" in data:
                error = data["error"]
                error_msg = error.get("error_msg", "Unknown error")
                error_code = error.get("error_code", 500)
                
                await logger.error(f"VK API error: {error_msg} (code: {error_code})")
                return {
                    "response": {
                        "ok": False,
                        "error_code": error_code,
                        "description": f"VK API error: {error_msg}"
                    }
                }

            # Возвращаем результат в формате системы
            result = data.get("response", {})
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": result,
                        "params_used": {
                            k: v for k, v in params.items() 
                            if k not in ['access_token', 'v']  # исключаем чувствительные данные
                        }
                    }
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"HTTP request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP request error: {e}"
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

