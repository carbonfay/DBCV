"""Telegram Send Photo интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID
import base64
import io

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
    InputFile = None
    TelegramError = Exception


class TelegramSendPhotoIntegration(BaseIntegration):
    """Интеграция для отправки фото в Telegram через Bot API."""

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
                "required": ["chat_id", "photo_content"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "photo_content": {
                        "type": "string",
                        "title": "Photo Content",
                        "description": "Содержимое фото в base64 или URL"
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
                    "title": "Отправка фото из base64",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "photo_content": "{$session.photo_base64$}",
                        "caption": "Фото от пользователя"
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

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
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

        # Получаем параметры из config
        chat_id = config.get("chat_id")
        photo_content = config.get("photo_content")
        caption = config.get("caption")
        parse_mode = config.get("parse_mode")

        if not chat_id or not photo_content:
            await logger.error("chat_id and photo_content are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id and photo_content are required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            
            # Проверяем, является ли photo_content URL или base64
            if photo_content.startswith('http'):
                # Это URL, отправляем как есть
                result = await bot.send_photo(
                    chat_id=str(chat_id),
                    photo=photo_content,
                    caption=caption if caption else None,
                    parse_mode=parse_mode if parse_mode else None
                )
            else:
                # Это base64 содержимое, нужно конвертировать в байты
                try:
                    image_bytes = base64.b64decode(photo_content)
                    image_io = io.BytesIO(image_bytes)
                    
                    result = await bot.send_photo(
                        chat_id=str(chat_id),
                        photo=image_io,
                        caption=caption if caption else None,
                        parse_mode=parse_mode if parse_mode else None
                    )
                except Exception as e:
                    # Если ошибка декодирования base64, пробуем отправить как есть (может быть file_id)
                    result = await bot.send_photo(
                        chat_id=str(chat_id),
                        photo=photo_content,
                        caption=caption if caption else None,
                        parse_mode=parse_mode if parse_mode else None
                    )

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": result.message_id,
                        "chat": {
                            "id": result.chat.id,
                            "type": result.chat.type
                        },
                        "photo": [
                            {
                                "file_id": photo.file_id,
                                "file_unique_id": photo.file_unique_id,
                                "file_size": photo.file_size,
                                "width": photo.width,
                                "height": photo.height
                            } for photo in result.photo
                        ],
                        "caption": result.caption,
                        "date": result.date
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

