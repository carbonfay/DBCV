"""Telegram Send Video Note (кружок) интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID
import os

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

from telegram import Bot
from telegram.error import TelegramError


class TelegramSendVideoNoteIntegration(BaseIntegration):
    """Интеграция для отправки видеосообщений (кружков) в Telegram."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_video_note",
            version="1.0.0",
            name="Telegram Send Video Note",
            description="Отправка видеосообщения (кружка) в Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя"
                    },
                    "video_note": {
                        "type": "string",
                        "title": "Video Note File Path",
                        "description": "Путь к mp4 файлу видеосообщения (кружка)"
                    },
                    "video_note_file_id": {
                        "type": "string",
                        "title": "Video Note File ID",
                        "description": "file_id ранее загруженного video note"
                    },
                    "duration": {
                        "type": "number",
                        "title": "Duration",
                        "description": "Длительность видео в секундах",
                        "default": None
                    },
                    "length": {
                        "type": "number",
                        "title": "Length",
                        "description": "Ширина/высота видео (например 360)",
                        "default": None
                    },
                    "disable_notification": {
                        "type": "boolean",
                        "title": "Disable Notification",
                        "description": "Отправить без уведомления",
                        "default": False
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=22.5",
            examples=[
                {
                    "title": "Отправка video note из файла",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "video_note": "/data/videos/circle.mp4",
                        "length": 360
                    }
                },
                {
                    "title": "Отправка video note по file_id",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "video_note_file_id": "DQACAgIAAxkBAAIBQ2..."
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

        # Получаем credentials
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

        # payload с расшифрованными данными
        payload = creds.get("payload", {}) or creds
        bot_token = payload.get("bot_token") or payload.get("token")

        if not bot_token:
            await logger.error(f"bot_token not found in credentials. Keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "bot_token not found in credentials"
                }
            }

        # Параметры
        chat_id = config.get("chat_id")
        video_path = config.get("video_note")
        video_file_id = config.get("video_note_file_id")
        duration = config.get("duration")
        length = config.get("length")
        disable_notification = config.get("disable_notification", False)

        # Валидация
        if not chat_id:
            await logger.error("chat_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id is required"
                }
            }

        if not video_path and not video_file_id:
            await logger.error("Either video_note or video_note_file_id must be provided")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Either video_note or video_note_file_id must be provided"
                }
            }

        if video_path and video_file_id:
            await logger.error("Provide only one of video_note or video_note_file_id")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Provide only one of video_note or video_note_file_id"
                }
            }

        try:
            bot = Bot(token=bot_token)

            # Отправка по file_id
            if video_file_id:
                result = await bot.send_video_note(
                    chat_id=str(chat_id),
                    video_note=video_file_id,
                    duration=duration,
                    length=length,
                    disable_notification=disable_notification
                )

            # Отправка из файла
            else:
                if not os.path.exists(video_path):
                    await logger.error(f"Video file not found: {video_path}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": f"Video file not found: {video_path}"
                        }
                    }

                with open(video_path, "rb") as video_file:
                    result = await bot.send_video_note(
                        chat_id=str(chat_id),
                        video_note=video_file,
                        duration=duration,
                        length=length,
                        disable_notification=disable_notification
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
                        "video_note": {
                            "duration": result.video_note.duration,
                            "length": result.video_note.length,
                            "file_id": result.video_note.file_id,
                            "file_unique_id": result.video_note.file_unique_id
                        },
                        "date": result.date
                    }
                }
            }

        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, "error_code", 500),
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
