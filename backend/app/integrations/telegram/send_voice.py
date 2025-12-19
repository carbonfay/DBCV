"""Telegram Send Voice интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID
import base64
import io

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


class TelegramSendVoiceIntegration(BaseIntegration):
    """Интеграция для отправки голосовых сообщений в Telegram через Bot API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_voice",
            version="1.0.0",
            name="Telegram Send Voice",
            description="Отправка голосовых сообщений в Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id", "voice_content"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "voice_content": {
                        "type": "string",
                        "title": "Voice Content",
                        "description": "Содержимое голосового сообщения в base64 или URL"
                    },
                    "caption": {
                        "type": "string",
                        "title": "Caption",
                        "description": "Подпись к голосовому сообщению"
                    },
                    "parse_mode": {
                        "type": "string",
                        "title": "Parse Mode",
                        "enum": ["HTML", "Markdown", "MarkdownV2"],
                        "default": None
                    },
                    "duration": {
                        "type": "integer",
                        "title": "Duration",
                        "description": "Продолжительность аудио в секундах"
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправка голосового сообщения из base64",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "voice_content": "{$session.voice_base64$}",
                        "caption": "Голосовое сообщение"
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
        voice_content = config.get("voice_content")
        caption = config.get("caption")
        parse_mode = config.get("parse_mode")
        duration = config.get("duration")

        if not chat_id or not voice_content:
            await logger.error("chat_id and voice_content are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id and voice_content are required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            
            # Проверяем, является ли voice_content URL или base64
            if voice_content.startswith('http'):
                # Это URL, отправляем как есть
                result = await bot.send_voice(
                    chat_id=str(chat_id),
                    voice=voice_content,
                    caption=caption if caption else None,
                    parse_mode=parse_mode if parse_mode else None,
                    duration=duration if duration else None
                )
            else:
                # Это base64 содержимое, нужно конвертировать в байты
                try:
                    voice_bytes = base64.b64decode(voice_content)
                    voice_io = io.BytesIO(voice_bytes)
                    
                    result = await bot.send_voice(
                        chat_id=str(chat_id),
                        voice=voice_io,
                        caption=caption if caption else None,
                        parse_mode=parse_mode if parse_mode else None,
                        duration=duration if duration else None
                    )
                except Exception as e:
                    # Если ошибка декодирования base64, пробуем отправить как есть (может быть file_id)
                    result = await bot.send_voice(
                        chat_id=str(chat_id),
                        voice=voice_content,
                        caption=caption if caption else None,
                        parse_mode=parse_mode if parse_mode else None,
                        duration=duration if duration else None
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
                        "voice": {
                            "file_id": result.voice.file_id,
                            "file_unique_id": result.voice.file_unique_id,
                            "file_size": result.voice.file_size,
                            "duration": result.voice.duration
                        },
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

