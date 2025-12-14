"""Discord Send Photo интеграция используя discord.py библиотеку."""
from typing import Dict, Any
from uuid import UUID
import base64
import io

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord = None


class DiscordSendPhotoIntegration(BaseIntegration):
    """Интеграция для отправки фото в Discord через discord.py."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="discord_send_photo",
            version="1.0.0",
            name="Discord Send Photo",
            description="Отправка фото в Discord через Discord Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/discord.svg",
            color="#5865F2",
            config_schema={
                "type": "object",
                "required": ["channel_id", "photo_content"],
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "title": "Channel ID",
                        "description": "ID текстового канала в Discord"
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
                    "filename": {
                        "type": "string",
                        "title": "Filename",
                        "description": "Имя файла для фото (по умолчанию photo.jpg)",
                        "default": "photo.jpg"
                    }
                }
            },
            credentials_provider="discord",
            credentials_strategy="api_key",
            library_name="discord.py>=2.3.0" if DISCORD_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправка фото из base64",
                    "config": {
                        "channel_id": "{$session.discord_channel_id$}",
                        "photo_content": "{$session.photo_base64$}",
                        "caption": "Фото от пользователя",
                        "filename": "user_photo.jpg"
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
        Выполняет интеграцию используя библиотеку discord.py.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not DISCORD_AVAILABLE:
            await logger.error("discord.py library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "discord.py library is not installed"
                }
            }

        # Получаем bot_token из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="discord",
            strategy="api_key"
        )

        if not creds:
            await logger.error("Discord credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Discord bot_token not found in credentials"
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
        channel_id = config.get("channel_id")
        photo_content = config.get("photo_content")
        caption = config.get("caption", "")
        filename = config.get("filename", "photo.jpg")

        if not channel_id or not photo_content:
            await logger.error("channel_id and photo_content are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "channel_id and photo_content are required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем временный бота для отправки фото
            intents = discord.Intents.default()
            intents.message_content = True
            intents.messages = True
            intents.guilds = True
            intents.guild_messages = True

            bot = commands.Bot(command_prefix="!", intents=intents)

            @bot.event
            async def on_ready():
                try:
                    # Находим канал по ID
                    channel = bot.get_channel(int(channel_id))
                    if not channel:
                        # Пытаемся получить канал по ID (может быть частный канал)
                        channel = await bot.fetch_channel(int(channel_id))

                    if channel:
                        # Проверяем, является ли photo_content URL или base64
                        if photo_content.startswith('http'):
                            # Это URL, отправляем как есть с caption
                            if caption:
                                message = await channel.send(content=caption, embed=discord.Embed().set_image(url=photo_content))
                            else:
                                message = await channel.send(photo_content)
                            
                            result = {
                                "id": message.id,
                                "channel_id": str(message.channel.id),
                                "content": caption,
                                "author_id": str(message.author.id),
                                "timestamp": message.created_at.isoformat(),
                                "attachments": [str(attachment.url) for attachment in message.attachments]
                            }
                        else:
                            # Это base64 содержимое, нужно конвертировать в байты
                            try:
                                image_bytes = base64.b64decode(photo_content)
                                image_io = io.BytesIO(image_bytes)
                                
                                # Создаем Discord файл
                                discord_file = discord.File(image_io, filename=filename)
                                
                                # Отправляем фото с caption
                                if caption:
                                    message = await channel.send(content=caption, file=discord_file)
                                else:
                                    message = await channel.send(file=discord_file)
                                
                                result = {
                                    "id": message.id,
                                    "channel_id": str(message.channel.id),
                                    "content": caption,
                                    "author_id": str(message.author.id),
                                    "timestamp": message.created_at.isoformat(),
                                    "attachments": [str(attachment.url) for attachment in message.attachments]
                                }
                            except Exception as e:
                                # Если ошибка декодирования base64, пробуем обработать как текст
                                result = {
                                    "error": f"Could not process photo content: {str(e)}"
                                }
                    else:
                        result = {
                            "error": f"Channel with ID {channel_id} not found"
                        }
                except Exception as e:
                    result = {
                        "error": str(e)
                    }
                finally:
                    # Сохраняем результат в атрибуте бота
                    bot.sent_photo_result = result
                    await bot.close()

            # Запускаем бота с токеном
            await bot.start(bot_token, reconnect=False)

            # Ждем завершения отправки фото
            result = getattr(bot, 'sent_photo_result', None)
            if result and 'error' not in result:
                return {
                    "response": {
                        "ok": True,
                        "result": result
                    }
                }
            else:
                error_msg = result.get('error', 'Failed to send photo') if result else 'Unknown error'
                await logger.error(f"Failed to send Discord photo: {error_msg}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": error_msg
                    }
                }

        except discord.LoginFailure:
            await logger.error("Invalid Discord bot token")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Invalid Discord bot token"
                }
            }
        except discord.HTTPException as e:
            await logger.error(f"Discord HTTP error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.status,
                    "description": f"HTTP error: {e.text}"
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

