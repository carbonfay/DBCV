"""Telegram Send Photo интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID
from io import BytesIO
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from telegram import Bot, InputFile
    from telegram.error import TelegramError
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception


class TelegramSendPhotoIntegration(BaseIntegration):
    """Интеграция для отправки изображений в Telegram через python-telegram-bot."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_photo",
            version="1.0.3",
            name="Telegram Send Photo",
            description="Отправка изображения (URL, file_id или файл) в Telegram через Bot API",
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
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})",
                    },
                    "photo": {
                        "type": "string",
                        "title": "Photo",
                        "description": "Ссылка на изображение, file_id Telegram или путь к файлу",
                    },
                    "caption": {
                        "type": "string",
                        "title": "Caption",
                        "description": "Подпись к изображению (необязательно)",
                    },
                    "parse_mode": {
                        "type": "string",
                        "title": "Parse Mode",
                        "enum": ["HTML", "Markdown", "MarkdownV2"],
                        "default": None,
                    },
                },
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправка изображения",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "photo": "https://example.com/image.png",
                        "caption": "Картинка из DBCV",
                    },
                }
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
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
                    "description": "python-telegram-bot library is not installed",
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="telegram",
            strategy="api_key",
        )

        if not creds:
            await logger.error("Telegram credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Telegram bot_token not found in credentials",
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
                    "description": "bot_token not found in credentials",
                }
            }

        chat_id = config.get("chat_id")
        # Telegram строго валидирует URL; уберём случайные кавычки/пробелы
        raw_photo = config.get("photo")
        photo = raw_photo.strip().strip('"').strip("'") if isinstance(raw_photo, str) else raw_photo
        caption = config.get("caption")
        parse_mode = config.get("parse_mode")

        if not chat_id or not photo:
            await logger.error("chat_id and photo are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id and photo are required",
                }
            }

        try:
            bot = Bot(token=bot_token)

            # Если передан URL, скачиваем сами и отправляем как файл,
            # чтобы избежать ошибок Telegram при загрузке.
            telegram_photo = photo
            if isinstance(photo, str) and photo.startswith(("http://", "https://")):
                try:
                    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                        resp = await client.get(photo)
                    if resp.status_code != 200:
                        raise TelegramError(f"Failed to fetch photo: HTTP {resp.status_code}")
                    content_type = resp.headers.get("Content-Type", "")
                    if not content_type.startswith("image/"):
                        raise TelegramError(f"Wrong content type: {content_type or 'unknown'}")
                    filename = photo.rsplit("/", 1)[-1] or "photo.jpg"
                    telegram_photo = InputFile(BytesIO(resp.content), filename=filename)
                except TelegramError:
                    raise
                except Exception as e:
                    raise TelegramError(f"Download error: {e}")
            result = await bot.send_photo(
                chat_id=str(chat_id),
                photo=telegram_photo,
                caption=caption if caption else None,
                parse_mode=parse_mode if parse_mode else None,
            )

            photo_sizes = []
            if getattr(result, "photo", None):
                for size in result.photo:
                    photo_sizes.append(
                        {
                            "file_id": getattr(size, "file_id", None),
                            "file_unique_id": getattr(size, "file_unique_id", None),
                            "width": getattr(size, "width", None),
                            "height": getattr(size, "height", None),
                        }
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
                        "caption": getattr(result, "caption", None),
                        "photo": photo_sizes,
                        "date": result.date,
                    },
                }
            }
        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.error_code if hasattr(e, "error_code") else 500,
                    "description": str(e),
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }

