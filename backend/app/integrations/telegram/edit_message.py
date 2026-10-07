from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception


class TelegramEditMessageIntegration(BaseIntegration):
    """Editing messages integration in Telegram with python-telegram-bot."""
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
                "required": ["chat_id", "message_id", "text"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя"
                    },
                    "message_id": {
                        "type": "string",
                        "title": "Message ID",
                        "description": "ID сообщения для редактирования (число или переменная, например {$session.last_message_id$})"
                    },
                    "text": {
                        "type": "string",
                        "title": "New Message Text",
                        "description": "Новый текст сообщения"
                    },
                    "parse_mode": {
                        "type": "string",
                        "title": "Parse Mode",
                        "enum": ["HTML", "Markdown", "MarkdownV2"],
                        "default": None
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Редактирование сообщения",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "message_id": 123,
                        "text": "Updated text"
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
        """Выполняет интеграцию редактирования сообщения."""
        if not TELEGRAM_BOT_AVAILABLE:
            await logger.error("python-telegram-bot library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "python-telegram-bot library is not installed"
                }
            }
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
        payload = creds.get("payload", {}) or creds
        bot_token = payload.get("bot_token") or payload.get("token")
        if not bot_token:
            await logger.error(
                f"bot_token not found in credentials. Available keys: {list(payload.keys())}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "bot_token not found in credentials"
                }
            }
        chat_id = config.get("chat_id")
        message_id = config.get("message_id")
        text = config.get("text")
        parse_mode = config.get("parse_mode")

        if not chat_id or not message_id or not text:
            await logger.error("chat_id, message_id and text are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id, message_id and text are required"
                }
            }
        try:
            bot = Bot(token=bot_token)
            message = await bot.edit_message_text(
                chat_id=str(chat_id),
                message_id=int(message_id),
                text=str(text),
                parse_mode=parse_mode if parse_mode else None
            )
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "updates": [message.to_dict()],
                        "count": 1
                    }
                }
            }
        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.error_code if hasattr(e, "error_code") else 400,
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
