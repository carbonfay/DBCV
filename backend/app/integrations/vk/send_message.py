"""VK Send Message интеграция используя httpx библиотеку."""
from typing import Dict, Any
from uuid import UUID
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Константы для настройки токена и версии API.
VK_DEFAULT_API_VERSION = "5.131"
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


def _prepare_json_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


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
                "required": ["random_id"],
                "anyOf": [
                    {"required": ["user_id"]},
                    {"required": ["peer_id"]},
                    {"required": ["peer_ids"]},
                    {"required": ["domain"]},
                    {"required": ["chat_id"]},
                    {"required": ["user_ids"]},
                ],
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "title": "User ID",
                        "description": "ID пользователя, которому отправляется сообщение"
                    },
                    "peer_id": {
                        "type": "integer",
                        "title": "Peer ID",
                        "description": "ID получателя: пользователь, беседа (2000000000+ID), сообщество (-ID)"
                    },
                    "peer_ids": {
                        "type": ["string", "array"],
                        "title": "Peer IDs",
                        "items": {"type": "integer"},
                        "description": "ID получателей через запятую или массив (до 100)"
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
                    "user_ids": {
                        "type": ["string", "array"],
                        "title": "User IDs",
                        "items": {"type": "integer"},
                        "description": "ID получателей через запятую или массив (до 100)"
                    },
                    "message": {
                        "type": "string",
                        "title": "Message",
                        "description": "Текст сообщения (обязателен, если нет attachment)"
                    },
                    "random_id": {
                        "type": "integer",
                        "title": "Random ID",
                        "description": "Идентификатор сообщения (0 отключает проверку уникальности)"
                    },
                    "lat": {
                        "type": "string",
                        "title": "Latitude",
                        "description": "Географическая широта (-90..90)"
                    },
                    "long": {
                        "type": "string",
                        "title": "Longitude",
                        "description": "Географическая долгота (-180..180)"
                    },
                    "attachment": {
                        "type": ["string", "array"],
                        "title": "Attachments",
                        "items": {"type": "string"},
                        "description": "Вложения VK (строка через запятую или массив)"
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
                    },
                    "forward": {
                        "title": "Forward",
                        "description": "JSON-объект для пересылки сообщений",
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ]
                    },
                    "sticker_id": {
                        "type": "integer",
                        "title": "Sticker ID",
                        "description": "ID стикера"
                    },
                    "group_id": {
                        "type": "integer",
                        "title": "Group ID",
                        "description": "ID сообщества (для сообщений сообщества с ключом пользователя)"
                    },
                    "keyboard": {
                        "title": "Keyboard",
                        "description": "Клавиатура VK (object или JSON string)",
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ]
                    },
                    "template": {
                        "title": "Template",
                        "description": "Шаблон сообщения (object или JSON string)",
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ]
                    },
                    "payload": {
                        "title": "Payload",
                        "description": "Полезные данные (object или JSON string)",
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"}
                        ]
                    },
                    "content_source": {
                        "title": "Content Source",
                        "description": "Источник контента для чат-ботов (object или JSON string)",
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
                    "intent": {
                        "type": "string",
                        "title": "Intent",
                        "description": "Интент для сообщения"
                    },
                    "subscribe_id": {
                        "type": "integer",
                        "title": "Subscribe ID",
                        "description": "ID для работы с интентами"
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
                        "user_id": 123456,
                        "message": "Привет из DBCV!",
                        "random_id": 1
                    }
                },
                {
                    "title": "Сообщение с параметрами",
                    "config": {
                        "peer_id": 2000000001,
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

        user_id = config.get("user_id")
        peer_id = config.get("peer_id")
        peer_ids = config.get("peer_ids")
        domain = config.get("domain")
        chat_id = config.get("chat_id")
        user_ids = config.get("user_ids")
        message = config.get("message")

        has_recipient = any(
            value not in (None, "")
            for value in (user_id, peer_id, peer_ids, domain, chat_id, user_ids)
        )
        if not has_recipient:
            await logger.error("user_id or peer_id or peer_ids or domain or chat_id or user_ids is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "recipient field is required"
                }
            }

        random_id = config.get("random_id")
        if random_id in (None, ""):
            await logger.error("random_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "random_id is required"
                }
            }
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

        params: Dict[str, Any] = {
            "random_id": random_id,
            "access_token": access_token,
            "v": VK_API_VERSION,
        }

        if user_id not in (None, ""):
            try:
                params["user_id"] = int(user_id)
            except (TypeError, ValueError):
                await logger.error("user_id must be an integer")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "user_id must be an integer"
                    }
                }

        if peer_id not in (None, ""):
            try:
                params["peer_id"] = int(peer_id)
            except (TypeError, ValueError):
                await logger.error("peer_id must be an integer")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "peer_id must be an integer"
                    }
                }

        if peer_ids not in (None, ""):
            params["peer_ids"] = _normalize_comma_list(peer_ids)

        if domain not in (None, ""):
            params["domain"] = str(domain)

        if chat_id not in (None, ""):
            try:
                params["chat_id"] = int(chat_id)
            except (TypeError, ValueError):
                await logger.error("chat_id must be an integer")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "chat_id must be an integer"
                    }
                }

        if user_ids not in (None, ""):
            params["user_ids"] = _normalize_comma_list(user_ids)

        attachment = _normalize_comma_list(config.get("attachment"))
        if attachment:
            params["attachment"] = attachment

        if message not in (None, ""):
            params["message"] = str(message)
        elif not attachment:
            await logger.error("message or attachment is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "message or attachment is required"
                }
            }

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

        sticker_id = config.get("sticker_id")
        if sticker_id not in (None, ""):
            try:
                params["sticker_id"] = int(sticker_id)
            except (TypeError, ValueError):
                await logger.error("sticker_id must be an integer")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "sticker_id must be an integer"
                    }
                }

        group_id = config.get("group_id")
        if group_id not in (None, ""):
            try:
                params["group_id"] = int(group_id)
            except (TypeError, ValueError):
                await logger.error("group_id must be an integer")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "group_id must be an integer"
                    }
                }

        subscribe_id = config.get("subscribe_id")
        if subscribe_id not in (None, ""):
            try:
                params["subscribe_id"] = int(subscribe_id)
            except (TypeError, ValueError):
                await logger.error("subscribe_id must be an integer")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "subscribe_id must be an integer"
                    }
                }

        lat_value = config.get("lat")
        if lat_value not in (None, ""):
            params["lat"] = str(lat_value)

        long_value = config.get("long")
        if long_value not in (None, ""):
            params["long"] = str(long_value)

        intent_value = config.get("intent")
        if intent_value not in (None, ""):
            params["intent"] = str(intent_value)

        json_fields = {
            "keyboard": config.get("keyboard"),
            "template": config.get("template"),
            "payload": config.get("payload"),
            "content_source": config.get("content_source"),
            "forward": config.get("forward"),
        }

        for field_name, field_value in json_fields.items():
            if field_value is None:
                continue
            try:
                field_payload = _prepare_json_field(field_value)
            except (TypeError, ValueError) as exc:
                await logger.error(f"Invalid {field_name} payload: {exc}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": f"{field_name} must be an object or valid JSON string"
                    }
                }
            if field_payload:
                params[field_name] = field_payload

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

            result_payload = {
                "message_id": message_id,
                "random_id": random_id,
            }
            for key in ("peer_id", "user_id", "peer_ids", "user_ids", "chat_id", "domain"):
                if key in params:
                    result_payload[key] = params[key]

            return {
                "response": {
                    "ok": True,
                    "result": result_payload
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
