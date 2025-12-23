"""Telegram Send Voice интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any, Optional
from uuid import UUID
import io
import base64

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


class TelegramSendVoiceIntegration(BaseIntegration):
    """Интеграция для отправки голосовых сообщений в Telegram через Bot API"""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_voice",
            version="1.0.0",
            name="Telegram Send Voice",
            description="Отправка голосового сообщения (voice) в Telegram через Bot API",
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
                    "voice_url": {
                        "type": "string",
                        "title": "Voice file URL",
                        "description": "URL на файл голосового сообщения (ogg/mp3). Один из voice_url, voice_base64 или voice_file_id должен быть указан."
                    },
                    "voice_base64": {
                        "type": "string",
                        "title": "Voice file (base64)",
                        "description": "Base64-закодированное содержимое голосового файла (ogg/mp3). Один из voice_url, voice_base64 или voice_file_id должен быть указан."
                    },
                    "voice_file_id": {
                        "type": "string",
                        "title": "Existing Telegram File ID",
                        "description": "Если у вас уже есть file_id загруженного файла в Telegram, можно использовать его напрямую."
                    },
                    "caption": {"type": "string", "title": "Caption"},
                    "duration": {"type": "integer", "title": "Duration (seconds)"},
                    "filename": {"type": "string", "title": "Filename (for uploaded bytes)"}
                },
                "oneOf": [
                    {"required": ["voice_url"]},
                    {"required": ["voice_base64"]},
                    {"required": ["voice_file_id"]}
                ]
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправка по URL",
                    "config": {"chat_id": "{$user.telegram_chat_id$}", "voice_url": "https://example.com/voice.ogg"}
                },
                {
                    "title": "Отправка по base64",
                    "config": {"chat_id": "{$user.telegram_chat_id$}", "voice_base64": "<BASE64_STRING>"}
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
            return {"response": {"ok": False, "error_code": 500, "description": "python-telegram-bot library is not installed"}}

        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="telegram",
            strategy="api_key"
        )

        if not creds:
            await logger.error("Telegram credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "Telegram bot_token not found in credentials"}}

        payload = creds.get("payload", {}) if isinstance(creds, dict) else creds
        if not payload:
            payload = creds

        bot_token = payload.get("bot_token") or payload.get("token")
        if not bot_token:
            await logger.error("bot_token not found in credentials")
            return {"response": {"ok": False, "error_code": 401, "description": "bot_token not found in credentials"}}

        chat_id = config.get("chat_id")
        if not chat_id:
            await logger.error("chat_id is required")
            return {"response": {"ok": False, "error_code": 400, "description": "chat_id is required"}}

        voice_file_id = config.get("voice_file_id")
        voice_base64 = config.get("voice_base64")
        voice_url = config.get("voice_url")
        caption = config.get("caption")
        duration = config.get("duration")
        filename = config.get("filename") or "voice.ogg"

        try:
            bot = Bot(token=bot_token)

            # Если указан file_id — используем его напрямую
            if voice_file_id:
                result = await bot.send_voice(chat_id=str(chat_id), voice=str(voice_file_id), caption=caption, duration=duration)

            # Если base64 — декодируем и отправляем как файловый объект
            elif voice_base64:
                try:
                    data = base64.b64decode(voice_base64)
                except Exception as e:
                    await logger.error(f"Invalid base64 data: {e}")
                    return {"response": {"ok": False, "error_code": 400, "description": "Invalid base64 data"}}

                bio = io.BytesIO(data)
                bio.name = filename
                result = await bot.send_voice(chat_id=str(chat_id), voice=bio, caption=caption, duration=duration)

            # Если URL — загружаем и отправляем
            elif voice_url:
                # Асинхронная загрузка файла через httpx
                import httpx
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.get(voice_url)
                    resp.raise_for_status()
                    bio = io.BytesIO(resp.content)
                    bio.name = filename
                    result = await bot.send_voice(chat_id=str(chat_id), voice=bio, caption=caption, duration=duration)

            else:
                await logger.error("No voice source provided (voice_url, voice_base64 or voice_file_id required)")
                return {"response": {"ok": False, "error_code": 400, "description": "No voice source provided (voice_url, voice_base64 or voice_file_id required)"}}

            # Формируем удобный результат
            voice = getattr(result, "voice", None)
            voice_info: Optional[Dict[str, Any]] = None
            if voice:
                voice_info = {
                    "file_id": getattr(voice, "file_id", None),
                    "mime_type": getattr(voice, "mime_type", None),
                    "file_size": getattr(voice, "file_size", None),
                    "duration": getattr(voice, "duration", None)
                }

            return {"response": {"ok": True, "result": {"message_id": result.message_id, "voice": voice_info}}}

        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {"response": {"ok": False, "error_code": getattr(e, 'error_code', 500), "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
