"""Discord Send Message интеграция используя discord.py библиотеку."""
from typing import Dict, Any
from uuid import UUID

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


class DiscordSendMessageIntegration(BaseIntegration):
    """Интеграция для отправки сообщений в Discord через discord.py."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="discord_send_message",
            version="1.0.0",
            name="Discord Send Message",
            description="Отправка текстового сообщения в Discord через Discord Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/discord.svg",
            color="#5865F2",
            config_schema={
                "type": "object",
                "required": ["channel_id", "text"],
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "title": "Channel ID",
                        "description": "ID текстового канала в Discord (можно использовать переменные: {$session.discord_channel_id$})"
                    },
                    "text": {
                        "type": "string",
                        "title": "Message Text",
                        "description": "Текст сообщения для отправки в Discord"
                    }
                }
            },
            credentials_provider="discord",
            credentials_strategy="api_key",
            library_name="discord.py>=2.3.0" if DISCORD_AVAILABLE else None,
            examples=[
                {
                    "title": "Простое сообщение",
                    "config": {
                        "channel_id": "{$session.discord_channel_id$}",
                        "text": "Hello from DBCV!"
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
        text = config.get("text")

        if not channel_id or not text:
            await logger.error("channel_id and text are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "channel_id and text are required"
                }
            }

        # Создаем временный бота для отправки сообщения
        try:
            # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
            intents = discord.Intents.default()
            intents.message_content = True  # Для чтения сообщений
            intents.messages = True  # Для отправки сообщений
            intents.guilds = True  # Для доступа к гильдиям
            intents.guild_messages = True  # Для отправки сообщений в гильдиях

            bot = commands.Bot(command_prefix="!", intents=intents)

            @bot.event
            async def on_ready():
                # Находим канал по ID
                try:
                    channel = bot.get_channel(int(channel_id))
                    if not channel:
                        # Пытаемся получить канал по ID (может быть частный канал)
                        channel = await bot.fetch_channel(int(channel_id))

                    if channel:
                        # Отправляем сообщение
                        message = await channel.send(text)
                        # Сохраняем результат в атрибуте бота
                        bot.sent_message_result = {
                            "id": message.id,
                            "channel_id": str(message.channel.id),
                            "content": message.content,
                            "author_id": str(message.author.id),
                            "timestamp": message.created_at.isoformat()
                        }
                    else:
                        bot.sent_message_result = {
                            "error": f"Channel with ID {channel_id} not found"
                        }
                except Exception as e:
                    bot.sent_message_result = {
                        "error": str(e)
                    }
                finally:
                    await bot.close()

            # Запускаем бота с токеном
            await bot.start(bot_token, reconnect=False)

            # Ждем завершения отправки сообщения
            # Результат сохранен в атрибуте bot.sent_message_result
            result = getattr(bot, 'sent_message_result', None)
            if result and 'error' not in result:
                return {
                    "response": {
                        "ok": True,
                        "result": result
                    }
                }
            else:
                error_msg = result.get('error', 'Failed to send message') if result else 'Unknown error'
                await logger.error(f"Failed to send Discord message: {error_msg}")
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

