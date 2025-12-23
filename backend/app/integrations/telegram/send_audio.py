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
    """Интеграция для отправки аудио в Telegram через python-telegram-bot."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_sendAudio",
            version="1.0.0",
            name="Telegram Send Audio",
            description="Отправка аудиофайла в Telegram через Bot API. Поддерживает MP3, M4A и другие аудиоформаты.",
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
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "audio": {
                        "type": "string",
                        "title": "Audio",
                        "description": "URL аудиофайла или file_id ранее загруженного файла"
                    },
                    "caption": {
                        "type": "string",
                        "title": "Caption",
                        "description": "Подпись к аудио (0-1024 символа)"
                    },
                    "parse_mode": {
                        "type": "string",
                        "title": "Parse Mode",
                        "description": "Режим форматирования подписи",
                        "enum": ["HTML", "Markdown", "MarkdownV2"],
                        "default": None
                    },
                    "duration": {
                        "type": "integer",
                        "title": "Duration",
                        "description": "Длительность аудио в секундах"
                    },
                    "performer": {
                        "type": "string",
                        "title": "Performer",
                        "description": "Исполнитель аудио"
                    },
                    "title": {
                        "type": "string",
                        "title": "Title",
                        "description": "Название трека"
                    },
                    "thumbnail": {
                        "type": "string",
                        "title": "Thumbnail",
                        "description": "URL миниатюры аудио (JPEG, максимум 200kB)"
                    },
                    "disable_notification": {
                        "type": "boolean",
                        "title": "Disable Notification",
                        "description": "Отправить сообщение без звука",
                        "default": False
                    },
                    "protect_content": {
                        "type": "boolean",
                        "title": "Protect Content",
                        "description": "Защитить контент от пересылки и сохранения",
                        "default": False
                    },
                    "reply_to_message_id": {
                        "type": "integer",
                        "title": "Reply to Message ID",
                        "description": "ID сообщения, на которое нужно ответить"
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправка аудио по URL",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "audio": "https://example.com/song.mp3",
                        "caption": "🎵 Моя любимая песня!",
                        "performer": "Artist Name",
                        "title": "Song Title"
                    }
                },
                {
                    "title": "Отправка аудио с форматированием",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "audio": "https://example.com/podcast.mp3",
                        "caption": "<b>Подкаст:</b> Выпуск #1",
                        "parse_mode": "HTML",
                        "duration": 3600
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
        
        # Получаем обязательные параметры из config
        chat_id = config.get("chat_id")
        audio = config.get("audio")
        
        if not chat_id or not audio:
            await logger.error("chat_id and audio are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id and audio are required"
                }
            }
        
        # Получаем опциональные параметры
        caption = config.get("caption")
        parse_mode = config.get("parse_mode")
        duration = config.get("duration")
        performer = config.get("performer")
        title = config.get("title")
        thumbnail = config.get("thumbnail")
        disable_notification = config.get("disable_notification", False)
        protect_content = config.get("protect_content", False)
        reply_to_message_id = config.get("reply_to_message_id")
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            
            # Формируем kwargs для send_audio
            kwargs = {
                "chat_id": str(chat_id),
                "audio": str(audio),
            }
            
            if caption:
                kwargs["caption"] = str(caption)
            if parse_mode:
                kwargs["parse_mode"] = parse_mode
            if duration is not None:
                kwargs["duration"] = int(duration)
            if performer:
                kwargs["performer"] = str(performer)
            if title:
                kwargs["title"] = str(title)
            if thumbnail:
                kwargs["thumbnail"] = str(thumbnail)
            if disable_notification:
                kwargs["disable_notification"] = True
            if protect_content:
                kwargs["protect_content"] = True
            if reply_to_message_id is not None:
                kwargs["reply_to_message_id"] = int(reply_to_message_id)
            
            result = await bot.send_audio(**kwargs)
            
            # Формируем ответ
            audio_info = {
                "file_id": result.audio.file_id,
                "file_unique_id": result.audio.file_unique_id,
                "duration": result.audio.duration,
            }
            
            if result.audio.file_name:
                audio_info["file_name"] = result.audio.file_name
            if result.audio.mime_type:
                audio_info["mime_type"] = result.audio.mime_type
            if result.audio.file_size:
                audio_info["file_size"] = result.audio.file_size
            if result.audio.performer:
                audio_info["performer"] = result.audio.performer
            if result.audio.title:
                audio_info["title"] = result.audio.title
            
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
                        "audio": audio_info,
                        "caption": result.caption,
                        "date": result.date.isoformat() if result.date else None
                    }
                }
            }
        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, 'error_code', 500) if hasattr(e, 'error_code') else 500,
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

