"""Telegram Send Audio интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception


class TelegramSendAudioIntegration(BaseIntegration):
    """Интеграция для отправки аудиофайлов в Telegram через python-telegram-bot."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_audio",
            version="1.0.0",
            name="Telegram Send Audio",
            description="Отправка аудио (файла или file_id) в Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id", "audio"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя"
                    },
                    "audio": {
                        "type": "string",
                        "title": "Audio",
                        "description": "file_id, URL или путь к файлу (если поддерживается)"
                    },
                    "caption": {
                        "type": "string",
                        "title": "Caption",
                        "description": "Подпись к аудиосообщению"
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
                    "title": "Send audio (example)",
                    "config": {
                        # Use a real chat id or a variable that resolves to it in your system
                        "chat_id": "123456789",
                        # file_id or URL of the audio; ensure this is available to the bot
                        "audio": "audio-file-id-or-url",
                        "caption": "Here is an audio"
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
        Выполняет интеграцию используя библиотеку python-telegram-bot.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
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

        # Получаем bot_token из credentials
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

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
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
        audio = config.get("audio")
        caption = config.get("caption")
        parse_mode = config.get("parse_mode")

        if not chat_id or not audio:
            await logger.error("chat_id and audio are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id and audio are required"
                }
            }

        try:
            bot = Bot(token=bot_token)
            result = await bot.send_audio(
                chat_id=str(chat_id),
                audio=audio,
                caption=str(caption) if caption else None,
                parse_mode=parse_mode if parse_mode else None
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
                        "audio": {
                            "file_id": getattr(result.audio, 'file_id', None)
                        },
                        "caption": getattr(result, 'caption', None),
                        "date": getattr(result, 'date', None)
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
