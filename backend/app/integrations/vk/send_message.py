"""VK Send Message интеграция используя httpx библиотеку."""
from typing import Dict, Any
from uuid import UUID
import json
import random

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Константы для настройки токена и версии API.
VK_DEFAULT_API_VERSION = "5.131"
VK_RANDOM_ID_MIN = 1
VK_RANDOM_ID_MAX = 2**31 - 1
VK_API_VERSION = VK_DEFAULT_API_VERSION
VK_TOKEN_KEYS = ("access_token", "token", "api_key", "vk_token")
VK_API_URL = "https://api.vk.com/method/messages.send"
VK_HTTP_TIMEOUT = 10.0

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


def _coerce_vk_bool(value: Any) -> int | None:
    if value is None:
        return None
    return 1 if bool(value) else 0


def _normalize_comma_list(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(item) for item in value)
    return str(value)


def _prepare_keyboard(keyboard: Any) -> str:
    if keyboard is None:
        return ""
    if isinstance(keyboard, str):
        return keyboard
    return json.dumps(keyboard, ensure_ascii=False)


class VkSendMessageIntegration(BaseIntegration):
    """Интеграция для отправки сообщений в VK через httpx."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_send_message",
            version="1.0.0",
            name="VK Send Message",
            description="Отправка текстового сообщения во ВКонтакте через VK API",
            category="messaging",
            icon_s3_key="icons/integrations/vk.svg",
            color="#4C75A3",
            config_schema={
                "type": "object",
                "required": ["peer_id", "message"],
                "properties": {
                    "peer_id": {
                        "type": "string",
                        "title": "Peer ID",
                        "description": "ID пользователя/чата VK (можно использовать переменные: {$user.vk_id$})"
                    },
                    "message": {
                        "type": "string",
                        "title": "Message",
                        "description": "Текст сообщения"
                    },
                    "random_id": {
                        "type": "integer",
                        "title": "Random ID",
                        "description": "Идентификатор сообщения (если не указан, будет сгенерирован автоматически)"
                    },
                    "attachment": {
                        "type": ["string", "array"],
                        "title": "Attachments",
                        "items": {"type": "string"},
                        "description": "Вложения VK (строка через запятую или массив)"
                    },
                    "keyboard": {
                        "title": "Keyboard",
                        "description": "Клавиатура VK (object или JSON string)",
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ]
                    },
                    "dont_parse_links": {
                        "type": "boolean",
                        "title": "Don't Parse Links",
                        "description": "Не парсить ссылки"
                    },
                    "disable_mentions": {
                        "type": "boolean",
                        "title": "Disable Mentions",
                        "description": "Отключить упоминания"
                    },
                    "reply_to": {
                        "type": "integer",
                        "title": "Reply To",
                        "description": "ID сообщения, на которое нужно ответить"
                    },
                    "forward_messages": {
                        "type": ["string", "array", "integer"],
                        "title": "Forward Messages",
                        "items": {"type": "integer"},
                        "description": "ID пересылаемых сообщений (через запятую или массив)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Простое сообщение",
                    "config": {
                        "peer_id": "{$user.vk_id$}",
                        "message": "Привет из DBCV!"
                    }
                },
                {
                    "title": "Сообщение с параметрами",
                    "config": {
                        "peer_id": "2000000001",
                        "message": "Сообщение в беседу",
                        "random_id": 12345,
                        "dont_parse_links": True,
                        "disable_mentions": True
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
        Выполняет интеграцию используя библиотеку httpx.

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
                    "description": "httpx library is not installed"
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )

        if not creds:
            await logger.error("VK credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "VK access token not found in credentials"
                }
            }

        payload = creds.get("payload", {}) if creds else {}
        if not payload:
            payload = creds or {}

        access_token = None
        for key in VK_TOKEN_KEYS:
            if payload.get(key):
                access_token = payload.get(key)
                break

        if not access_token:
            await logger.error(f"VK token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "VK access token not found in credentials"
                }
            }

        peer_id = config.get("peer_id")
        message = config.get("message")
        if peer_id in (None, "") or message in (None, ""):
            await logger.error("peer_id and message are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "peer_id and message are required"
                }
            }

        random_id = config.get("random_id")
        if random_id is None:
            random_id = random.randint(VK_RANDOM_ID_MIN, VK_RANDOM_ID_MAX)
        else:
            try:
                random_id = int(random_id)
            except (TypeError, ValueError):
                await logger.error("random_id must be an integer")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "random_id must be an integer"
                    }
                }

        try:
            peer_id_value = int(peer_id)
        except (TypeError, ValueError):
            peer_id_value = peer_id

        params: Dict[str, Any] = {
            "peer_id": peer_id_value,
            "message": str(message),
            "random_id": random_id,
            "access_token": access_token,
            "v": VK_API_VERSION,
        }

        attachment = _normalize_comma_list(config.get("attachment"))
        if attachment:
            params["attachment"] = attachment

        keyboard_config = config.get("keyboard")
        if keyboard_config is not None:
            try:
                keyboard_payload = _prepare_keyboard(keyboard_config)
            except (TypeError, ValueError) as exc:
                await logger.error(f"Invalid keyboard payload: {exc}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "keyboard must be an object or valid JSON string"
                    }
                }
            if keyboard_payload:
                params["keyboard"] = keyboard_payload

        dont_parse_links = _coerce_vk_bool(config.get("dont_parse_links"))
        if dont_parse_links is not None:
            params["dont_parse_links"] = dont_parse_links

        disable_mentions = _coerce_vk_bool(config.get("disable_mentions"))
        if disable_mentions is not None:
            params["disable_mentions"] = disable_mentions

        reply_to = config.get("reply_to")
        if reply_to is not None:
            try:
                params["reply_to"] = int(reply_to)
            except (TypeError, ValueError):
                await logger.error("reply_to must be an integer")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "reply_to must be an integer"
                    }
                }

        forward_messages = _normalize_comma_list(config.get("forward_messages"))
        if forward_messages:
            params["forward_messages"] = forward_messages

        try:
            async with httpx.AsyncClient(timeout=VK_HTTP_TIMEOUT) as client:
                response = await client.post(VK_API_URL, data=params)
                response.raise_for_status()
                try:
                    payload = response.json()
                except ValueError as exc:
                    await logger.error(f"VK API invalid JSON response: {exc}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 500,
                            "description": "VK API returned invalid JSON"
                        }
                    }

            if isinstance(payload, dict) and payload.get("error"):
                error = payload.get("error") or {}
                description = (
                    error.get("error_msg")
                    or error.get("error_text")
                    or "VK API error"
                )
                return {
                    "response": {
                        "ok": False,
                        "error_code": error.get("error_code", 500),
                        "description": description
                    }
                }

            result = payload.get("response") if isinstance(payload, dict) else None
            message_id = result
            if isinstance(result, dict):
                message_id = result.get("message_id") or result.get("id")

            if message_id is None:
                await logger.error("VK API did not return message_id")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": "VK API response missing message_id"
                    }
                }

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": message_id,
                        "peer_id": peer_id_value,
                        "random_id": random_id
                    }
                }
            }
        except httpx.HTTPStatusError as exc:
            await logger.error(f"VK API HTTP status error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": exc.response.status_code if exc.response else 500,
                    "description": str(exc)
                }
            }
        except httpx.RequestError as exc:
            await logger.error(f"VK API request error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 502,
                    "description": str(exc)
                }
            }
        except Exception as exc:
            await logger.error(f"Unexpected error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(exc)
                }
            }
