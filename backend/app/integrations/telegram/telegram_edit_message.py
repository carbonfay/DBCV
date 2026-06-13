"""Telegram Edit Message интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    from telegram import Bot, InlineKeyboardMarkup
    from telegram.error import TelegramError
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception
    InlineKeyboardMarkup = None


class TelegramEditMessageIntegration(BaseIntegration):
    """Интеграция для редактирования сообщений в Telegram."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_edit_message",
            version="1.0.0",
            name="Telegram Edit Message",
            description="Редактирование существующего сообщения в Telegram",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "oneOf": [
                    {"required": ["chat_id", "message_id"]},
                    {"required": ["inline_message_id"]}
                ],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "message_id": {
                        "type": "integer",
                        "title": "Message ID",
                        "description": "ID сообщения для редактирования"
                    },
                    "inline_message_id": {
                        "type": "string",
                        "title": "Inline Message ID",
                        "description": "ID инлайн-сообщения (альтернатива chat_id+message_id)"
                    },
                    "text": {
                        "type": "string",
                        "title": "New Text",
                        "description": "Новый текст сообщения (обязателен, если не указан reply_markup)"
                    },
                    "parse_mode": {
                        "type": "string",
                        "title": "Parse Mode",
                        "enum": ["HTML", "Markdown", "MarkdownV2"],
                        "default": None
                    },
                    "disable_web_page_preview": {
                        "type": "boolean",
                        "title": "Disable Web Page Preview",
                        "default": False
                    },
                    "reply_markup": {
                        "type": "object",
                        "title": "Reply Markup",
                        "description": "JSON для InlineKeyboardMarkup"
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Редактировать текст сообщения",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "message_id": 12345,
                        "text": "Новый текст сообщения"
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
        Выполняет редактирование сообщения.
        """
        if not TELEGRAM_BOT_AVAILABLE:
            await logger.error("python-telegram-bot library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "python-telegram-bot library is not installed"
                }
            }

        # Получение токена
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="telegram",
            strategy="api_key"
        )
        if not creds:
            await logger.error("Telegram credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Telegram bot_token not found in credentials"
                }
            }

        payload = creds.get("payload", creds)
        bot_token = payload.get("bot_token") or payload.get("token")
        if not bot_token:
            await logger.error("bot_token not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "bot_token not found in credentials"
                }
            }

        # Параметры из конфига
        chat_id = config.get("chat_id")
        message_id = config.get("message_id")
        inline_message_id = config.get("inline_message_id")
        text = config.get("text")
        parse_mode = config.get("parse_mode")
        disable_web_page_preview = config.get("disable_web_page_preview", False)
        reply_markup = config.get("reply_markup")

        if not text and not reply_markup:
            await logger.error("Either text or reply_markup must be provided")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Either text or reply_markup must be provided"
                }
            }

        # Преобразование reply_markup
        if reply_markup and InlineKeyboardMarkup:
            try:
                reply_markup = InlineKeyboardMarkup.de_json(reply_markup, None)
            except Exception as e:
                await logger.error(f"Invalid reply_markup: {e}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": f"Invalid reply_markup: {e}"
                    }
                }

        try:
            bot = Bot(token=bot_token)
            if text is not None:
                result = await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    inline_message_id=inline_message_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    reply_markup=reply_markup
                )
            else:
                result = await bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=message_id,
                    inline_message_id=inline_message_id,
                    reply_markup=reply_markup
                )

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": result.message_id,
                        "chat": {
                            "id": result.chat.id,
                            "type": result.chat.type
                        },
                        "text": getattr(result, "text", None),
                        "date": result.date
                    }
                }
            }
        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, 'error_code', 500),
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