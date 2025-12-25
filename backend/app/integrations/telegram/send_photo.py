"""Telegram Send Photo интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any, Optional
from uuid import UUID
import os

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


class TelegramSendPhotoIntegration(BaseIntegration):
    """Интеграция для отправки фото в Telegram через python-telegram-bot."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_photo",
            version="1.0.0",
            name="Telegram Send Photo",
            description="Отправка фото в Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id", "photo"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "photo": {
                        "type": "string",
                        "title": "Photo",
                        "description": "file_id, URL или путь к файлу"
                    },
                    "caption": {
                        "type": "string",
                        "title": "Caption",
                        "description": "Подпись к фото"
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
                    "title": "Отправка фото по file_id",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "photo": "1234:ABCD...",
                        "caption": "Here is a photo"
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

        payload = creds.get("payload", {})
        if not payload:
            payload = creds

        bot_token = payload.get("bot_token") or payload.get("token")
        if not bot_token:
            await logger.error(f"bot_token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "bot_token not found in credentials"
                }
            }

        chat_id = config.get("chat_id")
        photo = config.get("photo")
        caption = config.get("caption")
        parse_mode = config.get("parse_mode")

        if not chat_id or not photo:
            await logger.error("chat_id and photo are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id and photo are required"
                }
            }

        file_obj: Optional[Any] = None
        try:
            bot = Bot(token=bot_token)

            # Если photo указан как путь к локальному файлу, откроем его
            if isinstance(photo, str) and os.path.exists(photo):
                file_obj = open(photo, "rb")
                send_photo_arg = file_obj
            else:
                send_photo_arg = photo

            result = await bot.send_photo(
                chat_id=str(chat_id),
                photo=send_photo_arg,
                caption=str(caption) if caption is not None else None,
                parse_mode=parse_mode if parse_mode else None
            )

            # Сформируем массив photo с нужными полями
            photo_list = []
            try:
                for p in getattr(result, "photo", []) or []:
                    photo_list.append({
                        "file_id": getattr(p, "file_id", None),
                        "width": getattr(p, "width", None),
                        "height": getattr(p, "height", None),
                        "file_size": getattr(p, "file_size", None)
                    })
            except Exception:
                photo_list = []

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": getattr(result, "message_id", None),
                        "chat": {
                            "id": getattr(result.chat, "id", None),
                            "type": getattr(result.chat, "type", None)
                        },
                        "photo": photo_list
                    }
                }
            }

        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
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
        finally:
            if file_obj:
                try:
                    file_obj.close()
                except Exception:
                    pass
