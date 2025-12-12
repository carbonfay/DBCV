"""Telegram Send Audio интеграция используя python-telegram-bot библиотеку."""
import importlib
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    telegram_module = importlib.import_module("telegram")
    telegram_error_module = importlib.import_module("telegram.error")

    Bot = getattr(telegram_module, "Bot")
    TelegramError = getattr(telegram_error_module, "TelegramError")
    TELEGRAM_BOT_AVAILABLE = True
except (ImportError, AttributeError):
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception


class TelegramSendAudioIntegration(BaseIntegration):
    """Интеграция для отправки аудио в Telegram через python-telegram-bot."""

    @staticmethod
    def _failure(description: str, error_code: int) -> Dict[str, Any]:
        return {
            "response": {
                "ok": False,
                "error_code": error_code,
                "description": description,
            }
        }

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_audio",
            version="1.0.0",
            name="Telegram Send Audio",
            description="Отправляет аудио-файл пользователю или в чат Telegram",
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
                        "description": "ID чата или пользователя (можно использовать {$user.telegram_chat_id$})",
                    },
                    "audio_file_id": {
                        "type": "string",
                        "title": "Audio File ID",
                        "description": "file_id аудио, уже загруженного в Telegram",
                    },
                    "audio_url": {
                        "type": "string",
                        "title": "Audio URL",
                        "description": "Прямая ссылка на аудио (HTTP/HTTPS) или путь в S3",
                    },
                    "caption": {
                        "type": "string",
                        "title": "Caption",
                        "description": "Подпись к аудио",
                    },
                    "parse_mode": {
                        "type": "string",
                        "title": "Parse Mode",
                        "enum": ["HTML", "Markdown", "MarkdownV2"],
                        "default": None,
                    },
                    "title": {
                        "type": "string",
                        "title": "Title",
                        "description": "Название трека",
                    },
                    "performer": {
                        "type": "string",
                        "title": "Performer",
                        "description": "Исполнитель трека",
                    },
                    "duration": {
                        "type": "integer",
                        "title": "Duration",
                        "description": "Длительность в секундах",
                        "minimum": 0,
                    },
                },
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправка аудио по URL",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "audio_url": "https://example.com/audio.mp3",
                        "caption": "Новый эпизод подкаста",
                    },
                },
                {
                    "title": "Отправка аудио по file_id",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "audio_file_id": "AwADAgADbXXXXXXXXXXXGBdh0Y",
                    },
                },
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not TELEGRAM_BOT_AVAILABLE:
            await logger.error("python-telegram-bot library is not available")
            return self._failure("python-telegram-bot library is not installed", 500)

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="telegram",
            strategy="api_key",
        )

        if not creds:
            await logger.error("Telegram credentials not found")
            return self._failure("Telegram bot_token not found in credentials", 401)

        payload = creds.get("payload") or creds
        bot_token = payload.get("bot_token") or payload.get("token")
        if not bot_token:
            await logger.error(f"bot_token not found in credentials. Available keys: {list(payload.keys())}")
            return self._failure("bot_token not found in credentials", 401)

        chat_id = config.get("chat_id")
        audio_file_id = config.get("audio_file_id")
        audio_url = config.get("audio_url")

        if not chat_id:
            await logger.error("chat_id is required")
            return self._failure("chat_id is required", 400)

        if audio_file_id and audio_url:
            await logger.error("Provide either audio_file_id or audio_url, not both")
            return self._failure("Specify only one of audio_file_id or audio_url", 400)

        audio_source: Optional[str] = audio_file_id or audio_url
        if not audio_source:
            await logger.error("audio_file_id or audio_url is required")
            return self._failure("Specify audio_file_id or audio_url", 400)

        caption = config.get("caption")
        parse_mode = config.get("parse_mode")
        title = config.get("title")
        performer = config.get("performer")
        duration = config.get("duration")
        duration_value: Optional[int] = None
        if duration is not None:
            try:
                duration_value = int(duration)
                if duration_value < 0:
                    raise ValueError
            except (TypeError, ValueError):
                await logger.error("duration must be a non-negative integer")
                return self._failure("duration must be a non-negative integer", 400)

        try:
            bot = Bot(token=bot_token)
            send_kwargs = {
                "chat_id": str(chat_id),
                "audio": str(audio_source),
                "caption": str(caption) if caption else None,
                "parse_mode": parse_mode if caption and parse_mode else None,
                "title": str(title) if title else None,
                "performer": str(performer) if performer else None,
                "duration": duration_value,
            }
            send_kwargs = {key: value for key, value in send_kwargs.items() if value is not None}
            result = await bot.send_audio(
                **send_kwargs,
            )

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": result.message_id,
                        "chat": {
                            "id": result.chat.id,
                            "type": result.chat.type,
                        },
                        "audio": {
                            "file_id": result.audio.file_id if result.audio else None,
                            "duration": result.audio.duration if result.audio else None,
                            "mime_type": result.audio.mime_type if result.audio else None,
                            "file_size": result.audio.file_size if result.audio else None,
                        },
                        "caption": result.caption,
                        "date": result.date.isoformat() if result.date else None,
                    },
                }
            }
        except TelegramError as exc:
            await logger.error(f"Telegram error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": exc.error_code if hasattr(exc, "error_code") else 500,
                    "description": str(exc),
                }
            }
        except Exception as exc:
            await logger.error(f"Unexpected error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(exc),
                }
            }

