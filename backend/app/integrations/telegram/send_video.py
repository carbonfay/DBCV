"""Telegram Send Video интеграция используя python-telegram-bot библиотеку.

Этот модуль реализует интеграцию для отправки видео через Bot API
с использованием официальной библиотеки `python-telegram-bot` (async).
"""
from typing import Dict, Any, Optional
from uuid import UUID
import os

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Попытка импортировать клиент telegram — если библиотека не установлена,
# флаг `TELEGRAM_BOT_AVAILABLE` будет False и дальнейшая логика вернёт ошибку.
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception


class TelegramSendVideoIntegration(BaseIntegration):
    """Интеграция для отправки видео в Telegram через python-telegram-bot."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_video",
            version="1.0.0",
            name="Telegram Send Video",
            description="Отправка видео в Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id", "video"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "video": {
                        "type": "string",
                        "title": "Video",
                        "description": "file_id, URL или путь к файлу"
                    },
                    "caption": {
                        "type": "string",
                        "title": "Caption",
                        "description": "Подпись к видео"
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
            # Указываем рекомендуемую библиотеку и версию из SAFE_LIBRARIES.md
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправка видео по file_id",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "video": "BAACAgQAAxkDAAIB1G...",
                        "caption": "Here is a video"
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
        # Если библиотека python-telegram-bot не установлена — возвращаем ошибку
        if not TELEGRAM_BOT_AVAILABLE:
            await logger.error("python-telegram-bot library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "python-telegram-bot library is not installed"
                }
            }

        # Получаем дефолтные credentials для данного бота через резолвер
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

        # В базе credentials могут лежать либо в корне, либо в поле "payload"
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
        video = config.get("video")
        caption = config.get("caption")
        parse_mode = config.get("parse_mode")

        # Проверка обязательных параметров
        if not chat_id or not video:
            await logger.error("chat_id and video are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id and video are required"
                }
            }

        # Поддерживаем три варианта `video`: file_id, URL или локальный путь.
        # Если параметр — путь к существующему файлу, откроем его и передадим
        # файловый объект в библиотеку (не забудем закрыть в finally).
        file_obj: Optional[Any] = None
        try:
            bot = Bot(token=bot_token)

            # Если video указан как путь к локальному файлу, откроем его
            if isinstance(video, str) and os.path.exists(video):
                file_obj = open(video, "rb")
                send_video_arg = file_obj
            else:
                # В противном случае передаём либо file_id, либо URL
                send_video_arg = video

            # Выполняем асинхронную отправку видео через клиента
            result = await bot.send_video(
                chat_id=str(chat_id),
                video=send_video_arg,
                caption=str(caption) if caption is not None else None,
                parse_mode=parse_mode if parse_mode else None
            )

            # Сформируем объект video с нужными полями
            # Соберём полезные поля из ответа telegram (если они есть)
            video_obj = None
            try:
                v = getattr(result, "video", None)
                if v:
                    video_obj = {
                        "file_id": getattr(v, "file_id", None),
                        "width": getattr(v, "width", None),
                        "height": getattr(v, "height", None),
                        "duration": getattr(v, "duration", None),
                        "file_size": getattr(v, "file_size", None)
                    }
            except Exception:
                # Невозможность распарсить video не критична — вернём None
                video_obj = None

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": getattr(result, "message_id", None),
                        "chat": {
                            "id": getattr(result.chat, "id", None),
                            "type": getattr(result.chat, "type", None)
                        },
                        "video": video_obj
                    }
                }
            }

        except TelegramError as e:
            # Ошибки библиотеки telegram — логируем и возвращаем структурированную ошибку
            await logger.error(f"Telegram error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.error_code if hasattr(e, 'error_code') else 500,
                    "description": str(e)
                }
            }
        except Exception as e:
            # Любые непредвиденные ошибки — логируем и возвращаем 500
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
